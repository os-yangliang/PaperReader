"""
论文阅读多智能体系统 - FastAPI 后端 API
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import json
import asyncio
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.coordinator import PaperReaderCoordinator
from services.service_manager import get_llm_service, get_vector_store, get_history_store
from config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB, CORS_ALLOW_ORIGINS

app = FastAPI(
    title="论文阅读助手 API",
    description="基于 LangChain + LangGraph 构建的智能论文分析与问答系统",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
class AppState:
    def __init__(self):
        self.coordinator: Optional[PaperReaderCoordinator] = None
        self.current_summary: str = ""
        self.current_structure: str = ""
        self.is_document_loaded: bool = False
        self.document_info: dict = {}
        self.init_error: str = ""
        self.current_history_id: Optional[str] = None
        self.current_document_id: Optional[str] = None
        
        # 使用服务管理器获取历史记录服务
        try:
            self.history_store = get_history_store()
        except Exception as e:
            print(f"[WARNING] 历史记录服务初始化失败: {e}")
            self.history_store = None

    def ensure_coordinator(self):
        """确保协调器已初始化（使用依赖注入）"""
        if self.coordinator is None:
            try:
                # 使用服务管理器获取共享服务实例
                llm_service = get_llm_service()
                vector_store = get_vector_store()
                
                # 创建协调器，传入共享服务
                self.coordinator = PaperReaderCoordinator(
                    llm_service=llm_service,
                    vector_store=vector_store
                )
                self.init_error = ""
            except ValueError as e:
                self.init_error = str(e)
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                self.init_error = f"系统初始化失败: {str(e)}"
                raise HTTPException(status_code=500, detail=self.init_error)
    
    def save_to_history(self, doc_info: dict, structure: str, summary: str) -> Optional[str]:
        """保存分析记录到历史（持久化到 ChromaDB）"""
        print(f"[DEBUG] save_to_history 被调用, history_store={self.history_store is not None}")
        print(f"[DEBUG] doc_info={doc_info}")
        
        if not self.history_store:
            print("[WARNING] history_store 未初始化，无法保存历史记录")
            return None
        
        try:
            document_id = doc_info.get("document_id", "")
            print(f"[DEBUG] 准备保存历史记录, document_id={document_id}")
            
            history_id = self.history_store.add_analysis_history(
                document_id=document_id,
                filename=doc_info.get("filename", "未知文件"),
                title=doc_info.get("title", ""),
                file_type=doc_info.get("file_type", ""),
                page_count=doc_info.get("page_count", 0),
                word_count=doc_info.get("word_count", 0),
                processing_time=doc_info.get("processing_time", 0),
                structure=structure,
                summary=summary
            )
            self.current_history_id = history_id
            self.current_document_id = document_id
            print(f"[DEBUG] 历史记录保存成功, history_id={history_id}")
            return history_id
        except Exception as e:
            import traceback
            print(f"[ERROR] 保存历史记录失败: {e}")
            print(f"[ERROR] 详细错误: {traceback.format_exc()}")
            return None
    
    def save_chat_message(self, role: str, content: str, source_chunks: List[str] = None):
        """保存对话消息到历史"""
        if not self.history_store or not self.current_document_id:
            return
        
        try:
            self.history_store.add_chat_message(
                document_id=self.current_document_id,
                role=role,
                content=content,
                source_chunks=source_chunks
            )
        except Exception as e:
            print(f"[ERROR] 保存对话消息失败: {e}")

state = AppState()


# 请求/响应模型
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    success: bool
    answer: str
    source_chunks: List[str] = []

class AnalysisResponse(BaseModel):
    success: bool
    status: str
    document_info: dict = {}
    structure: str = ""
    summary: str = ""
    error: str = ""

class DocumentInfoResponse(BaseModel):
    is_loaded: bool
    info: dict = {}
    structure: str = ""
    summary: str = ""

class HistoryItem(BaseModel):
    id: str
    filename: str
    title: str = ""
    file_type: str = ""
    page_count: int = 0
    word_count: int = 0
    processing_time: float = 0
    analyzed_at: str = ""

class HistoryListResponse(BaseModel):
    history: List[HistoryItem] = []
    current_id: Optional[str] = None

class ChatHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str = ""
    source_chunks: List[str] = []


@app.get("/")
async def root():
    return {"message": "论文阅读助手 API", "version": "2.0.0"}


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "is_document_loaded": state.is_document_loaded,
        "has_coordinator": state.coordinator is not None
    }


@app.get("/api/document", response_model=DocumentInfoResponse)
async def get_document_info():
    """获取当前文档信息"""
    return DocumentInfoResponse(
        is_loaded=state.is_document_loaded,
        info=state.document_info,
        structure=state.current_structure,
        summary=state.current_summary
    )


@app.post("/api/upload", response_model=AnalysisResponse)
async def upload_and_analyze(file: UploadFile = File(...)):
    """上传并分析论文"""
    
    try:
        # 检查文件类型
        filename = file.filename
        _, ext = os.path.splitext(filename)
        
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {ext}，请上传 PDF 或 Word 文档"
            )
        
        state.ensure_coordinator()
        
        # 读取文件内容
        file_bytes = await file.read()

        # 简单的大小限制（避免超大文件导致内存/磁盘压力）
        max_bytes = int(MAX_FILE_SIZE_MB * 1024 * 1024)
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大：{len(file_bytes) / (1024 * 1024):.2f}MB，最大支持 {MAX_FILE_SIZE_MB}MB"
            )
        
        # 处理文档
        result = state.coordinator.process_document(
            file_bytes=file_bytes,
            filename=filename
        )
        
        if result.success:
            state.is_document_loaded = True
            state.current_summary = result.summary
            state.current_structure = result.structure_info
            
            # 获取文档信息
            doc_info = state.coordinator.get_current_document_info()
            if doc_info:
                state.document_info = {
                    "filename": doc_info['filename'],
                    "title": doc_info['title'],
                    "file_type": doc_info['file_type'].upper(),
                    "page_count": doc_info['page_count'],
                    "word_count": doc_info['word_count'],
                    "document_id": doc_info['document_id'],
                    "processing_time": result.total_time
                }
            
            # 保存到历史记录（持久化到 ChromaDB）
            state.save_to_history(state.document_info, result.structure_info, result.summary)
            
            return AnalysisResponse(
                success=True,
                status=f"文档解析完成！标题: {result.paper_title}",
                document_info=state.document_info,
                structure=result.structure_info,
                summary=result.summary
            )
        else:
            state.is_document_loaded = False
            return AnalysisResponse(
                success=False,
                status="处理失败",
                error=result.error_message
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] 文档分析失败: {error_detail}")
        return AnalysisResponse(
            success=False,
            status="处理失败",
            error=str(e)
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天问答"""
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    if not state.is_document_loaded:
        raise HTTPException(status_code=400, detail="请先上传并解析论文文档")
    
    state.ensure_coordinator()
    
    # 保存用户消息
    state.save_chat_message("user", request.message)
    
    # 获取回答
    result = state.coordinator.ask_question(request.message)
    
    if result.success:
        # 保存助手回复
        state.save_chat_message("assistant", result.answer, result.source_chunks[:3] if result.source_chunks else [])
        
        return ChatResponse(
            success=True,
            answer=result.answer,
            source_chunks=result.source_chunks[:3] if result.source_chunks else []
        )
    else:
        return ChatResponse(
            success=False,
            answer=f"回答失败: {result.error_message}",
            source_chunks=[]
        )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天问答"""
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    if not state.is_document_loaded:
        raise HTTPException(status_code=400, detail="请先上传并解析论文文档")
    
    state.ensure_coordinator()
    
    # 保存用户消息
    state.save_chat_message("user", request.message)
    
    async def generate():
        full_response = ""
        try:
            for chunk in state.coordinator.ask_question_stream(request.message):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
            
            # 保存完整的助手回复
            state.save_chat_message("assistant", full_response)
            
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/suggestions")
async def get_suggestions():
    """获取建议问题"""
    if not state.is_document_loaded:
        return {"questions": []}
    
    state.ensure_coordinator()
    questions = state.coordinator.get_suggested_questions()
    
    return {"questions": questions}


@app.post("/api/clear")
async def clear_chat():
    """清除聊天历史"""
    if state.coordinator:
        state.coordinator.clear_chat_history()
    # 同时清除持久化的对话记录
    if state.history_store and state.current_document_id:
        state.history_store.clear_chat_history(state.current_document_id)
    return {"success": True}


@app.delete("/api/document")
async def clear_document():
    """清除当前文档"""
    state.is_document_loaded = False
    state.current_summary = ""
    state.current_structure = ""
    state.document_info = {}
    state.current_history_id = None
    state.current_document_id = None
    if state.coordinator:
        state.coordinator.clear_chat_history()
    return {"success": True}


@app.get("/api/history", response_model=HistoryListResponse)
async def get_analysis_history():
    """获取分析历史记录列表（从 ChromaDB 读取）"""
    if not state.history_store:
        return HistoryListResponse(history=[], current_id=None)
    
    try:
        history_list = state.history_store.get_analysis_history_list()
        history_items = [
            HistoryItem(
                id=h["id"],
                filename=h["filename"],
                title=h.get("title", ""),
                file_type=h.get("file_type", ""),
                page_count=h.get("page_count", 0),
                word_count=h.get("word_count", 0),
                processing_time=h.get("processing_time", 0),
                analyzed_at=h.get("analyzed_at", "")
            )
            for h in history_list
        ]
        return HistoryListResponse(
            history=history_items,
            current_id=state.current_history_id
        )
    except Exception as e:
        print(f"[ERROR] 获取历史记录失败: {e}")
        return HistoryListResponse(history=[], current_id=None)


@app.get("/api/history/{history_id}")
async def get_history_detail(history_id: str):
    """获取指定历史记录详情"""
    if not state.history_store:
        raise HTTPException(status_code=500, detail="历史记录服务不可用")
    
    item = state.history_store.get_analysis_history_detail(history_id)
    if not item:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return item


@app.post("/api/history/{history_id}/load")
async def load_history_item(history_id: str):
    """加载历史记录到当前状态"""
    if not state.history_store:
        raise HTTPException(status_code=500, detail="历史记录服务不可用")
    
    item = state.history_store.get_analysis_history_detail(history_id)
    if not item:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    
    # 更新当前状态
    state.current_summary = item.get("summary", "")
    state.current_structure = item.get("structure", "")
    state.is_document_loaded = True
    state.current_history_id = history_id
    state.current_document_id = item.get("document_id", "")
    state.document_info = {
        "filename": item["filename"],
        "title": item.get("title", ""),
        "file_type": item.get("file_type", ""),
        "page_count": item.get("page_count", 0),
        "word_count": item.get("word_count", 0),
        "processing_time": item.get("processing_time", 0),
        "document_id": item.get("document_id", "")
    }
    
    # 尝试加载向量存储（用于问答）
    if state.coordinator and state.current_document_id:
        try:
            # 尝试加载已有的向量集合
            loaded = state.coordinator.vector_store.load_collection(state.current_document_id)
            if loaded:
                # 设置 QA Agent 的上下文
                state.coordinator.qa_agent.set_document_context(
                    doc_id=state.current_document_id,
                    paper_title=item.get("title", ""),
                    paper_summary=state.current_summary[:500]
                )
        except Exception as e:
            print(f"[WARNING] 加载向量集合失败: {e}")
    
    # 获取该文档的对话历史
    chat_history = []
    if state.history_store:
        chat_history = state.history_store.get_chat_history(state.current_document_id)
    
    return {
        "success": True,
        "document_info": state.document_info,
        "structure": state.current_structure,
        "summary": state.current_summary,
        "chat_history": chat_history
    }


@app.delete("/api/history/{history_id}")
async def delete_history_item(history_id: str):
    """删除指定历史记录"""
    if not state.history_store:
        raise HTTPException(status_code=500, detail="历史记录服务不可用")
    
    # 获取记录详情以获取 document_id
    item = state.history_store.get_analysis_history_detail(history_id)
    if not item:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    
    # 删除历史记录（同时会删除相关对话）
    success = state.history_store.delete_analysis_history(history_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    # 尝试删除向量集合
    if state.coordinator and item.get("document_id"):
        try:
            state.coordinator.vector_store.delete_collection(item["document_id"])
        except Exception as e:
            print(f"[WARNING] 删除向量集合失败: {e}")
    
    # 如果删除的是当前记录，清除当前状态
    if state.current_history_id == history_id:
        state.current_history_id = None
        state.current_document_id = None
        state.is_document_loaded = False
        state.current_summary = ""
        state.current_structure = ""
        state.document_info = {}
    
    return {"success": True}


@app.get("/api/history/{history_id}/chat")
async def get_history_chat(history_id: str):
    """获取指定历史记录的对话历史"""
    if not state.history_store:
        return {"chat_history": []}
    
    # 从 history_id 提取 document_id
    item = state.history_store.get_analysis_history_detail(history_id)
    if not item:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    
    document_id = item.get("document_id", "")
    chat_history = state.history_store.get_chat_history(document_id)
    
    return {"chat_history": chat_history}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

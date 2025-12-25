"""
问答 Agent - 基于 RAG 的论文问答
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import time

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from services.llm_service import LLMService
from services.vector_store import VectorStoreService
from prompts.templates import QA_PROMPT, CHAT_SYSTEM_PROMPT


@dataclass
class QAResult:
    """问答结果"""
    success: bool
    answer: str = ""
    source_chunks: List[str] = None
    error_message: str = ""
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.source_chunks is None:
            self.source_chunks = []


class QAAgent:
    """问答 Agent - 基于 RAG 回答论文相关问题"""
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        vector_store: Optional[VectorStoreService] = None
    ):
        self.llm_service = llm_service or LLMService()
        self.vector_store = vector_store or VectorStoreService()
        
        # 聊天历史
        self.chat_history: List[Dict[str, str]] = []
        
        # 当前文档信息
        self.current_doc_id: Optional[str] = None
        self.current_paper_title: str = ""
        self.current_paper_summary: str = ""
    
    def set_document_context(
        self,
        doc_id: str,
        paper_title: str = "",
        paper_summary: str = ""
    ) -> bool:
        """
        设置当前文档上下文
        
        Args:
            doc_id: 文档 ID
            paper_title: 论文标题
            paper_summary: 论文摘要
            
        Returns:
            bool: 是否成功设置
        """
        try:
            # 加载向量集合
            success = self.vector_store.load_collection(doc_id)
            if success:
                self.current_doc_id = doc_id
                self.current_paper_title = paper_title
                self.current_paper_summary = paper_summary
                self.chat_history = []  # 重置聊天历史
                return True
            return False
        except Exception:
            return False
    
    def ask(
        self,
        question: str,
        top_k: int = 5,
        use_history: bool = True
    ) -> QAResult:
        """
        回答问题
        
        Args:
            question: 用户问题
            top_k: 检索的相关文档数量
            use_history: 是否使用聊天历史
            
        Returns:
            QAResult: 问答结果
        """
        start_time = time.time()
        
        if self.current_doc_id is None:
            return QAResult(
                success=False,
                error_message="请先上传并解析论文文档"
            )
        
        try:
            # 检索相关内容
            relevant_docs = self.vector_store.similarity_search(question, k=top_k)
            
            # 构建上下文
            context = self._build_context(relevant_docs)
            source_chunks = [doc.page_content[:200] + "..." for doc in relevant_docs]
            
            # 构建系统提示
            system_prompt = self._build_system_prompt()
            
            # 准备聊天历史
            history = self.chat_history if use_history else None
            
            # 构建完整问题（包含上下文）
            full_prompt = QA_PROMPT.format(context=context, question=question)
            
            # 调用 LLM
            answer = self.llm_service.chat_sync(
                user_message=full_prompt,
                system_prompt=system_prompt,
                chat_history=history
            )
            
            # 更新聊天历史
            if use_history:
                self.chat_history.append({"role": "user", "content": question})
                self.chat_history.append({"role": "assistant", "content": answer})
                
                # 限制历史长度
                if len(self.chat_history) > 20:
                    self.chat_history = self.chat_history[-20:]
            
            processing_time = time.time() - start_time
            
            return QAResult(
                success=True,
                answer=answer,
                source_chunks=source_chunks,
                processing_time=processing_time
            )
            
        except Exception as e:
            return QAResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def ask_async(
        self,
        question: str,
        top_k: int = 5,
        use_history: bool = True
    ) -> QAResult:
        """异步回答问题"""
        start_time = time.time()
        
        if self.current_doc_id is None:
            return QAResult(
                success=False,
                error_message="请先上传并解析论文文档"
            )
        
        try:
            relevant_docs = self.vector_store.similarity_search(question, k=top_k)
            context = self._build_context(relevant_docs)
            source_chunks = [doc.page_content[:200] + "..." for doc in relevant_docs]
            
            system_prompt = self._build_system_prompt()
            history = self.chat_history if use_history else None
            full_prompt = QA_PROMPT.format(context=context, question=question)
            
            answer = await self.llm_service.chat(
                user_message=full_prompt,
                system_prompt=system_prompt,
                chat_history=history
            )
            
            if use_history:
                self.chat_history.append({"role": "user", "content": question})
                self.chat_history.append({"role": "assistant", "content": answer})
                if len(self.chat_history) > 20:
                    self.chat_history = self.chat_history[-20:]
            
            return QAResult(
                success=True,
                answer=answer,
                source_chunks=source_chunks,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            return QAResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def ask_stream(
        self,
        question: str,
        top_k: int = 5
    ):
        """
        流式回答问题
        
        Args:
            question: 用户问题
            top_k: 检索的相关文档数量
            
        Yields:
            str: 流式输出的回答片段
        """
        if self.current_doc_id is None:
            yield "请先上传并解析论文文档"
            return
        
        try:
            # 检索相关内容
            relevant_docs = self.vector_store.similarity_search(question, k=top_k)
            context = self._build_context(relevant_docs)
            
            # 构建完整 prompt
            system_prompt = self._build_system_prompt()
            full_prompt = QA_PROMPT.format(context=context, question=question)
            
            # 流式生成
            full_answer = ""
            for chunk in self.llm_service.stream_chat(
                user_message=full_prompt,
                system_prompt=system_prompt,
                chat_history=self.chat_history
            ):
                full_answer += chunk
                yield chunk
            
            # 更新聊天历史
            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": full_answer})
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
                
        except Exception as e:
            yield f"回答问题时出错: {str(e)}"
    
    def _build_context(self, documents: List[Document]) -> str:
        """构建上下文"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[片段 {i}]\n{doc.page_content}")
        return "\n\n".join(context_parts)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return CHAT_SYSTEM_PROMPT.format(
            paper_title=self.current_paper_title or "未知标题",
            paper_summary=self.current_paper_summary[:1000] if self.current_paper_summary else "暂无摘要"
        )
    
    def clear_history(self) -> None:
        """清除聊天历史"""
        self.chat_history = []
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """获取聊天历史"""
        return self.chat_history.copy()
    
    def get_suggested_questions(self) -> List[str]:
        """获取建议问题列表"""
        return [
            "这篇论文的主要研究问题是什么？",
            "论文使用了什么方法来解决问题？",
            "实验结果如何？有什么重要发现？",
            "这篇论文的创新点是什么？",
            "论文有什么局限性或不足？",
            "作者提出了哪些未来研究方向？",
            "论文中使用了哪些数据集？",
            "与其他方法相比，这个方法有什么优势？"
        ]

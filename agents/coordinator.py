"""
协调 Agent - 使用 LangGraph 管理多智能体工作流
"""
from typing import TypedDict, Optional, List, Dict, Any, Literal
from dataclasses import dataclass, field
import time

from langgraph.graph import StateGraph, END

from services.document_parser import ParsedDocument
from services.llm_service import LLMService
from services.vector_store import VectorStoreService
from agents.parser_agent import ParserAgent, ParserResult
from agents.summarizer_agent import SummarizerAgent, SummaryResult
from agents.qa_agent import QAAgent, QAResult


class PaperReaderState(TypedDict):
    """论文阅读系统状态"""
    # 输入
    file_path: Optional[str]
    file_bytes: Optional[bytes]
    filename: Optional[str]
    user_question: Optional[str]
    
    # 处理状态
    current_stage: str
    error_message: Optional[str]
    
    # 解析结果
    document_id: Optional[str]
    parsed_doc: Optional[ParsedDocument]
    structure_info: Optional[str]
    
    # 摘要结果
    summary: Optional[str]
    keywords: Optional[str]
    
    # 问答结果
    qa_answer: Optional[str]
    source_chunks: List[str]
    
    # 统计信息
    processing_times: Dict[str, float]


@dataclass
class ProcessingResult:
    """处理结果汇总"""
    success: bool
    stage: str
    document_id: str = ""
    paper_title: str = ""
    structure_info: str = ""
    summary: str = ""
    keywords: str = ""
    qa_answer: str = ""
    source_chunks: List[str] = field(default_factory=list)
    error_message: str = ""
    total_time: float = 0.0
    stage_times: Dict[str, float] = field(default_factory=dict)


class PaperReaderCoordinator:
    """
    论文阅读协调器 - 管理多智能体工作流
    
    工作流程:
    1. 文档上传 -> 解析 Agent 处理
    2. 解析完成 -> 摘要 Agent 生成分析报告
    3. 用户提问 -> 问答 Agent 回答
    """
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        vector_store: Optional[VectorStoreService] = None
    ):
        # 初始化共享服务
        try:
            self.llm_service = llm_service or LLMService()
        except ValueError as e:
            # API Key 未配置等错误
            raise ValueError(f"LLM 服务初始化失败: {str(e)}")
        
        try:
            self.vector_store = vector_store or VectorStoreService()
        except Exception as e:
            raise ValueError(f"向量存储服务初始化失败: {str(e)}")
        
        # 初始化各个 Agent
        self.parser_agent = ParserAgent(
            vector_store=self.vector_store,
            llm_service=self.llm_service
        )
        self.summarizer_agent = SummarizerAgent(llm_service=self.llm_service)
        self.qa_agent = QAAgent(
            llm_service=self.llm_service,
            vector_store=self.vector_store
        )
        
        # 当前状态
        self.current_state: Optional[PaperReaderState] = None
        
        # 构建工作流图
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建 LangGraph 工作流"""
        # 创建状态图
        workflow = StateGraph(PaperReaderState)
        
        # 添加节点
        workflow.add_node("parse", self._parse_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("qa", self._qa_node)
        workflow.add_node("error", self._error_node)
        
        # 设置入口点
        workflow.set_entry_point("parse")
        
        # 添加边
        workflow.add_conditional_edges(
            "parse",
            self._route_after_parse,
            {
                "summarize": "summarize",
                "error": "error"
            }
        )
        
        workflow.add_conditional_edges(
            "summarize",
            self._route_after_summarize,
            {
                "end": END,
                "error": "error"
            }
        )
        
        workflow.add_edge("qa", END)
        workflow.add_edge("error", END)
        
        return workflow.compile()
    
    def _parse_node(self, state: PaperReaderState) -> PaperReaderState:
        """解析节点"""
        start_time = time.time()
        
        try:
            if state.get("file_bytes") and state.get("filename"):
                # 从字节流解析
                result = self.parser_agent.parse_document_from_bytes(
                    state["file_bytes"],
                    state["filename"]
                )
            elif state.get("file_path"):
                # 从文件路径解析
                result = self.parser_agent.parse_document(state["file_path"])
            else:
                return {
                    **state,
                    "current_stage": "error",
                    "error_message": "未提供文件"
                }
            
            if result.success:
                processing_times = state.get("processing_times", {})
                processing_times["parse"] = time.time() - start_time
                
                return {
                    **state,
                    "current_stage": "parsed",
                    "document_id": result.document_id,
                    "parsed_doc": result.parsed_doc,
                    "structure_info": result.structure_info,
                    "processing_times": processing_times
                }
            else:
                return {
                    **state,
                    "current_stage": "error",
                    "error_message": result.error_message
                }
                
        except Exception as e:
            return {
                **state,
                "current_stage": "error",
                "error_message": str(e)
            }
    
    def _summarize_node(self, state: PaperReaderState) -> PaperReaderState:
        """摘要节点"""
        start_time = time.time()
        
        try:
            parsed_doc = state.get("parsed_doc")
            if not parsed_doc:
                return {
                    **state,
                    "current_stage": "error",
                    "error_message": "缺少解析后的文档"
                }
            
            result = self.summarizer_agent.generate_summary(parsed_doc)
            
            processing_times = state.get("processing_times", {})
            processing_times["summarize"] = time.time() - start_time
            
            if result.success:
                return {
                    **state,
                    "current_stage": "summarized",
                    "summary": result.summary,
                    "keywords": result.keywords,
                    "processing_times": processing_times
                }
            else:
                return {
                    **state,
                    "current_stage": "error",
                    "error_message": result.error_message,
                    "processing_times": processing_times
                }
                
        except Exception as e:
            return {
                **state,
                "current_stage": "error",
                "error_message": str(e)
            }
    
    def _qa_node(self, state: PaperReaderState) -> PaperReaderState:
        """问答节点"""
        start_time = time.time()
        
        try:
            question = state.get("user_question")
            if not question:
                return {
                    **state,
                    "current_stage": "error",
                    "error_message": "未提供问题"
                }
            
            result = self.qa_agent.ask(question)
            
            processing_times = state.get("processing_times", {})
            processing_times["qa"] = time.time() - start_time
            
            if result.success:
                return {
                    **state,
                    "current_stage": "answered",
                    "qa_answer": result.answer,
                    "source_chunks": result.source_chunks,
                    "processing_times": processing_times
                }
            else:
                return {
                    **state,
                    "current_stage": "error",
                    "error_message": result.error_message,
                    "processing_times": processing_times
                }
                
        except Exception as e:
            return {
                **state,
                "current_stage": "error",
                "error_message": str(e)
            }
    
    def _error_node(self, state: PaperReaderState) -> PaperReaderState:
        """错误处理节点"""
        return {
            **state,
            "current_stage": "failed"
        }
    
    def _route_after_parse(self, state: PaperReaderState) -> Literal["summarize", "error"]:
        """解析后的路由决策"""
        if state.get("current_stage") == "parsed":
            return "summarize"
        return "error"
    
    def _route_after_summarize(self, state: PaperReaderState) -> Literal["end", "error"]:
        """摘要后的路由决策"""
        if state.get("current_stage") == "summarized":
            return "end"
        return "error"
    
    def process_document(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> ProcessingResult:
        """
        处理文档（完整流程：解析 + 摘要）
        
        Args:
            file_path: 文件路径
            file_bytes: 文件字节流
            filename: 文件名
            
        Returns:
            ProcessingResult: 处理结果
        """
        start_time = time.time()
        
        # 初始化状态
        initial_state: PaperReaderState = {
            "file_path": file_path,
            "file_bytes": file_bytes,
            "filename": filename,
            "user_question": None,
            "current_stage": "start",
            "error_message": None,
            "document_id": None,
            "parsed_doc": None,
            "structure_info": None,
            "summary": None,
            "keywords": None,
            "qa_answer": None,
            "source_chunks": [],
            "processing_times": {}
        }
        
        # 运行工作流
        try:
            final_state = self.workflow.invoke(initial_state)
            self.current_state = final_state
            
            # 设置问答 Agent 的文档上下文
            if final_state.get("document_id"):
                parsed_doc = final_state.get("parsed_doc")
                self.qa_agent.set_document_context(
                    doc_id=final_state["document_id"],
                    paper_title=parsed_doc.title if parsed_doc else "",
                    paper_summary=final_state.get("summary", "")[:500]
                )
            
            total_time = time.time() - start_time
            
            if final_state.get("current_stage") in ["summarized", "answered"]:
                parsed_doc = final_state.get("parsed_doc")
                return ProcessingResult(
                    success=True,
                    stage=final_state["current_stage"],
                    document_id=final_state.get("document_id", ""),
                    paper_title=parsed_doc.title if parsed_doc else "",
                    structure_info=final_state.get("structure_info", ""),
                    summary=final_state.get("summary", ""),
                    keywords=final_state.get("keywords", ""),
                    total_time=total_time,
                    stage_times=final_state.get("processing_times", {})
                )
            else:
                return ProcessingResult(
                    success=False,
                    stage=final_state.get("current_stage", "unknown"),
                    error_message=final_state.get("error_message", "未知错误"),
                    total_time=total_time
                )
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                stage="exception",
                error_message=str(e),
                total_time=time.time() - start_time
            )
    
    def ask_question(self, question: str) -> QAResult:
        """
        回答问题（使用已解析的文档）
        
        Args:
            question: 用户问题
            
        Returns:
            QAResult: 问答结果
        """
        return self.qa_agent.ask(question)
    
    def ask_question_stream(self, question: str):
        """
        流式回答问题
        
        Args:
            question: 用户问题
            
        Yields:
            str: 流式输出的回答片段
        """
        yield from self.qa_agent.ask_stream(question)
    
    def get_suggested_questions(self) -> List[str]:
        """获取建议问题"""
        return self.qa_agent.get_suggested_questions()
    
    def clear_chat_history(self) -> None:
        """清除聊天历史"""
        self.qa_agent.clear_history()
    
    def get_current_document_info(self) -> Optional[Dict[str, Any]]:
        """获取当前文档信息"""
        if self.current_state and self.current_state.get("parsed_doc"):
            parsed_doc = self.current_state["parsed_doc"]
            return {
                "document_id": self.current_state.get("document_id"),
                "filename": parsed_doc.filename,
                "title": parsed_doc.title,
                "page_count": parsed_doc.page_count,
                "word_count": parsed_doc.word_count,
                "file_type": parsed_doc.file_type
            }
        return None

"""
文档解析 Agent - 负责解析和预处理论文文档
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import time

from services.document_parser import DocumentParser, ParsedDocument
from services.vector_store import VectorStoreService
from services.llm_service import LLMService
from prompts.templates import STRUCTURE_ANALYSIS_PROMPT


@dataclass
class ParserResult:
    """解析结果"""
    success: bool
    document_id: str
    parsed_doc: Optional[ParsedDocument] = None
    structure_info: str = ""
    error_message: str = ""
    processing_time: float = 0.0


class ParserAgent:
    """文档解析 Agent"""
    
    def __init__(
        self,
        vector_store: VectorStoreService,
        llm_service: LLMService,
        document_parser: Optional[DocumentParser] = None
    ):
        """
        初始化解析 Agent
        
        Args:
            vector_store: 向量存储服务（必需）
            llm_service: LLM 服务（必需）
            document_parser: 文档解析器（可选，默认创建新实例）
        """
        self.document_parser = document_parser or DocumentParser()
        self.vector_store = vector_store
        self.llm_service = llm_service
    
    def _generate_document_id(self, filename: str, content: str) -> str:
        """生成文档唯一ID"""
        hash_input = f"{filename}_{len(content)}_{content[:1000]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def parse_document(self, file_path: str) -> ParserResult:
        """
        解析文档文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            ParserResult: 解析结果
        """
        start_time = time.time()
        
        try:
            # 解析文档
            parsed_doc = self.document_parser.parse(file_path)
            
            # 生成文档ID
            doc_id = self._generate_document_id(parsed_doc.filename, parsed_doc.content)
            
            # 分析文档结构
            structure_info = self._analyze_structure(parsed_doc)
            
            # 将文档内容存入向量数据库
            self._store_document(doc_id, parsed_doc)
            
            processing_time = time.time() - start_time
            
            return ParserResult(
                success=True,
                document_id=doc_id,
                parsed_doc=parsed_doc,
                structure_info=structure_info,
                processing_time=processing_time
            )
            
        except Exception as e:
            return ParserResult(
                success=False,
                document_id="",
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def parse_document_from_bytes(
        self,
        file_bytes: bytes,
        filename: str
    ) -> ParserResult:
        """
        从字节流解析文档（用于文件上传）
        
        Args:
            file_bytes: 文件字节流
            filename: 文件名
            
        Returns:
            ParserResult: 解析结果
        """
        start_time = time.time()
        
        try:
            # 解析文档
            parsed_doc = self.document_parser.parse_from_bytes(file_bytes, filename)
            
            # 生成文档ID
            doc_id = self._generate_document_id(parsed_doc.filename, parsed_doc.content)
            
            # 分析文档结构
            structure_info = self._analyze_structure(parsed_doc)
            
            # 将文档内容存入向量数据库
            self._store_document(doc_id, parsed_doc)
            
            processing_time = time.time() - start_time
            
            return ParserResult(
                success=True,
                document_id=doc_id,
                parsed_doc=parsed_doc,
                structure_info=structure_info,
                processing_time=processing_time
            )
            
        except Exception as e:
            return ParserResult(
                success=False,
                document_id="",
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _analyze_structure(self, parsed_doc: ParsedDocument) -> str:
        """使用 LLM 分析文档结构"""
        try:
            # 截取文档开头部分进行结构分析（节省 token）
            content_preview = parsed_doc.content[:8000] if len(parsed_doc.content) > 8000 else parsed_doc.content
            
            structure_info = self.llm_service.generate_with_prompt(
                STRUCTURE_ANALYSIS_PROMPT,
                {"paper_content": content_preview}
            )
            return structure_info
        except Exception as e:
            return f"结构分析失败: {str(e)}"
    
    def _store_document(self, doc_id: str, parsed_doc: ParsedDocument) -> None:
        """将文档存入向量数据库"""
        # 创建集合
        self.vector_store.create_collection(doc_id)
        
        # 准备元数据
        base_metadata = {
            "filename": parsed_doc.filename,
            "file_type": parsed_doc.file_type,
            "title": parsed_doc.title,
            "page_count": parsed_doc.page_count
        }
        
        # 如果已有分块，直接使用；否则使用自动分块
        if parsed_doc.chunks:
            metadatas = [base_metadata.copy() for _ in parsed_doc.chunks]
            self.vector_store.add_documents(parsed_doc.chunks, metadatas)
        else:
            self.vector_store.add_document_with_splitting(
                parsed_doc.content,
                base_metadata
            )
    
    def get_document_info(self, parsed_doc: ParsedDocument) -> Dict[str, Any]:
        """获取文档基本信息摘要"""
        return {
            "filename": parsed_doc.filename,
            "file_type": parsed_doc.file_type,
            "title": parsed_doc.title,
            "page_count": parsed_doc.page_count,
            "word_count": parsed_doc.word_count,
            "chunk_count": len(parsed_doc.chunks),
            "metadata": parsed_doc.metadata
        }

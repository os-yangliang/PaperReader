"""
向量存储服务 - ChromaDB 集成
"""
import os
from typing import List, Optional, Dict, Any
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS
)
from services.chroma_client import get_chroma_client
from utils.text_splitter import TextSplitter


class VectorStoreService:
    """向量存储服务 - 基于 ChromaDB"""
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        self.persist_directory = persist_directory or CHROMA_PERSIST_DIR
        self.collection_name = collection_name or COLLECTION_NAME
        self.embedding_model_name = embedding_model or EMBEDDING_MODEL
        
        # 确保持久化目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 初始化 Embedding 模型
        self.embeddings = self._create_embeddings()
        
        # 初始化向量存储
        self.vector_store: Optional[Any] = None
        self._current_collection_id: Optional[str] = None
    
    def _create_embeddings(self) -> HuggingFaceEmbeddings:
        """创建 Embedding 模型"""
        return HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def _get_chroma_class(self):
        """
        获取 Chroma VectorStore 实现。

        为了避免额外依赖（如 langchain-chroma），优先使用 langchain-community 里的 Chroma。
        """
        try:
            # LangChain 新版通常在这里
            from langchain_community.vectorstores import Chroma  # type: ignore
            return Chroma
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "未找到 Chroma VectorStore 实现。请确认已安装 `langchain-community` 且版本包含 Chroma。"
            ) from e
    
    def create_collection(self, collection_id: str) -> None:
        """
        创建新的向量集合（用于新文档）
        
        Args:
            collection_id: 集合唯一标识符
        """
        collection_name = f"{self.collection_name}_{collection_id}"

        Chroma = self._get_chroma_class()
        # 使用共享的 ChromaDB 客户端，避免冲突
        client = get_chroma_client(self.persist_directory)
        self.vector_store = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )
        self._current_collection_id = collection_id
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        collection_id: Optional[str] = None
    ) -> None:
        """
        添加文档到向量存储
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
            collection_id: 集合 ID（可选，使用当前集合）
        """
        if collection_id and collection_id != self._current_collection_id:
            self.create_collection(collection_id)
        
        if self.vector_store is None:
            raise ValueError("请先创建集合（调用 create_collection）")
        
        # 创建 Document 对象
        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            metadata["chunk_index"] = i
            documents.append(Document(page_content=text, metadata=metadata))
        
        # 添加到向量存储
        self.vector_store.add_documents(documents)
    
    def add_document_with_splitting(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection_id: Optional[str] = None,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ) -> int:
        """
        添加长文档（自动分块）
        
        Args:
            text: 原始文本
            metadata: 元数据
            collection_id: 集合 ID
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            
        Returns:
            int: 创建的分块数量
        """
        if collection_id and collection_id != self._current_collection_id:
            self.create_collection(collection_id)
        
        if self.vector_store is None:
            raise ValueError("请先创建集合")

        # 使用统一的文本分块工具
        chunks = TextSplitter.split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        # 为每个分块添加元数据
        metadatas = []
        base_metadata = metadata or {}
        for i, chunk in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            metadatas.append(chunk_metadata)
        
        self.add_documents(chunks, metadatas)
        return len(chunks)
    
    def similarity_search(
        self,
        query: str,
        k: int = TOP_K_RESULTS,
        collection_id: Optional[str] = None
    ) -> List[Document]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            collection_id: 集合 ID
            
        Returns:
            List[Document]: 相关文档列表
        """
        if collection_id and collection_id != self._current_collection_id:
            self.load_collection(collection_id)
        
        if self.vector_store is None:
            raise ValueError("向量存储未初始化")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = TOP_K_RESULTS,
        collection_id: Optional[str] = None
    ) -> List[tuple]:
        """
        带分数的相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            collection_id: 集合 ID
            
        Returns:
            List[tuple]: (Document, score) 列表
        """
        if collection_id and collection_id != self._current_collection_id:
            self.load_collection(collection_id)
        
        if self.vector_store is None:
            raise ValueError("向量存储未初始化")
        
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def load_collection(self, collection_id: str) -> bool:
        """
        加载已存在的集合
        
        Args:
            collection_id: 集合 ID
            
        Returns:
            bool: 是否成功加载
        """
        collection_name = f"{self.collection_name}_{collection_id}"
        
        try:
            Chroma = self._get_chroma_class()
            # 使用共享的 ChromaDB 客户端，避免冲突
            client = get_chroma_client(self.persist_directory)
            self.vector_store = Chroma(
                client=client,
                collection_name=collection_name,
                embedding_function=self.embeddings,
            )
            self._current_collection_id = collection_id
            return True
        except Exception:
            return False
    
    def delete_collection(self, collection_id: str) -> bool:
        """
        删除集合
        
        Args:
            collection_id: 集合 ID
            
        Returns:
            bool: 是否成功删除
        """
        collection_name = f"{self.collection_name}_{collection_id}"
        
        try:
            # 使用全局客户端，避免冲突
            client = get_chroma_client(self.persist_directory)
            client.delete_collection(name=collection_name)
            
            if self._current_collection_id == collection_id:
                self.vector_store = None
                self._current_collection_id = None
            
            return True
        except Exception:
            return False
    
    def get_retriever(self, k: int = TOP_K_RESULTS):
        """
        获取检索器（用于 LangChain 链）
        
        Args:
            k: 返回结果数量
            
        Returns:
            VectorStoreRetriever
        """
        if self.vector_store is None:
            raise ValueError("向量存储未初始化")
        
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

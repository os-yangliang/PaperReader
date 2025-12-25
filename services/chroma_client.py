"""
ChromaDB 客户端单例 - 避免多个服务创建重复客户端导致冲突
"""
import os
import chromadb

from config import CHROMA_PERSIST_DIR


# 全局 ChromaDB 客户端单例
_chroma_client = None


def get_chroma_client(persist_directory: str = None) -> chromadb.ClientAPI:
    """
    获取全局 ChromaDB 客户端（单例模式）
    
    Args:
        persist_directory: 持久化目录，默认使用配置中的目录
        
    Returns:
        chromadb.ClientAPI: ChromaDB 客户端实例
    """
    global _chroma_client
    
    persist_dir = persist_directory or CHROMA_PERSIST_DIR
    
    if _chroma_client is None:
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        print(f"[ChromaDB] 初始化客户端，路径: {persist_dir}")
    
    return _chroma_client


def reset_chroma_client():
    """重置客户端（用于测试）"""
    global _chroma_client
    _chroma_client = None


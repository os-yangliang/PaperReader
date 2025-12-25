"""
服务管理器 - 实现依赖注入和单例模式
"""
from typing import Optional
from services.llm_service import LLMService
from services.vector_store import VectorStoreService
from services.history_store_sqlite import HistoryStoreService


class ServiceManager:
    """
    服务管理器 - 统一管理所有服务实例
    
    使用单例模式确保整个应用共享相同的服务实例，避免重复创建
    """
    
    _instance: Optional['ServiceManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化服务管理器（只初始化一次）"""
        if self._initialized:
            return
        
        # 初始化共享服务实例
        self._llm_service: Optional[LLMService] = None
        self._vector_store: Optional[VectorStoreService] = None
        self._history_store: Optional[HistoryStoreService] = None
        
        self._initialized = True
    
    @property
    def llm_service(self) -> LLMService:
        """获取 LLM 服务实例（延迟初始化）"""
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service
    
    @property
    def vector_store(self) -> VectorStoreService:
        """获取向量存储服务实例（延迟初始化）"""
        if self._vector_store is None:
            self._vector_store = VectorStoreService()
        return self._vector_store
    
    @property
    def history_store(self) -> HistoryStoreService:
        """获取历史记录服务实例（延迟初始化）"""
        if self._history_store is None:
            self._history_store = HistoryStoreService()
        return self._history_store
    
    def reset(self):
        """重置所有服务实例（主要用于测试）"""
        self._llm_service = None
        self._vector_store = None
        self._history_store = None
    
    @classmethod
    def get_instance(cls) -> 'ServiceManager':
        """获取服务管理器实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# 全局服务管理器实例
_service_manager = ServiceManager()


def get_llm_service() -> LLMService:
    """便捷函数：获取 LLM 服务"""
    return _service_manager.llm_service


def get_vector_store() -> VectorStoreService:
    """便捷函数：获取向量存储服务"""
    return _service_manager.vector_store


def get_history_store() -> HistoryStoreService:
    """便捷函数：获取历史记录服务"""
    return _service_manager.history_store


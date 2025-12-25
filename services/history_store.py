"""
历史记录存储服务 - 使用 ChromaDB 持久化存储分析历史和对话记录
"""
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import CHROMA_PERSIST_DIR
from services.chroma_client import get_chroma_client


class HistoryStoreService:
    """历史记录存储服务 - 基于 ChromaDB"""
    
    HISTORY_COLLECTION = "paper_analysis_history"
    CHAT_COLLECTION = "paper_chat_history"
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or CHROMA_PERSIST_DIR
        
        # 确保持久化目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 使用全局 ChromaDB 客户端
        self.client = get_chroma_client(self.persist_directory)
        
        # 获取或创建历史记录集合
        self.history_collection = self.client.get_or_create_collection(
            name=self.HISTORY_COLLECTION,
            metadata={"description": "论文分析历史记录"}
        )
        
        # 获取或创建对话记录集合
        self.chat_collection = self.client.get_or_create_collection(
            name=self.CHAT_COLLECTION,
            metadata={"description": "论文问答对话记录"}
        )
    
    # ==================== 分析历史记录 ====================
    
    def add_analysis_history(
        self,
        document_id: str,
        filename: str,
        title: str = "",
        file_type: str = "",
        page_count: int = 0,
        word_count: int = 0,
        processing_time: float = 0,
        structure: str = "",
        summary: str = ""
    ) -> str:
        """
        添加分析历史记录
        
        Args:
            document_id: 文档ID（用作唯一标识）
            filename: 文件名
            title: 论文标题
            file_type: 文件类型
            page_count: 页数
            word_count: 字数
            processing_time: 处理时间
            structure: 结构分析结果
            summary: 摘要分析结果
            
        Returns:
            str: 历史记录ID
        """
        print(f"[HistoryStore] add_analysis_history 被调用")
        print(f"[HistoryStore] document_id={document_id}, filename={filename}")
        
        history_id = f"h_{document_id}"
        analyzed_at = datetime.now().isoformat()
        
        # 准备元数据
        metadata = {
            "document_id": document_id,
            "filename": filename,
            "title": title or "",
            "file_type": file_type or "",
            "page_count": page_count,
            "word_count": word_count,
            "processing_time": processing_time,
            "analyzed_at": analyzed_at,
            "structure": structure[:10000] if structure else "",  # ChromaDB 元数据有大小限制
            "summary": summary[:10000] if summary else ""
        }
        
        # 用于搜索的文本内容
        content = f"{filename} {title} {file_type}"
        
        # 检查是否已存在
        existing = self.history_collection.get(ids=[history_id])
        print(f"[HistoryStore] 检查是否已存在: {existing['ids'] if existing else 'None'}")
        
        if existing and existing['ids']:
            # 更新现有记录
            self.history_collection.update(
                ids=[history_id],
                documents=[content],
                metadatas=[metadata]
            )
            print(f"[HistoryStore] 更新现有记录: {history_id}")
        else:
            # 添加新记录
            self.history_collection.add(
                ids=[history_id],
                documents=[content],
                metadatas=[metadata]
            )
            print(f"[HistoryStore] 添加新记录: {history_id}")
        
        # 验证保存结果
        count = self.history_collection.count()
        print(f"[HistoryStore] 当前历史记录总数: {count}")
        
        return history_id
    
    def get_analysis_history_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取分析历史记录列表
        
        Args:
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 历史记录列表，按时间倒序
        """
        try:
            # 获取所有记录
            results = self.history_collection.get(
                include=["metadatas"]
            )
            
            if not results or not results['ids']:
                return []
            
            # 构建历史列表
            history_list = []
            for i, history_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                history_list.append({
                    "id": history_id,
                    "document_id": metadata.get("document_id", ""),
                    "filename": metadata.get("filename", "未知文件"),
                    "title": metadata.get("title", ""),
                    "file_type": metadata.get("file_type", ""),
                    "page_count": metadata.get("page_count", 0),
                    "word_count": metadata.get("word_count", 0),
                    "processing_time": metadata.get("processing_time", 0),
                    "analyzed_at": metadata.get("analyzed_at", "")
                })
            
            # 按分析时间倒序排序
            history_list.sort(key=lambda x: x.get("analyzed_at", ""), reverse=True)
            
            return history_list[:limit]
            
        except Exception as e:
            print(f"[ERROR] 获取历史记录失败: {e}")
            return []
    
    def get_analysis_history_detail(self, history_id: str) -> Optional[Dict[str, Any]]:
        """
        获取历史记录详情（包含结构和摘要）
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            Dict: 历史记录详情
        """
        try:
            results = self.history_collection.get(
                ids=[history_id],
                include=["metadatas"]
            )
            
            if not results or not results['ids']:
                return None
            
            metadata = results['metadatas'][0] if results['metadatas'] else {}
            
            return {
                "id": history_id,
                "document_id": metadata.get("document_id", ""),
                "filename": metadata.get("filename", "未知文件"),
                "title": metadata.get("title", ""),
                "file_type": metadata.get("file_type", ""),
                "page_count": metadata.get("page_count", 0),
                "word_count": metadata.get("word_count", 0),
                "processing_time": metadata.get("processing_time", 0),
                "analyzed_at": metadata.get("analyzed_at", ""),
                "structure": metadata.get("structure", ""),
                "summary": metadata.get("summary", "")
            }
            
        except Exception as e:
            print(f"[ERROR] 获取历史记录详情失败: {e}")
            return None
    
    def delete_analysis_history(self, history_id: str) -> bool:
        """
        删除历史记录
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            self.history_collection.delete(ids=[history_id])
            # 同时删除相关的对话记录
            self._delete_chat_history_by_document(history_id)
            return True
        except Exception as e:
            print(f"[ERROR] 删除历史记录失败: {e}")
            return False
    
    # ==================== 对话记录 ====================
    
    def add_chat_message(
        self,
        document_id: str,
        role: str,
        content: str,
        source_chunks: Optional[List[str]] = None
    ) -> str:
        """
        添加对话消息
        
        Args:
            document_id: 关联的文档ID
            role: 角色 (user/assistant)
            content: 消息内容
            source_chunks: 来源文本块（仅assistant）
            
        Returns:
            str: 消息ID
        """
        message_id = f"m_{document_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        timestamp = datetime.now().isoformat()
        
        metadata = {
            "document_id": document_id,
            "role": role,
            "content": content[:10000],  # 限制大小
            "timestamp": timestamp,
            "source_chunks": json.dumps(source_chunks[:3] if source_chunks else [], ensure_ascii=False)
        }
        
        self.chat_collection.add(
            ids=[message_id],
            documents=[content[:1000]],  # 用于搜索的简短内容
            metadatas=[metadata]
        )
        
        return message_id
    
    def get_chat_history(self, document_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取指定文档的对话历史
        
        Args:
            document_id: 文档ID
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 对话记录列表
        """
        try:
            # 使用 where 过滤
            results = self.chat_collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if not results or not results['ids']:
                return []
            
            # 构建对话列表
            chat_list = []
            for i, msg_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                source_chunks = []
                try:
                    source_chunks = json.loads(metadata.get("source_chunks", "[]"))
                except:
                    pass
                    
                chat_list.append({
                    "id": msg_id,
                    "role": metadata.get("role", "user"),
                    "content": metadata.get("content", ""),
                    "timestamp": metadata.get("timestamp", ""),
                    "source_chunks": source_chunks
                })
            
            # 按时间排序
            chat_list.sort(key=lambda x: x.get("timestamp", ""))
            
            return chat_list[-limit:]
            
        except Exception as e:
            print(f"[ERROR] 获取对话历史失败: {e}")
            return []
    
    def clear_chat_history(self, document_id: str) -> bool:
        """
        清除指定文档的对话历史
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 是否成功
        """
        return self._delete_chat_history_by_document(f"h_{document_id}")
    
    def _delete_chat_history_by_document(self, history_id: str) -> bool:
        """根据历史记录ID删除相关对话"""
        try:
            # 从 history_id 提取 document_id
            document_id = history_id.replace("h_", "") if history_id.startswith("h_") else history_id
            
            # 获取该文档的所有对话
            results = self.chat_collection.get(
                where={"document_id": document_id}
            )
            
            if results and results['ids']:
                self.chat_collection.delete(ids=results['ids'])
            
            return True
        except Exception as e:
            print(f"[ERROR] 删除对话历史失败: {e}")
            return False


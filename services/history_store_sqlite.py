"""
历史记录存储服务 - 使用 SQLite 替代 ChromaDB
"""
import os
import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager


class HistoryStoreService:
    """历史记录存储服务 - 基于 SQLite"""
    
    def __init__(self, db_path: str = "./history.db"):
        """
        初始化历史记录服务
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使用 Row 对象，可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建分析历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    title TEXT,
                    file_type TEXT,
                    page_count INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 0,
                    processing_time REAL DEFAULT 0,
                    structure TEXT,
                    summary TEXT,
                    analyzed_at TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建对话历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    source_chunks TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES analysis_history(document_id)
                        ON DELETE CASCADE
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_document_id 
                ON chat_history(document_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_timestamp 
                ON chat_history(timestamp)
            """)
    
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
        history_id = f"h_{document_id}"
        analyzed_at = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 使用 INSERT OR REPLACE 处理重复
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_history (
                    id, document_id, filename, title, file_type,
                    page_count, word_count, processing_time,
                    structure, summary, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history_id, document_id, filename, title, file_type,
                page_count, word_count, processing_time,
                structure, summary, analyzed_at
            ))
        
        return history_id
    
    def get_analysis_history_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取分析历史记录列表
        
        Args:
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 历史记录列表，按时间倒序
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, document_id, filename, title, file_type,
                    page_count, word_count, processing_time, analyzed_at
                FROM analysis_history
                ORDER BY analyzed_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_analysis_history_detail(self, history_id: str) -> Optional[Dict[str, Any]]:
        """
        获取历史记录详情（包含结构和摘要）
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            Dict: 历史记录详情
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analysis_history WHERE id = ?
            """, (history_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_analysis_history(self, history_id: str) -> bool:
        """
        删除历史记录（会级联删除相关对话）
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 先获取 document_id
                cursor.execute(
                    "SELECT document_id FROM analysis_history WHERE id = ?",
                    (history_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                document_id = row['document_id']
                
                # 删除相关对话
                cursor.execute(
                    "DELETE FROM chat_history WHERE document_id = ?",
                    (document_id,)
                )
                
                # 删除历史记录
                cursor.execute(
                    "DELETE FROM analysis_history WHERE id = ?",
                    (history_id,)
                )
                
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
        
        # 将 source_chunks 序列化为 JSON
        source_chunks_json = json.dumps(
            source_chunks[:3] if source_chunks else [],
            ensure_ascii=False
        )
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (
                    id, document_id, role, content, source_chunks, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (message_id, document_id, role, content, source_chunks_json, timestamp))
        
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, role, content, source_chunks, timestamp
                FROM chat_history
                WHERE document_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (document_id, limit))
            
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                item = dict(row)
                # 反序列化 source_chunks
                try:
                    item['source_chunks'] = json.loads(item.get('source_chunks', '[]'))
                except:
                    item['source_chunks'] = []
                result.append(item)
            
            return result
    
    def clear_chat_history(self, document_id: str) -> bool:
        """
        清除指定文档的对话历史
        
        Args:
            document_id: 文档ID
            
        Returns:
            bool: 是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM chat_history WHERE document_id = ?",
                    (document_id,)
                )
                return True
        except Exception as e:
            print(f"[ERROR] 清除对话历史失败: {e}")
            return False


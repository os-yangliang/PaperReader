"""
统一的文本分块工具
"""
from typing import List


class TextSplitter:
    """文本分块工具类"""
    
    @staticmethod
    def split_text(
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> List[str]:
        """
        将文本分割为固定大小的块
        
        策略：尽量在句子/段落边界处分割，并保留一定重叠
        
        Args:
            text: 原始文本
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            
        Returns:
            List[str]: 文本块列表
        """
        if not text:
            return []
        
        # 定义分隔符优先级
        separators = ["\n\n", "\n", "。", ".", "！", "!", "？", "?", "；", ";", " "]
        
        chunks: List[str] = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # 计算结束位置
            end = start + chunk_size
            
            if end >= text_length:
                # 最后一块
                last_chunk = text[start:].strip()
                if last_chunk:
                    chunks.append(last_chunk)
                break
            
            # 在边界附近查找最佳分割点
            search_start = max(start + chunk_size - 100, start)
            best_split = end
            
            # 尝试在分隔符处分割
            for separator in separators:
                pos = text.rfind(separator, search_start, min(end + 50, text_length))
                if pos != -1 and pos > search_start:
                    best_split = pos + len(separator)
                    break
            
            # 提取当前块
            chunk = text[start:best_split].strip()
            if chunk:
                chunks.append(chunk)
            
            # 计算下一块的起始位置（带重叠）
            start = best_split - chunk_overlap
            if start < 0:
                start = 0
        
        return chunks


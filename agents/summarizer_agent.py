"""
摘要分析 Agent - 负责生成论文的详细分析报告
"""
from typing import Optional
from dataclasses import dataclass
import time

from services.llm_service import LLMService
from services.document_parser import ParsedDocument
from prompts.templates import PAPER_SUMMARY_PROMPT, KEYWORD_EXTRACTION_PROMPT


@dataclass
class SummaryResult:
    """摘要分析结果"""
    success: bool
    summary: str = ""
    keywords: str = ""
    error_message: str = ""
    processing_time: float = 0.0


class SummarizerAgent:
    """摘要分析 Agent - 生成论文详细分析报告"""
    
    def __init__(self, llm_service: LLMService):
        """
        初始化摘要 Agent
        
        Args:
            llm_service: LLM 服务（必需）
        """
        self.llm_service = llm_service
    
    def generate_summary(
        self,
        parsed_doc: ParsedDocument,
        max_content_length: int = 30000
    ) -> SummaryResult:
        """
        生成论文摘要分析
        
        Args:
            parsed_doc: 解析后的文档对象
            max_content_length: 最大内容长度（控制 token 消耗）
            
        Returns:
            SummaryResult: 摘要分析结果
        """
        start_time = time.time()
        
        try:
            # 准备论文内容（可能需要截断以控制 token）
            content = self._prepare_content(parsed_doc, max_content_length)
            
            # 生成详细摘要
            summary = self.llm_service.generate_with_prompt(
                PAPER_SUMMARY_PROMPT,
                {"paper_content": content}
            )
            
            # 提取关键词
            keywords = self._extract_keywords(content)
            
            processing_time = time.time() - start_time
            
            return SummaryResult(
                success=True,
                summary=summary,
                keywords=keywords,
                processing_time=processing_time
            )
            
        except Exception as e:
            return SummaryResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def generate_summary_async(
        self,
        parsed_doc: ParsedDocument,
        max_content_length: int = 30000
    ) -> SummaryResult:
        """
        异步生成论文摘要分析
        
        Args:
            parsed_doc: 解析后的文档对象
            max_content_length: 最大内容长度
            
        Returns:
            SummaryResult: 摘要分析结果
        """
        start_time = time.time()
        
        try:
            content = self._prepare_content(parsed_doc, max_content_length)
            
            # 异步生成摘要
            summary = await self.llm_service.generate_with_prompt_async(
                PAPER_SUMMARY_PROMPT,
                {"paper_content": content}
            )
            
            processing_time = time.time() - start_time
            
            return SummaryResult(
                success=True,
                summary=summary,
                processing_time=processing_time
            )
            
        except Exception as e:
            return SummaryResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def generate_summary_stream(
        self,
        parsed_doc: ParsedDocument,
        max_content_length: int = 30000
    ):
        """
        流式生成论文摘要分析
        
        Args:
            parsed_doc: 解析后的文档对象
            max_content_length: 最大内容长度
            
        Yields:
            str: 流式输出的摘要片段
        """
        content = self._prepare_content(parsed_doc, max_content_length)
        
        # 构建完整的 prompt
        prompt = PAPER_SUMMARY_PROMPT.format(paper_content=content)
        
        # 流式生成
        for chunk in self.llm_service.stream_chat(prompt):
            yield chunk
    
    def _prepare_content(
        self,
        parsed_doc: ParsedDocument,
        max_length: int
    ) -> str:
        """
        准备用于分析的内容
        
        如果内容太长，采用智能截取策略：
        1. 保留开头（摘要、引言）
        2. 保留结尾（结论）
        3. 中间部分采样
        """
        content = parsed_doc.content
        
        if len(content) <= max_length:
            return content
        
        # 智能截取策略
        # 保留前 40%（通常包含摘要、引言、方法）
        front_portion = int(max_length * 0.4)
        # 保留后 20%（通常包含结论）
        back_portion = int(max_length * 0.2)
        # 中间采样 40%
        middle_portion = max_length - front_portion - back_portion
        
        front = content[:front_portion]
        back = content[-back_portion:]
        
        # 中间部分均匀采样
        middle_start = front_portion
        middle_end = len(content) - back_portion
        middle_length = middle_end - middle_start
        
        if middle_length > middle_portion:
            # 采样中间部分
            step = middle_length // (middle_portion // 500)  # 每 500 字符采样一次
            middle_samples = []
            for i in range(middle_start, middle_end, step):
                sample = content[i:i+500]
                middle_samples.append(sample)
                if len("".join(middle_samples)) >= middle_portion:
                    break
            middle = "\n...[内容省略]...\n".join(middle_samples)
        else:
            middle = content[middle_start:middle_end]
        
        return f"{front}\n\n...[部分内容省略]...\n\n{middle}\n\n...[部分内容省略]...\n\n{back}"
    
    def _extract_keywords(self, content: str) -> str:
        """提取关键词"""
        try:
            # 只使用前 5000 字符提取关键词
            content_preview = content[:5000] if len(content) > 5000 else content
            
            keywords = self.llm_service.generate_with_prompt(
                KEYWORD_EXTRACTION_PROMPT,
                {"paper_content": content_preview}
            )
            return keywords
        except Exception:
            return ""
    
    def generate_quick_summary(
        self,
        parsed_doc: ParsedDocument,
        max_words: int = 1000
    ) -> str:
        """
        生成快速简短摘要
        
        Args:
            parsed_doc: 解析后的文档对象
            max_words: 最大字数
            
        Returns:
            str: 简短摘要
        """
        quick_prompt = f"""请用不超过{max_words}字简要概括以下论文的核心内容，包括：研究问题、方法、主要结果。

        论文内容：
        {{paper_content}}

        简要概括："""
        
        content = parsed_doc.content[:10000]  # 只使用前 10000 字符
        
        try:
            return self.llm_service.generate_with_prompt(
                quick_prompt,
                {"paper_content": content}
            )
        except Exception as e:
            return f"生成摘要失败: {str(e)}"

"""
LLM 服务 - DeepSeek API 集成
"""
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_BASE,
    DEEPSEEK_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)


class LLMService:
    """DeepSeek LLM 服务封装"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS
    ):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.model = model or DEEPSEEK_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 初始化 LLM
        self.llm = self._create_llm()
        
    def _create_llm(self) -> ChatOpenAI:
        """创建 LLM 实例"""
        if not self.api_key:
            raise ValueError(
                "未配置 DEEPSEEK_API_KEY。\n"
                "请按以下步骤配置：\n"
                "1. 在项目根目录创建 .env 文件（可复制 env.example）\n"
                "2. 设置 DEEPSEEK_API_KEY=你的API密钥\n"
                "3. 重启后端服务"
            )
        try:
            return ChatOpenAI(
                model=self.model,
                openai_api_key=self.api_key,
                openai_api_base=DEEPSEEK_API_BASE,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            raise ValueError(f"LLM 初始化失败: {str(e)}")
    
    def get_llm(self) -> ChatOpenAI:
        """获取 LLM 实例"""
        return self.llm
    
    async def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        异步聊天接口
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            chat_history: 聊天历史 [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            str: AI 回复
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # 添加当前用户消息
        messages.append(HumanMessage(content=user_message))
        
        # 调用 LLM
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def chat_sync(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        同步聊天接口
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            chat_history: 聊天历史
            
        Returns:
            str: AI 回复
        """
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_message))
        
        response = self.llm.invoke(messages)
        return response.content
    
    def generate_with_prompt(
        self,
        prompt_template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        使用 Prompt 模板生成内容
        
        Args:
            prompt_template: Prompt 模板字符串
            variables: 模板变量
            
        Returns:
            str: 生成的内容
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke(variables)
    
    async def generate_with_prompt_async(
        self,
        prompt_template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        异步使用 Prompt 模板生成内容
        
        Args:
            prompt_template: Prompt 模板字符串
            variables: 模板变量
            
        Returns:
            str: 生成的内容
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        return await chain.ainvoke(variables)
    
    def stream_chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        流式聊天接口（生成器）
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            chat_history: 聊天历史
            
        Yields:
            str: 流式输出的内容片段
        """
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_message))
        
        for chunk in self.llm.stream(messages):
            if chunk.content:
                yield chunk.content

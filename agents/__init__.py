"""
多智能体模块
"""
from .parser_agent import ParserAgent
from .summarizer_agent import SummarizerAgent
from .qa_agent import QAAgent
from .coordinator import PaperReaderCoordinator

__all__ = [
    "ParserAgent",
    "SummarizerAgent", 
    "QAAgent",
    "PaperReaderCoordinator"
]

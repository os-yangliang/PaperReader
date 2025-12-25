"""
配置文件 - 论文阅读多智能体系统
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek API 配置
DEEPSEEK_API_KEY = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# CORS 配置（逗号分隔），示例: http://localhost:3000,http://127.0.0.1:3000
# 注意：当 allow_credentials=True 时，FastAPI 不允许 allow_origins=["*"]
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in (os.getenv("CORS_ALLOW_ORIGINS") or "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

# LLM 参数配置
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 4096

# 向量数据库配置
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "paper_collection"

# Embedding 配置
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 文档处理配置
CHUNK_SIZE = 500  # 文本分块大小
CHUNK_OVERLAP = 100  # 分块重叠大小
MAX_FILE_SIZE_MB = 50  # 最大文件大小（MB）

# 检索配置
TOP_K_RESULTS = 5  # 检索返回的相关文档数量

# 支持的文件类型
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc"]

# 📚 论文阅读多智能体系统

基于 LangChain + LangGraph 构建的智能论文分析与问答系统，配备现代化 Vue 3 前端界面。

## ✨ 功能特点

- 🔍 **文档解析**: 支持 PDF 和 Word (docx/doc) 格式的论文上传
- 📊 **智能分析**: 自动生成结构化的论文分析报告
- 💬 **智能问答**: 基于 RAG 的论文对话问答系统
- 🤖 **多智能体架构**: 使用 LangGraph 协调多个专业 Agent
- 🎨 **现代化界面**: Vue 3 + Vite 构建的精美前端

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Vue 3 前端界面                              │
├─────────────────────────────────────────────────────────────────┤
│                   FastAPI 后端 API                               │
├─────────────────────────────────────────────────────────────────┤
│                 协调 Agent (Coordinator)                         │
├──────────┬──────────────┬──────────────┬────────────────────────┤
│ 解析Agent │  摘要Agent   │   问答Agent  │    ...                 │
├──────────┴──────────────┴──────────────┴────────────────────────┤
│         服务层 (LLM / 向量存储 / 文档解析)                        │
├────────────────────────────┬────────────────────────────────────┤
│      DeepSeek API          │         ChromaDB                   │
└────────────────────────────┴────────────────────────────────────┘
```

## 📦 安装

### 1. 安装后端依赖

```bash
cd paper_reader

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 配置 API Key

创建 `.env` 文件并填入您的 DeepSeek API Key（推荐从示例文件复制）:

```bash
copy env.example .env
```

```env
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

## 🚀 启动应用

### 方式一：一键启动（推荐）

双击运行 `start.bat`，将自动启动后端和前端服务器。

### 方式二：分别启动

**启动后端 API：**
```bash
# Windows
run_api.bat

# 或手动启动
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端开发服务器：**
```bash
# Windows
run_frontend.bat

# 或手动启动
cd frontend
npm run dev
```

### 方式三：使用原 Gradio 界面

```bash
python app.py
```

## 🌐 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| API 服务 | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| Gradio 界面 | http://localhost:7860 |

## 📖 使用说明

### 1️⃣ 上传论文
- 在"分析"页面上传 PDF 或 Word 格式的论文
- 支持拖拽上传
- 点击"开始分析"按钮

### 2️⃣ 查看分析结果
- **结构分析**: 论文的基本结构信息
- **详细摘要**: 包含以下内容的完整分析报告:
  - 论文概述
  - 研究背景与动机
  - 研究方法
  - 实验与结果
  - 创新点与贡献
  - 局限性与不足
  - 未来工作展望

### 3️⃣ 智能问答
- 切换到"问答"页面
- 输入任何关于论文的问题
- 系统将基于论文内容给出精准回答
- 支持流式响应

## 🔧 配置说明

主要配置项在 `config.py` 文件中:

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_MODEL` | 使用的模型 | deepseek-chat |
| `LLM_TEMPERATURE` | 生成温度 | 0.7 |
| `CHUNK_SIZE` | 文本分块大小 | 500 |
| `TOP_K_RESULTS` | 检索返回数量 | 5 |
| `MAX_FILE_SIZE_MB` | 最大文件大小 | 50MB |

## 📁 项目结构

```
paper_reader/
├── api.py                    # FastAPI 后端 API
├── app.py                    # Gradio 主应用入口（备用）
├── config.py                 # 配置文件
├── requirements.txt          # Python 依赖包
├── start.bat                 # 一键启动脚本
├── run_api.bat              # API 服务器启动脚本
├── run_frontend.bat         # 前端启动脚本
│
├── frontend/                 # Vue 3 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── style.css
│       ├── api/
│       │   └── index.js
│       └── views/
│           ├── Home.vue
│           ├── Analyze.vue
│           └── Chat.vue
│
├── agents/
│   ├── coordinator.py        # 协调 Agent (LangGraph)
│   ├── parser_agent.py       # 文档解析 Agent
│   ├── summarizer_agent.py   # 摘要分析 Agent
│   └── qa_agent.py           # RAG 问答 Agent
│
├── services/
│   ├── document_parser.py    # 文档解析服务
│   ├── vector_store.py       # ChromaDB 向量存储
│   └── llm_service.py        # DeepSeek LLM 服务
│
└── prompts/
    └── templates.py          # Prompt 模板
```

## 🛠️ 技术栈

**后端:**
- FastAPI - 高性能 Web 框架
- LangChain + LangGraph - 多智能体框架
- DeepSeek API - LLM 服务
- ChromaDB - 向量数据库
- PyMuPDF + python-docx - 文档解析

**前端:**
- Vue 3 - 渐进式 JavaScript 框架
- Vite - 下一代前端构建工具
- Tailwind CSS - 原子化 CSS 框架
- Axios - HTTP 客户端

## 🎨 界面预览

前端采用深色主题设计，具有以下特点：
- 玻璃态 (Glassmorphism) 设计风格
- 流畅的动画效果
- 响应式布局
- 优雅的 Markdown 渲染
- 实时流式响应

## ⚠️ 注意事项

1. 首次运行时会下载 Embedding 模型，可能需要一些时间
2. 确保网络可以访问 DeepSeek API
3. 大型论文的分析可能需要较长时间
4. 建议上传学术论文格式的文档以获得最佳效果
5. 需要 Node.js 18+ 来运行前端开发服务器

## 📝 License

MIT License

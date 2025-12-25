"""
论文阅读多智能体系统 - Gradio 主应用
"""
import gradio as gr
from typing import List, Tuple, Optional
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.coordinator import PaperReaderCoordinator
from config import SUPPORTED_EXTENSIONS


class PaperReaderApp:
    """论文阅读应用"""
    
    def __init__(self):
        self.coordinator: Optional[PaperReaderCoordinator] = None
        self.current_summary: str = ""
        self.current_structure: str = ""
        self.is_document_loaded: bool = False
    
    def _ensure_coordinator(self):
        """确保协调器已初始化"""
        if self.coordinator is None:
            self.coordinator = PaperReaderCoordinator()
    
    def upload_and_analyze(
        self,
        file,
        progress=gr.Progress()
    ) -> Tuple[str, str, str, str]:
        """
        上传并分析论文
        
        Returns:
            Tuple[状态消息, 文档信息, 结构分析, 详细摘要]
        """
        if file is None:
            return "❌ 请先上传文件", "", "", ""
        
        # 检查文件类型
        filename = os.path.basename(file.name)
        _, ext = os.path.splitext(filename)
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            return f"❌ 不支持的文件格式: {ext}，请上传 PDF 或 Word 文档", "", "", ""
        
        self._ensure_coordinator()
        
        progress(0.1, desc="正在读取文件...")
        
        # 读取文件内容
        with open(file.name, "rb") as f:
            file_bytes = f.read()
        
        progress(0.2, desc="正在解析文档...")
        
        # 处理文档
        result = self.coordinator.process_document(
            file_bytes=file_bytes,
            filename=filename
        )
        
        if result.success:
            self.is_document_loaded = True
            self.current_summary = result.summary
            self.current_structure = result.structure_info
            
            # 构建文档信息
            doc_info = self.coordinator.get_current_document_info()
            if doc_info:
                info_text = f"""### 📄 文档信息

| 属性 | 值 |
|------|-----|
| **文件名** | {doc_info['filename']} |
| **标题** | {doc_info['title'][:100]}{'...' if len(doc_info['title']) > 100 else ''} |
| **类型** | {doc_info['file_type'].upper()} |
| **页数** | {doc_info['page_count']} |
| **字数** | {doc_info['word_count']:,} |
| **文档ID** | {doc_info['document_id']} |

⏱️ **处理时间**: {result.total_time:.2f} 秒
"""
            else:
                info_text = "文档信息获取失败"
            
            status = f"✅ 文档解析完成！标题: {result.paper_title[:50]}..."
            
            progress(1.0, desc="分析完成！")
            
            return status, info_text, result.structure_info, result.summary
        else:
            self.is_document_loaded = False
            return f"❌ 处理失败: {result.error_message}", "", "", ""
    
    def chat(
        self,
        message: str,
        history: List[List[str]]
    ) -> Tuple[str, List[List[str]]]:
        """
        聊天问答
        
        Args:
            message: 用户消息
            history: 聊天历史
            
        Returns:
            Tuple[空字符串(清除输入), 更新后的历史]
        """
        if not message.strip():
            return "", history
        
        if not self.is_document_loaded:
            history.append([message, "❌ 请先上传并解析论文文档"])
            return "", history
        
        self._ensure_coordinator()
        
        # 获取回答
        result = self.coordinator.ask_question(message)
        
        if result.success:
            answer = result.answer
            
            # 添加来源信息
            if result.source_chunks:
                answer += "\n\n---\n📚 **参考来源:**\n"
                for i, chunk in enumerate(result.source_chunks[:3], 1):
                    answer += f"\n> {i}. {chunk[:150]}...\n"
        else:
            answer = f"❌ 回答失败: {result.error_message}"
        
        history.append([message, answer])
        return "", history
    
    def chat_stream(
        self,
        message: str,
        history: List[List[str]]
    ):
        """
        流式聊天问答
        
        Args:
            message: 用户消息
            history: 聊天历史
            
        Yields:
            更新后的历史
        """
        if not message.strip():
            yield "", history
            return
        
        if not self.is_document_loaded:
            history.append([message, "❌ 请先上传并解析论文文档"])
            yield "", history
            return
        
        self._ensure_coordinator()
        
        # 添加用户消息和空回复
        history.append([message, ""])
        
        # 流式生成回答
        full_response = ""
        for chunk in self.coordinator.ask_question_stream(message):
            full_response += chunk
            history[-1][1] = full_response
            yield "", history
    
    def get_suggested_questions(self) -> str:
        """获取建议问题"""
        if not self.is_document_loaded:
            return "请先上传论文文档"
        
        self._ensure_coordinator()
        questions = self.coordinator.get_suggested_questions()
        
        result = "### 💡 建议问题\n\n"
        for i, q in enumerate(questions, 1):
            result += f"{i}. {q}\n"
        
        return result
    
    def clear_chat(self) -> Tuple[List, str]:
        """清除聊天历史"""
        if self.coordinator:
            self.coordinator.clear_chat_history()
        return [], ""
    
    def use_suggested_question(self, question: str) -> str:
        """使用建议的问题"""
        return question


def create_app() -> gr.Blocks:
    """创建 Gradio 应用"""
    
    app_instance = PaperReaderApp()
    
    # 自定义 CSS
    custom_css = """
    .container { max-width: 1200px; margin: auto; }
    .header { text-align: center; margin-bottom: 20px; }
    .analysis-box { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; }
    """
    
    with gr.Blocks(
        title="📚 论文阅读助手",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as app:
        
        # 标题
        gr.Markdown("""
        # 📚 论文阅读多智能体系统
        
        基于 LangChain + LangGraph 构建的智能论文分析与问答系统
        
        **功能特点:**
        - 🔍 支持 PDF / Word 论文上传
        - 📊 自动生成结构化分析报告
        - 💬 智能对话问答
        - 🎯 基于 RAG 的精准回答
        """)
        
        with gr.Tabs() as tabs:
            
            # ===== Tab 1: 文件上传与分析 =====
            with gr.Tab("📤 上传与分析", id="upload"):
                with gr.Row():
                    with gr.Column(scale=1):
                        # 文件上传
                        file_input = gr.File(
                            label="上传论文文件",
                            file_types=[".pdf", ".docx", ".doc"],
                            type="filepath"
                        )
                        
                        analyze_btn = gr.Button(
                            "🚀 开始分析",
                            variant="primary",
                            size="lg"
                        )
                        
                        status_output = gr.Textbox(
                            label="状态",
                            interactive=False,
                            lines=1
                        )
                        
                        doc_info_output = gr.Markdown(
                            label="文档信息",
                            value=""
                        )
                    
                    with gr.Column(scale=2):
                        with gr.Tabs():
                            with gr.Tab("📋 结构分析"):
                                structure_output = gr.Markdown(
                                    label="论文结构",
                                    value="*上传文档后显示结构分析*"
                                )
                            
                            with gr.Tab("📝 详细摘要"):
                                summary_output = gr.Markdown(
                                    label="论文摘要",
                                    value="*上传文档后显示详细摘要*"
                                )
                
                # 绑定上传分析事件
                analyze_btn.click(
                    fn=app_instance.upload_and_analyze,
                    inputs=[file_input],
                    outputs=[status_output, doc_info_output, structure_output, summary_output],
                    show_progress=True
                )
            
            # ===== Tab 2: 智能问答 =====
            with gr.Tab("💬 智能问答", id="chat"):
                with gr.Row():
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            label="论文问答",
                            height=500
                        )
                        
                        with gr.Row():
                            msg_input = gr.Textbox(
                                label="输入问题",
                                placeholder="请输入您关于论文的问题...",
                                lines=2,
                                scale=4
                            )
                            
                            with gr.Column(scale=1):
                                send_btn = gr.Button("发送", variant="primary")
                                clear_btn = gr.Button("清除历史")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 💡 建议问题")
                        
                        suggested_questions = [
                            "这篇论文的主要研究问题是什么？",
                            "论文使用了什么方法？",
                            "实验结果如何？",
                            "论文的创新点是什么？",
                            "有什么局限性？",
                            "作者提出了哪些未来工作？"
                        ]
                        
                        for q in suggested_questions:
                            gr.Button(
                                q,
                                size="sm"
                            ).click(
                                fn=lambda x=q: x,
                                outputs=[msg_input]
                            )
                
                # 绑定聊天事件
                send_btn.click(
                    fn=app_instance.chat,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot]
                )
                
                msg_input.submit(
                    fn=app_instance.chat,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot]
                )
                
                clear_btn.click(
                    fn=app_instance.clear_chat,
                    outputs=[chatbot, msg_input]
                )
            
            # ===== Tab 3: 使用说明 =====
            with gr.Tab("📖 使用说明", id="help"):
                gr.Markdown("""
                ## 使用说明
                
                ### 1️⃣ 上传论文
                - 支持 **PDF** 和 **Word (docx/doc)** 格式
                - 文件大小限制: 50MB
                - 建议上传学术论文以获得最佳效果
                
                ### 2️⃣ 自动分析
                点击"开始分析"后，系统将:
                1. 解析文档内容
                2. 识别论文结构
                3. 生成详细分析报告，包括:
                   - 论文概述
                   - 研究方法
                   - 实验结果
                   - 创新点
                   - 局限性分析
                
                ### 3️⃣ 智能问答
                分析完成后，您可以:
                - 询问任何关于论文的问题
                - 使用建议问题快速了解论文
                - 进行多轮对话深入讨论
                
                ### ⚙️ 配置说明
                
                在使用前，请确保已配置 DeepSeek API Key:
                
                1. 复制 `env.example` 为 `.env`
                2. 填入您的 DeepSeek API Key
                
                ```
                DEEPSEEK_API_KEY=your-api-key-here
                ```
                
                ### 🔧 技术架构
                
                - **LLM**: DeepSeek Chat
                - **多智能体框架**: LangChain + LangGraph
                - **向量数据库**: ChromaDB
                - **文档解析**: PyMuPDF + python-docx
                """)
        
        # 页脚
        gr.Markdown("""
        ---
        <center>
        
        🛠️ 基于 LangChain 多智能体架构 | 📚 论文阅读助手 v1.0
        
        </center>
        """)
    
    return app


def main():
    """主函数"""
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()

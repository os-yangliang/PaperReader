<template>
  <div class="max-w-6xl mx-auto h-[calc(100vh-12rem)]">
    <div class="grid lg:grid-cols-4 gap-6 h-full">
      <!-- 左侧：文档信息 & 建议问题 -->
      <div class="lg:col-span-1 space-y-6">
        <!-- 文档状态 -->
        <div class="glass-card p-5">
          <h3 class="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <span>📄</span>
            <span>当前文档</span>
          </h3>
          
          <div v-if="isDocumentLoaded" class="space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl
                          bg-gradient-to-br from-green-500/20 to-primary-500/20 border border-green-500/30">
                ✅
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-white text-sm font-medium truncate">{{ documentInfo?.title || documentInfo?.filename }}</p>
                <p class="text-gray-500 text-xs">{{ documentInfo?.word_count?.toLocaleString() }} 字</p>
              </div>
            </div>
          </div>
          
          <div v-else class="text-center py-4">
            <div class="w-12 h-12 mx-auto rounded-xl flex items-center justify-center text-2xl mb-3
                        bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border border-yellow-500/30">
              ⚠️
            </div>
            <p class="text-gray-400 text-sm mb-4">尚未加载文档</p>
            <router-link to="/analyze" class="btn-primary text-sm px-4 py-2 inline-flex items-center gap-2">
              <span>📤</span>
              <span>上传论文</span>
            </router-link>
          </div>
        </div>
        
        <!-- 建议问题 -->
        <div v-if="isDocumentLoaded" class="glass-card p-5">
          <h3 class="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
            <span>💡</span>
            <span>建议问题</span>
          </h3>
          
          <div class="space-y-2">
            <button
              v-for="(question, index) in suggestedQuestions"
              :key="index"
              @click="askQuestion(question)"
              class="w-full text-left px-4 py-3 rounded-xl text-sm text-gray-300 
                     bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10
                     transition-all duration-300 line-clamp-2"
            >
              {{ question }}
            </button>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div v-if="messages.length > 0" class="glass-card p-5">
          <button
            @click="clearChat"
            class="btn-secondary w-full text-sm flex items-center justify-center gap-2"
          >
            <span>🗑️</span>
            <span>清除对话</span>
          </button>
        </div>
      </div>
      
      <!-- 右侧：聊天区域 -->
      <div class="lg:col-span-3 glass-card flex flex-col overflow-hidden">
        <!-- 聊天头部 -->
        <div class="px-6 py-4 border-b border-white/5 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl
                      bg-gradient-to-br from-primary-500/20 to-accent-500/20 border border-white/10">
            🤖
          </div>
          <div>
            <h2 class="text-white font-medium">论文问答助手</h2>
            <p class="text-gray-500 text-xs">基于 RAG 技术的智能问答</p>
          </div>
        </div>
        
        <!-- 聊天消息列表 -->
        <div 
          ref="messagesRef"
          class="flex-1 overflow-y-auto p-6 space-y-6"
        >
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="text-center py-12">
            <div class="w-20 h-20 mx-auto rounded-2xl flex items-center justify-center text-4xl mb-6
                        bg-gradient-to-br from-primary-500/20 to-accent-500/20 border border-white/10">
              💬
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">开始对话</h3>
            <p class="text-gray-400 max-w-md mx-auto">
              {{ isDocumentLoaded 
                ? '向我询问任何关于论文的问题，我会基于论文内容为您解答' 
                : '请先上传并分析论文，然后开始对话' 
              }}
            </p>
          </div>
          
          <!-- 消息列表 -->
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="animate-slide-up"
            :style="{ animationDelay: `${index * 0.05}s` }"
          >
            <!-- 用户消息 -->
            <div v-if="message.role === 'user'" class="flex justify-end">
              <div class="chat-bubble user">
                {{ message.content }}
              </div>
            </div>
            
            <!-- AI 消息 -->
            <div v-else class="flex gap-3">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center text-lg flex-shrink-0
                          bg-gradient-to-br from-primary-500/20 to-accent-500/20 border border-white/10">
                🤖
              </div>
              <div class="flex-1 min-w-0">
                <div class="chat-bubble assistant">
                  <div 
                    class="markdown-content" 
                    v-html="renderMarkdown(message.content)"
                  ></div>
                  <span v-if="message.isTyping" class="typing-cursor"></span>
                </div>
                
                <!-- 来源引用 -->
                <div v-if="message.sources?.length" class="mt-3 space-y-2">
                  <div class="text-xs text-gray-500 flex items-center gap-1">
                    <span>📚</span>
                    <span>参考来源</span>
                  </div>
                  <div class="space-y-2">
                    <div
                      v-for="(source, i) in message.sources.slice(0, 3)"
                      :key="i"
                      class="text-xs text-gray-400 bg-white/5 rounded-lg px-3 py-2 border border-white/5"
                    >
                      {{ source.slice(0, 150) }}{{ source.length > 150 ? '...' : '' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="isLoading" class="flex gap-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center text-lg flex-shrink-0
                        bg-gradient-to-br from-primary-500/20 to-accent-500/20 border border-white/10">
              🤖
            </div>
            <div class="chat-bubble assistant">
              <div class="loading-dots text-primary-400">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="p-4 border-t border-white/5">
          <form @submit.prevent="sendMessage" class="flex gap-3">
            <input
              v-model="inputMessage"
              type="text"
              :placeholder="isDocumentLoaded ? '输入您的问题...' : '请先上传论文文档'"
              :disabled="!isDocumentLoaded || isLoading"
              class="input-glass flex-1"
              @keydown.enter.prevent="sendMessage"
            />
            <button
              type="submit"
              :disabled="!inputMessage.trim() || !isDocumentLoaded || isLoading"
              class="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="hidden sm:inline">发送</span>
              <span class="sm:hidden">➤</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { marked } from 'marked'
import api from '../api'

// 状态
const messagesRef = ref(null)
const inputMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const isDocumentLoaded = ref(false)
const documentInfo = ref(null)
const suggestedQuestions = ref([
  '这篇论文的主要研究问题是什么？',
  '论文使用了什么方法？',
  '实验结果如何？',
  '论文的创新点是什么？',
  '有什么局限性？',
  '作者提出了哪些未来工作？'
])

// 方法
const renderMarkdown = (content) => {
  if (!content) return ''
  return marked(content)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const askQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

const sendMessage = async () => {
  const question = inputMessage.value.trim()
  if (!question || !isDocumentLoaded.value || isLoading.value) return
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: question
  })
  
  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()
  
  try {
    // 使用流式响应
    const assistantMessage = {
      role: 'assistant',
      content: '',
      isTyping: true,
      sources: []
    }
    messages.value.push(assistantMessage)
    scrollToBottom()
    
    // 尝试流式获取
    try {
      for await (const chunk of api.chatStream(question)) {
        assistantMessage.content += chunk
        scrollToBottom()
      }
    } catch (streamError) {
      // 如果流式失败，回退到普通请求
      const result = await api.chat(question)
      assistantMessage.content = result.answer
      assistantMessage.sources = result.source_chunks || []
    }
    
    assistantMessage.isTyping = false
    
    // 获取来源（如果流式没有提供）
    if (!assistantMessage.sources.length) {
      try {
        const result = await api.chat(question)
        assistantMessage.sources = result.source_chunks || []
      } catch (e) {
        // 忽略
      }
    }
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: `❌ 抱歉，发生错误：${err.message}`,
      isTyping: false
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const clearChat = async () => {
  messages.value = []
  try {
    await api.clearChat()
  } catch (e) {
    // 忽略错误
  }
}

// 监听消息变化，自动滚动
watch(messages, scrollToBottom, { deep: true })

// 加载历史对话记录
const loadChatHistory = () => {
  try {
    const savedHistory = sessionStorage.getItem('chatHistory')
    if (savedHistory) {
      const chatHistory = JSON.parse(savedHistory)
      // 转换格式
      messages.value = chatHistory.map(msg => ({
        role: msg.role,
        content: msg.content,
        sources: msg.source_chunks || [],
        isTyping: false
      }))
      // 清除 sessionStorage
      sessionStorage.removeItem('chatHistory')
      scrollToBottom()
    }
  } catch (e) {
    // 忽略错误
  }
}

// 初始化
onMounted(async () => {
  try {
    const doc = await api.getDocument()
    isDocumentLoaded.value = doc.is_loaded
    documentInfo.value = doc.info
    
    // 加载历史对话记录
    loadChatHistory()
    
    // 获取建议问题
    if (doc.is_loaded) {
      const suggestions = await api.getSuggestions()
      if (suggestions.questions?.length) {
        suggestedQuestions.value = suggestions.questions
      }
    }
  } catch (e) {
    // 忽略错误
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>


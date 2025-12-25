<template>
  <div class="max-w-7xl mx-auto">
    <h1 class="text-4xl font-bold mb-2 gradient-text">📊 论文分析</h1>
    <p class="text-gray-400 mb-8">上传您的论文文件，AI 将自动进行深度分析</p>
    
    <div class="grid lg:grid-cols-12 gap-6">
      <!-- 最左侧：历史分析面板 -->
      <div class="lg:col-span-3">
        <div class="glass-card p-4 sticky top-24">
          <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <span>📜</span>
            <span>历史分析</span>
            <span v-if="historyList.length" class="ml-auto text-xs text-gray-500 font-normal">
              {{ historyList.length }} 篇
            </span>
          </h2>
          
          <!-- 历史列表 -->
          <div v-if="historyList.length" class="space-y-2 max-h-[60vh] overflow-y-auto custom-scrollbar">
            <div 
              v-for="item in historyList" 
              :key="item.id"
              @click="loadHistoryItem(item.id)"
              class="group relative p-3 rounded-xl cursor-pointer transition-all duration-300
                     hover:bg-white/5 border border-transparent"
              :class="{ 
                'bg-gradient-to-r from-primary-500/10 to-accent-500/10 border-primary-500/30': currentHistoryId === item.id,
                'hover:border-white/10': currentHistoryId !== item.id
              }"
            >
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center text-lg flex-shrink-0
                            bg-gradient-to-br from-primary-500/20 to-accent-500/20">
                  {{ getFileIcon(item.file_type) }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-white text-sm font-medium truncate" :title="item.filename">
                    {{ item.filename }}
                  </p>
                  <p class="text-gray-500 text-xs mt-1">
                    {{ formatDate(item.analyzed_at) }}
                  </p>
                </div>
              </div>
              
              <!-- 删除按钮 -->
              <button
                @click.stop="deleteHistoryItem(item.id)"
                class="absolute top-2 right-2 w-6 h-6 rounded-lg flex items-center justify-center
                       text-gray-500 hover:text-red-400 hover:bg-red-500/10 
                       opacity-0 group-hover:opacity-100 transition-all duration-300"
                title="删除记录"
              >
                ✕
              </button>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-else class="text-center py-8">
            <div class="text-4xl mb-3 opacity-50">📭</div>
            <p class="text-gray-500 text-sm">暂无分析记录</p>
            <p class="text-gray-600 text-xs mt-1">上传论文后将自动保存</p>
          </div>
        </div>
      </div>
      
      <!-- 中间：上传区域 -->
      <div class="lg:col-span-3">
        <div class="glass-card p-6 sticky top-24">
          <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <span>📤</span>
            <span>上传文件</span>
          </h2>
          
          <!-- 拖拽上传区域 -->
          <div
            ref="dropzoneRef"
            class="dropzone"
            :class="{ 'drag-over': isDragging, 'border-green-500': file }"
            @click="triggerFileInput"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept=".pdf,.doc,.docx"
              class="hidden"
              @change="handleFileSelect"
            />
            
            <div v-if="!file" class="space-y-4">
              <div class="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center text-4xl
                          bg-gradient-to-br from-primary-500/20 to-accent-500/20 border border-white/10">
                📄
              </div>
              <div>
                <p class="text-white font-medium">拖拽文件到此处</p>
                <p class="text-gray-400 text-sm mt-1">或点击选择文件</p>
              </div>
              <div class="text-gray-500 text-xs">
                支持 PDF、Word（.doc, .docx）格式
              </div>
            </div>
            
            <div v-else class="space-y-3">
              <div class="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center text-4xl
                          bg-gradient-to-br from-green-500/20 to-primary-500/20 border border-green-500/30">
                ✅
              </div>
              <p class="text-white font-medium truncate px-4">{{ file.name }}</p>
              <p class="text-gray-400 text-sm">{{ formatFileSize(file.size) }}</p>
            </div>
          </div>
          
          <!-- 分析按钮 -->
          <button
            v-if="file && !isAnalyzing && !analysisResult"
            @click="startAnalysis"
            class="btn-primary w-full mt-6 flex items-center justify-center gap-2"
          >
            <span>🚀</span>
            <span>开始分析</span>
          </button>
          
          <!-- 分析进度 -->
          <div v-if="isAnalyzing" class="mt-6 space-y-4">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400">{{ analyzeStatus }}</span>
              <span class="text-primary-400">{{ uploadProgress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-bar-fill" :style="{ width: `${uploadProgress}%` }"></div>
            </div>
            <div class="flex justify-center">
              <div class="loading-dots text-primary-400">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
          
          <!-- 重新上传 -->
          <button
            v-if="analysisResult"
            @click="resetUpload"
            class="btn-secondary w-full mt-6 flex items-center justify-center gap-2"
          >
            <span>🔄</span>
            <span>重新上传</span>
          </button>
          
          <!-- 文档信息 -->
          <div v-if="documentInfo" class="mt-6 space-y-3">
            <h3 class="text-sm font-medium text-gray-400 flex items-center gap-2">
              <span>📋</span>
              <span>文档信息</span>
            </h3>
            <div class="glass-card-light p-4 space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-400">文件名</span>
                <span class="text-white truncate max-w-[150px]">{{ documentInfo.filename }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">类型</span>
                <span class="text-white">{{ documentInfo.file_type }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">页数</span>
                <span class="text-white">{{ documentInfo.page_count }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">字数</span>
                <span class="text-white">{{ documentInfo.word_count?.toLocaleString() }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">处理时间</span>
                <span class="text-white">{{ documentInfo.processing_time?.toFixed(2) }}s</span>
              </div>
            </div>
          </div>
          
          <!-- 快速操作 -->
          <div v-if="analysisResult" class="mt-6">
            <router-link 
              to="/chat" 
              class="btn-primary w-full flex items-center justify-center gap-2"
            >
              <span>💬</span>
              <span>开始问答</span>
            </router-link>
          </div>
        </div>
      </div>
      
      <!-- 右侧：分析结果 -->
      <div class="lg:col-span-6 space-y-6">
        <!-- 占位状态 -->
        <div v-if="!analysisResult && !isAnalyzing" class="glass-card p-12 text-center">
          <div class="w-24 h-24 mx-auto rounded-3xl flex items-center justify-center text-5xl mb-6
                      bg-gradient-to-br from-primary-500/10 to-accent-500/10 border border-white/10">
            📊
          </div>
          <h3 class="text-xl font-semibold text-white mb-3">等待分析</h3>
          <p class="text-gray-400">上传论文文件后，系统将自动进行深度分析</p>
        </div>
        
        <!-- 分析中状态 -->
        <div v-if="isAnalyzing" class="glass-card p-12 text-center">
          <div class="w-24 h-24 mx-auto rounded-3xl flex items-center justify-center text-5xl mb-6
                      bg-gradient-to-br from-primary-500/20 to-accent-500/20 border border-white/10 animate-pulse-slow">
            ⚡
          </div>
          <h3 class="text-xl font-semibold text-white mb-3">正在分析中...</h3>
          <p class="text-gray-400">AI 正在解析您的论文，请稍候</p>
        </div>
        
        <!-- 分析结果 -->
        <template v-if="analysisResult">
          <!-- Tab 切换 -->
          <div class="glass-card p-2 flex gap-2">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              class="flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all duration-300"
              :class="activeTab === tab.key 
                ? 'bg-gradient-to-r from-primary-500/20 to-accent-500/20 text-white border border-white/10' 
                : 'text-gray-400 hover:text-white hover:bg-white/5'"
            >
              <span class="mr-2">{{ tab.icon }}</span>
              {{ tab.label }}
            </button>
          </div>
          
          <!-- 结构分析 -->
          <div v-show="activeTab === 'structure'" class="glass-card p-6 animate-fade-in">
            <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>📋</span>
              <span>论文结构</span>
            </h3>
            <div class="markdown-content prose prose-invert max-w-none" v-html="renderedStructure"></div>
          </div>
          
          <!-- 详细摘要 -->
          <div v-show="activeTab === 'summary'" class="glass-card p-6 animate-fade-in">
            <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>📝</span>
              <span>详细分析</span>
            </h3>
            <div class="markdown-content prose prose-invert max-w-none" v-html="renderedSummary"></div>
          </div>
        </template>
        
        <!-- 错误提示 -->
        <div v-if="error" class="glass-card p-6 border border-red-500/30 bg-red-500/10">
          <div class="flex items-start gap-4">
            <div class="text-3xl">❌</div>
            <div>
              <h3 class="text-lg font-semibold text-red-400 mb-2">分析失败</h3>
              <p class="text-gray-400">{{ error }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import api from '../api'

// 状态
const fileInputRef = ref(null)
const dropzoneRef = ref(null)
const file = ref(null)
const isDragging = ref(false)
const isAnalyzing = ref(false)
const uploadProgress = ref(0)
const analyzeStatus = ref('')
const analysisResult = ref(null)
const documentInfo = ref(null)
const error = ref(null)
const activeTab = ref('structure')

// 历史记录状态
const historyList = ref([])
const currentHistoryId = ref(null)
const isLoadingHistory = ref(false)

const tabs = [
  { key: 'structure', icon: '📋', label: '结构分析' },
  { key: 'summary', icon: '📝', label: '详细摘要' }
]

// 计算属性
const renderedStructure = computed(() => {
  if (!analysisResult.value?.structure) return ''
  return marked(analysisResult.value.structure)
})

const renderedSummary = computed(() => {
  if (!analysisResult.value?.summary) return ''
  return marked(analysisResult.value.summary)
})

// 方法
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (e) => {
  const selectedFile = e.target.files?.[0]
  if (selectedFile) {
    file.value = selectedFile
    error.value = null
  }
}

const handleDrop = (e) => {
  isDragging.value = false
  const droppedFile = e.dataTransfer.files?.[0]
  if (droppedFile) {
    // 检查文件类型
    const ext = droppedFile.name.split('.').pop()?.toLowerCase()
    if (['pdf', 'doc', 'docx'].includes(ext)) {
      file.value = droppedFile
      error.value = null
    } else {
      error.value = '不支持的文件格式，请上传 PDF 或 Word 文档'
    }
  }
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const startAnalysis = async () => {
  if (!file.value) return
  
  isAnalyzing.value = true
  uploadProgress.value = 0
  analyzeStatus.value = '正在上传文件...'
  error.value = null
  
  try {
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 30) {
        uploadProgress.value += 2
      }
    }, 100)
    
    // 上传并分析
    analyzeStatus.value = '正在分析论文...'
    const result = await api.uploadAndAnalyze(file.value, (progress) => {
      uploadProgress.value = Math.max(uploadProgress.value, progress * 0.3)
    })
    
    clearInterval(progressInterval)
    
    // 模拟分析进度
    uploadProgress.value = 50
    analyzeStatus.value = '正在生成分析报告...'
    
    await new Promise(resolve => setTimeout(resolve, 500))
    uploadProgress.value = 100
    
    if (result.success) {
      analysisResult.value = result
      documentInfo.value = result.document_info
      analyzeStatus.value = '分析完成！'
      // 刷新历史列表
      await fetchHistory()
    } else {
      throw new Error(result.error || '分析失败')
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isAnalyzing.value = false
  }
}

const resetUpload = async () => {
  file.value = null
  analysisResult.value = null
  documentInfo.value = null
  error.value = null
  uploadProgress.value = 0
  currentHistoryId.value = null
  
  // 清除后端文档
  try {
    await api.clearDocument()
  } catch (e) {
    // 忽略错误
  }
}

// 历史记录相关方法
const fetchHistory = async () => {
  try {
    console.log('[Analyze] 正在获取历史记录...')
    const res = await api.getHistory()
    console.log('[Analyze] 获取到历史记录:', res)
    historyList.value = res.history || []
    currentHistoryId.value = res.current_id
    console.log('[Analyze] historyList 更新为:', historyList.value)
  } catch (e) {
    console.error('[Analyze] 获取历史记录失败:', e)
  }
}

const loadHistoryItem = async (historyId) => {
  if (isLoadingHistory.value || historyId === currentHistoryId.value) return
  
  isLoadingHistory.value = true
  error.value = null
  
  try {
    const res = await api.loadHistory(historyId)
    if (res.success) {
      currentHistoryId.value = historyId
      documentInfo.value = res.document_info
      analysisResult.value = {
        structure: res.structure,
        summary: res.summary
      }
      file.value = null  // 清除文件选择状态
      
      // 将对话历史存储到 sessionStorage，供 Chat 页面使用
      if (res.chat_history && res.chat_history.length > 0) {
        sessionStorage.setItem('chatHistory', JSON.stringify(res.chat_history))
      } else {
        sessionStorage.removeItem('chatHistory')
      }
    }
  } catch (e) {
    error.value = e.message
  } finally {
    isLoadingHistory.value = false
  }
}

const deleteHistoryItem = async (historyId) => {
  try {
    await api.deleteHistory(historyId)
    // 从列表中移除
    historyList.value = historyList.value.filter(h => h.id !== historyId)
    // 如果删除的是当前显示的，清除显示
    if (currentHistoryId.value === historyId) {
      currentHistoryId.value = null
      analysisResult.value = null
      documentInfo.value = null
    }
  } catch (e) {
    // 忽略错误
  }
}

const getFileIcon = (fileType) => {
  const type = (fileType || '').toLowerCase()
  if (type.includes('pdf')) return '📕'
  if (type.includes('doc')) return '📘'
  return '📄'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    
    // 小于1分钟
    if (diff < 60000) return '刚刚'
    // 小于1小时
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
    // 小于24小时
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
    // 小于7天
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
    // 其他
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return ''
  }
}

// 初始化时检查是否已有文档并获取历史记录
onMounted(async () => {
  // 获取历史记录
  await fetchHistory()
  
  try {
    const doc = await api.getDocument()
    if (doc.is_loaded) {
      documentInfo.value = doc.info
      analysisResult.value = {
        structure: doc.structure,
        summary: doc.summary
      }
    }
  } catch (e) {
    // 忽略错误
  }
})
</script>


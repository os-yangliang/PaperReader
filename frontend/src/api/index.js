import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5分钟超时，因为分析可能需要较长时间
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default {
  // 获取系统状态
  getStatus() {
    return api.get('/status')
  },

  // 获取文档信息
  getDocument() {
    return api.get('/document')
  },

  // 上传并分析文档
  async uploadAndAnalyze(file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  },

  // 发送聊天消息
  chat(message) {
    return api.post('/chat', { message })
  },

  // 流式聊天
  async *chatStream(message) {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.chunk) {
              yield data.chunk
            }
            if (data.done) {
              return
            }
            if (data.error) {
              throw new Error(data.error)
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  },

  // 获取建议问题
  getSuggestions() {
    return api.get('/suggestions')
  },

  // 清除聊天历史
  clearChat() {
    return api.post('/clear')
  },

  // 清除文档
  clearDocument() {
    return api.delete('/document')
  },

  // 获取分析历史列表
  getHistory() {
    return api.get('/history')
  },

  // 获取历史记录详情
  getHistoryDetail(historyId) {
    return api.get(`/history/${historyId}`)
  },

  // 加载历史记录
  loadHistory(historyId) {
    return api.post(`/history/${historyId}/load`)
  },

  // 删除历史记录
  deleteHistory(historyId) {
    return api.delete(`/history/${historyId}`)
  },

  // 获取历史对话记录
  getHistoryChat(historyId) {
    return api.get(`/history/${historyId}/chat`)
  }
}


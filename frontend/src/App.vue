<template>
  <div class="min-h-screen relative">
    <!-- 背景效果 -->
    <div class="bg-mesh"></div>
    <div class="bg-grid"></div>
    
    <!-- 导航栏 -->
    <nav class="fixed top-0 left-0 right-0 z-50 glass-card border-0 border-b border-white/5">
      <div class="max-w-7xl mx-auto px-6">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <router-link to="/" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-2xl 
                        bg-gradient-to-br from-primary-500 to-accent-500 
                        group-hover:shadow-glow transition-all duration-300">
              📚
            </div>
            <span class="font-display text-xl font-semibold gradient-text">
              论文阅读助手
            </span>
          </router-link>
          
          <!-- 导航链接 -->
          <div class="flex items-center gap-2">
            <template v-for="link in navLinks" :key="link.to || link.label">
              <!-- 普通路由链接 -->
              <router-link 
                v-if="link.to"
                :to="link.to"
                class="nav-link px-4 py-2 rounded-lg text-gray-400 hover:text-white 
                       hover:bg-white/5 transition-all duration-300"
                :class="{ 'text-white bg-white/10': $route.path === link.to }"
              >
                <span class="mr-2">{{ link.icon }}</span>
                {{ link.label }}
              </router-link>
              <!-- 功能开发中的按钮 -->
              <button
                v-else
                @click="showDevToast"
                class="nav-link px-4 py-2 rounded-lg text-gray-400 hover:text-white 
                       hover:bg-white/5 transition-all duration-300 cursor-pointer"
              >
                <span class="mr-2">{{ link.icon }}</span>
                {{ link.label }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </nav>
    
    <!-- 功能开发中提示 Toast -->
    <Transition name="toast">
      <div 
        v-if="showToast" 
        class="fixed top-24 left-1/2 -translate-x-1/2 z-[100] 
               glass-card px-6 py-3 rounded-xl border border-amber-500/30 
               bg-gradient-to-r from-amber-500/10 to-orange-500/10
               shadow-lg shadow-amber-500/10"
      >
        <div class="flex items-center gap-3">
          <span class="text-2xl animate-bounce">🚧</span>
          <span class="text-amber-300 font-medium">功能开发中，敬请期待！</span>
        </div>
      </div>
    </Transition>
    
    <!-- 主内容区 -->
    <main class="relative z-10 pt-24 pb-12 px-6">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <!-- 页脚 -->
    <footer class="relative z-10 border-t border-white/5 py-6">
      <div class="max-w-7xl mx-auto px-6 text-center text-gray-500 text-sm">
        <p>🛠️ 基于 LangChain 多智能体架构 | 📚 论文阅读助手 v2.0</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const navLinks = [
  { to: '/', icon: '🏠', label: '首页' },
  { to: '/analyze', icon: '📊', label: '分析' },
  { to: '/chat', icon: '💬', label: '问答' },
  { to: null, icon: '💻', label: '代码' }  // 功能开发中
]

// Toast 提示
const showToast = ref(false)
let toastTimer = null

const showDevToast = () => {
  showToast.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    showToast.value = false
  }, 2000)
}
</script>

<style scoped>
.page-enter-active {
  animation: slideUp 0.4s ease-out;
}

.page-leave-active {
  animation: fadeOut 0.2s ease-in;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

/* Toast 动画 */
.toast-enter-active {
  animation: toastIn 0.3s ease-out;
}

.toast-leave-active {
  animation: toastOut 0.3s ease-in;
}

@keyframes toastIn {
  from {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

@keyframes toastOut {
  from {
    opacity: 1;
    transform: translate(-50%, 0);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
}
</style>


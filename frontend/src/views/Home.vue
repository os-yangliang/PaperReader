<template>
  <div class="max-w-6xl mx-auto">
    <!-- Hero Section -->
    <section class="text-center py-16 animate-fade-in">
      <!-- 装饰性图标 -->
      <div class="relative inline-block mb-8">
        <div class="w-32 h-32 rounded-3xl flex items-center justify-center text-7xl
                    bg-gradient-to-br from-primary-500/20 to-accent-500/20
                    border border-white/10 animate-float">
          📚
        </div>
        <!-- 光晕效果 -->
        <div class="absolute inset-0 rounded-3xl bg-gradient-to-br from-primary-500 to-accent-500 opacity-20 blur-2xl"></div>
      </div>
      
      <h1 class="text-5xl md:text-6xl font-display font-bold mb-6">
        <span class="gradient-text">论文阅读</span>
        <span class="text-white">多智能体系统</span>
      </h1>
      
      <p class="text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
        基于 <span class="text-primary-400 font-medium">LangChain + LangGraph</span> 构建的智能论文分析与问答系统
        <br>
        让 AI 帮您深度理解学术论文
      </p>
      
      <!-- CTA 按钮 -->
      <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
        <router-link to="/analyze" class="btn-primary text-lg px-8 py-4 flex items-center gap-2">
          <span>🚀</span>
          <span>开始分析论文</span>
        </router-link>
        <router-link to="/chat" class="btn-secondary text-lg px-8 py-4 flex items-center gap-2">
          <span>💬</span>
          <span>智能问答</span>
        </router-link>
      </div>
    </section>
    
    <!-- 功能特点 -->
    <section class="py-16">
      <h2 class="text-3xl font-bold text-center mb-12 gradient-text">核心功能</h2>
      
      <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div 
          v-for="(feature, index) in features" 
          :key="feature.title"
          class="glass-card p-6 doc-card"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl mb-4
                      bg-gradient-to-br from-primary-500/20 to-accent-500/20 border border-white/10">
            {{ feature.icon }}
          </div>
          <h3 class="text-lg font-semibold text-white mb-2">{{ feature.title }}</h3>
          <p class="text-gray-400 text-sm leading-relaxed">{{ feature.desc }}</p>
        </div>
      </div>
    </section>
    
    <!-- 代码生成 -->
    <section class="py-16">
      <h2 class="text-3xl font-bold text-center mb-12 gradient-text">代码生成</h2>
      <p class="text-center text-gray-400 mb-8 max-w-2xl mx-auto">
        根据论文所提方法，AI 自动分析并生成对应的实现代码
      </p>
      
      <div class="glass-card p-6 overflow-hidden">
        <!-- 代码生成演示 -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl
                        bg-gradient-to-br from-green-500/20 to-primary-500/20 border border-white/10">
              💻
            </div>
            <div>
              <h3 class="text-white font-medium">自动代码生成</h3>
              <p class="text-gray-500 text-xs">基于论文方法论自动生成实现代码</p>
            </div>
          </div>
          <div class="flex gap-2">
            <span class="px-3 py-1 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">Python</span>
            <span class="px-3 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">PyTorch</span>
          </div>
        </div>
        
        <!-- 代码展示区 -->
        <div class="bg-dark-900/80 rounded-xl p-4 font-mono text-sm overflow-x-auto border border-white/5">
          <div class="flex items-center gap-2 mb-4 pb-3 border-b border-white/10">
            <div class="w-3 h-3 rounded-full bg-red-500/80"></div>
            <div class="w-3 h-3 rounded-full bg-yellow-500/80"></div>
            <div class="w-3 h-3 rounded-full bg-green-500/80"></div>
            <span class="ml-2 text-gray-500 text-xs">model.py - 根据论文方法生成</span>
          </div>
          <pre class="text-gray-300 leading-relaxed"><span class="text-purple-400">import</span> <span class="text-blue-300">torch</span>
<span class="text-purple-400">import</span> <span class="text-blue-300">torch.nn</span> <span class="text-purple-400">as</span> <span class="text-blue-300">nn</span>

<span class="text-purple-400">class</span> <span class="text-yellow-400">AttentionModule</span>(<span class="text-blue-300">nn.Module</span>):
    <span class="text-gray-500">"""基于论文提出的注意力机制实现"""</span>
    
    <span class="text-purple-400">def</span> <span class="text-green-400">__init__</span>(<span class="text-orange-400">self</span>, dim, heads=<span class="text-cyan-400">8</span>):
        <span class="text-blue-300">super</span>().__init__()
        <span class="text-orange-400">self</span>.heads = heads
        <span class="text-orange-400">self</span>.scale = dim ** -<span class="text-cyan-400">0.5</span>
        <span class="text-orange-400">self</span>.qkv = <span class="text-blue-300">nn.Linear</span>(dim, dim * <span class="text-cyan-400">3</span>)
        <span class="text-orange-400">self</span>.proj = <span class="text-blue-300">nn.Linear</span>(dim, dim)
    
    <span class="text-purple-400">def</span> <span class="text-green-400">forward</span>(<span class="text-orange-400">self</span>, x):
        <span class="text-gray-500"># 论文公式 (3): Multi-head Attention</span>
        qkv = <span class="text-orange-400">self</span>.qkv(x).chunk(<span class="text-cyan-400">3</span>, dim=-<span class="text-cyan-400">1</span>)
        q, k, v = <span class="text-blue-300">map</span>(<span class="text-purple-400">lambda</span> t: t.view(...), qkv)
        attn = (q @ k.transpose(-<span class="text-cyan-400">2</span>, -<span class="text-cyan-400">1</span>)) * <span class="text-orange-400">self</span>.scale
        <span class="text-purple-400">return</span> <span class="text-orange-400">self</span>.proj(attn.softmax(dim=-<span class="text-cyan-400">1</span>) @ v)</pre>
        </div>
        
        <!-- 功能说明 -->
        <div class="grid md:grid-cols-3 gap-4 mt-6">
          <div class="glass-card-light p-4 text-center">
            <div class="text-2xl mb-2">🔍</div>
            <h4 class="text-white text-sm font-medium mb-1">方法提取</h4>
            <p class="text-gray-500 text-xs">自动识别论文核心算法</p>
          </div>
          <div class="glass-card-light p-4 text-center">
            <div class="text-2xl mb-2">⚡</div>
            <h4 class="text-white text-sm font-medium mb-1">代码转换</h4>
            <p class="text-gray-500 text-xs">将公式转为可执行代码</p>
          </div>
          <div class="glass-card-light p-4 text-center">
            <div class="text-2xl mb-2">📦</div>
            <h4 class="text-white text-sm font-medium mb-1">框架适配</h4>
            <p class="text-gray-500 text-xs">支持主流深度学习框架</p>
          </div>
        </div>
      </div>
    </section>
    
    <!-- 使用流程 -->
    <section class="py-16">
      <h2 class="text-3xl font-bold text-center mb-12 gradient-text">使用流程</h2>
      
      <div class="grid md:grid-cols-3 gap-8">
        <div 
          v-for="(step, index) in steps" 
          :key="step.title"
          class="relative"
        >
          <!-- 连接线 -->
          <div 
            v-if="index < steps.length - 1"
            class="hidden md:block absolute top-16 left-1/2 w-full h-0.5 bg-gradient-to-r from-primary-500/50 to-accent-500/50"
          ></div>
          
          <div class="glass-card p-8 text-center relative z-10">
            <div class="w-16 h-16 rounded-full flex items-center justify-center text-4xl mb-6 mx-auto
                        bg-gradient-to-br from-primary-500 to-accent-500 shadow-glow">
              {{ step.icon }}
            </div>
            <div class="text-sm text-primary-400 font-medium mb-2">步骤 {{ index + 1 }}</div>
            <h3 class="text-xl font-semibold text-white mb-3">{{ step.title }}</h3>
            <p class="text-gray-400 text-sm">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>
    
    <!-- 底部 CTA -->
    <section class="py-16 text-center">
      <div class="glass-card p-12 relative overflow-hidden">
        <!-- 背景装饰 -->
        <div class="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-accent-500/10"></div>
        
        <div class="relative z-10">
          <h2 class="text-3xl font-bold text-white mb-4">准备好了吗？</h2>
          <p class="text-gray-400 mb-8">上传您的论文，让 AI 为您提供深度分析</p>
          <router-link to="/analyze" class="btn-primary text-lg px-10 py-4 inline-flex items-center gap-2">
            <span>📄</span>
            <span>上传论文开始</span>
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
const features = [
  {
    icon: '🔍',
    title: '文档解析',
    desc: '支持 PDF 和 Word 格式，智能提取文档内容与结构'
  },
  {
    icon: '📊',
    title: '智能分析',
    desc: '自动生成结构化分析报告，包含方法、结果、创新点等'
  },
  {
    icon: '💬',
    title: '智能问答',
    desc: '基于 RAG 技术，精准回答论文相关问题'
  },
  {
    icon: '💻',
    title: '代码生成',
    desc: '根据论文方法自动生成对应实现代码'
  }
]

const steps = [
  {
    icon: '📤',
    title: '上传论文',
    desc: '支持 PDF、Word 格式的学术论文'
  },
  {
    icon: '⚡',
    title: '自动分析',
    desc: '系统自动解析并生成详细分析报告'
  },
  {
    icon: '💡',
    title: '智能问答',
    desc: '向 AI 询问任何关于论文的问题'
  }
]
</script>


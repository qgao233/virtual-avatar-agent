<template>
  <div class="app-container">
    <!-- 使用 GridLayout 组件创建 1行2列布局 -->
    <GridLayout
      :rows="1"
      :columns="2"
      :gap="12"
      :default-column-ratios="[0.8, 0.2]"
    >
      <!-- 第1列: 视频显示区域 -->
      <template #cell-0>
        <VideoDisplay
          ref="videoDisplayRef"
          :auto-start="true"
          @stream-ready="handleStreamReady"
          @stream-error="handleStreamError"
        />
      </template>

      <!-- 第2列: 聊天面板 -->
      <template #cell-1>
        <ChatPanel
          ref="chatPanelRef"
          username="我"
          remote-name="对方"
          @send-message="handleSendMessage"
          @typing="handleTyping"
        />
      </template>
    </GridLayout>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import GridLayout from './components/GridLayout.vue'
import VideoDisplay from './components/VideoDisplay.vue'
import ChatPanel from './components/ChatPanel.vue'

// 组件引用
const videoDisplayRef = ref<InstanceType<typeof VideoDisplay> | null>(null)
const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null)

/**
 * 处理视频流就绪
 */
const handleStreamReady = (stream: MediaStream) => {
  console.log('本地视频流就绪:', stream)
  // TODO: 可以在这里将流发送到后端或其他端点
}

/**
 * 处理视频流错误
 */
const handleStreamError = (error: Error) => {
  console.error('视频流错误:', error)
  alert('无法访问摄像头，请检查权限设置')
}

/**
 * 处理发送消息
 */
const handleSendMessage = (message: string) => {
  console.log('发送消息:', message)
  // TODO: 发送消息到后端 API
  // 示例: 模拟收到回复
  setTimeout(() => {
    chatPanelRef.value?.receiveMessage('收到你的消息: ' + message)
  }, 1000)
}

/**
 * 处理正在输入
 */
const handleTyping = (isTyping: boolean) => {
  console.log('正在输入:', isTyping)
  // TODO: 通知对方正在输入
}
</script>

<style scoped>
.app-container {
  width: 100vw;
  height: 100vh;
  padding: 16px;
  box-sizing: border-box;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 全局样式重置 */
:deep(*) {
  box-sizing: border-box;
}
</style>

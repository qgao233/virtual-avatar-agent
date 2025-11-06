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
          @asr-partial-text="handleAsrPartialText"
          @asr-final-text="handleAsrFinalText"
          @asr-speech-start="handleAsrSpeechStart"
          @asr-speech-stop="handleAsrSpeechStop"
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
  // 标记为正在发送/系统回复中
  chatPanelRef.value?.setSending(true)
  
  // TODO: 发送消息到后端 API
  // 示例: 模拟收到回复
  setTimeout(() => {
    chatPanelRef.value?.receiveMessage('收到你的消息: ' + message)
    
    // 回复完成，允许用户继续发送
    chatPanelRef.value?.setSending(false)
  }, 2000)
}

/**
 * 处理正在输入
 */
const handleTyping = (isTyping: boolean) => {
  console.log('正在输入:', isTyping)
  // TODO: 通知对方正在输入
}

/**
 * 处理 ASR 部分识别结果
 */
const handleAsrPartialText = (text: string) => {
  // 更新聊天面板的输入区域
  chatPanelRef.value?.updateVoiceText(text)
}

/**
 * 处理 ASR 最终识别结果
 */
const handleAsrFinalText = (text: string) => {
  // 更新聊天面板的输入区域
  chatPanelRef.value?.updateVoiceText(text)
}

/**
 * 处理语音开始
 */
const handleAsrSpeechStart = () => {
  // 禁用输入区域，保存当前文字
  chatPanelRef.value?.startVoiceInput()
}

/**
 * 处理语音停止
 */
const handleAsrSpeechStop = () => {
  // 自动发送识别的文字，恢复之前的文字
  chatPanelRef.value?.endVoiceInput()
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

<template>
  <div class="chat-panel">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <div class="header-title">
        <span class="title-icon">💬</span>
        <span class="title-text">聊天</span>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="clearMessages" title="清空消息">
          🗑️
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div ref="messagesContainerRef" class="messages-container">
      <div
        v-for="(message, index) in messages"
        :key="message.id"
        class="message-wrapper"
        :class="{ 'message-self': message.isSelf }"
      >
        <div class="message-bubble">
          <div class="message-header">
            <span class="message-sender">{{ message.sender }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-content">{{ message.content }}</div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">💭</div>
        <div class="empty-text">暂无消息</div>
      </div>

      <!-- 正在输入提示 -->
      <div v-if="isTyping" class="typing-indicator">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-text">对方正在输入...</span>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-container">
      <div class="input-wrapper">
        <textarea
          ref="inputRef"
          v-model="inputMessage"
          class="message-input"
          :class="{ 'voice-input': isVoiceInput }"
          :placeholder="isVoiceInput ? '🎤 语音输入中...' : '输入消息...'"
          :disabled="isVoiceInput"
          :readonly="isVoiceInput"
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.shift.enter.exact="handleShiftEnter"
          @input="handleInput"
        ></textarea>
        <button
          class="send-btn"
          :disabled="!inputMessage.trim() || isSending || isVoiceInput"
          @click="sendMessage"
          :title="isSending ? '系统回复中...' : '发送消息'"
        >
          <span class="send-icon">{{ isSending ? '⏳' : '📤' }}</span>
        </button>
      </div>
      <div class="input-hint">
        <span v-if="isVoiceInput" class="voice-hint">🎤 正在语音输入...</span>
        <span v-else-if="voiceInputStarted && !isVoiceInput" class="voice-hint">⏳ 等待识别完成...</span>
        <span v-else-if="isSending" class="sending-hint">⏳ 系统回复中...</span>
        <span v-else>按 Enter 发送，Shift + Enter 换行</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

interface Message {
  id: string
  sender: string
  content: string
  timestamp: Date
  isSelf: boolean
}

interface Props {
  /** 当前用户名 */
  username?: string
  /** 对方用户名 */
  remoteName?: string
}

const props = withDefaults(defineProps<Props>(), {
  username: '我',
  remoteName: '对方'
})

const emit = defineEmits<{
  sendMessage: [message: string]
  typing: [isTyping: boolean]
}>()

// 消息列表
const messages = ref<Message[]>([])

// 输入框
const inputMessage = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const messagesContainerRef = ref<HTMLDivElement | null>(null)

// 状态
const isTyping = ref(false)
const isVoiceInput = ref(false) // 语音输入中
const isSending = ref(false) // 正在发送/系统回复中
const savedInput = ref('') // 保存的用户输入
const voiceInputStarted = ref(false) // 语音是否已经开始（用于判断是否应该回显）
const pendingVoiceText = ref('') // 等待发送的语音文字

/**
 * 发送消息
 */
const sendMessage = () => {
  const content = inputMessage.value.trim()
  if (!content) return

  const message: Message = {
    id: Date.now().toString(),
    sender: props.username,
    content,
    timestamp: new Date(),
    isSelf: true
  }

  messages.value.push(message)
  inputMessage.value = ''

  // 发送事件给父组件
  emit('sendMessage', content)

  // 滚动到底部
  scrollToBottom()

  // 重置输入框高度
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
}

/**
 * 接收消息
 */
const receiveMessage = (content: string, sender?: string) => {
  const message: Message = {
    id: Date.now().toString(),
    sender: sender || props.remoteName,
    content,
    timestamp: new Date(),
    isSelf: false
  }

  messages.value.push(message)
  scrollToBottom()
}

/**
 * 清空消息
 */
const clearMessages = () => {
  if (messages.value.length === 0) return
  
  if (confirm('确定要清空所有消息吗?')) {
    messages.value = []
  }
}

/**
 * 处理 Shift + Enter
 */
const handleShiftEnter = (e: KeyboardEvent) => {
  // 允许换行，不做处理
}

/**
 * 处理输入
 */
const handleInput = () => {
  // 自动调整输入框高度
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = `${Math.min(inputRef.value.scrollHeight, 120)}px`
  }

  // 触发正在输入事件
  emit('typing', inputMessage.value.length > 0)
}

/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainerRef.value) {
      messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
    }
  })
}

/**
 * 格式化时间
 */
const formatTime = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }

  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }

  // 今天
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  // 其他
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 设置对方正在输入状态
 */
const setTyping = (typing: boolean) => {
  isTyping.value = typing
}

/**
 * 开始语音输入
 */
const startVoiceInput = () => {
  if (isVoiceInput.value) return
  
  // 保存当前输入的文字
  savedInput.value = inputMessage.value
  
  // 清空输入区域
  inputMessage.value = ''
  
  // 标记为语音输入中
  isVoiceInput.value = true
  voiceInputStarted.value = true
  pendingVoiceText.value = ''
  
  console.log('🎤 开始语音输入，已保存文字:', savedInput.value)
}

/**
 * 更新语音识别的文字（partial 或 final）
 */
const updateVoiceText = (text: string) => {
  // 只有在 speech_start 之后才回显文字
  if (!voiceInputStarted.value) {
    console.log('⚠️  语音未开始，忽略文字:', text)
    return
  }
  
  // 如果语音输入已经结束（等待发送），则累积文字
  if (!isVoiceInput.value) {
    pendingVoiceText.value = text
    return
  }
  
  // 正常回显到输入区域
  inputMessage.value = text
  pendingVoiceText.value = text
  
  console.log('📝 回显语音文字:', text)
  
  // 自动调整输入框高度
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = `${Math.min(inputRef.value.scrollHeight, 120)}px`
  }
}

/**
 * 结束语音输入并延迟发送
 * 等待可能还在传输的 final_text
 */
const endVoiceInput = () => {
  if (!isVoiceInput.value) return
  
  console.log('⏹️  检测到语音停止，准备发送...')
  
  // 标记语音输入已结束（但不立即发送）
  isVoiceInput.value = false
  
  // 延迟 500ms 发送，等待可能的 final_text
  setTimeout(() => {
    // 使用最新的文字（可能在延迟期间更新）
    const voiceText = (pendingVoiceText.value || inputMessage.value).trim()
    
    console.log('📤 延迟后发送语音文字:', voiceText)
    
    // 如果有识别到的文字，自动发送
    if (voiceText) {
      // 临时设置输入框内容为最终文字
      inputMessage.value = voiceText
      sendMessage()
    }
    
    // 恢复之前保存的文字
    inputMessage.value = savedInput.value
    savedInput.value = ''
    
    // 重置语音输入状态
    voiceInputStarted.value = false
    pendingVoiceText.value = ''
    
    // 重置输入框高度
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
      inputRef.value.style.height = `${Math.min(inputRef.value.scrollHeight, 120)}px`
    }
  }, 500) // 延迟 500ms
}

/**
 * 设置发送状态（系统回复时禁用发送）
 */
const setSending = (sending: boolean) => {
  isSending.value = sending
}

// 监听消息变化，自动滚动
watch(
  () => messages.value.length,
  () => {
    scrollToBottom()
  }
)

// 暴露方法给父组件
defineExpose({
  receiveMessage,
  clearMessages,
  setTyping,
  startVoiceInput,
  updateVoiceText,
  endVoiceInput,
  setSending
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

/* 聊天头部 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #fff;
  border-bottom: 1px solid #e5e5e5;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.title-icon {
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.2s ease;
}

.action-btn:hover {
  background: #f0f0f0;
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #999;
}

/* 消息气泡 */
.message-wrapper {
  display: flex;
  justify-content: flex-start;
  animation: messageSlideIn 0.3s ease;
}

.message-wrapper.message-self {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-self .message-bubble {
  background: #3b82f6;
  color: #fff;
}

.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  opacity: 0.7;
}

.message-sender {
  font-weight: 500;
}

.message-time {
  font-size: 11px;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
}

/* 正在输入提示 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 12px;
  width: fit-content;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #999;
  animation: typingBounce 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

.typing-text {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

/* 输入区域 */
.input-container {
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e5e5e5;
}

.input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.2s ease;
  min-height: 40px;
  max-height: 120px;
}

.message-input:focus {
  border-color: #3b82f6;
}

.message-input.voice-input {
  background: #f0f9ff;
  border-color: #3b82f6;
  color: #1e40af;
  cursor: not-allowed;
}

.message-input:disabled {
  opacity: 0.7;
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: #e5e5e5;
  cursor: not-allowed;
}

.send-icon {
  font-size: 18px;
}

.input-hint {
  margin-top: 6px;
  font-size: 11px;
  color: #999;
  text-align: center;
}

.voice-hint {
  color: #3b82f6;
  font-weight: 500;
}

.sending-hint {
  color: #f59e0b;
  font-weight: 500;
}

/* 动画 */
@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typingBounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-6px);
  }
}
</style>


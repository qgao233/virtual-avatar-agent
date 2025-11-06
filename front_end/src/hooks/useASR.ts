/**
 * 语音识别 Hook
 * 使用 WebSocket 连接后端实时语音识别服务
 */
import { ref, onUnmounted } from 'vue'

export interface ASRConfig {
  /** WebSocket URL */
  url?: string
  /** 是否自动重连 */
  autoReconnect?: boolean
  /** 重连间隔（毫秒） */
  reconnectInterval?: number
  /** 最大重连次数 */
  maxReconnectAttempts?: number
  /** 是否打印详细日志 */
  verbose?: boolean
  /** 事件回调 */
  onPartialText?: (text: string) => void
  onFinalText?: (text: string) => void
  onSpeechStart?: () => void
  onSpeechStop?: () => void
  onConnected?: (sessionId: string) => void
  onError?: (error: string) => void
}

export interface ASRMessage {
  type: 'connected' | 'partial' | 'final' | 'speech_start' | 'speech_stop' | 'error'
  text?: string
  session_id?: string
  asr_session_id?: string
  message?: string
}

export function useASR(config: ASRConfig = {}) {
  const {
    url = 'ws://localhost:8000/api/sr/realtime',
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    verbose = true,
    onPartialText,
    onFinalText,
    onSpeechStart,
    onSpeechStop,
    onConnected,
    onError
  } = config

  // 状态
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const sessionId = ref<string | null>(null)
  const error = ref<string | null>(null)

  // WebSocket 实例
  let ws: WebSocket | null = null
  let reconnectAttempts = 0
  let reconnectTimer: number | null = null

  /**
   * 建立 WebSocket 连接
   */
  const connect = () => {
    if (isConnecting.value || isConnected.value) {
      if (verbose) console.log('⚠️  ASR 已连接或正在连接中')
      return
    }

    isConnecting.value = true
    error.value = null

    if (verbose) console.log('🔌 正在连接 ASR WebSocket...', url)

    try {
      ws = new WebSocket(url)

      ws.onopen = () => {
        isConnected.value = true
        isConnecting.value = false
        reconnectAttempts = 0
        if (verbose) console.log('✓ ASR WebSocket 已连接')
      }

      ws.onmessage = (event) => {
        try {
          const data: ASRMessage = JSON.parse(event.data)
          
          if (verbose) {
            console.log('📨 收到 ASR 消息:', data)
          }

          handleMessage(data)
        } catch (e) {
          console.error('❌ 解析 ASR 消息失败:', e)
        }
      }

      ws.onerror = (event) => {
        console.error('❌ ASR WebSocket 错误:', event)
        error.value = 'WebSocket 连接错误'
      }

      ws.onclose = (event) => {
        isConnected.value = false
        isConnecting.value = false
        sessionId.value = null

        if (verbose) {
          console.log('✗ ASR WebSocket 已断开', {
            code: event.code,
            reason: event.reason
          })
        }

        // 自动重连
        if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          if (verbose) {
            console.log(`🔄 尝试重连 ASR (${reconnectAttempts}/${maxReconnectAttempts})...`)
          }
          reconnectTimer = window.setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          error.value = '达到最大重连次数'
          if (verbose) console.log('❌ 达到最大重连次数，停止重连')
        }
      }
    } catch (e) {
      console.error('❌ 创建 WebSocket 失败:', e)
      isConnecting.value = false
      error.value = '创建 WebSocket 失败'
    }
  }

  /**
   * 断开连接
   */
  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    if (ws) {
      if (verbose) console.log('🔌 正在断开 ASR WebSocket...')
      
      // 发送停止命令
      if (ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify({ action: 'stop' }))
        } catch (e) {
          console.error('发送停止命令失败:', e)
        }
      }

      ws.close()
      ws = null
    }

    isConnected.value = false
    isConnecting.value = false
    sessionId.value = null
    reconnectAttempts = 0
  }

  /**
   * 发送音频数据
   */
  const sendAudio = (audioData: ArrayBuffer | Blob) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('⚠️  WebSocket 未连接，无法发送音频')
      return false
    }

    try {
      ws.send(audioData)
      return true
    } catch (e) {
      console.error('❌ 发送音频数据失败:', e)
      return false
    }
  }

  /**
   * 处理接收到的消息
   */
  const handleMessage = (data: ASRMessage) => {
    switch (data.type) {
      case 'connected':
        sessionId.value = data.session_id || null
        console.log('✓ ASR 会话已建立:', {
          session_id: data.session_id,
          asr_session_id: data.asr_session_id
        })
        onConnected?.(data.session_id || '')
        break

      case 'partial':
        if (data.text) {
          onPartialText?.(data.text)
        }
        break

      case 'final':
        console.log('✓ 最终识别结果:', data.text)
        if (data.text) {
          onFinalText?.(data.text)
        }
        break

      case 'speech_start':
        console.log('🎤 检测到语音开始')
        onSpeechStart?.()
        break

      case 'speech_stop':
        console.log('⏹️  检测到语音停止')
        onSpeechStop?.()
        break

      case 'error':
        console.error('❌ ASR 错误:', data.message)
        error.value = data.message || 'ASR 错误'
        onError?.(data.message || 'ASR 错误')
        break

      default:
        console.log('❓ 未知消息类型:', data)
    }
  }

  /**
   * 清理资源
   */
  onUnmounted(() => {
    disconnect()
  })

  return {
    // 状态
    isConnected,
    isConnecting,
    sessionId,
    error,

    // 方法
    connect,
    disconnect,
    sendAudio
  }
}


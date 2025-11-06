/**
 * 语音识别整合 Hook
 * 整合 ASR WebSocket 连接和音频录音功能
 */
import { ref, watch } from 'vue'
import { useASR } from './useASR'
import { useAudioRecorder } from './useAudioRecorder'

export interface VoiceRecognitionConfig {
  /** WebSocket URL */
  asrUrl?: string
  /** 采样率 */
  sampleRate?: number
  /** 缓冲区大小 */
  bufferSize?: number
  /** 是否自动重连 */
  autoReconnect?: boolean
  /** 是否打印详细日志 */
  verbose?: boolean
}

export function useVoiceRecognition(config: VoiceRecognitionConfig = {}) {
  const {
    asrUrl = 'ws://localhost:8000/api/sr/realtime',
    sampleRate = 16000,
    bufferSize = 4096,
    autoReconnect = true,
    verbose = true
  } = config

  // 状态
  const isActive = ref(false)
  const audioStream = ref<MediaStream | null>(null)

  // 使用 ASR Hook
  const {
    isConnected: asrConnected,
    isConnecting: asrConnecting,
    sessionId: asrSessionId,
    error: asrError,
    connect: connectASR,
    disconnect: disconnectASR,
    sendAudio: sendAudioToASR
  } = useASR({
    url: asrUrl,
    autoReconnect,
    verbose
  })

  // 使用音频录音 Hook
  const {
    isRecording,
    error: recorderError,
    startRecording,
    stopRecording
  } = useAudioRecorder({
    sampleRate,
    bufferSize,
    verbose
  })

  /**
   * 启动语音识别
   */
  const start = (stream: MediaStream) => {
    if (isActive.value) {
      if (verbose) console.log('⚠️  语音识别已启动')
      return
    }

    if (!stream) {
      console.error('❌ 音频流未提供')
      return
    }

    audioStream.value = stream
    isActive.value = true

    if (verbose) console.log('🚀 启动语音识别...')

    // 1. 连接 ASR WebSocket
    connectASR()

    // 2. 等待连接建立后开始录音
    const checkConnection = setInterval(() => {
      if (asrConnected.value) {
        clearInterval(checkConnection)
        
        // 开始录音并发送数据
        startRecording(stream, (pcmData) => {
          sendAudioToASR(pcmData)
        })
      }
    }, 100)

    // 超时处理
    setTimeout(() => {
      clearInterval(checkConnection)
      if (!asrConnected.value) {
        console.error('❌ ASR 连接超时')
        stop()
      }
    }, 5000)
  }

  /**
   * 停止语音识别
   */
  const stop = () => {
    if (!isActive.value) {
      if (verbose) console.log('⚠️  语音识别未启动')
      return
    }

    if (verbose) console.log('⏹️  停止语音识别...')

    // 停止录音
    stopRecording()

    // 断开 ASR
    disconnectASR()

    audioStream.value = null
    isActive.value = false
  }

  /**
   * 切换语音识别状态
   */
  const toggle = (stream?: MediaStream) => {
    if (isActive.value) {
      stop()
    } else if (stream) {
      start(stream)
    } else {
      console.error('❌ 需要提供音频流')
    }
  }

  return {
    // 状态
    isActive,
    isRecording,
    asrConnected,
    asrConnecting,
    asrSessionId,
    asrError,
    recorderError,

    // 方法
    start,
    stop,
    toggle
  }
}


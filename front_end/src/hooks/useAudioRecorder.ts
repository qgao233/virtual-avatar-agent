/**
 * 音频录音 Hook
 * 将音频流转换为 PCM 格式并通过回调发送
 */
import { ref, onUnmounted } from 'vue'

export interface AudioRecorderConfig {
  /** 采样率 */
  sampleRate?: number
  /** 缓冲区大小 */
  bufferSize?: number
  /** 是否打印详细日志 */
  verbose?: boolean
}

export function useAudioRecorder(config: AudioRecorderConfig = {}) {
  const {
    sampleRate = 16000,
    bufferSize = 4096,
    verbose = true
  } = config

  // 状态
  const isRecording = ref(false)
  const error = ref<string | null>(null)

  // 音频处理相关
  let audioContext: AudioContext | null = null
  let source: MediaStreamAudioSourceNode | null = null
  let processor: ScriptProcessorNode | null = null
  let onAudioDataCallback: ((data: ArrayBuffer) => void) | null = null

  /**
   * 将 Float32Array 转换为 16-bit PCM
   */
  const convertFloat32ToPCM16 = (float32Array: Float32Array): ArrayBuffer => {
    const buffer = new ArrayBuffer(float32Array.length * 2)
    const view = new DataView(buffer)
    
    for (let i = 0; i < float32Array.length; i++) {
      // 将 [-1, 1] 范围的浮点数转换为 [-32768, 32767] 范围的整数
      let sample = Math.max(-1, Math.min(1, float32Array[i]))
      sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
      view.setInt16(i * 2, sample, true)  // true 表示小端序
    }
    
    return buffer
  }

  /**
   * 开始录音
   */
  const startRecording = (
    audioStream: MediaStream,
    onAudioData: (data: ArrayBuffer) => void
  ) => {
    if (isRecording.value) {
      if (verbose) console.log('⚠️  已在录音中')
      return
    }

    if (!audioStream) {
      error.value = '音频流未提供'
      console.error('❌ 音频流未提供')
      return
    }

    try {
      // 创建 AudioContext
      audioContext = new AudioContext({
        sampleRate: sampleRate
      })
      
      // 创建音频源
      source = audioContext.createMediaStreamSource(audioStream)
      
      // 创建 ScriptProcessor
      processor = audioContext.createScriptProcessor(bufferSize, 1, 1)
      
      // 保存回调
      onAudioDataCallback = onAudioData
      
      // 处理音频数据
      processor.onaudioprocess = (event) => {
        if (!isRecording.value || !onAudioDataCallback) return
        
        // 获取音频数据
        const inputData = event.inputBuffer.getChannelData(0)
        
        // 转换为 16-bit PCM
        const pcmData = convertFloat32ToPCM16(inputData)
        
        // 通过回调发送
        onAudioDataCallback(pcmData)
      }
      
      // 连接音频节点
      source.connect(processor)
      processor.connect(audioContext.destination)
      
      isRecording.value = true
      error.value = null
      
      if (verbose) {
        console.log(`✓ 开始录音 (PCM ${sampleRate}Hz, buffer ${bufferSize})`)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '启动录音失败'
      console.error('❌ 启动录音失败:', err)
    }
  }

  /**
   * 停止录音
   */
  const stopRecording = () => {
    if (!isRecording.value) {
      if (verbose) console.log('⚠️  未在录音中')
      return
    }

    try {
      // 断开连接
      if (source) {
        source.disconnect()
        source = null
      }
      
      if (processor) {
        processor.disconnect()
        processor = null
      }
      
      // 关闭 AudioContext
      if (audioContext && audioContext.state !== 'closed') {
        audioContext.close()
        audioContext = null
      }
      
      onAudioDataCallback = null
      isRecording.value = false
      
      if (verbose) console.log('✓ 录音已停止')
    } catch (err) {
      console.error('❌ 停止录音时出错:', err)
    }
  }

  /**
   * 清理资源
   */
  onUnmounted(() => {
    stopRecording()
  })

  return {
    // 状态
    isRecording,
    error,

    // 方法
    startRecording,
    stopRecording
  }
}


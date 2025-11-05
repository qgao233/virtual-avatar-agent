<template>
  <div class="video-display">
    <!-- 主视频窗口 (对方画面) -->
    <VideoWindow
      ref="remoteWindowRef"
      :stream="remoteStream"
      :autoplay="true"
      :muted="false"
      :mirror="false"
      placeholder-icon="📹"
      placeholder-text="等待对方加入..."
    >
      <!-- 顶部状态栏 -->
      <template #overlay>
        <div class="status-bar">
          <span class="status-item">
            <span class="status-dot" :class="{ active: isConnected }"></span>
            {{ isConnected ? '已连接' : '未连接' }}
          </span>
          <span class="status-item" v-if="duration">
            ⏱️ {{ formatDuration(duration) }}
          </span>
        </div>
      </template>

      <!-- 自定义内容: 人脸识别框等 -->
      <template #content>
        <slot name="remote-content"></slot>
      </template>
    </VideoWindow>

    <!-- 本地视频小窗 (自己的画面) -->
    <div class="local-video-wrapper">
      <VideoWindow
        ref="localWindowRef"
        :stream="localStream"
        :autoplay="true"
        :muted="true"
        :mirror="true"
        :is-small="true"
        placeholder-icon="👤"
        placeholder-text=""
      >
        <!-- 控制按钮 -->
        <template #controls>
          <div class="controls">
            <button 
              class="control-btn"
              :class="{ active: isCameraOn }"
              @click="toggleCamera"
              title="摄像头"
            >
              {{ isCameraOn ? '📹' : '📹❌' }}
            </button>
            <button 
              class="control-btn"
              :class="{ active: isMicOn }"
              @click="toggleMic"
              title="麦克风"
            >
              {{ isMicOn ? '🎤' : '🎤❌' }}
            </button>
          </div>
        </template>

        <!-- 自定义内容: 本地视频的额外信息 -->
        <template #content>
          <slot name="local-content"></slot>
        </template>
      </VideoWindow>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import VideoWindow from './VideoWindow.vue'

interface Props {
  /** 是否自动启动摄像头 */
  autoStart?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoStart: true
})

const emit = defineEmits<{
  streamReady: [stream: MediaStream]
  streamError: [error: Error]
}>()

// 视频窗口引用
const localWindowRef = ref<InstanceType<typeof VideoWindow> | null>(null)
const remoteWindowRef = ref<InstanceType<typeof VideoWindow> | null>(null)

// 媒体流
const localStream = ref<MediaStream | null>(null)
const remoteStream = ref<MediaStream | null>(null)

// 控制状态
const isCameraOn = ref(false)
const isMicOn = ref(false)
const isConnected = ref(false)
const duration = ref(0)

// 人脸识别相关
const recognitionGap = ref(1000) // 默认 1 秒
const localFaces = ref<any[]>([])

let durationInterval: number | null = null
let recognitionInterval: number | null = null

const API_BASE_URL = 'http://localhost:8000'

/**
 * 启动本地摄像头
 */
const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user'
      },
      audio: true
    })

    localStream.value = stream
    isCameraOn.value = true
    isMicOn.value = true

    emit('streamReady', stream)
  } catch (error) {
    console.error('启动摄像头失败:', error)
    emit('streamError', error as Error)
  }
}

/**
 * 停止本地摄像头
 */
const stopCamera = () => {
  if (localStream.value) {
    localStream.value.getTracks().forEach(track => track.stop())
    localStream.value = null
  }

  isCameraOn.value = false
  isMicOn.value = false
}

/**
 * 切换摄像头
 */
const toggleCamera = () => {
  if (!localStream.value) {
    startCamera()
    return
  }

  const videoTrack = localStream.value.getVideoTracks()[0]
  if (videoTrack) {
    videoTrack.enabled = !videoTrack.enabled
    isCameraOn.value = videoTrack.enabled
  }
}

/**
 * 切换麦克风
 */
const toggleMic = () => {
  if (!localStream.value) return

  const audioTrack = localStream.value.getAudioTracks()[0]
  if (audioTrack) {
    audioTrack.enabled = !audioTrack.enabled
    isMicOn.value = audioTrack.enabled
  }
}

/**
 * 设置远程视频流
 */
const setRemoteStream = (stream: MediaStream) => {
  remoteStream.value = stream
  isConnected.value = true
  startDurationTimer()
}

/**
 * 开始计时
 */
const startDurationTimer = () => {
  if (durationInterval) return
  
  duration.value = 0
  durationInterval = window.setInterval(() => {
    duration.value++
  }, 1000)
}

/**
 * 停止计时
 */
const stopDurationTimer = () => {
  if (durationInterval) {
    clearInterval(durationInterval)
    durationInterval = null
  }
  duration.value = 0
}

/**
 * 格式化时长
 */
const formatDuration = (seconds: number): string => {
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hrs > 0) {
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * 获取识别间隔时间
 */
const fetchRecognitionGap = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/cv/recognition-gap`)
    const data = await response.json()
    recognitionGap.value = data.recognition_gap || 1000
    console.log('识别间隔:', recognitionGap.value, 'ms')
  } catch (error) {
    console.error('获取识别间隔失败:', error)
    recognitionGap.value = 1000 // 使用默认值
  }
}

/**
 * 调用人脸识别 API
 */
const recognizeFaces = async () => {
  if (!localWindowRef.value) return
  
  try {
    // 从视频捕获当前帧
    const blob = await localWindowRef.value.captureFrameAsync()
    if (!blob) return
    
    // 创建 FormData
    const formData = new FormData()
    formData.append('file', blob, 'frame.jpg')
    
    // 调用识别 API
    const response = await fetch(`${API_BASE_URL}/api/cv/recognize-faces`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      console.error('识别失败:', response.statusText)
      return
    }
    
    const data = await response.json()
    console.log('📸 人脸识别结果:', data)
    
    // 更新人脸数据
    if (data.faces && data.faces.length > 0) {
      localFaces.value = data.faces
      console.log(`✓ 检测到 ${data.faces.length} 个人脸，开始绘制...`)
      
      // 在 Canvas 上绘制人脸框
      localWindowRef.value.drawFaces(data.faces)
    } else {
      // 没有检测到人脸,清空 Canvas
      console.log('ℹ️  未检测到人脸')
      localFaces.value = []
      localWindowRef.value.clearCanvas()
    }
  } catch (error) {
    console.error('人脸识别出错:', error)
  }
}

/**
 * 启动人脸识别定时器
 */
const startFaceRecognition = () => {
  if (recognitionInterval) return
  
  console.log('启动人脸识别,间隔:', recognitionGap.value, 'ms')
  
  // 立即执行一次
  recognizeFaces()
  
  // 设置定时器
  recognitionInterval = window.setInterval(() => {
    recognizeFaces()
  }, recognitionGap.value)
}

/**
 * 停止人脸识别定时器
 */
const stopFaceRecognition = () => {
  if (recognitionInterval) {
    clearInterval(recognitionInterval)
    recognitionInterval = null
    console.log('停止人脸识别')
  }
  
  // 清空人脸数据和 Canvas
  localFaces.value = []
  if (localWindowRef.value) {
    localWindowRef.value.clearCanvas()
  }
}

onMounted(async () => {
  // 获取识别间隔
  await fetchRecognitionGap()
  
  // 启动摄像头
  if (props.autoStart) {
    await startCamera()
    
    // 等待视频流准备好后启动人脸识别
    setTimeout(() => {
      startFaceRecognition()
    }, 1000)
  }
})

onUnmounted(() => {
  stopCamera()
  stopDurationTimer()
  stopFaceRecognition()
})

// 暴露方法给父组件
defineExpose({
  startCamera,
  stopCamera,
  toggleCamera,
  toggleMic,
  setRemoteStream,
  getLocalStream: () => localStream.value,
  getRemoteStream: () => remoteStream.value,
  startFaceRecognition,
  stopFaceRecognition,
  recognizeFaces
})
</script>

<style scoped>
.video-display {
  position: relative;
  width: 100%;
  height: 100%;
  background: #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
}

/* 本地视频小窗位置 */
.local-video-wrapper {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 240px;
  height: 180px;
  z-index: 100;
}

/* 状态栏样式 */
.status-bar {
  margin: 16px;
  display: inline-flex;
  gap: 16px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  font-size: 14px;
  color: #fff;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
  transition: background 0.3s ease;
}

.status-dot.active {
  background: #22c55e;
  box-shadow: 0 0 8px #22c55e;
}

/* 控制按钮样式 */
.controls {
  display: flex;
  gap: 8px;
  justify-content: center;
  padding: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.local-video-wrapper:hover .controls {
  opacity: 1;
}

.control-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.control-btn:hover {
  background: rgba(0, 0, 0, 0.9);
  transform: scale(1.1);
}

.control-btn.active {
  background: rgba(59, 130, 246, 0.8);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .local-video-wrapper {
    width: 160px;
    height: 120px;
    bottom: 12px;
    right: 12px;
  }

  .status-bar {
    font-size: 12px;
    padding: 6px 12px;
    margin: 12px;
  }
}
</style>


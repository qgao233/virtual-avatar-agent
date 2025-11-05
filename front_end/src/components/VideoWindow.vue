<template>
  <div class="video-window" :class="{ 'is-small': isSmall }">
    <!-- 视频层 -->
    <video
      ref="videoRef"
      class="video-element"
      :autoplay="autoplay"
      :muted="muted"
      :playsinline="true"
      :style="{ transform: mirror ? 'scaleX(-1)' : 'none' }"
    ></video>

    <!-- Canvas 绘制层 -->
    <canvas
      ref="canvasRef"
      class="canvas-layer"
    ></canvas>

    <!-- 占位符 -->
    <div v-if="!hasStream" class="placeholder">
      <slot name="placeholder">
        <div class="placeholder-icon">{{ placeholderIcon }}</div>
        <div class="placeholder-text">{{ placeholderText }}</div>
      </slot>
    </div>

    <!-- 顶部覆盖层 (状态信息等) -->
    <div v-if="$slots.overlay" class="overlay-top">
      <slot name="overlay"></slot>
    </div>

    <!-- 底部覆盖层 (控制按钮等) -->
    <div v-if="$slots.controls" class="overlay-bottom">
      <slot name="controls"></slot>
    </div>

    <!-- 自定义内容 (人脸识别框等) -->
    <div v-if="$slots.content" class="custom-content">
      <slot name="content"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'

interface Props {
  /** 是否为小窗口 */
  isSmall?: boolean
  /** 视频流 */
  stream?: MediaStream | null
  /** 是否自动播放 */
  autoplay?: boolean
  /** 是否静音 */
  muted?: boolean
  /** 是否镜像翻转 */
  mirror?: boolean
  /** 占位符图标 */
  placeholderIcon?: string
  /** 占位符文本 */
  placeholderText?: string
}

interface FaceData {
  face_id: number
  bbox: {
    x1: number
    y1: number
    x2: number
    y2: number
  }
  name: string
  confidence: number
  distance?: number
}

const props = withDefaults(defineProps<Props>(), {
  isSmall: false,
  stream: null,
  autoplay: true,
  muted: false,
  mirror: false,
  placeholderIcon: '📹',
  placeholderText: '暂无视频'
})

const emit = defineEmits<{
  videoReady: [video: HTMLVideoElement]
  canvasReady: [canvas: HTMLCanvasElement]
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const hasStream = ref(false)

let ctx: CanvasRenderingContext2D | null = null
let resizeObserver: ResizeObserver | null = null

/**
 * 设置视频流
 */
const setStream = (stream: MediaStream | null) => {
  if (videoRef.value) {
    videoRef.value.srcObject = stream
    hasStream.value = !!stream
    
    // 视频加载后更新 canvas 尺寸
    if (stream) {
      videoRef.value.onloadedmetadata = () => {
        updateCanvasSize()
      }
    }
  }
}

/**
 * 更新 Canvas 尺寸以匹配视频
 */
const updateCanvasSize = () => {
  if (videoRef.value && canvasRef.value) {
    const video = videoRef.value
    const canvas = canvasRef.value
    
    // 设置 canvas 尺寸与视频显示区域一致
    const rect = video.getBoundingClientRect()
    canvas.width = rect.width
    canvas.height = rect.height
    
    // 获取绘图上下文
    if (!ctx) {
      ctx = canvas.getContext('2d')
    }
  }
}

/**
 * 清空 Canvas
 */
const clearCanvas = () => {
  if (ctx && canvasRef.value) {
    ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  }
}

/**
 * 绘制人脸识别框
 */
const drawFaces = (faces: FaceData[]) => {
  if (!ctx || !canvasRef.value || !videoRef.value) return
  
  // 清空画布
  clearCanvas()
  
  // 获取缩放比例
  // 后端返回的坐标是基于原始视频分辨率 (videoWidth x videoHeight)
  // Canvas 的尺寸是基于显示尺寸 (canvas.width x canvas.height)
  const video = videoRef.value
  const canvas = canvasRef.value
  
  const scaleX = canvas.width / video.videoWidth
  const scaleY = canvas.height / video.videoHeight
  
  console.log('绘制人脸框:', {
    faces: faces.length,
    videoSize: { width: video.videoWidth, height: video.videoHeight },
    canvasSize: { width: canvas.width, height: canvas.height },
    scale: { x: scaleX, y: scaleY }
  })
  
  // 绘制每个人脸
  faces.forEach(face => {
    const { bbox, name, confidence } = face
    
    // 缩放坐标
    const x1 = bbox.x1 * scaleX
    const y1 = bbox.y1 * scaleY
    const x2 = bbox.x2 * scaleX
    const y2 = bbox.y2 * scaleY
    const width = x2 - x1
    const height = y2 - y1
    
    console.log('绘制人脸:', {
      name,
      original: bbox,
      scaled: { x1, y1, x2, y2, width, height }
    })
    
    // 绘制矩形框
    ctx!.strokeStyle = name === 'Unknown' ? '#ff0000' : '#00ff00'
    ctx!.lineWidth = 3
    ctx!.strokeRect(x1, y1, width, height)
    
    // 绘制标签背景
    const label = `${name} (${(confidence * 100).toFixed(0)}%)`
    ctx!.font = '16px Arial'
    const textMetrics = ctx!.measureText(label)
    const textWidth = textMetrics.width
    const textHeight = 20
    
    const labelX = x1
    const labelY = y1 - 5
    
    // 背景
    ctx!.fillStyle = name === 'Unknown' ? 'rgba(255, 0, 0, 0.8)' : 'rgba(0, 255, 0, 0.8)'
    ctx!.fillRect(labelX, labelY - textHeight, textWidth + 10, textHeight + 5)
    
    // 文字
    ctx!.fillStyle = '#ffffff'
    ctx!.fillText(label, labelX + 5, labelY - 5)
  })
}

/**
 * 绘制自定义图形
 */
const drawCustom = (drawFunc: (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => void) => {
  if (ctx && canvasRef.value) {
    clearCanvas()
    drawFunc(ctx, canvasRef.value)
  }
}

/**
 * 获取视频元素
 */
const getVideoElement = () => videoRef.value

/**
 * 获取 Canvas 元素
 */
const getCanvasElement = () => canvasRef.value

/**
 * 获取绘图上下文
 */
const getContext = () => ctx

/**
 * 从视频捕获当前帧
 */
const captureFrame = (): Blob | null => {
  if (!videoRef.value || !canvasRef.value) return null
  
  const video = videoRef.value
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  const tempCtx = canvas.getContext('2d')
  if (!tempCtx) return null
  
  // 如果是镜像,需要翻转
  if (props.mirror) {
    tempCtx.translate(canvas.width, 0)
    tempCtx.scale(-1, 1)
  }
  
  tempCtx.drawImage(video, 0, 0, canvas.width, canvas.height)
  
  // 转换为 Blob
  let blob: Blob | null = null
  canvas.toBlob((b) => {
    blob = b
  }, 'image/jpeg', 0.95)
  
  return blob
}

/**
 * 从视频捕获当前帧 (异步版本)
 */
const captureFrameAsync = (): Promise<Blob | null> => {
  return new Promise((resolve) => {
    if (!videoRef.value || !canvasRef.value) {
      resolve(null)
      return
    }
    
    const video = videoRef.value
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    
    const tempCtx = canvas.getContext('2d')
    if (!tempCtx) {
      resolve(null)
      return
    }
    
    // 如果是镜像,需要翻转
    if (props.mirror) {
      tempCtx.translate(canvas.width, 0)
      tempCtx.scale(-1, 1)
    }
    
    tempCtx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    // 转换为 Blob
    canvas.toBlob((blob) => {
      resolve(blob)
    }, 'image/jpeg', 0.95)
  })
}

// 监听 stream prop 变化
watch(() => props.stream, (newStream) => {
  setStream(newStream)
}, { immediate: true })

onMounted(() => {
  nextTick(() => {
    if (videoRef.value) {
      emit('videoReady', videoRef.value)
    }
    
    if (canvasRef.value) {
      ctx = canvasRef.value.getContext('2d')
      emit('canvasReady', canvasRef.value)
      updateCanvasSize()
    }
    
    // 监听窗口大小变化
    if (canvasRef.value) {
      resizeObserver = new ResizeObserver(() => {
        updateCanvasSize()
      })
      resizeObserver.observe(canvasRef.value)
    }
    
    // 监听窗口 resize
    window.addEventListener('resize', updateCanvasSize)
  })
})

onUnmounted(() => {
  if (videoRef.value) {
    videoRef.value.srcObject = null
  }
  
  if (resizeObserver && canvasRef.value) {
    resizeObserver.unobserve(canvasRef.value)
    resizeObserver.disconnect()
  }
  
  window.removeEventListener('resize', updateCanvasSize)
})

// 暴露方法
defineExpose({
  setStream,
  getVideoElement,
  getCanvasElement,
  getContext,
  clearCanvas,
  drawFaces,
  drawCustom,
  captureFrame,
  captureFrameAsync,
  updateCanvasSize
})
</script>

<style scoped>
.video-window {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

/* 小窗口样式 */
.video-window.is-small {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.video-window.is-small:hover {
  transform: scale(1.05);
  border-color: rgba(59, 130, 246, 0.5);
}

/* 视频元素 */
.video-element {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* Canvas 绘制层 */
.canvas-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}

/* 占位符 */
.placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #666;
  z-index: 1;
}

.placeholder-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.video-window.is-small .placeholder-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.placeholder-text {
  font-size: 18px;
  color: #888;
}

.video-window.is-small .placeholder-text {
  font-size: 14px;
}

/* 顶部覆盖层 */
.overlay-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  pointer-events: none;
}

.overlay-top > * {
  pointer-events: auto;
}

/* 底部覆盖层 */
.overlay-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 10;
  pointer-events: none;
}

.overlay-bottom > * {
  pointer-events: auto;
}

/* 自定义内容层 */
.custom-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 5;
  pointer-events: none;
}

.custom-content > * {
  pointer-events: auto;
}
</style>


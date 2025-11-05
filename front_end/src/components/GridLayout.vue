<template>
    <div ref="containerRef" class="grid-layout">
      <div
        class="grid-container"
        :style="{
          display: 'grid',
          gridTemplateColumns: columnSizes.join(' '),
          gridTemplateRows: rowSizes.join(' '),
          gap: `${gap}px`,
          width: '100%',
          height: '100%'
        }"
      >
        <!-- 渲染 m*n 个格子 -->
        <div
          v-for="cellIndex in totalCells"
          :key="`cell-${cellIndex}`"
          class="grid-cell"
        >
          <slot :name="`cell-${cellIndex - 1}`"></slot>
        </div>
      </div>
  
      <!-- 垂直分隔线（调整列宽） -->
      <div
        v-for="colIndex in columns - 1"
        :key="`col-${colIndex}`"
        class="resize-handle resize-handle-vertical"
        :style="{
          left: `${getColumnPosition(colIndex - 1)}px`,
          height: '100%'
        }"
        @mousedown="(e) => startResize(e, 'column', colIndex - 1)"
      ></div>
  
      <!-- 水平分隔线（调整行高） -->
      <div
        v-for="rowIndex in rows - 1"
        :key="`row-${rowIndex}`"
        class="resize-handle resize-handle-horizontal"
        :style="{
          top: `${getRowPosition(rowIndex - 1)}px`,
          width: '100%'
        }"
        @mousedown="(e) => startResize(e, 'row', rowIndex - 1)"
      ></div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
  
  interface CellSize {
    /** 单元格索引 (0-based) */
    cellIndex: number
    /** 宽度比例 (0-1) 或像素值 */
    width?: number | string
    /** 高度比例 (0-1) 或像素值 */
    height?: number | string
  }
  
  interface Props {
    rows?: number
    columns?: number
    gap?: number
    /** 单元格初始尺寸配置 */
    cellSizes?: CellSize[]
    /** 默认列宽比例数组 */
    defaultColumnRatios?: number[]
    /** 默认行高比例数组 */
    defaultRowRatios?: number[]
  }
  
  const props = withDefaults(defineProps<Props>(), {
    rows: 2,
    columns: 2,
    gap: 8,
    cellSizes: () => [],
    defaultColumnRatios: () => [],
    defaultRowRatios: () => []
  })
  
  const containerRef = ref<HTMLElement | null>(null)
  const containerWidth = ref(0)
  const containerHeight = ref(0)
  
  // 计算总格子数
  const totalCells = computed(() => props.rows * props.columns)
  
  // 存储每列和每行的比例（0-1之间）
  const columnRatios = ref<number[]>([])
  const rowRatios = ref<number[]>([])
  
  // 调整状态
  const resizing = ref<{
    type: 'column' | 'row'
    index: number
    startPos: number
    startRatios: number[]
  } | null>(null)
  
  /**
   * 将单元格索引转换为行列坐标
   */
  const getCellPosition = (cellIndex: number): { row: number; col: number } => {
    const row = Math.floor(cellIndex / props.columns)
    const col = cellIndex % props.columns
    return { row, col }
  }
  
  /**
   * 解析尺寸值（支持比例和像素）
   */
  const parseSizeValue = (value: number | string | undefined, defaultValue: number): number => {
    if (value === undefined) return defaultValue
    
    if (typeof value === 'number') {
      // 如果是 0-1 之间的数字，视为比例
      if (value > 0 && value <= 1) {
        return value
      }
      // 否则视为像素值，需要转换为比例（在初始化时处理）
      return value
    }
    
    // 字符串类型，解析百分比或像素
    if (typeof value === 'string') {
      if (value.endsWith('%')) {
        return parseFloat(value) / 100
      }
      if (value.endsWith('px')) {
        return parseFloat(value)
      }
      return parseFloat(value)
    }
    
    return defaultValue
  }
  
  /**
   * 初始化比例
   * 支持从 cellSizes 或 defaultColumnRatios/defaultRowRatios 配置初始尺寸
   */
  const initializeRatios = () => {
    // 初始化列宽比例
    if (props.defaultColumnRatios.length === props.columns) {
      // 使用提供的默认列宽
      columnRatios.value = [...props.defaultColumnRatios]
    } else {
      // 平均分配
      columnRatios.value = Array(props.columns).fill(1 / props.columns)
    }
    
    // 初始化行高比例
    if (props.defaultRowRatios.length === props.rows) {
      // 使用提供的默认行高
      rowRatios.value = [...props.defaultRowRatios]
    } else {
      // 平均分配
      rowRatios.value = Array(props.rows).fill(1 / props.rows)
    }
    
    // 根据 cellSizes 配置调整特定单元格的尺寸
    if (props.cellSizes.length > 0) {
      applyCellSizes()
    }
  }
  
  /**
   * 应用单元格尺寸配置
   */
  const applyCellSizes = () => {
    // 收集每列和每行的尺寸配置
    const columnSizeMap = new Map<number, number>()
    const rowSizeMap = new Map<number, number>()
    
    props.cellSizes.forEach(cellSize => {
      const { row, col } = getCellPosition(cellSize.cellIndex)
      
      if (cellSize.width !== undefined) {
        const width = parseSizeValue(cellSize.width, 1 / props.columns)
        // 如果同一列有多个配置，取平均值
        const existing = columnSizeMap.get(col)
        columnSizeMap.set(col, existing ? (existing + width) / 2 : width)
      }
      
      if (cellSize.height !== undefined) {
        const height = parseSizeValue(cellSize.height, 1 / props.rows)
        // 如果同一行有多个配置，取平均值
        const existing = rowSizeMap.get(row)
        rowSizeMap.set(row, existing ? (existing + height) / 2 : height)
      }
    })
    
    // 应用列宽配置
    if (columnSizeMap.size > 0) {
      const newColumnRatios = [...columnRatios.value]
      let totalConfigured = 0
      let configuredCount = 0
      
      columnSizeMap.forEach((ratio, col) => {
        newColumnRatios[col] = ratio
        totalConfigured += ratio
        configuredCount++
      })
      
      // 调整未配置的列，使总和为 1
      const remaining = 1 - totalConfigured
      const unconfiguredCount = props.columns - configuredCount
      
      if (unconfiguredCount > 0 && remaining > 0) {
        const avgRemaining = remaining / unconfiguredCount
        for (let i = 0; i < props.columns; i++) {
          if (!columnSizeMap.has(i)) {
            newColumnRatios[i] = avgRemaining
          }
        }
      }
      
      columnRatios.value = newColumnRatios
    }
    
    // 应用行高配置
    if (rowSizeMap.size > 0) {
      const newRowRatios = [...rowRatios.value]
      let totalConfigured = 0
      let configuredCount = 0
      
      rowSizeMap.forEach((ratio, row) => {
        newRowRatios[row] = ratio
        totalConfigured += ratio
        configuredCount++
      })
      
      // 调整未配置的行，使总和为 1
      const remaining = 1 - totalConfigured
      const unconfiguredCount = props.rows - configuredCount
      
      if (unconfiguredCount > 0 && remaining > 0) {
        const avgRemaining = remaining / unconfiguredCount
        for (let i = 0; i < props.rows; i++) {
          if (!rowSizeMap.has(i)) {
            newRowRatios[i] = avgRemaining
          }
        }
      }
      
      rowRatios.value = newRowRatios
    }
  }
  
  // 计算实际的列宽和行高（CSS grid template values）
  const columnSizes = computed(() => {
    return columnRatios.value.map(ratio => `${ratio * 100}%`)
  })
  
  const rowSizes = computed(() => {
    return rowRatios.value.map(ratio => `${ratio * 100}%`)
  })
  
  // 获取列分隔线的位置
  const getColumnPosition = (colIndex: number): number => {
    const totalGap = (props.columns - 1) * props.gap
    const availableWidth = containerWidth.value - totalGap
    
    let position = 0
    // 计算第 colIndex 列的右边界位置
    for (let i = 0; i <= colIndex; i++) {
      position += (columnRatios.value[i] || 0) * availableWidth
      if (i < colIndex) {
        position += props.gap
      }
    }
    
    return position
  }
  
  // 获取行分隔线的位置
  const getRowPosition = (rowIndex: number): number => {
    const totalGap = (props.rows - 1) * props.gap
    const availableHeight = containerHeight.value - totalGap
    
    let position = 0
    // 计算第 rowIndex 行的下边界位置
    for (let i = 0; i <= rowIndex; i++) {
      position += (rowRatios.value[i] || 0) * availableHeight
      if (i < rowIndex) {
        position += props.gap
      }
    }
    
    return position
  }
  
  // 开始调整大小
  const startResize = (e: MouseEvent, type: 'column' | 'row', index: number) => {
    e.preventDefault()
    
    resizing.value = {
      type,
      index,
      startPos: type === 'column' ? e.clientX : e.clientY,
      startRatios: type === 'column' ? [...columnRatios.value] : [...rowRatios.value]
    }
    
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
    document.body.style.cursor = type === 'column' ? 'col-resize' : 'row-resize'
    document.body.style.userSelect = 'none'
  }
  
  // 鼠标移动
  const onMouseMove = (e: MouseEvent) => {
    if (!resizing.value || !containerRef.value) return
    
    const { type, index, startPos, startRatios } = resizing.value
    
    if (type === 'column') {
      const delta = e.clientX - startPos
      const totalGap = (props.columns - 1) * props.gap
      const availableWidth = containerWidth.value - totalGap
      const deltaRatio = delta / availableWidth
      
      // 调整相邻两列的比例
      const newLeftRatio = (startRatios[index] || 0) + deltaRatio
      const newRightRatio = (startRatios[index + 1] || 0) - deltaRatio
      
      // 确保比例不小于最小值（例如5%）
      const minRatio = 0.05
      if (newLeftRatio >= minRatio && newRightRatio >= minRatio) {
        const newRatios = [...columnRatios.value]
        newRatios[index] = newLeftRatio
        newRatios[index + 1] = newRightRatio
        columnRatios.value = newRatios
      }
    } else {
      const delta = e.clientY - startPos
      const totalGap = (props.rows - 1) * props.gap
      const availableHeight = containerHeight.value - totalGap
      const deltaRatio = delta / availableHeight
      
      // 调整相邻两行的比例
      const newTopRatio = (startRatios[index] || 0) + deltaRatio
      const newBottomRatio = (startRatios[index + 1] || 0) - deltaRatio
      
      // 确保比例不小于最小值
      const minRatio = 0.05
      if (newTopRatio >= minRatio && newBottomRatio >= minRatio) {
        const newRatios = [...rowRatios.value]
        newRatios[index] = newTopRatio
        newRatios[index + 1] = newBottomRatio
        rowRatios.value = newRatios
      }
    }
  }
  
  // 鼠标释放
  const onMouseUp = () => {
    if (resizing.value) {
      resizing.value = null
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }
  
  // 更新容器尺寸
  const updateContainerSize = () => {
    if (containerRef.value) {
      const rect = containerRef.value.getBoundingClientRect()
      containerWidth.value = rect.width
      containerHeight.value = rect.height
    }
  }
  
  // ResizeObserver 监听容器尺寸变化
  let resizeObserver: ResizeObserver | null = null
  
  // 监听 props 变化，重新初始化
  watch(
    () => [props.rows, props.columns, props.cellSizes, props.defaultColumnRatios, props.defaultRowRatios],
    () => {
      initializeRatios()
    },
    { deep: true }
  )
  
  onMounted(() => {
    initializeRatios()
    updateContainerSize()
    
    if (containerRef.value) {
      resizeObserver = new ResizeObserver(() => {
        updateContainerSize()
      })
      resizeObserver.observe(containerRef.value)
    }
    
    window.addEventListener('resize', updateContainerSize)
  })
  
  onUnmounted(() => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    window.removeEventListener('resize', updateContainerSize)
    
    if (resizeObserver && containerRef.value) {
      resizeObserver.unobserve(containerRef.value)
      resizeObserver.disconnect()
    }
  })
  
  // 导出方法供外部使用
  defineExpose({
    /** 重置为初始尺寸 */
    resetSizes: initializeRatios,
    /** 获取当前列宽比例 */
    getColumnRatios: () => [...columnRatios.value],
    /** 获取当前行高比例 */
    getRowRatios: () => [...rowRatios.value],
    /** 设置列宽比例 */
    setColumnRatios: (ratios: number[]) => {
      if (ratios.length === props.columns) {
        columnRatios.value = [...ratios]
      }
    },
    /** 设置行高比例 */
    setRowRatios: (ratios: number[]) => {
      if (ratios.length === props.rows) {
        rowRatios.value = [...ratios]
      }
    }
  })
  </script>
  
  <style scoped>
  .grid-layout {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  
  .grid-container {
    width: 100%;
    height: 100%;
    position: relative;
    z-index: 1;
  }
  
  .grid-cell {
    width: 100%;
    height: 100%;
    overflow: auto;
    position: relative;
    z-index: 1;
  }
  
  .resize-handle {
    position: absolute;
    z-index: 100;
    background: transparent;
    transition: background-color 0.2s;
  }
  
  .resize-handle:hover {
    background-color: rgba(59, 130, 246, 0.5);
  }
  
  .resize-handle-vertical {
    top: 0;
    width: 12px;
    cursor: col-resize;
    transform: translateX(-6px);
  }
  
  /* 增加一个视觉提示线 */
  .resize-handle-vertical::before {
    content: '';
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 2px;
    background: rgba(200, 200, 200, 0.3);
    transform: translateX(-50%);
    transition: background-color 0.2s;
  }
  
  .resize-handle-vertical:hover::before {
    background: rgba(59, 130, 246, 0.8);
  }
  
  .resize-handle-horizontal {
    left: 0;
    height: 12px;
    cursor: row-resize;
    transform: translateY(-6px);
  }
  
  /* 增加一个视觉提示线 */
  .resize-handle-horizontal::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    height: 2px;
    background: rgba(200, 200, 200, 0.3);
    transform: translateY(-50%);
    transition: background-color 0.2s;
  }
  
  .resize-handle-horizontal:hover::before {
    background: rgba(59, 130, 246, 0.8);
  }
  
  .resize-handle:active {
    background-color: rgba(59, 130, 246, 0.5);
  }
  </style>
  
  
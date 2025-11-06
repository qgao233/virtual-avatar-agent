/**
 * 定时器控制器接口
 */
export interface IntervalController {
  /** 停止定时器 */
  clear: () => void
  /** 检查定时器是否正在运行 */
  isRunning: () => boolean
}

/**
 * 创建一个保证最小间隔的定时器
 * 
 * 与 setInterval 不同，此函数确保：
 * 1. 每次回调执行完成后，至少等待指定的间隔时间才开始下一次执行
 * 2. 如果回调执行时间超过间隔时间，则立即开始下一次执行
 * 
 * @param callback 要执行的异步回调函数
 * @param interval 最小间隔时间（毫秒）
 * @returns 定时器控制器，包含 clear 和 isRunning 方法
 * 
 * @example
 * ```typescript
 * const controller = setIntervalAtLeast(async () => {
 *   await fetchData()
 * }, 2000)
 * 
 * // 停止定时器
 * controller.clear()
 * ```
 */
export function setIntervalAtLeast<T = unknown>(
  callback: () => Promise<T>,
  interval: number
): IntervalController {
  let isActive = true
  let timeoutId: number | null = null

  const execute = async () => {
    // 如果已经停止，不再执行
    if (!isActive) return

    const start = Date.now()

    try {
      // 执行回调
      await callback()
    } catch (error) {
      console.error('setIntervalAtLeast 回调执行出错:', error)
    }

    // 如果在执行期间被停止，不再调度下一次
    if (!isActive) return

    const elapsed = Date.now() - start
    console.log('setIntervalAtLeast elapsed: ',elapsed)
    const delay = Math.max(0, interval - elapsed)

    // 调度下一次执行
    timeoutId = window.setTimeout(execute, delay)
  }

  // 启动第一次执行
  execute()

  // 返回控制器
  return {
    clear: () => {
      isActive = false
      if (timeoutId !== null) {
        clearTimeout(timeoutId)
        timeoutId = null
      }
    },
    isRunning: () => isActive
  }
}

/**
 * 示例：使用 setIntervalAtLeast
 */
// const controller = setIntervalAtLeast(async () => {
//   console.log('执行任务...')
//   await new Promise(resolve => setTimeout(resolve, 1000))
//   return '完成'
// }, 2000)

// 5秒后停止
// setTimeout(() => {
//   controller.clear()
//   console.log('定时器已停止')
// }, 5000)
/**
 * 前端配置文件
 */

// API 基础 URL
export const API_BASE_URL = 'http://localhost:8000'

// API 端点
export const API_ENDPOINTS = {
  // 计算机视觉
  CV: {
    RECOGNITION_GAP: `${API_BASE_URL}/api/cv/recognition-gap`,
    RECOGNIZE_FACES: `${API_BASE_URL}/api/cv/recognize-faces`
  },
  
  // 大语言模型
  LLM: {
    CHAT: `${API_BASE_URL}/api/llm/chat`,
    MULTI_AGENT: `${API_BASE_URL}/api/llm/multi-agent`,
    KB_SEARCH: `${API_BASE_URL}/api/llm/kb/search`
  },
  
  // 语音识别
  SR: {
    REALTIME: `ws://localhost:8000/api/sr/realtime`
  }
}


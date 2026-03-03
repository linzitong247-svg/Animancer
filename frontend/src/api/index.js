/**
 * API 封装
 * 提供与后端通信的接口
 */

import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 600000, // 10分钟超时，视频生成可能需要较长时间（Kling API 可能需要 5-8 分钟）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('Response error:', message)
    return Promise.reject(new Error(message))
  }
)

/**
 * 上传图片
 * @param {File} file - 图片文件
 * @returns {Promise} 上传结果
 */
export const uploadImage = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 开始生成动画
 * @param {Object} params - 生成参数
 * @param {File} params.file - 图片文件
 * @param {string} params.prompt - 用户输入的提示词
 * @returns {Promise} 生成任务结果
 */
export const startGeneration = async (params) => {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('prompt', params.prompt)
  return api.post('/generate', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取生成状态
 * @param {string} sessionId - 会话ID
 * @returns {Promise} 状态信息
 */
export const getGenerationStatus = async (sessionId) => {
  return api.get(`/status/${sessionId}`)
}

/**
 * 回答追问
 * @param {Object} params - 回答参数
 * @param {string} params.session_id - 会话ID
 * @param {string} params.answer - 用户回答
 * @returns {Promise} 回答结果
 */
export const answerQuestion = async (params) => {
  return api.post('/answer', params)
}

/**
 * 去背景
 * @param {Object} params - 去背景参数
 * @param {string} params.session_id - 会话ID
 * @returns {Promise} 去背景结果
 */
export const removeBackground = async (params) => {
  return api.post('/remove-bg', params)
}

/**
 * 导出 PNG
 * @param {Object} params - 导出参数
 * @param {string} params.session_id - 会话ID
 * @returns {Promise} 导出结果
 */
export const exportPng = async (params) => {
  return api.post('/export-png', params)
}

/**
 * 导出视频
 * @param {Object} params - 导出参数
 * @param {string} params.session_id - 会话ID
 * @returns {Promise} 导出结果
 */
export const exportVideo = async (params) => {
  return api.post('/export-video', params)
}

export default api

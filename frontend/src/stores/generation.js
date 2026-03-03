/**
 * 生成状态管理 Store
 * 使用 Pinia 管理动画生成的全局状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as api from '../api'

export const useGenerationStore = defineStore('generation', () => {
  // State
  const sessionId = ref(null)
  const uploadedImage = ref(null) // 预览 URL
  const uploadedFile = ref(null) // 原始文件对象
  const prompt = ref('')
  const status = ref('idle') // idle, uploading, generating, questioning, processing, completed, error
  const questions = ref([])
  const videoUrl = ref(null)
  const previewUrl = ref(null) // 透明 WebM 预览
  const downloadUrl = ref(null) // ZIP 下载
  const currentFrame = ref(null)
  const frames = ref([])
  const errorMessage = ref('')
  const isProcessing = ref(false)

  // Computed
  const hasImage = computed(() => !!uploadedImage.value)
  const canGenerate = computed(() => hasImage.value && prompt.value.trim().length > 0)
  const isIdle = computed(() => status.value === 'idle')
  const isLoading = computed(() => ['uploading', 'generating', 'processing'].includes(status.value))
  const isQuestioning = computed(() => status.value === 'questioning')
  const isCompleted = computed(() => status.value === 'completed')
  const hasError = computed(() => status.value === 'error')

  // Actions

  /**
   * 设置上传的图片
   * @param {File} file - 图片文件
   */
  const setUploadedImage = (file) => {
    uploadedImage.value = URL.createObjectURL(file)
    uploadedFile.value = file
  }

  /**
   * 设置提示词
   * @param {string} text - 提示词内容
   */
  const setPrompt = (text) => {
    prompt.value = text
  }

  /**
   * 开始生成动画
   */
  const startGeneration = async () => {
    if (!canGenerate.value) {
      errorMessage.value = '请先上传图片并输入提示词'
      status.value = 'error'
      return
    }

    if (!uploadedFile.value) {
      errorMessage.value = '请重新上传图片'
      status.value = 'error'
      return
    }

    try {
      status.value = 'generating'
      errorMessage.value = ''

      const response = await api.startGeneration({
        file: uploadedFile.value,
        prompt: prompt.value
      })

      sessionId.value = response.session_id
      status.value = response.status || 'generating'

      if (response.status === 'questioning' && response.questions) {
        questions.value = response.questions
        status.value = 'questioning'
      } else if (response.status === 'completed' && response.video_url) {
        videoUrl.value = response.video_url
        status.value = 'completed'
      }
    } catch (error) {
      errorMessage.value = error.message || '生成失败，请重试'
      status.value = 'error'
      console.error('Generation error:', error)
    }
  }

  /**
   * 回答追问
   * @param {string} answer - 用户回答
   */
  const answerQuestion = async (answer) => {
    if (!sessionId.value) {
      errorMessage.value = '会话不存在'
      return
    }

    try {
      status.value = 'processing'
      isProcessing.value = true
      errorMessage.value = ''

      const response = await api.answerQuestion({
        session_id: sessionId.value,
        answer
      })

      status.value = response.status || 'processing'

      if (response.status === 'questioning' && response.questions) {
        questions.value = response.questions
        status.value = 'questioning'
      } else if (response.status === 'completed' && response.video_url) {
        videoUrl.value = response.video_url
        status.value = 'completed'
      }

      if (response.questions) {
        questions.value = response.questions
      }
    } catch (error) {
      errorMessage.value = error.message || '提交回答失败'
      status.value = 'error'
      console.error('Answer error:', error)
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * 去背景
   */
  const removeBackground = async () => {
    if (!sessionId.value) {
      errorMessage.value = '会话不存在'
      return
    }

    try {
      status.value = 'processing'
      errorMessage.value = ''

      const response = await api.removeBackground({
        session_id: sessionId.value
      })

      // 存储预览和下载 URL
      if (response.preview_url) {
        previewUrl.value = response.preview_url
      }
      if (response.download_url) {
        downloadUrl.value = response.download_url
      }

      status.value = 'completed'
      ElMessage.success('去背景完成')
    } catch (error) {
      errorMessage.value = error.message || '去背景失败'
      status.value = 'error'
      console.error('Remove background error:', error)
    }
  }

  /**
   * 导出 PNG
   */
  const exportPng = async () => {
    if (!sessionId.value) {
      errorMessage.value = '会话不存在'
      return
    }

    try {
      status.value = 'processing'
      errorMessage.value = ''

      const response = await api.exportPng({
        session_id: sessionId.value
      })

      status.value = 'completed'
      return response
    } catch (error) {
      errorMessage.value = error.message || '导出失败'
      status.value = 'error'
      console.error('Export PNG error:', error)
    }
  }

  /**
   * 导出视频
   */
  const exportVideo = async () => {
    if (!sessionId.value) {
      errorMessage.value = '会话不存在'
      return
    }

    try {
      status.value = 'processing'
      errorMessage.value = ''

      const response = await api.exportVideo({
        session_id: sessionId.value
      })

      status.value = 'completed'
      return response
    } catch (error) {
      errorMessage.value = error.message || '导出失败'
      status.value = 'error'
      console.error('Export video error:', error)
    }
  }

  /**
   * 轮询获取生成状态
   */
  const pollStatus = async () => {
    if (!sessionId.value) return

    try {
      const response = await api.getGenerationStatus(sessionId.value)
      status.value = response.status

      if (response.status === 'completed' && response.video_url) {
        videoUrl.value = response.video_url
      }

      if (response.status === 'questioning' && response.questions) {
        questions.value = response.questions
      }

      return response
    } catch (error) {
      console.error('Poll status error:', error)
    }
  }

  /**
   * 重置状态
   */
  const reset = () => {
    sessionId.value = null
    uploadedImage.value = null
    uploadedFile.value = null
    prompt.value = ''
    status.value = 'idle'
    questions.value = []
    videoUrl.value = null
    currentFrame.value = null
    frames.value = []
    errorMessage.value = ''
    isProcessing.value = false
  }

  return {
    // State
    sessionId,
    uploadedImage,
    uploadedFile,
    prompt,
    status,
    questions,
    videoUrl,
    previewUrl,
    downloadUrl,
    currentFrame,
    frames,
    errorMessage,
    isProcessing,

    // Computed
    hasImage,
    canGenerate,
    isIdle,
    isLoading,
    isQuestioning,
    isCompleted,
    hasError,

    // Actions
    setUploadedImage,
    setPrompt,
    startGeneration,
    answerQuestion,
    removeBackground,
    exportPng,
    exportVideo,
    pollStatus,
    reset
  }
})

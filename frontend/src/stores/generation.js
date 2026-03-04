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
  const generationStage = ref(null) // null, 'sa_a', 'sa_g', 'sa_qc'
  let pollTimer = null

  // State - V1.5 追问轮数
  const questionRound = ref(0)
  const maxQuestionRounds = ref(2)
  const QUESTION_TIMEOUT = 60000 // 60秒超时
  let questionTimer = null

  // State - V2 答题卡模式
  const currentQuestionIndex = ref(0)  // 当前问题索引
  const selectedOptions = ref({})      // 用户选择 { question_id: selected_value }
  const customInputs = ref({})         // 自填内容 { question_id: custom_text }
  const questionAnswers = ref([])      // 最终答案数组

  // Computed
  const hasImage = computed(() => !!uploadedImage.value)
  const canGenerate = computed(() => hasImage.value && prompt.value.trim().length > 0)
  const isIdle = computed(() => status.value === 'idle')
  const isLoading = computed(() => ['uploading', 'generating', 'processing'].includes(status.value))
  const isQuestioning = computed(() => status.value === 'questioning')
  const isCompleted = computed(() => status.value === 'completed')
  const hasError = computed(() => status.value === 'error')

  // Computed - V2 答题卡模式
  const totalQuestions = computed(() => questions.value.length)
  const currentQuestion = computed(() => questions.value[currentQuestionIndex.value] || null)
  const hasMoreQuestions = computed(() => currentQuestionIndex.value < questions.value.length - 1)

  // Timer Functions - V1.5 追问超时

  /**
   * 开始追问超时计时器
   */
  const startQuestionTimer = () => {
    clearQuestionTimer()
    questionTimer = setTimeout(() => {
      console.log('[Store] 追问超时，自动继续')
      answerQuestion('（用户未及时回答，使用默认设置继续）')
    }, QUESTION_TIMEOUT)
  }

  /**
   * 清除追问超时计时器
   */
  const clearQuestionTimer = () => {
    if (questionTimer) {
      clearTimeout(questionTimer)
      questionTimer = null
    }
  }

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

      // V1.5: 更新追问轮数
      if (response.question_round !== undefined) {
        questionRound.value = response.question_round
      }
      if (response.max_question_rounds !== undefined) {
        maxQuestionRounds.value = response.max_question_rounds
      }

      if (response.status === 'questioning' && response.questions) {
        questions.value = response.questions
        status.value = 'questioning'
        // V1.5: 开始追问超时计时器
        startQuestionTimer()
      } else if (response.status === 'generating') {
        // V2: 后台生成中，启动轮询
        generationStage.value = response.generation_stage || 'sa_a'
        startPolling()
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

    // V1.5: 清除追问超时计时器
    clearQuestionTimer()

    try {
      status.value = 'processing'
      isProcessing.value = true
      errorMessage.value = ''

      const response = await api.answerQuestion({
        session_id: sessionId.value,
        answer
      })

      status.value = response.status || 'processing'

      // V1.5: 更新追问轮数
      if (response.question_round !== undefined) {
        questionRound.value = response.question_round
      }

      if (response.status === 'questioning' && response.questions) {
        questions.value = response.questions
        status.value = 'questioning'
        // V1.5: 重新开始追问超时计时器
        startQuestionTimer()
      } else if (response.status === 'completed' && response.video_url) {
        videoUrl.value = response.video_url
        status.value = 'completed'
        // V1.5: 清空追问问题
        questions.value = []
      } else {
        // V1.5: 其他状态（如 generating/processing），清空追问问题
        questions.value = []
      }
    } catch (error) {
      errorMessage.value = error.message || '提交回答失败'
      status.value = 'error'
      console.error('Answer error:', error)
    } finally {
      isProcessing.value = false
    }
  }

  // Actions - V2 答题卡模式

  /**
   * 选择选项
   * @param {string} questionId - 问题ID
   * @param {string} option - 选中的选项
   */
  const selectOption = (questionId, option) => {
    selectedOptions.value[questionId] = option
  }

  /**
   * 更新自填内容
   * @param {string} questionId - 问题ID
   * @param {string} value - 自填内容
   */
  const updateCustomInput = (questionId, value) => {
    customInputs.value[questionId] = value
  }

  /**
   * 确认当前问题，进入下一题
   * @returns {boolean} 是否还有下一题
   */
  const confirmQuestion = () => {
    const currentQ = currentQuestion.value
    if (!currentQ) return false

    const questionId = currentQ.id
    const selected = selectedOptions.value[questionId]

    // 记录答案
    questionAnswers.value.push({
      question_id: questionId,
      selected: selected,
      custom_input: customInputs.value[questionId] || null
    })

    // 进入下一题
    if (currentQuestionIndex.value < questions.value.length - 1) {
      currentQuestionIndex.value++
      return true // 还有下一题
    }
    return false // 已是最后一题
  }

  /**
   * 提交所有答案
   */
  const submitAllAnswers = async () => {
    if (!sessionId.value) return

    clearQuestionTimer()
    status.value = 'generating'
    isProcessing.value = true
    errorMessage.value = ''

    try {
      const response = await api.answerQuestion({
        session_id: sessionId.value,
        answers: questionAnswers.value
      })

      // 清空追问问题（保留 selectedOptions 用于显示完整咒语）
      questions.value = []
      currentQuestionIndex.value = 0
      customInputs.value = {}

      status.value = response.status || 'generating'
      generationStage.value = response.generation_stage || 'sa_a'

      if (response.status === 'completed' && response.video_url) {
        videoUrl.value = response.video_url
        status.value = 'completed'
        stopPolling()
      } else if (response.status === 'generating') {
        startPolling()
      }
    } catch (error) {
      errorMessage.value = error.message || '提交失败'
      status.value = 'error'
      console.error('Submit answers error:', error)
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * 重置追问状态
   */
  const resetQuestionState = () => {
    currentQuestionIndex.value = 0
    selectedOptions.value = {}
    customInputs.value = {}
    questionAnswers.value = []
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
   * 开始轮询生成状态
   */
  const startPolling = () => {
    stopPolling()
    pollTimer = setInterval(async () => {
      if (!sessionId.value) return
      try {
        const response = await api.getGenerationStatus(sessionId.value)
        generationStage.value = response.generation_stage || null

        if (response.status === 'completed') {
          stopPolling()
          if (response.video_url) {
            videoUrl.value = response.video_url
          }
          status.value = 'completed'
          generationStage.value = null
        } else if (response.status === 'failed' || response.status === 'error') {
          stopPolling()
          errorMessage.value = response.error || '生成失败'
          status.value = 'error'
          generationStage.value = null
        }
      } catch (error) {
        console.error('Poll status error:', error)
      }
    }, 3000)
  }

  /**
   * 停止轮询
   */
  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  /**
   * 轮询获取生成状态（单次）
   */
  const pollStatus = async () => {
    if (!sessionId.value) return

    try {
      const response = await api.getGenerationStatus(sessionId.value)
      status.value = response.status
      generationStage.value = response.generation_stage || null

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
    // V1.5: 重置追问轮数和计时器
    questionRound.value = 0
    clearQuestionTimer()
    // V2: 重置答题卡状态
    resetQuestionState()
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
    generationStage,
    // V1.5: 追问轮数状态
    questionRound,
    maxQuestionRounds,
    // V2: 答题卡状态
    currentQuestionIndex,
    selectedOptions,
    customInputs,
    questionAnswers,

    // Computed
    hasImage,
    canGenerate,
    isIdle,
    isLoading,
    isQuestioning,
    isCompleted,
    hasError,
    // V2: 答题卡计算属性
    totalQuestions,
    currentQuestion,
    hasMoreQuestions,

    // Actions
    setUploadedImage,
    setPrompt,
    startGeneration,
    answerQuestion,
    removeBackground,
    exportPng,
    exportVideo,
    pollStatus,
    reset,
    startPolling,
    stopPolling,
    // V2: 答题卡方法
    selectOption,
    updateCustomInput,
    confirmQuestion,
    submitAllAnswers,
    resetQuestionState
  }
})

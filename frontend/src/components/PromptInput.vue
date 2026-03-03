<template>
  <div class="prompt-input">
    <div class="input-section">
      <label class="input-label">
        <span>动作描述</span>
        <el-tooltip content="描述你想要生成的动画动作，如：角色行走、跳跃、攻击等" placement="top">
          <el-icon class="help-icon"><question-filled /></el-icon>
        </el-tooltip>
      </label>
      <el-input
        v-model="localPrompt"
        type="textarea"
        :rows="4"
        placeholder="描述你想要生成的动画动作...&#10;例如：&#10;- 角色缓慢行走，手臂自然摆动&#10;- 角色跳跃并落下&#10;- 角色挥剑攻击"
        :disabled="disabled || isLoading"
        maxlength="500"
        show-word-limit
        @keydown.ctrl.enter="handleSubmit"
      />
    </div>

    <div class="action-buttons">
      <el-button
        type="primary"
        size="large"
        :disabled="!canSubmit || disabled"
        :loading="isLoading"
        @click="handleSubmit"
      >
        <el-icon class="button-icon"><video-play /></el-icon>
        {{ isLoading ? '生成中...' : '开始生成' }}
      </el-button>
    </div>

    <!-- 追问对话区域 -->
    <transition name="slide-fade">
      <div v-if="questions.length > 0 || conversationHistory.length > 0" class="conversation-area">
        <div class="conversation-header">
          <span class="header-text">对话追问</span>
          <el-badge :value="questions.length" :hidden="questions.length === 0" type="primary" />
        </div>

        <div class="conversation-messages">
          <!-- 历史消息 -->
          <div
            v-for="(msg, index) in conversationHistory"
            :key="`history-${index}`"
            :class="['message', msg.role]"
          >
            <div class="message-content">
              <div class="message-text">{{ msg.content }}</div>
              <div class="message-time">{{ msg.time }}</div>
            </div>
          </div>

          <!-- 当前追问问题 -->
          <div
            v-for="(question, qIndex) in questions"
            :key="`question-${qIndex}`"
            class="message question"
          >
            <div class="message-content">
              <div class="message-text">{{ question }}</div>
            </div>
          </div>
        </div>

        <!-- 追问回答输入 -->
        <div v-if="questions.length > 0" class="answer-section">
          <el-input
            v-model="answerText"
            placeholder="请回答问题以继续生成..."
            :disabled="isAnswering"
            @keydown.ctrl.enter="handleAnswer"
          >
            <template #append>
              <el-button
                type="primary"
                :disabled="!answerText.trim() || isAnswering"
                :loading="isAnswering"
                @click="handleAnswer"
              >
                发送
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </transition>

    <!-- 生成状态提示 -->
    <transition name="fade">
      <div v-if="statusMessage" class="status-message">
        <el-icon class="status-icon" :class="statusType"><loading v-if="isLoading" /><info-filled v-else /></el-icon>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { QuestionFilled, VideoPlay, Loading, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useGenerationStore } from '../stores/generation'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'answer'])

const store = useGenerationStore()

const localPrompt = ref('')
const answerText = ref('')
const conversationHistory = ref([])
const isAnswering = ref(false)

// 从 store 获取状态
const isLoading = computed(() => store.isLoading || store.isProcessing)
const questions = computed(() => store.questions)
const status = computed(() => store.status)
const errorMessage = computed(() => store.errorMessage)

const canSubmit = computed(() => {
  return store.hasImage && localPrompt.value.trim().length > 0
})

const statusMessage = computed(() => {
  switch (status.value) {
    case 'uploading':
      return '正在上传图片...'
    case 'generating':
      return 'AI 正在生成动画，请稍候...'
    case 'processing':
      return '正在处理您的请求...'
    case 'completed':
      return '动画生成完成！'
    case 'error':
      return errorMessage.value || '生成失败，请重试'
    default:
      return ''
  }
})

const statusType = computed(() => {
  return status.value === 'error' ? 'error' : 'info'
})

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  localPrompt.value = newVal || ''
}, { immediate: true })

// 监听本地输入变化
watch(localPrompt, (newVal) => {
  emit('update:modelValue', newVal)
  store.setPrompt(newVal)
})

// 监听追问问题变化
watch(() => store.questions, (newQuestions) => {
  if (newQuestions.length > 0) {
    // 滚动到追问区域
    setTimeout(() => {
      const conversationArea = document.querySelector('.conversation-area')
      if (conversationArea) {
        conversationArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }, 100)
  }
})

/**
 * 提交生成请求
 */
const handleSubmit = () => {
  if (!canSubmit.value) {
    ElMessage.warning('请先上传图片并输入动作描述')
    return
  }

  const prompt = localPrompt.value.trim()
  if (!prompt) {
    ElMessage.warning('请输入动作描述')
    return
  }

  // 添加用户消息到历史
  conversationHistory.value.push({
    role: 'user',
    content: prompt,
    time: formatTime(new Date())
  })

  store.startGeneration()
}

/**
 * 回答追问
 */
const handleAnswer = () => {
  const answer = answerText.value.trim()
  if (!answer) {
    ElMessage.warning('请输入回答内容')
    return
  }

  // 添加用户回答到历史
  questions.value.forEach((question) => {
    conversationHistory.value.push({
      role: 'assistant',
      content: question,
      time: formatTime(new Date())
    })
  })

  conversationHistory.value.push({
    role: 'user',
    content: answer,
    time: formatTime(new Date())
  })

  const currentAnswer = answer
  answerText.value = ''
  isAnswering.value = true

  emit('answer', currentAnswer)
  store.answerQuestion(currentAnswer).finally(() => {
    isAnswering.value = false
  })
}

/**
 * 格式化时间
 */
const formatTime = (date) => {
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}
</script>

<style scoped>
.prompt-input {
  width: 100%;
}

.input-section {
  margin-bottom: 20px;
}

.input-label {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.help-icon {
  margin-left: 6px;
  font-size: 16px;
  color: var(--el-text-color-secondary);
  cursor: help;
}

:deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.action-buttons .el-button {
  flex: 1;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}

.button-icon {
  margin-right: 8px;
}

/* 对话区域 */
.conversation-area {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 12px;
  border: 1px solid var(--el-border-color);
}

.conversation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.conversation-messages {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 16px;
  padding-right: 8px;
}

.conversation-messages::-webkit-scrollbar {
  width: 6px;
}

.conversation-messages::-webkit-scrollbar-track {
  background: transparent;
}

.conversation-messages::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

.message {
  display: flex;
  margin-bottom: 12px;
  animation: messageSlide 0.3s ease;
}

@keyframes messageSlide {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message.question {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
}

.message.user .message-content {
  background: var(--el-color-primary);
  color: #fff;
  padding: 10px 14px;
  border-radius: 12px 12px 0 12px;
}

.message.assistant .message-content,
.message.question .message-content {
  background: #fff;
  padding: 10px 14px;
  border-radius: 12px 12px 12px 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message.question .message-content {
  background: #fff9e6;
  border: 1px solid #ffe58f;
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.message.user .message-text {
  color: #fff;
}

.message-time {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.7;
}

.answer-section {
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 12px;
}

/* 状态消息 */
.status-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin-top: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  font-size: 14px;
}

.status-message.error {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.status-icon {
  font-size: 18px;
}

.status-icon.error {
  color: var(--el-color-danger);
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

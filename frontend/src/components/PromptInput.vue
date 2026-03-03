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

    <!-- V2: 答题卡区域 -->
    <transition name="slide-fade">
      <div v-if="showQuestionCard" class="question-area">
        <QuestionCard
          :question="currentQuestion"
          :current-step="currentStep"
          :total-steps="totalQuestions"
          :answers-history="answersHistory"
          @confirm="handleQuestionConfirm"
        />
      </div>
    </transition>

    <!-- 生成状态提示 -->
    <transition name="fade">
      <div v-if="statusMessage" class="status-message" :class="{ error: status === 'error' }">
        <el-icon class="status-icon" :class="{ error: status === 'error' }">
          <loading v-if="isLoading" />
          <info-filled v-else />
        </el-icon>
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
import QuestionCard from './QuestionCard.vue'

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

const emit = defineEmits(['update:modelValue', 'submit'])

const store = useGenerationStore()

const localPrompt = ref('')

// 从 store 获取状态
const isLoading = computed(() => store.isLoading || store.isProcessing)
const status = computed(() => store.status)
const errorMessage = computed(() => store.errorMessage)

// V2: 答题卡相关状态
const questions = computed(() => store.questions)
const currentQuestion = computed(() => store.currentQuestion)
const currentQuestionIndex = computed(() => store.currentQuestionIndex)
const totalQuestions = computed(() => store.totalQuestions)

const currentStep = computed(() => currentQuestionIndex.value + 1)

const showQuestionCard = computed(() => {
  return store.isQuestioning && questions.value.length > 0 && currentQuestion.value
})

// 构建答题历史状态（用于显示 ✅🔄⏳ 状态）
const answersHistory = computed(() => {
  return questions.value.map((q, idx) => {
    // 获取问题名称（去掉"请选择"前缀）
    const label = q.question.replace('请选择', '')

    // 确定状态
    let status = 'pending' // 待选择
    let value = ''

    if (idx < currentQuestionIndex.value) {
      // 已答完的问题
      status = 'done'
      // 从 questionAnswers 中获取答案
      const answer = store.questionAnswers.find(a => a.question_id === q.id)
      value = answer?.custom_input || answer?.selected || ''
    } else if (idx === currentQuestionIndex.value) {
      // 当前答题中的问题
      status = 'current'
      value = ''
    }

    return {
      status,      // 'done' | 'current' | 'pending'
      label,       // 问题名称（如"角色性格"）
      value        // 已答问题的答案值
    }
  })
})

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

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  localPrompt.value = newVal || ''
}, { immediate: true })

// 监听本地输入变化
watch(localPrompt, (newVal) => {
  emit('update:modelValue', newVal)
  store.setPrompt(newVal)
})

// 监听追问问题变化，滚动到答题卡区域
watch(showQuestionCard, (show) => {
  if (show) {
    setTimeout(() => {
      const questionArea = document.querySelector('.question-area')
      if (questionArea) {
        questionArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
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

  store.startGeneration()
}

/**
 * V2: 处理答题卡确认
 */
const handleQuestionConfirm = async ({ questionId, selected, customInput }) => {
  // 更新 store 中的选择状态
  store.selectOption(questionId, customInput || selected)

  if (customInput) {
    store.updateCustomInput(questionId, customInput)
  }

  // 确认当前问题
  const hasMore = store.confirmQuestion()

  // 如果没有更多问题，提交所有答案
  if (!hasMore) {
    await store.submitAllAnswers()
  }
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

/* V2: 答题卡区域 */
.question-area {
  margin-top: 20px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

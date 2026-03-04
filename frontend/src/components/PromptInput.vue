<template>
  <div class="grimoire">
    <!-- Section header -->
    <div class="section-header">
      <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
        <path d="M2 17l10 5 10-5"/>
        <path d="M2 12l10 5 10-5"/>
      </svg>
      <h3 class="section-title">INCANTATION</h3>
    </div>

    <!-- Prompt textarea -->
    <div class="input-section">
      <div class="textarea-wrap">
        <textarea
          v-model="localPrompt"
          class="prompt-area"
          rows="4"
          placeholder="描述你想要生成的动画动作...&#10;例如：&#10;- 角色缓慢行走，手臂自然摆动&#10;- 角色跳跃并落下&#10;- 角色挥剑攻击"
          :disabled="disabled || isLoading"
          maxlength="500"
          @keydown.ctrl.enter="handleSubmit"
        ></textarea>
        <span class="char-count">{{ localPrompt.length }} / 500</span>
      </div>
    </div>

    <!-- Submit button -->
    <div class="action-buttons">
      <button
        class="btn-gold"
        :disabled="!canSubmit || disabled"
        @click="handleSubmit"
      >
        <span v-if="isLoading" class="btn-spinner"></span>
        <span v-else class="btn-star">&#10022;</span>
        {{ isLoading ? '生成中...' : '开始生成' }}
      </button>
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
        <span class="status-indicator" :class="{ spinning: isLoading, error: status === 'error' }">
          <svg v-if="isLoading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/>
            <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="12" cy="16" r="1"/>
          </svg>
        </span>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
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
/* ── Grimoire card ──────────────────────────────────── */
.grimoire {
  width: 100%;
  background: linear-gradient(
    165deg,
    rgba(38, 34, 69, 0.7) 0%,
    rgba(19, 18, 32, 0.85) 100%
  );
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 28px 24px;
  position: relative;
  overflow: visible;
}

.grimoire::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 16px;
  padding: 1px;
  background: linear-gradient(
    160deg,
    var(--lavender) 0%,
    transparent 40%,
    transparent 60%,
    var(--gold-dim) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.45;
}

/* ── Section header ─────────────────────────────────── */
.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.section-icon {
  width: 20px;
  height: 20px;
  color: var(--lavender);
  flex-shrink: 0;
}

.section-title {
  font-family: 'Cinzel', serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 3px;
  color: var(--lavender);
  margin: 0;
  text-transform: uppercase;
}

/* ── Input section ──────────────────────────────────── */
.input-section {
  margin-bottom: 20px;
}

.textarea-wrap {
  position: relative;
}

.prompt-area {
  width: 100%;
  min-height: 120px;
  padding: 14px 16px;
  padding-bottom: 30px;
  background: rgba(19, 18, 32, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  color: var(--text-bright);
  font-family: 'Cormorant Garamond', 'Georgia', serif;
  font-size: 15px;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
  box-sizing: border-box;
}

.prompt-area::placeholder {
  color: var(--text-dim);
  font-family: 'Cormorant Garamond', 'Georgia', serif;
  font-style: italic;
  font-size: 14px;
  opacity: 0.7;
}

.prompt-area:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--gold-dim);
}

.prompt-area:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.char-count {
  position: absolute;
  bottom: 8px;
  right: 14px;
  font-size: 11px;
  color: var(--text-dim);
  font-family: 'Cormorant Garamond', serif;
  pointer-events: none;
  user-select: none;
}

/* ── Gold button ────────────────────────────────────── */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.btn-gold {
  flex: 1;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 28px;
  background: linear-gradient(135deg, var(--gold-dim) 0%, var(--amber) 50%, var(--gold) 100%);
  color: var(--void);
  border: none;
  border-radius: 10px;
  font-family: 'Cinzel', serif;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn-gold::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.15) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.05) 100%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-gold:hover:not(:disabled)::before {
  opacity: 1;
}

.btn-gold:hover:not(:disabled) {
  box-shadow: 0 0 24px var(--gold-glow), 0 4px 16px rgba(0, 0, 0, 0.3);
  transform: translateY(-1px);
}

.btn-gold:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 0 12px var(--gold-glow);
}

.btn-gold:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  filter: saturate(0.3);
}

.btn-star {
  font-size: 16px;
  line-height: 1;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--void);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ── Question area ──────────────────────────────────── */
.question-area {
  margin-top: 20px;
  background: rgba(8, 7, 13, 0.45);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px;
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

/* ── Status message ─────────────────────────────────── */
.status-message {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-top: 16px;
  background: rgba(8, 7, 13, 0.5);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  font-size: 13px;
  color: var(--text-mid);
  font-family: 'Cormorant Garamond', serif;
}

.status-message.error {
  background: rgba(180, 40, 60, 0.12);
  border-color: var(--rose);
  color: var(--rose);
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.status-indicator svg {
  width: 18px;
  height: 18px;
  color: var(--lavender);
}

.status-indicator.spinning svg {
  animation: spin 1.2s linear infinite;
}

.status-indicator.error svg {
  color: var(--rose);
}

/* ── Transitions ────────────────────────────────────── */
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

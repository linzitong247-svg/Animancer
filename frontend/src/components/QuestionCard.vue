<template>
  <div class="question-area">
    <!-- Answers status timeline -->
    <div v-if="answersHistory.length > 0" class="answers-status">
      <div class="status-line"></div>
      <div
        v-for="(ans, idx) in answersHistory"
        :key="idx"
        :class="['status-item', ans.status]"
      >
        <span class="status-dot"></span>
        <span class="status-text">{{ ans.label }}：{{ ans.status === 'done' ? ans.value : ans.status === 'current' ? '答题中...' : '待选择' }}</span>
      </div>
    </div>

    <!-- Step badge -->
    <div class="question-header">
      <span class="step-badge">STEP {{ toRoman(currentStep) }} / {{ toRoman(totalSteps) }}</span>
      <span class="question-title">{{ question.question }}</span>
    </div>

    <!-- Options 2x2 grid -->
    <div class="options-grid">
      <div
        v-for="(option, index) in question.options"
        :key="index"
        :class="['option-item', { selected: selectedIndex === index }]"
        @click="handleSelect(index)"
      >
        {{ option }}
      </div>
    </div>

    <!-- Custom text input -->
    <transition name="slide">
      <div v-if="showCustomInput" class="custom-input-wrapper">
        <input
          v-model="customText"
          class="custom-input"
          placeholder="请输入..."
          @keydown.enter="handleConfirm"
        />
      </div>
    </transition>

    <!-- Confirm button -->
    <div class="action-area">
      <button
        class="btn-gold"
        :disabled="!canConfirm"
        @click="handleConfirm"
      >
        确定
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  question: {
    type: Object,
    required: true
  },
  currentStep: {
    type: Number,
    default: 1
  },
  totalSteps: {
    type: Number,
    default: 3
  },
  answersHistory: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['confirm'])

const selectedIndex = ref(null)
const customText = ref('')

// Roman numeral conversion
const toRoman = (num) => {
  const lookup = [
    [1000, 'M'], [900, 'CM'], [500, 'D'], [400, 'CD'],
    [100, 'C'], [90, 'XC'], [50, 'L'], [40, 'XL'],
    [10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']
  ]
  let result = ''
  let remaining = num
  for (const [value, symbol] of lookup) {
    while (remaining >= value) {
      result += symbol
      remaining -= value
    }
  }
  return result
}

// 是否是"其他（自填）"选项
const isCustomOption = computed(() => {
  if (selectedIndex.value === null) return false
  const option = props.question.options[selectedIndex.value]
  return option.includes('其他') || option.includes('自填')
})

const showCustomInput = computed(() => isCustomOption.value)

const canConfirm = computed(() => {
  if (selectedIndex.value === null) return false
  if (isCustomOption.value && !customText.value.trim()) return false
  return true
})

const handleSelect = (index) => {
  selectedIndex.value = index
  if (!isCustomOption.value) {
    customText.value = ''
  }
}

const handleConfirm = () => {
  if (!canConfirm.value) return

  const option = props.question.options[selectedIndex.value]
  emit('confirm', {
    questionId: props.question.id,
    selected: option,
    customInput: isCustomOption.value ? customText.value : null
  })
}

// 重置状态
watch(() => props.question, () => {
  selectedIndex.value = null
  customText.value = ''
}, { immediate: true })
</script>

<style scoped>
/* ── Outer dark inset panel ── */
.question-area {
  background: var(--obsidian);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 28px 24px;
  box-shadow: inset 0 2px 12px rgba(0, 0, 0, 0.25);
}

/* ── Answers status timeline ── */
.answers-status {
  position: relative;
  background: var(--void);
  border-left: 2px solid var(--gold);
  border-radius: 10px;
  padding: 14px 16px 14px 22px;
  margin-bottom: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
  font-size: 13px;
  position: relative;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-sizing: border-box;
}

/* Completed: emerald solid dot */
.status-item.done .status-dot {
  background: var(--emerald);
  box-shadow: 0 0 6px var(--emerald);
}

/* Current: gold pulsing dot */
.status-item.current .status-dot {
  background: var(--gold);
  box-shadow: 0 0 8px var(--gold);
  animation: pulse 1.8s ease-in-out infinite;
}

/* Pending: gray hollow dot */
.status-item.pending .status-dot {
  background: transparent;
  border: 2px solid var(--slate);
}

.status-text {
  color: var(--text-dim);
}

.status-item.done .status-text {
  color: var(--emerald);
}

.status-item.current .status-text {
  color: var(--gold);
  font-weight: 600;
}

.status-item.pending .status-text {
  color: var(--text-dim);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.35);
  }
}

/* ── Question header ── */
.question-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.step-badge {
  display: inline-flex;
  align-self: flex-start;
  font-family: 'Cinzel', serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--gold);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15), rgba(212, 175, 55, 0.06));
  border: 1px solid var(--gold);
  border-radius: 999px;
  padding: 4px 16px;
}

.question-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-bright);
  line-height: 1.5;
}

/* ── Options 2x2 grid ── */
.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.option-item {
  padding: 14px 16px;
  background: var(--obsidian);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  text-align: center;
  color: var(--text-mid);
  cursor: pointer;
  transition: all 0.25s ease;
  user-select: none;
  font-size: 14px;
}

.option-item:hover {
  border-color: var(--gold);
  background: var(--gold-dim);
  color: var(--text-bright);
}

.option-item.selected {
  border-color: var(--gold);
  background: var(--gold-dim);
  color: var(--gold);
  font-weight: 600;
  box-shadow: inset 0 0 18px var(--gold-glow);
}

/* ── Custom text input ── */
.custom-input-wrapper {
  margin-bottom: 20px;
}

.custom-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--void);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-bright);
  font-size: 14px;
  outline: none;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
  box-sizing: border-box;
}

.custom-input::placeholder {
  color: var(--text-dim);
}

.custom-input:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 2px var(--gold-glow);
}

/* ── Confirm button ── */
.action-area {
  display: flex;
  justify-content: flex-end;
}

.btn-gold {
  padding: 10px 32px;
  background: linear-gradient(135deg, var(--gold), var(--amber));
  color: var(--void);
  font-size: 14px;
  font-weight: 700;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
  letter-spacing: 0.06em;
}

.btn-gold:hover:not(:disabled) {
  box-shadow: 0 0 20px var(--gold-glow), 0 4px 12px rgba(0, 0, 0, 0.4);
  transform: translateY(-1px);
}

.btn-gold:active:not(:disabled) {
  transform: translateY(0);
}

.btn-gold:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* ── Slide transition ── */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>

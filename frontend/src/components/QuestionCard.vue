<template>
  <div class="question-card">
    <div class="question-header">
      <span class="step-indicator">步骤 {{ currentStep }}/{{ totalSteps }}</span>
      <span class="question-title">{{ question.question }}</span>
    </div>

    <!-- 已答状态列表 -->
    <div v-if="answersHistory.length > 0" class="answers-status">
      <div
        v-for="(ans, idx) in answersHistory"
        :key="idx"
        :class="['status-item', ans.status]"
      >
        <span class="status-icon">{{ ans.status === 'done' ? '✅' : ans.status === 'current' ? '🔄' : '⏳' }}</span>
        <span class="status-text">{{ ans.label }}：{{ ans.status === 'done' ? ans.value : ans.status === 'current' ? '答题中...' : '待选择' }}</span>
      </div>
    </div>

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

    <!-- 自填输入框 -->
    <transition name="slide">
      <div v-if="showCustomInput" class="custom-input-wrapper">
        <el-input
          v-model="customText"
          placeholder="请输入..."
          @keydown.enter="handleConfirm"
        />
      </div>
    </transition>

    <div class="action-area">
      <el-button
        type="primary"
        :disabled="!canConfirm"
        @click="handleConfirm"
      >
        确定
      </el-button>
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
.question-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  padding: 20px;
}

.question-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.step-indicator {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.question-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 已答状态列表 */
.answers-status {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}

.status-icon {
  font-size: 14px;
}

.status-text {
  color: var(--el-text-color-regular);
}

.status-item.current .status-text {
  color: var(--el-color-primary);
  font-weight: 500;
}

.status-item.pending .status-text {
  color: var(--el-text-color-placeholder);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.option-item {
  padding: 12px 16px;
  border: 2px solid var(--el-border-color);
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.option-item:hover {
  border-color: var(--el-color-primary-light-3);
  background: var(--el-fill-color-light);
}

.option-item.selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.custom-input-wrapper {
  margin-bottom: 16px;
}

.action-area {
  display: flex;
  justify-content: flex-end;
}

/* 过渡动画 */
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

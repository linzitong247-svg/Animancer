<script setup>
import { computed } from 'vue'
import { useGenerationStore } from '../stores/generation'

const store = useGenerationStore()

const statusText = computed(() => {
  switch (store.status) {
    case 'uploading': return '上传角色图像...'
    case 'generating':
      // 根据 generationStage 显示不同的阶段文字
      if (store.generationStage === 'sa_a') return '生成提示词...'
      if (store.generationStage === 'sa_g') return '生成动画...'
      if (store.generationStage === 'sa_qc') return '质量检测...'
      return '正在召唤动画精灵...'
    case 'processing': return '精炼动画序列...'
    default: return '处理中...'
  }
})

const progressPercent = computed(() => {
  switch (store.status) {
    case 'uploading': return 20
    case 'generating': return 55
    case 'processing': return 85
    default: return 0
  }
})

// 完整咒语 = 用户输入 + 细化选项
const fullPrompt = computed(() => {
  const parts = []

  // 用户输入
  if (store.prompt) {
    parts.push(store.prompt)
  }

  // 细化选项（如活泼可爱、行走、侧面）
  const options = store.selectedOptions
  if (options && Object.keys(options).length > 0) {
    const optionValues = Object.values(options).filter(v => v)
    if (optionValues.length > 0) {
      parts.push(optionValues.join('、'))
    }
  }

  return parts.join(' | ')
})
</script>

<template>
  <div class="generation-progress">
    <div class="progress-header">
      <!-- Spinning loader ring -->
      <div class="loader-ring"></div>
      <div class="progress-info">
        <span class="progress-status">{{ statusText }}</span>
        <span class="progress-percent">{{ progressPercent }}%</span>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="progress-track">
      <div
        class="progress-fill"
        :style="{ width: progressPercent + '%' }"
      ></div>
    </div>

    <!-- Parameter summary -->
    <div v-if="fullPrompt" class="progress-summary">
      <span class="summary-label">咒语</span>
      <span class="summary-value">{{ fullPrompt }}</span>
    </div>
  </div>
</template>

<style scoped>
.generation-progress {
  background: linear-gradient(160deg, rgba(38, 34, 69, 0.6), rgba(19, 18, 32, 0.75));
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 18px;
  backdrop-filter: blur(8px);
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

/* Spinning loader ring */
.loader-ring {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(212, 168, 83, 0.15);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: orbit 1s linear infinite;
  flex-shrink: 0;
}

@keyframes orbit {
  to { transform: rotate(360deg); }
}

.progress-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.progress-status {
  font-size: 13px;
  color: var(--text-bright);
}

.progress-percent {
  font-family: 'Cinzel', serif;
  font-size: 14px;
  color: var(--gold);
  font-weight: 600;
}

/* Progress bar */
.progress-track {
  width: 100%;
  height: 4px;
  background: var(--obsidian);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--amber), var(--amethyst));
  border-radius: 2px;
  transition: width 0.6s ease;
  position: relative;
}

/* Shimmer animation */
.progress-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.2) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Parameter summary */
.progress-summary {
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.summary-label {
  font-size: 11px;
  color: var(--text-dim);
  flex-shrink: 0;
}

.summary-value {
  font-size: 12px;
  color: var(--text-mid);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

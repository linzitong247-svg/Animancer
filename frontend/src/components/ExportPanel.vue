<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useGenerationStore } from '../stores/generation'

const props = defineProps({
  videoId: String,
  hasVideo: Boolean
})

const store = useGenerationStore()
const removingBg = ref(false)
async function handleRemoveBg() {
  removingBg.value = true
  try {
    await store.removeBackground()
  } finally {
    removingBg.value = false
  }
}

function handleDownloadZip() {
  if (!store.downloadUrl) return
  const link = document.createElement('a')
  link.href = store.downloadUrl
  link.download = 'animancer-frames.zip'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  setTimeout(() => {
    ElMessage.success('下载完成')
  }, 5000)
}
</script>

<template>
  <div class="grimoire export-panel">
    <div class="section-header">
      <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      <h4 class="section-title">EXPORT</h4>
    </div>

    <div class="actions">
      <button
        class="btn-ghost"
        :disabled="!hasVideo || removingBg"
        @click="handleRemoveBg"
      >
        <span v-if="removingBg" class="spinner"></span>
        <span v-else class="btn-icon">&#10022;</span>
        去除背景
      </button>

      <button
        class="btn-gold"
        :disabled="!store.downloadUrl"
        @click="handleDownloadZip"
      >
        <span class="btn-icon">&#8681;</span>
        下载 ZIP
      </button>
    </div>

    <p class="info-text">
      去除背景后将生成带透明通道的 PNG 序列帧
    </p>
  </div>
</template>

<style scoped>
.export-panel {
  padding: 20px 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.header-icon {
  width: 18px;
  height: 18px;
  color: var(--emerald);
  flex-shrink: 0;
}

.section-title {
  margin: 0;
  font-family: 'Cinzel', serif;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.15em;
  color: var(--text-bright);
}

.actions {
  display: flex;
  gap: 12px;
}

.actions .btn-ghost,
.actions .btn-gold {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-icon {
  font-size: 14px;
  line-height: 1;
}

.info-text {
  margin: 14px 0 0 0;
  font-size: 12px;
  color: var(--text-dim);
  line-height: 1.6;
}

/* Spinner */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border-subtle);
  border-top-color: var(--lavender);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

<script setup>
import { ref, computed } from 'vue'
import ImageUpload from '../components/ImageUpload.vue'
import PromptInput from '../components/PromptInput.vue'
import VideoPreview from '../components/VideoPreview.vue'
import ExportPanel from '../components/ExportPanel.vue'
import StepSidebar from '../components/StepSidebar.vue'
import GenerationProgress from '../components/GenerationProgress.vue'
import { useGenerationStore } from '../stores/generation'

const store = useGenerationStore()
const promptText = ref('')

const currentStep = computed(() => {
  if (!store.hasImage) return 1
  if (store.isCompleted) return 5
  if (store.isLoading) return 4
  if (store.isQuestioning) return 3
  // 有图片但还没开始生成（无论prompt是否为空）→ step 2
  if (store.status === 'idle') return 2
  return 2
})

const generationStage = computed(() => store.generationStage)


</script>

<template>
  <div class="home">
    <header class="header anim-fade-down">
      <div class="brand">
        <span class="brand-name">Animancer</span>
        <span class="brand-cn">唤灵师</span>
        <span class="brand-ver">v2.0</span>
      </div>
    </header>

    <div class="workspace">
      <StepSidebar :current-step="currentStep" :generation-stage="generationStage" class="anim-slide-right" />

      <div class="panel panel-input">
        <ImageUpload class="anim-rise" style="animation-delay: 0.10s" />
        <PromptInput v-model="promptText" class="anim-rise" style="animation-delay: 0.18s" />
      </div>

      <div class="panel panel-preview">
        <VideoPreview
          v-if="store.previewUrl"
          :src="store.previewUrl"
          :fps="24"
        />
        <VideoPreview
          v-else-if="store.videoUrl"
          :src="store.videoUrl"
          :fps="24"
        />
        <div v-else class="preview-placeholder anim-rise" style="animation-delay: 0.12s">
          <div class="placeholder-sigil">
            <div class="placeholder-orbit"></div>
            <div class="placeholder-orbit placeholder-orbit-reverse"></div>
            <span class="placeholder-icon">✦</span>
          </div>
          <p class="placeholder-text">Awaiting conjuration...</p>
          <p class="placeholder-hint">上传角色图片并描述动作后开始生成</p>
        </div>

        <GenerationProgress v-if="store.isLoading" class="anim-rise" style="animation-delay: 0.22s" />

        <ExportPanel
          v-if="store.videoUrl"
          :video-id="store.sessionId"
          :has-video="!!store.videoUrl"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr;
  position: relative;
  z-index: 1;
}

/* Header */
.header {
  padding: 14px 28px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(12, 11, 20, 0.6);
  backdrop-filter: blur(16px);
  z-index: 2;
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.brand-name {
  font-family: 'Cinzel Decorative', serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--gold);
  text-shadow: 0 0 20px var(--gold-glow);
}

.brand-cn {
  font-size: 13px;
  color: var(--text-mid);
  letter-spacing: 2px;
}

.brand-ver {
  font-family: 'Cinzel', serif;
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 1px;
  padding: 2px 8px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
}

/* Workspace — 3 column layout */
.workspace {
  display: grid;
  grid-template-columns: 120px 1fr 1fr;
  overflow: hidden;
}

.panel {
  overflow-y: auto;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-input {
  border-right: 1px solid var(--border-subtle);
}

.panel-preview {
  background: rgba(28, 25, 53, 0.18);
}

/* Preview placeholder */
.preview-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 300px;
  border: 1px dashed rgba(219, 180, 96, 0.15);
  border-radius: 14px;
  background: rgba(28, 25, 53, 0.35);
}

.placeholder-sigil {
  width: 64px;
  height: 64px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  font-size: 20px;
  color: var(--amber);
  opacity: 0.4;
  z-index: 1;
}

.placeholder-orbit {
  position: absolute;
  inset: 0;
  border: 1px solid rgba(219, 180, 96, 0.15);
  border-radius: 50%;
  border-top-color: rgba(219, 180, 96, 0.4);
  animation: orbit 6s linear infinite;
}

.placeholder-orbit-reverse {
  inset: -6px;
  border-color: rgba(157, 142, 199, 0.06);
  border-top-color: rgba(157, 142, 199, 0.15);
  animation: orbit 10s linear infinite reverse;
}

@keyframes orbit {
  to { transform: rotate(360deg); }
}

.placeholder-text {
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 16px;
  color: var(--text-mid);
  letter-spacing: 1px;
}

.placeholder-hint {
  font-size: 12px;
  color: var(--text-dim);
}

</style>

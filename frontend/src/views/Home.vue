<script setup>
import { ref } from 'vue'
import ImageUpload from '../components/ImageUpload.vue'
import PromptInput from '../components/PromptInput.vue'
import VideoPreview from '../components/VideoPreview.vue'
import ExportPanel from '../components/ExportPanel.vue'
import { useGenerationStore } from '../stores/generation'

const store = useGenerationStore()

const promptText = ref('')

function downloadZip() {
  if (store.downloadUrl) {
    const link = document.createElement('a')
    link.href = store.downloadUrl
    link.download = ''
    link.click()
  }
}
</script>

<template>
  <div class="home">
    <div class="header">
      <h1>Animancer 唤灵师</h1>
      <p>2D角色动作动画生成工具</p>
    </div>

    <div class="main-content">
      <!-- 左侧：输入区域 -->
      <div class="left-panel">
        <ImageUpload />

        <PromptInput
          v-model="promptText"
          :loading="store.status === 'generating'"
        />
      </div>

      <!-- 右侧：预览区域 -->
      <div class="right-panel">
        <!-- 优先显示透明背景预览，否则显示原始视频 -->
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
        <div v-else class="preview-placeholder">
          <el-empty description="上传图片并输入描述后生成动画" />
        </div>

        <!-- 下载按钮 -->
        <div v-if="store.downloadUrl" class="download-section">
          <el-button type="success" @click="downloadZip">
            下载 PNG 序列帧 (ZIP)
          </el-button>
        </div>

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
.home { padding: 20px; max-width: 1400px; margin: 0 auto; }
.header { text-align: center; margin-bottom: 24px; }
.header h1 { margin: 0; font-size: 32px; }
.header p { margin: 8px 0 0; color: #909399; }

.main-content { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.left-panel, .right-panel { display: flex; flex-direction: column; gap: 16px; }

.preview-placeholder {
  border: 2px dashed #e4e7ed;
  border-radius: 8px;
  padding: 40px;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.download-section {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}
</style>

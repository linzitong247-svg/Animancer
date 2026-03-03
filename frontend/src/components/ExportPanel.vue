<script setup>
import { ref } from 'vue'
import { MagicStick, InfoFilled } from '@element-plus/icons-vue'
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
</script>

<template>
  <div class="export-panel">
    <h4>导出选项</h4>

    <div class="actions">
      <el-button
        type="primary"
        :disabled="!hasVideo || removingBg"
        :loading="removingBg"
        @click="handleRemoveBg"
      >
        <el-icon><MagicStick /></el-icon>
        去除背景
      </el-button>
    </div>

    <div class="info">
      <el-text size="small" type="info">
        <el-icon><InfoFilled /></el-icon>
        去除背景后将生成带透明通道的 PNG 序列帧
      </el-text>
    </div>
  </div>
</template>

<style scoped>
.export-panel { padding: 16px; border: 1px solid #e4e7ed; border-radius: 8px; }
.export-panel h4 { margin: 0 0 12px 0; font-size: 16px; }
.actions { display: flex; gap: 12px; }
.info { margin-top: 12px; }
</style>

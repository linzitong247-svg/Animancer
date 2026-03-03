<template>
  <div class="image-upload">
    <div class="upload-section">
      <el-upload
        class="upload-area"
        drag
        :auto-upload="false"
        :show-file-list="false"
        accept=".jpg,.jpeg,.png"
        :disabled="disabled"
        :on-change="handleFileChange"
      >
        <div v-if="!previewUrl" class="upload-placeholder">
          <el-icon class="upload-icon"><upload-filled /></el-icon>
          <div class="upload-text">点击或拖拽图片到此处上传</div>
          <div class="upload-hint">支持 JPG、PNG 格式，建议图片清晰度 512x512 以上</div>
        </div>
        <div v-else class="image-preview">
          <img :src="previewUrl" alt="预览图片" />
          <div class="preview-overlay">
            <el-icon class="preview-icon" @click.stop="handleRemove"><circle-close /></el-icon>
          </div>
        </div>
      </el-upload>
    </div>

    <div v-if="previewUrl && !disabled" class="image-info">
      <div class="info-item">
        <span class="label">文件名：</span>
        <span class="value">{{ fileName }}</span>
      </div>
      <div class="info-item">
        <span class="label">文件大小：</span>
        <span class="value">{{ fileSize }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { UploadFilled, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useGenerationStore } from '../stores/generation'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'remove'])

const store = useGenerationStore()
const previewUrl = ref(null)
const fileName = ref('')
const fileSize = ref('')

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal !== previewUrl.value) {
    previewUrl.value = newVal
  }
}, { immediate: true })

// 监听 store 中的图片变化
watch(() => store.uploadedImage, (newVal) => {
  if (newVal) {
    previewUrl.value = newVal
  }
})

/**
 * 文件选择变化时处理
 */
const handleFileChange = (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return

  const isImage = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage) {
    ElMessage.error('只支持 JPG、PNG 格式的图片！')
    return
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB！')
    return
  }

  // 设置文件信息
  fileName.value = file.name
  fileSize.value = formatFileSize(file.size)

  // 设置本地预览
  previewUrl.value = URL.createObjectURL(file)

  // 保存到 store（不自动上传，在生成时一起上传）
  store.setUploadedImage(file)
}

/**
 * 移除图片
 */
const handleRemove = () => {
  previewUrl.value = null
  fileName.value = ''
  fileSize.value = ''
  emit('update:modelValue', null)
  emit('remove')
}

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.image-upload {
  width: 100%;
}

.upload-section {
  margin-bottom: 16px;
}

.upload-area {
  width: 100%;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  min-height: 280px;
  padding: 20px;
  border: 2px dashed var(--el-border-color);
  border-radius: 12px;
  background: var(--el-fill-color-light);
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
  background: var(--el-fill-color);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 240px;
}

.upload-icon {
  font-size: 64px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}

.upload-text {
  font-size: 16px;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  font-weight: 500;
}

.upload-hint {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  text-align: center;
  line-height: 1.6;
}

.image-preview {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview img {
  max-width: 100%;
  max-height: 280px;
  object-fit: contain;
  border-radius: 8px;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-preview:hover .preview-overlay {
  opacity: 1;
}

.preview-icon {
  font-size: 40px;
  color: #fff;
  cursor: pointer;
}

.image-info {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .label {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  min-width: 80px;
}

.info-item .value {
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 500;
}

:deep(.el-upload.is-disabled .el-upload-dragger) {
  background: var(--el-fill-color-lighter);
  border-color: var(--el-border-color-lighter);
  cursor: not-allowed;
}
</style>

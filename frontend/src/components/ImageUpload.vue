<template>
  <div class="grimoire image-upload">
    <!-- Section Header -->
    <div class="section-header">
      <span class="section-icon">&#x2726;</span>
      <span class="section-title" style="color: var(--amber);">CHARACTER</span>
    </div>

    <!-- Upload Zone (no preview) -->
    <div
      v-if="!previewUrl"
      class="drop-zone"
      :class="{ 'drop-zone--hover': isDragOver, 'drop-zone--disabled': disabled }"
      @dragenter.prevent="onDragEnter"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      @click="triggerFileInput"
    >
      <div class="drop-zone__circle">
        <svg class="drop-zone__icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M24 4v28M14 22l10 10 10-10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M8 34v6a4 4 0 004 4h24a4 4 0 004-4v-6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="drop-zone__text">点击或拖拽图片到此处上传</div>
      <div class="drop-zone__hint">支持 JPG、PNG 格式，建议图片清晰度 512x512 以上</div>
      <input
        ref="fileInputRef"
        type="file"
        accept=".jpg,.jpeg,.png"
        class="drop-zone__input"
        :disabled="disabled"
        @change="onFileInputChange"
      />
    </div>

    <!-- Image Preview -->
    <div v-else class="preview">
      <div class="preview__canvas">
        <img :src="previewUrl" alt="预览图片" class="preview__img" />
        <div class="preview__overlay" @click="handleRemove">
          <svg class="preview__remove-icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2"/>
            <path d="M11 11l10 10M21 11l-10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- File Info -->
    <div v-if="previewUrl && !disabled" class="file-info">
      <div class="file-info__row">
        <span class="file-info__label">文件名：</span>
        <span class="file-info__value">{{ fileName }}</span>
      </div>
      <div class="file-info__row">
        <span class="file-info__label">文件大小：</span>
        <span class="file-info__value">{{ fileSize }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
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
const isDragOver = ref(false)
const fileInputRef = ref(null)

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

/* ---- Drag-and-drop + file input helpers ---- */

function processFile(file) {
  if (!file) return
  // Wrap in the shape handleFileChange expects
  handleFileChange({ raw: file })
}

function triggerFileInput() {
  if (props.disabled) return
  fileInputRef.value?.click()
}

function onFileInputChange(e) {
  const file = e.target.files?.[0]
  processFile(file)
  // Reset so the same file can be re-selected
  e.target.value = ''
}

function onDragEnter() {
  if (props.disabled) return
  isDragOver.value = true
}

function onDragOver() {
  if (props.disabled) return
  isDragOver.value = true
}

function onDragLeave() {
  isDragOver.value = false
}

function onDrop(e) {
  isDragOver.value = false
  if (props.disabled) return
  const file = e.dataTransfer?.files?.[0]
  processFile(file)
}
</script>

<style scoped>
/* ========================================
   Drop Zone — magic circle style
   ======================================== */
.drop-zone {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  border: 2px dashed rgba(212, 168, 83, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.4s, border-color 0.4s;
}

.drop-zone:hover,
.drop-zone--hover {
  border-color: var(--amber);
  background: radial-gradient(ellipse at center, rgba(212, 168, 83, 0.06) 0%, transparent 70%);
}

.drop-zone--disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

.drop-zone__input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  pointer-events: none; /* clicks handled by parent */
}

/* ---- Orbiting circle icon ---- */
.drop-zone__circle {
  position: relative;
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.drop-zone__circle::before,
.drop-zone__circle::after {
  content: '';
  position: absolute;
  border: 1px solid rgba(212, 168, 83, 0.18);
  border-radius: 50%;
}

.drop-zone__circle::before {
  width: 72px;
  height: 72px;
  animation: orbit 8s linear infinite;
}

.drop-zone__circle::after {
  width: 96px;
  height: 96px;
  animation: orbit 12s linear infinite reverse;
}

@keyframes orbit {
  0%   { transform: rotate(0deg); border-color: rgba(212, 168, 83, 0.18); }
  50%  { border-color: rgba(212, 168, 83, 0.35); }
  100% { transform: rotate(360deg); border-color: rgba(212, 168, 83, 0.18); }
}

.drop-zone__icon {
  width: 36px;
  height: 36px;
  color: var(--text-dim);
  transition: color 0.3s;
}

.drop-zone:hover .drop-zone__icon,
.drop-zone--hover .drop-zone__icon {
  color: var(--gold);
}

.drop-zone__text {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-mid);
  margin-bottom: 6px;
}

.drop-zone__hint {
  font-size: 12px;
  color: var(--text-dim);
  text-align: center;
  line-height: 1.6;
}

/* ========================================
   Image Preview — checkerboard for transparency
   ======================================== */
.preview {
  margin-bottom: 0;
}

.preview__canvas {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  /* dark checkerboard for transparent areas */
  background-color: var(--abyss);
  background-image:
    linear-gradient(45deg, var(--obsidian) 25%, transparent 25%),
    linear-gradient(-45deg, var(--obsidian) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, var(--obsidian) 75%),
    linear-gradient(-45deg, transparent 75%, var(--obsidian) 75%);
  background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
}

.preview__img {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

.preview__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 7, 13, 0.55);
  opacity: 0;
  transition: opacity 0.3s;
  cursor: pointer;
}

.preview__canvas:hover .preview__overlay {
  opacity: 1;
}

.preview__remove-icon {
  width: 40px;
  height: 40px;
  color: #fff;
  transition: color 0.2s;
}

.preview__remove-icon:hover {
  color: var(--rose);
}

/* ========================================
   File Info — dark background subtle
   ======================================== */
.file-info {
  margin-top: 14px;
  padding: 12px 16px;
  background: rgba(14, 13, 23, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
}

.file-info__row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.file-info__row:last-child {
  margin-bottom: 0;
}

.file-info__label {
  color: var(--text-dim);
  font-size: 13px;
  min-width: 76px;
}

.file-info__value {
  color: var(--text-mid);
  font-size: 13px;
  font-weight: 500;
}
</style>

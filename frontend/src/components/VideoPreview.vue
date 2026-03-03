<script setup>
import { ref } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'

const props = defineProps({
  src: String,
  fps: { type: Number, default: 24 }
})

const emit = defineEmits(['frame-change'])

const videoRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const currentFrame = ref(0)
const totalFrames = ref(0)

function togglePlay() {
  if (!videoRef.value) return
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

function seekTo(time) {
  if (!videoRef.value) return
  videoRef.value.currentTime = time
  currentTime.value = time
  updateFrame()
}

function stepFrame(direction = 1) {
  if (!videoRef.value) return
  const frameDuration = 1 / props.fps
  const newTime = Math.min(Math.max(0, videoRef.value.currentTime + direction * frameDuration), duration.value)
  seekTo(newTime)
  if (isPlaying.value) {
    videoRef.value.pause()
    isPlaying.value = false
  }
}

function updateFrame() {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime
  currentFrame.value = Math.floor(currentTime.value * props.fps)
}

function onLoadedMetadata() {
  if (!videoRef.value) return
  duration.value = videoRef.value.duration
  totalFrames.value = Math.floor(duration.value * props.fps)
}

function onTimeUpdate() {
  updateFrame()
  if (isPlaying.value && videoRef.value?.ended) {
    isPlaying.value = false
  }
}

function formatTime(seconds) {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <div class="video-preview">
    <video
      ref="videoRef"
      :src="src"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @ended="isPlaying = false"
    ></video>

    <div class="controls">
      <div class="playback-controls">
        <el-button @click="togglePlay" circle>
          <el-icon><VideoPlay v-if="!isPlaying" /><VideoPause v-else /></el-icon>
        </el-button>

        <el-button-group>
          <el-button @click="() => stepFrame(-1)" :disabled="isPlaying">上一帧</el-button>
          <el-button @click="() => stepFrame(1)" :disabled="isPlaying">下一帧</el-button>
        </el-button-group>

        <span class="frame-counter">{{ currentFrame }} / {{ totalFrames }} 帧</span>
      </div>

      <div class="progress-bar">
        <el-slider :model-value="currentTime" :max="duration" :step="0.001" @change="(val) => seekTo(val)" />
        <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-preview { border: 1px solid #e4e7ed; border-radius: 8px; overflow: hidden; }
.video-preview video {
  width: 100%;
  max-height: 400px;
  display: block;
  /* 棋盘格背景 - 用于显示透明区域 */
  background-image:
    linear-gradient(45deg, #ccc 25%, transparent 25%),
    linear-gradient(-45deg, #ccc 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #ccc 75%),
    linear-gradient(-45deg, transparent 75%, #ccc 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  background-color: #fff;
}
.controls { padding: 12px; background: #f5f7fa; }
.playback-controls { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.frame-counter { font-family: monospace; font-size: 14px; color: #606266; }
.progress-bar { display: flex; align-items: center; gap: 12px; }
.time-display { font-family: monospace; font-size: 12px; color: #909399; min-width: 80px; }
</style>

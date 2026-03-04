<script setup>
import { ref, computed } from 'vue'

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

const progressPercent = computed(() => {
  if (!duration.value) return 0
  return (currentTime.value / duration.value) * 100
})

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

function onRangeInput(e) {
  const val = parseFloat(e.target.value)
  seekTo(val)
}
</script>

<template>
  <div class="preview-frame">
    <div class="preview-label">PREVIEW</div>

    <div class="video-viewport">
      <video
        ref="videoRef"
        :src="src"
        @loadedmetadata="onLoadedMetadata"
        @timeupdate="onTimeUpdate"
        @ended="isPlaying = false"
      ></video>
    </div>

    <div class="controls">
      <div class="playback-controls">
        <button
          class="step-btn"
          :disabled="isPlaying"
          @click="stepFrame(-1)"
          title="Previous frame"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6 8.5 6V6z" />
          </svg>
        </button>

        <button class="play-btn" @click="togglePlay" title="Play / Pause">
          <svg v-if="!isPlaying" viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
            <path d="M8 5v14l11-7z" />
          </svg>
          <svg v-else viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
          </svg>
        </button>

        <button
          class="step-btn"
          :disabled="isPlaying"
          @click="stepFrame(1)"
          title="Next frame"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
          </svg>
        </button>

        <span class="frame-counter">
          {{ currentFrame }}<span class="frame-sep">/</span>{{ totalFrames }} frames
        </span>
      </div>

      <div class="timeline-row">
        <div class="timeline-track-wrapper">
          <input
            type="range"
            class="timeline-range"
            :value="currentTime"
            :max="duration || 0"
            step="0.001"
            min="0"
            @input="onRangeInput"
            :style="{ '--progress': progressPercent + '%' }"
          />
        </div>
        <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preview-frame {
  position: relative;
  background: var(--slate);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  overflow: hidden;
}

/* ── Top-right label ── */
.preview-label {
  position: absolute;
  top: 12px;
  right: 16px;
  font-family: 'Cinzel', serif;
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--text-dim);
  pointer-events: none;
  z-index: 2;
  text-transform: uppercase;
}

/* ── Video viewport ── */
.video-viewport {
  position: relative;
  background:
    repeating-conic-gradient(var(--slate) 0% 25%, var(--abyss) 0% 50%)
    50% / 20px 20px;
}

.video-viewport video {
  display: block;
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  background: transparent;
}

/* ── Controls area ── */
.controls {
  padding: 14px 18px 16px;
  background: var(--obsidian);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Playback row ── */
.playback-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Play button — gold gradient circle with glow */
.play-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--gold), var(--amber));
  color: var(--void);
  box-shadow: 0 0 14px var(--gold-glow), 0 2px 6px rgba(0, 0, 0, 0.4);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.play-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 0 22px var(--gold-glow), 0 2px 8px rgba(0, 0, 0, 0.5);
}
.play-btn:active {
  transform: scale(0.96);
}

/* Step buttons — transparent circles */
.step-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-mid);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.step-btn:hover:not(:disabled) {
  border-color: var(--gold);
  color: var(--gold);
  background: var(--gold-dim);
}
.step-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Frame counter */
.frame-counter {
  font-family: 'Cinzel', serif;
  font-size: 13px;
  letter-spacing: 0.06em;
  color: var(--text-mid);
  margin-left: auto;
}
.frame-sep {
  margin: 0 2px;
  color: var(--text-dim);
}

/* ── Timeline row ── */
.timeline-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.timeline-track-wrapper {
  flex: 1;
  position: relative;
}

/* Custom range input */
.timeline-range {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  background: linear-gradient(
    to right,
    var(--gold) 0%,
    var(--amethyst) var(--progress, 0%),
    var(--obsidian) var(--progress, 0%),
    var(--obsidian) 100%
  );
}

/* Webkit track */
.timeline-range::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 2px;
  background: transparent;
}

/* Webkit thumb */
.timeline-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--gold);
  border: 2px solid var(--abyss);
  box-shadow: 0 0 8px var(--gold-glow);
  margin-top: -5px;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.timeline-range::-webkit-slider-thumb:hover {
  transform: scale(1.25);
  box-shadow: 0 0 14px var(--gold-glow);
}

/* Firefox track */
.timeline-range::-moz-range-track {
  height: 4px;
  border-radius: 2px;
  background: var(--obsidian);
}

/* Firefox progress fill */
.timeline-range::-moz-range-progress {
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(to right, var(--gold), var(--amethyst));
}

/* Firefox thumb */
.timeline-range::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--gold);
  border: 2px solid var(--abyss);
  box-shadow: 0 0 8px var(--gold-glow);
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.timeline-range::-moz-range-thumb:hover {
  transform: scale(1.25);
  box-shadow: 0 0 14px var(--gold-glow);
}

/* Time display */
.time-display {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--text-dim);
  min-width: 80px;
  text-align: right;
  white-space: nowrap;
}
</style>

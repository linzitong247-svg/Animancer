<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const containerRef = ref(null)
const PARTICLE_COUNT = 35

const particles = Array.from({ length: PARTICLE_COUNT }, (_, i) => {
  const size = 1.2 + Math.random() * 2.3
  const duration = 10 + Math.random() * 15
  const delay = Math.random() * 12
  const left = Math.random() * 100
  const isGold = Math.random() < 0.7
  return { id: i, size, duration, delay, left, isGold }
})
</script>

<template>
  <div ref="containerRef" class="particle-canvas">
    <div
      v-for="p in particles"
      :key="p.id"
      class="particle"
      :style="{
        width: p.size + 'px',
        height: p.size + 'px',
        left: p.left + '%',
        animationDuration: p.duration + 's',
        animationDelay: p.delay + 's',
        background: p.isGold
          ? 'radial-gradient(circle, var(--gold), transparent)'
          : 'radial-gradient(circle, var(--lavender), transparent)',
      }"
    />
  </div>
</template>

<style scoped>
.particle-canvas {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.particle {
  position: absolute;
  bottom: -10px;
  border-radius: 50%;
  opacity: 0;
  animation: drift linear infinite;
}

@keyframes drift {
  0% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.1;
  }
  100% {
    transform: translateY(-100vh) translateX(30px);
    opacity: 0;
  }
}
</style>

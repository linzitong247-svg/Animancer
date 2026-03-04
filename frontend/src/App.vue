<script setup>
import Home from './views/Home.vue'
import ParticleCanvas from './components/ParticleCanvas.vue'
</script>

<template>
  <div id="app">
    <!-- Atmosphere layers — fixed positioning, no layout impact -->
    <div class="atmosphere">
      <div class="gradient-mesh"></div>
      <div class="noise-grain"></div>
      <ParticleCanvas />
    </div>
    <Home />
  </div>
</template>

<style>
/* ========================================
   Element Plus Dark Theme Overrides
   ======================================== */
:root {
  --el-color-primary: #d4a853;
  --el-color-primary-light-3: #e0bc6e;
  --el-color-primary-light-5: #e8cf8f;
  --el-color-primary-light-7: #f0dfb0;
  --el-color-primary-light-8: #f5e9c8;
  --el-color-primary-light-9: #faf4e3;
  --el-color-primary-dark-2: #b8862d;
  --el-color-success: #5eb88a;
  --el-color-danger: #c9616b;
  --el-bg-color: #0e0d17;
  --el-bg-color-overlay: #16142a;
  --el-bg-color-page: #08070d;
  --el-fill-color: #1e1b3a;
  --el-fill-color-light: #16142a;
  --el-fill-color-lighter: #0e0d17;
  --el-fill-color-blank: #08070d;
  --el-text-color-primary: #f0ece0;
  --el-text-color-regular: #a09b8e;
  --el-text-color-secondary: #5c584e;
  --el-text-color-placeholder: #5c584e;
  --el-border-color: rgba(212, 168, 83, 0.08);
  --el-border-color-light: rgba(212, 168, 83, 0.06);
  --el-border-color-lighter: rgba(212, 168, 83, 0.04);
  --el-border-radius-base: 10px;
  --el-border-radius-small: 6px;
  --el-border-radius-round: 20px;
  --el-border-radius-circle: 100%;
  --el-mask-color: rgba(8, 7, 13, 0.7);
}

/* el-message dark styling */
.el-message {
  background: var(--obsidian) !important;
  border-color: var(--border-subtle) !important;
}
.el-message .el-message__content {
  color: var(--text-bright) !important;
}
</style>

<style scoped>
#app {
  position: relative;
  height: 100%;
  min-height: 100vh;
}

/* ========================================
   Atmosphere Layers
   ======================================== */
.atmosphere {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.gradient-mesh {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 15% 20%, rgba(126, 110, 168, 0.16), transparent),
    radial-gradient(ellipse 55% 45% at 80% 70%, rgba(219, 180, 96, 0.12), transparent);
}

.noise-grain {
  position: absolute;
  inset: 0;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 256px 256px;
}
</style>

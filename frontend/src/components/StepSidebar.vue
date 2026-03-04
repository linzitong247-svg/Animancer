<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStep: {
    type: Number,
    default: 1
  },
  generationStage: {
    type: String,
    default: null,
    validator: (value) => [null, 'sa_a', 'sa_g', 'sa_qc'].includes(value)
  }
})

const steps = [
  { num: 1, label: '上传角色', icon: '◈' },
  { num: 2, label: '描述动作', icon: '✎' },
  { num: 3, label: '细化选项', icon: '☰' },
  { num: 4, label: '生成动画', icon: '✦', hasSubSteps: true },
  { num: 5, label: '导出结果', icon: '↓' },
]

const subSteps = [
  { id: 'sa_a', label: '提示词生成' },
  { id: 'sa_g', label: '动画生成' },
  { id: 'sa_qc', label: '质量检测' },
]

const getStepState = (stepNum) => {
  if (stepNum < props.currentStep) return 'completed'
  if (stepNum === props.currentStep) return 'current'
  return 'pending'
}

const getSubStepState = (subStepId, index) => {
  // 当 currentStep < 4: 所有子步骤为 pending
  if (props.currentStep < 4) return 'pending'
  // 当 currentStep > 4 (即5): 所有子步骤为 completed
  if (props.currentStep > 4) return 'completed'
  // 当 currentStep === 4
  if (props.currentStep === 4) {
    if (props.generationStage === 'sa_a') {
      // 第1个子步骤为 current，其他为 pending
      if (subStepId === 'sa_a') return 'current'
      return 'pending'
    }
    if (props.generationStage === 'sa_g') {
      // 第1个 completed，第2个 current，第3个 pending
      if (subStepId === 'sa_a') return 'completed'
      if (subStepId === 'sa_g') return 'current'
      return 'pending'
    }
    if (props.generationStage === 'sa_qc') {
      // 第1、2个 completed，第3个 current
      if (subStepId === 'sa_a') return 'completed'
      if (subStepId === 'sa_g') return 'completed'
      if (subStepId === 'sa_qc') return 'current'
    }
    // 如果 generationStage 为 null，默认 pending
    return 'pending'
  }
  return 'pending'
}
</script>

<template>
  <aside class="step-sidebar">
    <!-- Brand logo -->
    <div class="sidebar-brand">
      <div class="brand-sigil">
        <span class="sigil-letter">A</span>
        <div class="sigil-orbit"></div>
        <div class="sigil-orbit sigil-orbit-reverse"></div>
      </div>
    </div>

    <!-- Step list -->
    <nav class="step-list">
      <div
        v-for="(step, index) in steps"
        :key="step.num"
        :class="['step-item', getStepState(step.num)]"
      >
        <!-- Connector line (not on first) -->
        <div
          v-if="index > 0"
          :class="[
            'step-line',
            getStepState(step.num),
            { 'sub-connector': steps[index - 1]?.hasSubSteps }
          ]"
        ></div>

        <!-- Step dot -->
        <div :class="['step-dot', getStepState(step.num)]">
          <span v-if="getStepState(step.num) === 'completed'" class="dot-check">✓</span>
        </div>

        <!-- Step label -->
        <span :class="['step-label', getStepState(step.num)]">{{ step.label }}</span>

        <!-- Sub steps for step 4 -->
        <div v-if="step.hasSubSteps" class="sub-steps">
          <!-- Connector from main step to first sub-step (dashed) -->
          <div :class="['sub-step-line', getSubStepState(subSteps[0].id, 0)]"></div>

          <div
            v-for="(subStep, subIndex) in subSteps"
            :key="subStep.id"
            :class="['sub-step-item', getSubStepState(subStep.id, subIndex)]"
          >
            <!-- Dashed connector line -->
            <div v-if="subIndex > 0" :class="['sub-step-line', getSubStepState(subStep.id, subIndex)]"></div>

            <!-- Small dot -->
            <div :class="['sub-step-dot', getSubStepState(subStep.id, subIndex)]">
              <span v-if="getSubStepState(subStep.id, subIndex) === 'completed'" class="sub-dot-check">✓</span>
            </div>

            <!-- Label -->
            <span :class="['sub-step-label', getSubStepState(subStep.id, subIndex)]">{{ subStep.label }}</span>
          </div>
        </div>
      </div>
    </nav>

    <div class="sidebar-spacer"></div>
  </aside>
</template>

<style scoped>
.step-sidebar {
  background: linear-gradient(180deg, var(--obsidian), var(--abyss));
  border-right: 1px solid var(--border-subtle);
  padding: 14px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
}

/* Right edge gold shimmer line */
.step-sidebar::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, transparent, var(--amber), transparent);
  opacity: 0.15;
}

/* Brand sigil */
.sidebar-brand {
  margin-bottom: 28px;
  padding: 8px 0;
}

.brand-sigil {
  width: 42px;
  height: 42px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sigil-letter {
  font-family: 'Cinzel Decorative', serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--gold);
  text-shadow: 0 0 12px var(--gold-glow);
  position: relative;
  z-index: 1;
}

.sigil-orbit {
  position: absolute;
  inset: 0;
  border: 1px solid rgba(212, 168, 83, 0.15);
  border-radius: 50%;
  border-top-color: var(--amber);
  animation: orbit 6s linear infinite;
}

.sigil-orbit-reverse {
  inset: -4px;
  border-color: rgba(157, 142, 199, 0.1);
  border-top-color: var(--lavender);
  animation: orbit 10s linear infinite reverse;
}

@keyframes orbit {
  to { transform: rotate(360deg); }
}

/* Step list */
.step-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  width: 100%;
  padding: 0 10px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

/* Connector line */
.step-line {
  width: 2px;
  height: 20px;
  margin-bottom: 4px;
  transition: background 0.3s;
}

.step-line.completed {
  background: var(--emerald);
}

.step-line.current {
  background: var(--amber);
  background-image: repeating-linear-gradient(
    to bottom,
    var(--amber) 0px,
    var(--amber) 4px,
    transparent 4px,
    transparent 8px
  );
  animation: dash-flow 1s linear infinite;
}

.step-line.pending {
  background: var(--text-dim);
  opacity: 0.3;
}

/* Sub-connector style (dashed line between sub-steps group and normal steps) */
.step-line.sub-connector {
  background: transparent;
  width: 1px;
  height: 12px;
  margin-bottom: 3px;
  margin-left: 12px;
  border-left: 1px dashed;
}

.step-line.sub-connector.completed {
  border-color: var(--emerald);
}

.step-line.sub-connector.current {
  border-color: var(--amber);
  animation: dash-pulse 1s ease-in-out infinite;
}

.step-line.sub-connector.pending {
  border-color: var(--text-dim);
  opacity: 0.3;
}

@keyframes dash-flow {
  to { background-position: 0 8px; }
}

/* Step dot */
.step-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
  transition: all 0.3s;
  font-size: 10px;
}

.step-dot.completed {
  background: var(--emerald);
  color: var(--void);
}

.dot-check {
  font-size: 11px;
  font-weight: 700;
}

.step-dot.current {
  background: var(--amber);
  color: var(--void);
  box-shadow: 0 0 12px var(--gold-glow);
  animation: pulse 1.5s ease-in-out infinite;
}

.step-dot.pending {
  background: transparent;
  border: 1.5px solid var(--text-dim);
  opacity: 0.4;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 8px var(--gold-glow); }
  50% { box-shadow: 0 0 18px var(--gold-glow); }
}

/* Step label */
.step-label {
  font-size: 10px;
  letter-spacing: 0.5px;
  text-align: center;
  transition: color 0.3s;
  margin-bottom: 2px;
  white-space: nowrap;
}

.step-label.completed {
  color: var(--text-mid);
}

.step-label.current {
  color: var(--gold);
  text-shadow: 0 0 10px var(--gold-glow);
  font-weight: 500;
}

.step-label.pending {
  color: var(--text-dim);
  opacity: 0.5;
}

/* Sub steps container */
.sub-steps {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 8px;
  padding-left: 12px;
}

.sub-step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

/* Sub step connector line (dashed) */
.sub-step-line {
  width: 1px;
  height: 12px;
  margin-bottom: 3px;
  transition: background 0.3s;
  border-left: 1px dashed;
}

.sub-step-line.completed {
  border-color: var(--emerald);
}

.sub-step-line.current {
  border-color: var(--amber);
  animation: dash-pulse 1s ease-in-out infinite;
}

.sub-step-line.pending {
  border-color: var(--text-dim);
  opacity: 0.3;
}

@keyframes dash-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Sub step dot (smaller) */
.sub-step-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2px;
  transition: all 0.3s;
  font-size: 8px;
}

.sub-step-dot.completed {
  background: var(--emerald);
  color: var(--void);
}

.sub-dot-check {
  font-size: 8px;
  font-weight: 700;
}

.sub-step-dot.current {
  background: var(--amber);
  color: var(--void);
  box-shadow: 0 0 8px var(--gold-glow);
  animation: pulse 1.5s ease-in-out infinite;
}

.sub-step-dot.pending {
  background: transparent;
  border: 1px solid var(--text-dim);
  opacity: 0.4;
}

/* Sub step label */
.sub-step-label {
  font-size: 8px;
  letter-spacing: 0.3px;
  text-align: center;
  transition: color 0.3s;
  white-space: nowrap;
}

.sub-step-label.completed {
  color: var(--text-mid);
}

.sub-step-label.current {
  color: var(--gold);
  text-shadow: 0 0 8px var(--gold-glow);
  font-weight: 500;
}

.sub-step-label.pending {
  color: var(--text-dim);
  opacity: 0.5;
}

.sidebar-spacer {
  flex: 1;
}
</style>

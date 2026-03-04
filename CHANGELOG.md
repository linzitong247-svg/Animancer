# Changelog

All notable changes to Animancer will be documented in this file.

## [V2.0] - 2026-03-05

### Added - 前端视觉重构（暗金魔法主题）

- **全新视觉设计**：魔法工坊（Arcane Workshop）主题
  - 暗色奢华 + 暗黑奇幻风格
  - 深色底（#0c0b14）+ 琥珀金主色（#d4a853）+ 薰衣草紫辅色（#9d8ec7）
  - Google Fonts 字体（Cinzel Decorative / Cormorant Garamond / Noto Sans SC）

- **新组件**：
  - `StepSidebar.vue`：5 步进度侧栏（上传 → 描述 → 细化 → 生成 → 导出）
  - `ParticleCanvas.vue`：金色/紫色粒子上浮背景
  - `GenerationProgress.vue`：渐变进度条 + shimmer 动画

- **布局重构**：
  - 三栏布局：进度侧栏（~120px）+ 左面板（输入）+ 右面板（预览）
  - 品牌顶栏：Cinzel Decorative 字体 "Animancer 唤灵师 v2.0"
  - 旋转魔法阵预览占位符

- **组件视觉升级**：
  - `ImageUpload`：魔法阵风格上传区，双轨道旋转圆环
  - `PromptInput`：渐变边框卡片，Cormorant Garamond 斜体 placeholder
  - `QuestionCard`：暗色内嵌面板，金色边线时间线，选中态内发光
  - `VideoPreview`：自定义播放按钮/滑块，金色渐变样式
  - `ExportPanel`：btn-ghost + btn-gold 双按钮

- **动画系统**：
  - 入场动画：staggered reveal（顶栏 → 侧栏 → 卡片依次浮现）
  - 交互动画：hover 发光、按钮光扫、选项选中发光
  - 持续动画：粒子飘浮、魔法阵旋转、进度步骤脉冲

### Changed - 后端优化

- **SAA System Prompt**：新增 2D 横版游戏约束
  - 侧视角构图，禁止 3D 透视和镜头旋转
  - 固定镜头，只有角色动
  - 可循环动作（首尾姿态一致）
  - 角色必须始终完整在画面内（不能出框）

- **Kling API**：传尾帧实现循环播放
  - 默认模型升级为 `kling-v2`
  - 支持模型：v2.1 / v2.5-turbo / v2.6 / v3
  - 首帧=尾帧=用户上传图片，动画可无缝循环

- **SAQC 质量检查**：启用真实质检
  - 删除测试模式硬编码返回
  - 5 张关键帧（0% / 25% / 50% / 75% / 95%）传给 LLM 评估
  - 新评估维度：Pose Plausibility (40%) / Visual Consistency (30%) / Frame Quality (30%)
  - Pass 阈值从 20 提升到 60

- **LLM 服务**：扩展多图支持
  - `chat()` 新增 `image_urls` 参数支持多张图片

### Removed

- **Element Plus 全量导入**：移除后 CSS 从 381KB → 43KB，JS 从 1197KB → 164KB
- 仅保留 `ElMessage` 样式导入

### Technical

- 全局 CSS 变量重写（暗色调色板、金色系、辅助色）
- 全局 `.grimoire` 卡片样式 + `.btn-gold` / `.btn-ghost` 按钮
- `generation.js` 新增 `currentStep` 计算属性
- 亮度调优：提亮暗色调色板，增强文字对比度

---

## [V1.5] - 2026-03-03

### Added

- **答题卡模式**：将开放式追问改为选择题答题卡
  - 3 个固定问题：角色性格、动作类型、镜头角度
  - 每个问题提供 3-4 个预设选项 + "其他（自填）"
  - 2x2 网格选项布局，点击选择
  - 答题进度状态显示（✅已答、🔄答题中、⏳待选择）

- **QuestionCard 组件**：新建答题卡 UI 组件
  - 支持单选选项
  - "其他"选项时展开自填输入框
  - 显示当前步骤（x/3）

### Changed

- **后端问题模板**：`QUESTION_TEMPLATES` 固定问题，不再依赖 LLM 生成
- **API 请求格式**：`/api/answer` 支持 `answers` 数组格式
- **状态码统一**：`need_more_info` → `questioning`

### Fixed

- JSON 解析失败（LLM 返回单引号字符串）
- 追问轮数逻辑（用户回答后直接进入生成）
- 前端问题列表状态同步
- 答题历史状态显示

### Technical

- 添加答题进度日志追踪
- 添加 JSON 解析容错（多种解析策略）
- 前端 store 新增答题卡状态管理

---

## [V1.0] - 2026-02-28

### Added

- **AI 动画生成**：上传图片 + 动作描述 → 自动生成动画视频
- **智能追问**：信息不足时 AI 主动询问
- **质量检查**：AI 自动评估生成结果
- **背景移除**：一键移除视频背景
- **WebM 预览**：透明背景视频浏览器预览
- **ZIP 下载**：PNG 序列帧打包下载
- **多 Agent 架构**：MA + SA_A + SA_G + SA_QC
- **Electron 桌面应用**支持

### Technical Stack

- 前端：Vue 3 + Vite + Element Plus + Pinia
- 后端：FastAPI + 智谱 GLM-4 + 可灵 AI
- 背景移除：RMBG-1.4
- 视频处理：FFmpeg

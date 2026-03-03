# Changelog

All notable changes to Animancer will be documented in this file.

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

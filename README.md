# 险而易见 · InsurDeck

AI 驱动的智能 PPT 生成桌面应用 —— 保险行业专版，同时支持通用场景。

## 功能概览

| 功能 | 说明 |
|------|------|
| 🤖 AI 智能生成 | 接入 OpenAI / Claude / DeepSeek / 通义千问 / 豆包 / 智谱 / Ollama 等 12+ 大模型 |
| 🖼️ AI 智能配图 | 8 家供应商可选（DALL·E 3 / ComfyUI 本地 / 通义万相 / 魔搭 等），自动为封面/章节/KPI 页配图 |
| 💬 AI 对话式编辑 | 编辑器内置 AI 助手，自然语言修改 PPT："把第3页标题加数据""换成表格布局" |
| 📊 数据驱动 | 上传 Excel 自动解析、匹配字段、填充保险会议模板 |
| 🎤 会议转写 | 会议录音转写文本 → 结构化提取 → 自动生成纪要 PPT |
| 📑 模板系统 | 24 套内置模板（含杂志编辑风 / 瑞士国际主义双设计语言包），支持 PPTX 导入 |
| 🎨 可视化编辑 | 画布拖拽编辑，17 种布局自由切换，实时 SVG 预览，幻灯片级撤销/重做 |
| 🔍 5 维设计评审 | 信息层级 / 配色协调 / 排版节奏 / 视觉焦点 / 品牌一致，达标显示 ★★★★★ |
| 📥 多格式导出 | PPTX / PDF / 分页 PNG，支持 OOXML 动画。公众号/小红书/分享卡多平台封面 |
| 🎙️ 语音旁白 | edge-tts 免费合成 + ElevenLabs/MiniMax 语音克隆，为备注生成自然语音 MP3 |
| 🌐 Web 部署 | Dockerfile 支持一键部署，CORS 全源模式，浏览器直接访问 |
| 💻 离线可用 | Ollama 本地模型 + ComfyUI 本地生图 + 离线规则引擎，完全离线也能用 |
| 🔐 安全存储 | API Key 系统级加密（Electron safeStorage + Fernet），不上传任何外部服务器 |
| ⚡ 生成缓存 | 相同输入 SHA256 去重，24h 内不重复调 API，节省费用 |

## 技术架构

```
┌──────────────────────────────────────────────┐
│                  Electron 壳                  │
│  ┌─────────────────┐  ┌───────────────────┐  │
│  │  React前端(Vite) │  │  Python后端(FastAPI)│  │
│  │  TypeScript      │  │  uvicorn :8099     │  │
│  │  Zustand 状态管理│  │  AI Provider 抽象层│  │
│  │  Tailwind CSS    │  │  SVGFiller 渲染引擎│  │
│  └─────────────────┘  └───────────────────┘  │
└──────────────────────────────────────────────┘
```

| 层级 | 技术选型 |
|------|----------|
| 桌面框架 | Electron 33 |
| 前端 | React 18 + TypeScript + Vite 6 |
| 状态管理 | Zustand 5 |
| 样式 | Tailwind CSS 3 |
| 后端 | Python FastAPI + uvicorn |
| PPT 生成 | python-pptx（原生 DrawingML 形状） |
| AI 接入 | openai / anthropic / httpx（多供应商兼容层） |
| 加密 | cryptography (Fernet) + Electron safeStorage |

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+（需安装 `cryptography`）
- Windows 10+ / macOS 10.13+

### 开发模式

```bash
# 安装前端依赖
npm install

# 安装后端依赖
cd backend
pip install -r requirements.txt
cd ..

# 启动开发（三端并行：React + Electron + Python）
npm run dev
```

### 生产构建

```bash
npm run build:all
# 产物在 release/ 目录
```

## 项目结构

```
AIPPTXPLUS/
├── src/                          # React 前端
│   ├── components/
│   │   ├── dashboard/            # 仪表盘组件（场景选择/输入/模板/模型）
│   │   ├── editor/               # 画布编辑器（元素拖拽/缩放/对齐）
│   │   ├── layout/               # 布局框架（侧栏/顶栏/状态栏）
│   │   └── slides/               # 幻灯片组件（大纲/预览/备注/质检）
│   ├── pages/                    # 页面
│   │   ├── Dashboard.tsx         # 首页：生成入口
│   │   ├── Editor.tsx            # 编辑器：三栏布局编辑
│   │   ├── Settings.tsx          # 设置：模型/AI/导出配置
│   │   ├── Presenter.tsx         # 演示模式
│   │   ├── Templates.tsx         # 模板浏览
│   │   ├── PromptLab.tsx         # 提示词实验室
│   │   └── Help.tsx              # 应用内帮助
│   ├── stores/projectStore.ts    # Zustand 全局状态
│   ├── types/index.ts            # TypeScript 类型定义
│   └── utils/                    # 工具函数
├── electron/                     # Electron 主进程
│   ├── main.ts                   # 窗口管理/Python进程/IPC
│   └── preload.ts                # 安全的 contextBridge API
├── backend/                      # Python 后端
│   ├── api/
│   │   ├── main.py               # FastAPI 应用入口
│   │   ├── key_store.py          # API密钥 Fernet 加密存储
│   │   └── routes/               # REST API 路由
│   ├── ai/provider.py            # AI 供应商抽象工厂（12+ 模型）
│   ├── slide_builder/
│   │   ├── pipeline.py           # 生成管线（规划→渲染→组装→质检）
│   │   ├── svg_filler.py         # SVG 渲染器（17 种布局）
│   │   ├── generator.py          # PPTX 生成器（原生形状）
│   │   └── deck_qa.py            # P0-P3 四级质检
│   ├── converters/               # 文件转换器
│   ├── data_driven/              # 数据驱动（Excel→模板填充）
│   ├── rule_engine/              # 离线规则引擎
│   ├── prompts/                  # AI 提示词（场景/预设）
│   └── templates/                # PPT 模板（22 内置 + 自定义）
├── package.json
└── README.md
```

## 使用指南

### 三种工作模式

| 模式 | 图标 | 说明 | 适合场景 |
|------|------|------|----------|
| **AI 替我做** | 🚀 | 给材料 → 一键自动出稿，无需人工介入 | 赶时间、材料完整 |
| **AI 帮我做** | 🎯 | 设定受众/风格/时长 → 审核大纲 → 生成 | 有明确需求、重要汇报 |
| **AI 陪我做** | 🤝 | 大纲逐页编辑、内容逐页微调、模板自由切换 | 精细打磨、完全掌控 |

三种模式共享 AI 引擎选择：云端大模型 / 本地 Ollama / 离线规则引擎。

### AI 引擎选择

| 引擎 | 说明 | 需要 |
|------|------|------|
| 云端网络 | 调用 OpenAI/Claude/DeepSeek 等云端 API | API Key |
| 本地 Ollama | 调用本地部署的大模型，完全离线 | 安装 Ollama + 拉取模型 |
| 离线规则 | 基于规则引擎生成 PPT，零依赖 | 无 |

### 基本流程

1. **选择模式 + 场景** — 三种工作模式中选一种，再选场景（报告/教育/提案/保险等）
2. **输入内容** — 直接输入文字 / 上传文件（PDF/DOCX/MD/TXT/PPTX/XMind）/ 粘贴URL / 上传Excel
3. **设定需求（可选）** — 选择受众、时长、风格，填写必含/避免的内容
4. **选择模板** — 22 套内置模板可选，也可导入自定义 PPTX 模板
5. **生成** — 点击生成，AI 自动分析内容、设计结构、填充模板
6. **编辑** — 在编辑器中修改标题/正文、切换布局、添加画布元素、补充资料
7. **导出** — PPTX / PDF / 分页PNG，支持动画效果

### 编辑器操作

**内容编辑**
- 左侧大纲列表点击标题直接编辑
- 右侧面板编辑标题、正文、布局类型
- 每行正文独立编辑，实时生效
- 演讲备注独立编辑，导出时写入 PPTX

**画布元素**
- 从工具栏拖拽文本/形状/图片/表格到画布
- 双击文字元素在画布上直接编辑
- 拖拽调整位置和大小，Shift+拖拽等比缩放
- Ctrl+C/V 复制粘贴，Ctrl+D 原地复制

**元素控制**
- 置顶/上移/下移/置底按钮控制层级
- 6 个对齐按钮（左中右、顶中底）对齐到画布
- 拖拽时自动吸附临近元素边缘和中心

**画布操作**
- +/- 按钮缩放画布（30%~200%），Ctrl+滚轮缩放
- 粘贴图片/截图到画布（Ctrl+V）
- 从 Excel 复制表格粘贴到画布

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + Enter` | 快速生成演示文稿 |
| `Ctrl + Z` | 撤销 |
| `Ctrl + Shift + Z` | 重做 |
| `Ctrl + C/V/D` | 画布元素 复制/粘贴/原地复制 |
| `Ctrl + ] / [` | 画布元素 上移/下移一层 |
| `Delete / Backspace` | 删除选中的画布元素 |
| `Shift + 拖拽` | 图片等比缩放 |
| `方向键 ↑↓←→` | 微移选中元素 / 切换幻灯片 |
| `Esc` | 退出演示 / 取消选中 |

## 保险行业模式

### 10 种会议类型 + 4 大高频场景

选择「保险」场景后可指定 10 种会议类型，每种都有专属的 AI 角色、任务目标和设计规范。

**四大高频场景（自动识别）：**

| 场景 | 自动识别词 | AI 角色 | 特色 |
|------|-----------|---------|------|
| **领导会议总结** | 领导/会议/部署/传达 | 战略传达专家 | 金句引用+任务RACI表 |
| **个人工作汇报** | 周报/月报/述职/一人一策 | 工作汇报专家 | KPI仪表盘+跟进清单 |
| **培训课件开发** | 课件/培训/话术/通关 | 资深培训师 | 正反对比+案例演练 |
| **优秀经验分享** | 标杆/萃取/转介绍/绩优 | 经验萃取专家 | 荣誉档案+方法论卡片 |

**10 种保险会议类型：**

| 会议类型 | AI 角色 | 特色布局 |
|----------|---------|----------|
| 业务对标复盘会 | 数据分析与对标改进顾问 | KPI仪表盘、柱状对比、排行榜 |
| 领导会议总结与指示 | 战略传达与任务分解专家 | 金句引用、任务RACI矩阵 |
| 业务启动会 | 战役启动策划专家 | 目标分解、军令状、竞赛规则 |
| 产品说明会 | 产品营销与路演专家 | 保障对比表、收益测算、客户案例 |
| 创业说明会 | 人才招募与事业规划专家 | 收入模型、成长路径、成功案例 |
| 服务权益说明会 | 客户服务与权益管理专家 | 权益对比、使用场景、VIP质感 |
| 经营复盘会 | 经营分析与财务顾问 | KPI全景、利润穿透、预算调整 |
| 绩优分享会 | 绩优典范萃取专家 | 荣誉档案、方法论、客户经营体系 |
| 产品培训 | 产品培训师与话术设计师 | 竞品对比、场景话术、异议处理 |
| 落后述职会 | 绩效改进顾问 | 差距三维对比、阶梯改进计划、帮扶方案 |

## AI 模型配置

支持 12 种 AI 供应商，在「设置」页面配置：

| 供应商 | 模型示例 | 类型 |
|--------|----------|------|
| DeepSeek | deepseek-v4-flash, deepseek-chat | 云端 |
| OpenAI | gpt-4o, gpt-4o-mini | 云端 |
| Anthropic | claude-sonnet-4, claude-opus-4 | 云端 |
| 通义千问 | qwen-max, qwen-plus | 云端 |
| 豆包 | doubao-pro-32k, doubao-seed-1-6 | 云端 |
| 智谱 GLM | glm-4-plus, glm-4-air | 云端 |
| Google Gemini | gemini-2.0-flash, gemini-1.5-pro | 云端 |
| Moonshot | moonshot-v1-8k, moonshot-v1-32k | 云端 |
| 讯飞星火 | spark-3.5, spark-4.0 | 云端 |
| 腾讯混元 | hunyuan-turbo, hunyuan-pro | 云端 |
| 文心一言 | ernie-4.0, ernie-3.5 | 云端 |
| Ollama | llama3, qwen2.5, mistral | 本地 |

**安全说明**：API Key 通过 Electron safeStorage（Windows DPAPI）系统级加密存储，生成时仅传输到本地 `127.0.0.1:8099` 后端，不经过任何外部服务器。

## 生成流程

```
输入内容
    │
    ▼
[1. 路由判断]  有Excel？→ 数据驱动 / 有会议纪要？→ 转写 / 正常 → AI生成
    │
    ▼
[2. AI 规划]   加载场景YAML → 拼接提示词（角色+任务+布局+设计+few-shot）→ 调用大模型
    │
    ▼
[3. 解析校验]  精确提取JSON → 布局白名单验证 → 自动补封面/目录/章节/结尾
    │
    ▼
[4. SVG 渲染]  SlideData → SVGFiller → 17种布局渲染 → 实时预览
    │
    ▼
[5. PPTX 组装] SlideData → PPTXGenerator → 原生DrawingML形状
    │
    ▼
[6. P0-P3 质检] DeckQA 四级检查 → 布局多样性 / 内容密度 / 结构完整性
    │
    ▼
PPTX + QA报告
```

## 内容质检（P0-P3）

| 级别 | 名称 | 说明 | 示例 |
|------|------|------|------|
| **P0** | 阻断 | 必须修复才能导出 | 空幻灯片、布局与数据不匹配 |
| **P1** | 警告 | 导出前建议修复 | 重复标题、内容溢出、缺封面/结尾 |
| **P2** | 建议 | 可忽略但建议改进 | 标题过长、无演讲备注、密度过低 |
| **P3** | 优化 | 锦上添花 | 建议使用状态标记、标签标注 |

## 预览同步机制

编辑幻灯片后，SVG 预览会在 0.8 秒内自动刷新（防抖），确保你看到的预览和导出效果完全一致。预览和 PPTX 导出共用同一套 SVGFiller 渲染引擎，不会出现"所见非所得"的问题。

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generate/pptx` | POST | 生成完整 PPTX |
| `/api/v1/generate/outline` | POST | 生成大纲预览 |
| `/api/v1/generate/supplement` | POST | AI 资料补充 |
| `/api/v1/generate/refresh-preview` | POST | 刷新单页 SVG 预览 |
| `/api/v1/templates/` | GET | 模板列表 |
| `/api/v1/templates/{id}` | GET | 模板详情 |
| `/api/v1/templates/import` | POST | 导入 PPTX 模板 |
| `/api/v1/templates/{id}` | DELETE | 删除自定义模板 |
| `/api/v1/convert/file` | POST | 文件转 Markdown |
| `/api/v1/convert/url` | POST | URL 转 Markdown |
| `/api/v1/convert/excel` | POST | Excel 解析上传 |
| `/api/v1/ai/configure` | POST | 配置 API Key |
| `/api/v1/ai/providers` | GET | 供应商列表 |
| `/api/v1/ai/connectivity-test` | POST | 连通性诊断 |
| `/api/v1/export/pptx` | POST | 导出 PPTX |
| `/api/v1/export` | POST | 导出 PDF/PNG |
| `/api/health` | GET | 健康检查 |

## 常见问题

**Q: 三种模式有什么区别？**
A: "AI替我做"给材料就出稿，全程自动；"AI帮我做"先审大纲再生成；"AI陪我做"每一步都可以手动调整。

**Q: 生成失败怎么办？**
A: AI 解析失败会自动重试一次（降低温度提高稳定性）。若仍失败，自动回退到离线规则引擎。

**Q: API Key 安全吗？**
A: 密钥通过 Electron safeStorage + Fernet 双重加密存储。生成时仅传输到本地 `127.0.0.1:8099`，不经过任何外部服务器。

**Q: 可以离线使用吗？**
A: 三种方式：① 本地 Ollama（需提前安装并拉取模型）；② 离线规则引擎（零依赖）；③ 以上都不可用时自动回退。

**Q: 编辑后预览会更新吗？**
A: 会。编辑内容后 0.8 秒自动刷新 SVG 预览，所见即所得。预览和导出共用同一渲染引擎。

**Q: 自定义 Ollama 地址怎么设？**
A: 在设置页面选择 Ollama 供应商，base_url 输入框可编辑，填入你的地址（如 `http://192.168.1.100:11434/v1`）。

## 许可证

MIT License

---

**险而易见 · InsurDeck** v1.0.0 · 作者：何克霖 · 福建龙岩

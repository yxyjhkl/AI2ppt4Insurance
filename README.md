# AI PPT Desktop

AI 驱动的 PPT 生成桌面应用 - 保险行业专用版本

![License](https://img.shields.io/github/license/yxyjhkl/AI2ppt4Insurance)
![Version](https://img.shields.io/github/v/release/yxyjhkl/AI2ppt4Insurance)

## 功能特性

- 🤖 **AI 智能生成** - 基于大语言模型自动生成专业 PPT
- 📊 **数据驱动模式** - 支持 JSON/CSV 数据导入生成报告
- 📑 **模板库** - 预置保险行业常用模板（理财建议书、产品推介、产说会等）
- 💻 **桌面应用** - Electron 跨平台桌面应用，离线可用
- 🎨 **可视化编辑** - 实时预览和编辑

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + TypeScript + Vite |
| 桌面 | Electron |
| 后端 | Python FastAPI |
| 状态管理 | Zustand |
| 样式 | Tailwind CSS |

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- Windows / macOS / Linux

### 安装

```bash
# 克隆仓库
git clone https://github.com/yxyjhkl/AI2ppt4Insurance.git
cd AI2ppt4Insurance

# 安装依赖
npm install

# 启动开发模式
npm run dev
```

### 生产构建

```bash
# 构建
npm run build:all
```

产物在 `release` 目录

## 项目结构

```
AI2ppt4Insurance/
├── src/                 # React 前端源码
│   ├── components/       # 组件
│   ├── pages/          # 页面
│   ├── hooks/         # 自定义 Hooks
│   ├── stores/        # Zustand 状态管理
│   └── utils/         # 工具函数
├── electron/           # Electron 主进程
├── backend/            # Python 后端
│   ├── api/           # FastAPI 接口
│   ├── slide_builder/# PPT 生成逻辑
│   └── templates/     # 模板定义
└── release/           # 构建产物
```

## 使用说明

1. **配置 API Key** - 在设置页面配置你的大模型 API Key
2. **选择场景** - 保险理财、产品推介、产说会等
3. **导入数据** - 支持 JSON/CSV 格式导入客户数据
4. **生成 PPT** - AI 自动生成专业演示文稿
5. **导出** - 支持导出 PPTX/PDF 格式

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 PR！
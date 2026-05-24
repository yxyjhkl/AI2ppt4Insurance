# 打包和分发指南

## 📦 快速打包

### 1. 安装依赖
```powershell
cd d:\APPbuild\AIPPTXPLUS
npm install

# 后端依赖
cd backend
pip install -r requirements.txt
```

### 2. 执行打包
```powershell
cd d:\APPbuild\AIPPTXPLUS
npm run build
```

### 3. 找到安装包
打包完成后，安装程序在：
```
release\AI PPT Desktop Setup 1.0.0.exe
```

---

## 📋 用户安装和使用

### 前置要求
- Windows 10/11
- Python 3.9+ (必须安装！)
- 用户需要先安装 Python 并添加到 PATH

### 安装步骤
1. 运行 `AI PPT Desktop Setup 1.0.0.exe`
2. 选择安装位置
3. 完成安装
4. 从桌面或开始菜单启动

---

## 🔧 进阶：Python 嵌入打包（推荐）

目前的方案需要用户自己安装 Python。如果要让用户无需安装 Python，需要：

### 方案 A：使用 PyInstaller 打包后端
1. 先把 Python 后端打包成 exe
2. 把生成的 exe 包含到 Electron 应用中
3. 修改 `electron/main.ts` 启动打包后的 exe

### 方案 B：使用 embedded Python
1. 下载嵌入式 Python 分发版
2. 包含到应用资源中
3. 使用这个嵌入式 Python 运行后端

### 方案 C：使用 Nuitka 编译 Python
把后端编译成原生可执行文件

---

## 🎨 自定义打包配置

### 修改应用名称
编辑 `package.json`：
```json
{
  "build": {
    "productName": "您的应用名称"
  }
}
```

### 修改应用图标
替换：
- `assets/icons/icon.png` (PNG 格式)
- `assets/icons/icon.ico` (Windows 图标)
- `assets/icons/icon.icns` (macOS 图标)

### 修改版本号
```json
{
  "version": "1.0.0"
}
```

---

## 📊 打包配置说明

当前配置在 `package.json` 的 `build` 部分：

```json
{
  "appId": "com.insurdeck.desktop",
  "productName": "AI PPT Desktop",
  "directories": {
    "output": "release"
  },
  "files": [
    "dist/**/*",
    "dist-electron/**/*",
    "backend/**/*"
  ],
  "win": {
    "target": ["nsis"],
    "icon": "assets/icons/icon.png"
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true
  }
}
```

---

## 🛠️ 故障排除

### 问题 1：打包时找不到 Python
- 确保用户已安装 Python 并添加到 PATH
- 或者使用嵌入 Python 的方案

### 问题 2：后端启动失败
- 检查 Python 依赖是否完整
- 查看应用日志（用户数据目录）

### 问题 3：打包体积太大
- 排除不必要的后端文件
- 压缩后端资源
- 使用 `asar` 格式打包

---

## 🎯 推荐下一步

1. **先测试当前打包方案**：用 `npm run build` 打一个包
2. **测试用户安装体验**：在一台没有 Python 的电脑上测试
3. **根据测试结果决定**：是否需要嵌入 Python

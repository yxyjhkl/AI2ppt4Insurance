import { app, BrowserWindow, ipcMain, dialog, Menu, safeStorage } from 'electron'
import * as path from 'path'
import * as fs from 'fs'
import { spawn, ChildProcess } from 'child_process'

let mainWindow: BrowserWindow | null = null
let pythonProcess: ChildProcess | null = null
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged

// 窗口状态存储
interface WindowState {
  width: number
  height: number
  x?: number
  y?: number
  maximized: boolean
}

function getWindowStatePath(): string {
  return path.join(app.getPath('userData'), 'window-state.json')
}

function loadWindowState(): WindowState {
  const defaultState: WindowState = {
    width: 1400,
    height: 900,
    maximized: false
  }
  try {
    const data = fs.readFileSync(getWindowStatePath(), 'utf-8')
    return { ...defaultState, ...JSON.parse(data) }
  } catch {
    return defaultState
  }
}

function saveWindowState(): void {
  if (!mainWindow) return
  const bounds = mainWindow.getBounds()
  const state: WindowState = {
    width: bounds.width,
    height: bounds.height,
    x: bounds.x,
    y: bounds.y,
    maximized: mainWindow.isMaximized()
  }
  try {
    fs.writeFileSync(getWindowStatePath(), JSON.stringify(state, null, 2))
  } catch {
    // 忽略保存错误
  }
}

function getStorePath(): string {
  return path.join(app.getPath('userData'), 'secure-store.json')
}

function loadStore(): Record<string, string> {
  try {
    const raw = fs.readFileSync(getStorePath(), 'utf-8')
    return JSON.parse(raw)
  } catch {
    return {}
  }
}

function saveStore(data: Record<string, string>): void {
  fs.writeFileSync(getStorePath(), JSON.stringify(data, null, 2), 'utf-8')
}

ipcMain.handle('store:set', (_event, key: string, value: string) => {
  if (!safeStorage.isEncryptionAvailable()) {
    throw new Error('系统加密不可用，无法安全存储 API Key')
  }
  const encrypted = safeStorage.encryptString(value)
  const storeData = loadStore()
  storeData[key] = encrypted.toString('base64')
  saveStore(storeData)
  return true
})

ipcMain.handle('store:get', (_event, key: string) => {
  if (!safeStorage.isEncryptionAvailable()) {
    throw new Error('系统加密不可用，无法读取安全存储')
  }
  const storeData = loadStore()
  const base64 = storeData[key]
  if (!base64) return null
  try {
    const buffer = Buffer.from(base64, 'base64')
    return safeStorage.decryptString(buffer)
  } catch {
    return null
  }
})

ipcMain.handle('store:delete', (_event, key: string) => {
  const storeData = loadStore()
  delete storeData[key]
  saveStore(storeData)
  return true
})

ipcMain.handle('store:has', (_event, key: string) => {
  const storeData = loadStore()
  return key in storeData
})

function getBackendPath(): string {
  if (isDev) {
    return path.join(__dirname, '..', 'backend')
  }
  return path.join(process.resourcesPath, 'backend')
}

let healthCheckInterval: ReturnType<typeof setInterval> | null = null
let backendReady = false

async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch('http://127.0.0.1:8099/api/health')
    return response.ok
  } catch {
    return false
  }
}

function notifyBackendStatus(status: 'starting' | 'ready' | 'error', message?: string): void {
  if (mainWindow) {
    mainWindow.webContents.send('backend:status', { status, message })
  }
}

function startPythonBackend(): void {
  const backendPath = getBackendPath()
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'
  
  notifyBackendStatus('starting', '正在启动后端服务...')

  pythonProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8099'], {
    cwd: backendPath,
    stdio: ['pipe', 'pipe', 'pipe'],
  })

  let startupOutput = ''
  const startupTimeout = setTimeout(() => {
    if (!backendReady) {
      console.error('[Python] Backend startup timeout')
      notifyBackendStatus('error', '后端启动超时，请检查 Python 环境')
    }
  }, 30000)

  pythonProcess.stdout?.on('data', (data: Buffer) => {
    const output = data.toString()
    console.log(`[Python] ${output}`)
    startupOutput += output
    
    // 检测 Uvicorn 启动成功标志
    if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
      // 开始健康检查
      startHealthCheck()
    }
  })

  pythonProcess.stderr?.on('data', (data: Buffer) => {
    const output = data.toString()
    console.error(`[Python] ${output}`)
    startupOutput += output
    
    // 检测常见错误
    if (output.includes('ModuleNotFoundError') || output.includes('No module named')) {
      notifyBackendStatus('error', '缺少 Python 依赖，请运行 pip install -r requirements.txt')
      clearTimeout(startupTimeout)
    }
  })

  pythonProcess.on('close', (code: number | null) => {
    console.log(`[Python] process exited with code ${code}`)
    pythonProcess = null
    backendReady = false
    
    if (healthCheckInterval) {
      clearInterval(healthCheckInterval)
      healthCheckInterval = null
    }
    
    // 如果是意外退出且不是正常关闭，通知用户
    if (code !== 0 && code !== null) {
      notifyBackendStatus('error', `后端意外退出 (代码: ${code})`)
    }
    
    clearTimeout(startupTimeout)
  })

  pythonProcess.on('error', (err: Error) => {
    console.error('[Python] Failed to start process:', err)
    notifyBackendStatus('error', `无法启动 Python: ${err.message}`)
    clearTimeout(startupTimeout)
  })
}

async function startHealthCheck(): Promise<void> {
  // 先进行一次快速检查
  let attempts = 0
  const maxAttempts = 10
  
  while (attempts < maxAttempts && !backendReady) {
    attempts++
    await new Promise(r => setTimeout(r, 1000))
    backendReady = await checkBackendHealth()
  }
  
  if (backendReady) {
    console.log('[Python] Backend is ready')
    notifyBackendStatus('ready')
  }
  
  // 启动定期健康检查
  healthCheckInterval = setInterval(async () => {
    const healthy = await checkBackendHealth()
    if (!healthy && backendReady) {
      console.warn('[Python] Backend health check failed')
      backendReady = false
      notifyBackendStatus('error', '后端连接断开')
    } else if (healthy && !backendReady) {
      console.log('[Python] Backend reconnected')
      backendReady = true
      notifyBackendStatus('ready')
    }
  }, 5000)
}

ipcMain.handle('backend:getStatus', async () => {
  return { ready: backendReady }
})

function createWindow(): void {
  const windowState = loadWindowState()
  
  mainWindow = new BrowserWindow({
    width: windowState.width,
    height: windowState.height,
    x: windowState.x,
    y: windowState.y,
    minWidth: 1024,
    minHeight: 700,
    title: '险而易见 · InsurDeck',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      nodeIntegrationInWorker: false,
      nodeIntegrationInSubFrames: false,
      sandbox: true,
      enableWebSQL: false,
      disableBlinkFeatures: 'Auxclick',
    },
  })

  // 阻止新窗口创建
  mainWindow.webContents.setWindowOpenHandler(() => {
    return { action: 'deny' }
  })

  // 保存窗口状态
  mainWindow.on('resize', saveWindowState)
  mainWindow.on('move', saveWindowState)
  mainWindow.on('close', saveWindowState)

  if (windowState.maximized) {
    mainWindow.maximize()
  }

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  const menuTemplate: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Project',
          accelerator: 'CmdOrCtrl+N',
          click: () => mainWindow?.webContents.send('menu:new-project'),
        },
        {
          label: 'Open File...',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow!, {
              filters: [
                { name: 'Documents', extensions: ['pdf', 'docx', 'md', 'txt', 'pptx'] },
              ],
              properties: ['openFile'],
            })
            if (!result.canceled && result.filePaths.length > 0) {
              mainWindow?.webContents.send('file:opened', result.filePaths[0])
            }
          },
        },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About 险而易见 · InsurDeck',
          click: () => {
            dialog.showMessageBox(mainWindow!, {
              type: 'info',
      title: 'About 险而易见 · InsurDeck',
      message: '险而易见 · InsurDeck v1.0.0',
              detail: 'AI-powered presentation generator.\nBuilt with Electron + React + Python.',
            })
          },
        },
      ],
    },
  ]

  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate))

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// 单实例锁
const gotTheLock = app.requestSingleInstanceLock()

if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })

  app.whenReady().then(() => {
    startPythonBackend()
    createWindow()

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
      }
    })
  })
}

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
})

ipcMain.handle('dialog:openFile', async (_, filters: { name: string; extensions: string[] }[]) => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    filters,
    properties: ['openFile'],
  })
  return result
})

ipcMain.handle('app:getBackendUrl', () => {
  return 'http://127.0.0.1:8099'
})

ipcMain.handle('dialog:saveFile', async (_, filters: { name: string; extensions: string[] }[]) => {
  const result = await dialog.showSaveDialog(mainWindow!, {
    filters,
  })
  return result
})

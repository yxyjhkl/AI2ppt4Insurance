import { app, BrowserWindow, ipcMain, dialog, Menu, safeStorage } from 'electron'
import * as path from 'path'
import * as fs from 'fs'
import { spawn, ChildProcess } from 'child_process'

let mainWindow: BrowserWindow | null = null
let pythonProcess: ChildProcess | null = null
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged

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

function startPythonBackend(): void {
  const backendPath = getBackendPath()
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'

  pythonProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8099'], {
    cwd: backendPath,
    stdio: ['pipe', 'pipe', 'pipe'],
  })

  pythonProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`[Python] ${data.toString()}`)
  })

  pythonProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`[Python] ${data.toString()}`)
  })

  pythonProcess.on('close', (code: number | null) => {
    console.log(`[Python] process exited with code ${code}`)
    pythonProcess = null
  })
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'AI PPT Desktop',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
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
          label: 'About AI PPT Desktop',
          click: () => {
            dialog.showMessageBox(mainWindow!, {
              type: 'info',
              title: 'About AI PPT Desktop',
              message: 'AI PPT Desktop v1.0.0',
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

app.whenReady().then(() => {
  startPythonBackend()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

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

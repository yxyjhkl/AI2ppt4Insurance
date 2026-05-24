import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  openFile: (filters: { name: string; extensions: string[] }[]) =>
    ipcRenderer.invoke('dialog:openFile', filters),
  saveFile: (filters: { name: string; extensions: string[] }[]) =>
    ipcRenderer.invoke('dialog:saveFile', filters),
  getBackendUrl: () => ipcRenderer.invoke('app:getBackendUrl'),
  onFileOpened: (callback: (filePath: string) => void) => {
    ipcRenderer.on('file:opened', (_event, filePath: string) => callback(filePath))
  },
  onNewProject: (callback: () => void) => {
    ipcRenderer.on('menu:new-project', () => callback())
  },
  onBackendStatus: (callback: (status: { status: string; message?: string }) => void) => {
    ipcRenderer.on('backend:status', (_event, data) => callback(data))
  },
  getBackendStatus: () => ipcRenderer.invoke('backend:getStatus'),
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel)
  },
  secureStore: {
    set: (key: string, value: string) => ipcRenderer.invoke('store:set', key, value),
    get: (key: string): Promise<string | null> => ipcRenderer.invoke('store:get', key),
    delete: (key: string) => ipcRenderer.invoke('store:delete', key),
    has: (key: string): Promise<boolean> => ipcRenderer.invoke('store:has', key),
  },
})
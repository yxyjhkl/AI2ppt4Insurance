import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  openFile: (filters: { name: string; extensions: string[] }[]) =>
    ipcRenderer.invoke('dialog:openFile', filters),
  saveFile: (filters: { name: string; extensions: string[] }[]) =>
    ipcRenderer.invoke('dialog:saveFile', filters),
  getBackendUrl: () => ipcRenderer.invoke('app:getBackendUrl'),
  onFileOpened: (callback: (filePath: string) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, filePath: string) => callback(filePath)
    ipcRenderer.on('file:opened', handler)
    return () => { ipcRenderer.removeListener('file:opened', handler) }
  },
  onNewProject: (callback: () => void) => {
    const handler = () => callback()
    ipcRenderer.on('menu:new-project', handler)
    return () => { ipcRenderer.removeListener('menu:new-project', handler) }
  },
  onBackendStatus: (callback: (status: { status: string; message?: string }) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, data: { status: string; message?: string }) => callback(data)
    ipcRenderer.on('backend:status', handler)
    return () => { ipcRenderer.removeListener('backend:status', handler) }
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
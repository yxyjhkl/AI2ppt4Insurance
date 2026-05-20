async function isElectronSecure(): Promise<boolean> {
  try {
    if (!window.electronAPI?.secureStore) return false
    return await window.electronAPI.secureStore.has('__health_check__')
  } catch {
    return false
  }
}

async function ensureElectronReady(): Promise<void> {
  try {
    await window.electronAPI!.secureStore!.set('__health_check__', '1')
  } catch {
    // ignore
  }
}

let electronAvailable: boolean | null = null

async function checkAvailability(): Promise<boolean> {
  if (electronAvailable !== null) return electronAvailable
  electronAvailable = await isElectronSecure()
  if (electronAvailable) {
    await ensureElectronReady()
    console.debug('[secureStore] 使用 Electron safeStorage 系统级加密')
  } else {
    console.debug('[secureStore] Electron 加密不可用，降级为 localStorage')
  }
  return electronAvailable
}

export async function getItem(key: string): Promise<string | null> {
  if (await checkAvailability()) {
    try {
      return await window.electronAPI!.secureStore!.get(key)
    } catch (e) {
      console.error('[secureStore] 读取失败:', e)
      return null
    }
  }
  return localStorage.getItem(key)
}

export async function setItem(key: string, value: string): Promise<boolean> {
  if (await checkAvailability()) {
    try {
      return await window.electronAPI!.secureStore!.set(key, value)
    } catch (e) {
      console.error('[secureStore] 写入失败:', e)
      return false
    }
  }
  try {
    localStorage.setItem(key, value)
    return true
  } catch (e) {
    console.error('[secureStore] localStorage 写入失败:', e)
    return false
  }
}

export async function removeItem(key: string): Promise<boolean> {
  if (await checkAvailability()) {
    try {
      return await window.electronAPI!.secureStore!.delete(key)
    } catch (e) {
      console.error('[secureStore] 删除失败:', e)
      return false
    }
  }
  localStorage.removeItem(key)
  return true
}

export async function getObject<T>(key: string): Promise<T | null> {
  const raw = await getItem(key)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

export async function setObject(key: string, value: unknown): Promise<boolean> {
  return setItem(key, JSON.stringify(value))
}
const memoryStore = new Map<string, string>()
let electronAvailable: boolean | null = null

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

async function checkAvailability(): Promise<boolean> {
  if (electronAvailable !== null) return electronAvailable
  electronAvailable = await isElectronSecure()
  if (electronAvailable) {
    await ensureElectronReady()
  }
  return electronAvailable
}

export async function getItem(key: string): Promise<string | null> {
  if (await checkAvailability()) {
    try {
      return await window.electronAPI!.secureStore!.get(key)
    } catch {
      return null
    }
  }
  return memoryStore.get(key) ?? null
}

export async function setItem(key: string, value: string): Promise<boolean> {
  if (await checkAvailability()) {
    try {
      return await window.electronAPI!.secureStore!.set(key, value)
    } catch {
      return false
    }
  }
  memoryStore.set(key, value)
  return true
}

export async function removeItem(key: string): Promise<boolean> {
  if (await checkAvailability()) {
    try {
      return await window.electronAPI!.secureStore!.delete(key)
    } catch {
      return false
    }
  }
  memoryStore.delete(key)
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
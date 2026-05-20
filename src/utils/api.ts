let cachedUrl: string | null = null

async function resolve(): Promise<string> {
  if (cachedUrl) return cachedUrl

  if (window.electronAPI) {
    try {
      cachedUrl = await window.electronAPI.getBackendUrl()
      return cachedUrl!
    } catch {
      cachedUrl = null
    }
  }

  cachedUrl = 'http://127.0.0.1:8099'
  return cachedUrl
}

export const apiConfig = {
  get baseUrl(): Promise<string> {
    return resolve()
  },
  async url(path: string): Promise<string> {
    const base = await resolve()
    return `${base}${path}`
  },
}

export function createAbortableFetch(
  signal?: AbortSignal,
): typeof fetch {
  return signal
    ? (input, init) => fetch(input, { ...init, signal })
    : fetch
}
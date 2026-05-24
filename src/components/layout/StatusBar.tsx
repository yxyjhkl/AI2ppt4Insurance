import { useEffect, useState, useRef } from 'react'
import { Network } from 'lucide-react'
import type { NetworkStatus } from '@/types'

export function StatusBar() {
  const [status, setStatus] = useState<NetworkStatus>({
    online: navigator.onLine,
    ollamaAvailable: false,
    backendReady: false,
  })
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastCheckRef = useRef<number>(0)

  useEffect(() => {
    const checkNetwork = async () => {
      const now = Date.now()
      if (now - lastCheckRef.current < 10000) return
      lastCheckRef.current = now

      setStatus((s) => ({ ...s, online: navigator.onLine }))
      let ollamaOk = false
      let backendOk = false

      try {
        const res = await fetch('http://127.0.0.1:11434/api/tags', { signal: AbortSignal.timeout(3000) })
        ollamaOk = res.ok
      } catch {
        ollamaOk = false
      }

      try {
        const res = await fetch('http://127.0.0.1:8099/api/health', { signal: AbortSignal.timeout(3000) })
        backendOk = res.ok
      } catch {
        backendOk = false
      }

      setStatus({ online: navigator.onLine, ollamaAvailable: ollamaOk, backendReady: backendOk })
    }

    checkNetwork()
    intervalRef.current = setInterval(checkNetwork, 30000)

    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        lastCheckRef.current = 0
        checkNetwork()
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [])

  const Dot = ({ ok }: { ok: boolean }) => (
    <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1 ${ok ? 'bg-green-500' : 'bg-gray-400'}`} />
  )

  return (
    <footer className="h-6 bg-gray-100 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex items-center px-3 text-xs text-gray-500 dark:text-gray-400 shrink-0 transition-colors">
      <Network className="w-3 h-3 mr-1" />
      <span className={status.online ? 'text-green-600' : 'text-gray-400'}>
        {status.online ? '在线' : '离线'}
      </span>
      <span className="mx-1.5 text-gray-300">|</span>
      <Dot ok={status.backendReady} />
      <span title={status.backendReady ? '后端服务运行正常' : '后端服务未启动，请运行 npm run dev:backend'}>
        后端: {status.backendReady ? '正常' : '未连接'}
      </span>
      <span className="mx-1.5 text-gray-300">|</span>
      <Dot ok={status.ollamaAvailable} />
      <span title={status.ollamaAvailable ? 'Ollama 本地模型可用' : 'Ollama 未检测到，启动后可离线使用'}>
        Ollama: {status.ollamaAvailable ? '可用' : '离线'}
      </span>
      <span className="mx-1.5 text-gray-300">|</span>
      <span className="text-gray-400">险而易见 · InsurDeck v1.0.0</span>
    </footer>
  )
}

import { useEffect, useState } from 'react'
import { Network } from 'lucide-react'
import type { NetworkStatus } from '@/types'

export function StatusBar() {
  const [status, setStatus] = useState<NetworkStatus>({
    online: navigator.onLine,
    ollamaAvailable: false,
    backendReady: false,
  })

  useEffect(() => {
    const checkNetwork = async () => {
      setStatus((s) => ({ ...s, online: navigator.onLine }))
      try {
        const res = await fetch('http://127.0.0.1:11434/api/tags')
        setStatus((s) => ({ ...s, ollamaAvailable: res.ok }))
      } catch {
        setStatus((s) => ({ ...s, ollamaAvailable: false }))
      }
      try {
        const res = await fetch('http://127.0.0.1:8099/api/health')
        setStatus((s) => ({ ...s, backendReady: res.ok }))
      } catch {
        setStatus((s) => ({ ...s, backendReady: false }))
      }
    }
    checkNetwork()
    const interval = setInterval(checkNetwork, 10000)
    return () => clearInterval(interval)
  }, [])

  const modeLabel = status.online ? '在线' : status.ollamaAvailable ? '本地 AI' : '离线'
  const modeColor = status.online ? 'text-green-600' : status.ollamaAvailable ? 'text-yellow-600' : 'text-gray-400'

  return (
    <footer className="h-6 bg-gray-100 border-t border-gray-200 flex items-center px-3 text-xs text-gray-500 shrink-0">
      <Network className="w-3 h-3 mr-1" />
      <span className={modeColor}>{modeLabel}</span>
      <span className="mx-2">|</span>
      <span>后端: {status.backendReady ? '正常' : '...'}</span>
      <span className="mx-2">|</span>
      <span>AI PPT Desktop v1.0.0</span>
    </footer>
  )
}
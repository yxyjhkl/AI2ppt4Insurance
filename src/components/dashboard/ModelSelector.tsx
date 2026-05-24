import { Loader2, Check } from 'lucide-react'

type ModeType = 'ai_network' | 'local_ollama' | 'rule_engine' | null

export function ModelSelector({
  mode,
  ollamaChecking,
  ollamaDetected,
  ollamaLocalModels,
  storedModels,
  selectedModelId,
  onSelect,
}: {
  mode: ModeType
  ollamaChecking: boolean
  ollamaDetected: boolean
  ollamaLocalModels: string[]
  storedModels: { model: string; name: string }[]
  selectedModelId: string
  onSelect: (id: string) => void
}) {
  if (mode === 'rule_engine') {
    return null
  }

  return (
    <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
      <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">5. 选择模型</h2>
      
      {mode === 'ai_network' ? (
        // AI网络模式：只显示云端模型
        <div className="space-y-2">
          {storedModels.length > 0 ? (
            <>
              <select className="input-field text-sm w-full" value={selectedModelId}
                onChange={(e) => onSelect(e.target.value)}>
                {storedModels.map(m => (
                  <option key={m.model} value={m.model}>{m.name}: {m.model}</option>
                ))}
              </select>
              <p className="text-xs text-gray-400">
                当前选择: {selectedModelId || '未选择'} — 可在「设置」页面添加更多模型
              </p>
            </>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-amber-600">
                未配置云端模型。请前往「设置」页面添加 API 密钥
              </p>
            </div>
          )}
        </div>
      ) : (
        // 本地部署模式：显示Ollama相关
        <>
          {ollamaChecking ? (
            <div className="flex items-center space-x-2 text-sm text-amber-600">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>正在检测本地 Ollama 模型...</span>
            </div>
          ) : ollamaDetected && ollamaLocalModels.length > 0 ? (
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-sm text-green-600">
                <Check className="w-4 h-4" />
                <span>检测到 Ollama 本地服务，{ollamaLocalModels.length} 个模型可用</span>
              </div>
              <select className="input-field text-sm w-full" value={selectedModelId}
                onChange={(e) => onSelect(e.target.value)}>
                {ollamaLocalModels.map(m => (
                  <option key={m} value={`ollama/${m}`}>{m} (Ollama 本地)</option>
                ))}
              </select>
              <p className="text-xs text-gray-400">
                当前选择: {selectedModelId || '未选择'} — Ollama 本地模型免费、隐私安全，无需 API Key
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-amber-600">
                {ollamaDetected ? '未检测到模型，请确保 Ollama 已拉取模型 (ollama pull <model>)' : '未检测到 Ollama 服务，请先启动 Ollama'}
              </p>
              <p className="text-xs text-gray-400">
                启动 Ollama 后将自动检测本地模型
              </p>
            </div>
          )}
        </>
      )}
    </section>
  )
}

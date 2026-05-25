import { useState, useEffect, useRef } from 'react'
import { Trash2, CheckCircle, Wifi, WifiOff, Loader2, RotateCcw, Save, Edit3 } from 'lucide-react'
import { apiConfig } from '@/utils/api'
import { getObject, setObject, getItem, setItem } from '@/utils/secureStore'
import { useProjectStore } from '@/stores/projectStore'

interface ProviderDef {
  id: string
  label: string
  baseUrl: string
  models: string[]
}

interface ModelEntry {
  id: string
  providerId: string
  name: string
  baseUrl: string
  apiKey: string
  model: string
}

const providers: ProviderDef[] = [
  { id: 'deepseek', label: 'DeepSeek（深度求索）', baseUrl: 'https://api.deepseek.com', models: ['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-chat', 'deepseek-reasoner'] },
  { id: 'qwen', label: '通义千问（阿里云）', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', models: ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen2.5-72b-instruct'] },
  { id: 'doubao', label: '豆包（火山引擎）', baseUrl: 'https://ark.cn-beijing.volces.com/api/v3', models: ['doubao-seed-1-6-251015', 'doubao-pro-32k', 'doubao-lite-32k'] },
  { id: 'glm', label: '智谱 GLM（智谱AI）', baseUrl: 'https://open.bigmodel.cn/api/paas/v4', models: ['glm-4-plus', 'glm-4-air', 'glm-4-flash'] },
  { id: 'moonshot', label: 'Moonshot（月之暗面）', baseUrl: 'https://api.moonshot.cn/v1', models: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'] },
  { id: 'spark', label: '讯飞星火', baseUrl: 'https://spark-api.xf-yun.com/v3.5/chat', models: ['spark-3.5', 'spark-4.0'] },
  { id: 'hunyuan', label: '腾讯混元', baseUrl: 'https://api.hunyuan.cloud.tencent.com/v1', models: ['hunyuan-turbo', 'hunyuan-pro', 'hunyuan-standard'] },
  { id: 'baidu', label: '文心一言（百度）', baseUrl: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat', models: ['ernie-4.0', 'ernie-3.5', 'ernie-speed'] },
  { id: 'openai', label: 'OpenAI（GPT 系列）', baseUrl: 'https://api.openai.com/v1', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
  { id: 'anthropic', label: 'Anthropic（Claude 系列）', baseUrl: 'https://api.anthropic.com', models: ['claude-sonnet-4', 'claude-opus-4', 'claude-3.5-sonnet', 'claude-3-haiku'] },
  { id: 'google', label: 'Google Gemini', baseUrl: 'https://generativelanguage.googleapis.com/v1beta', models: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'] },
  { id: 'ollama', label: 'Ollama（本地部署）', baseUrl: 'http://localhost:11434/v1', models: ['llama3', 'qwen2.5', 'mistral', 'gemma2', 'phi-3'] },
  { id: 'custom', label: '自定义接口', baseUrl: '', models: ['custom-model'] },
]

const DEFAULT_OLLAMA_MODELS = [...(providers.find(p => p.id === 'ollama')?.models ?? [])]

function getProvider(id: string) {
  return providers.find(p => p.id === id)
}

function getOllamaModelList(detected: string[], entry: ModelEntry): string[] {
  const combined = [...detected, ...DEFAULT_OLLAMA_MODELS]
  const unique = [...new Set(combined)]
  if (entry.model && !unique.includes(entry.model)) {
    unique.unshift(entry.model)
  }
  return unique
}

const STORAGE_KEY = 'aippt_models'

function defaultModels(): ModelEntry[] {
  return [
    { id: '1', providerId: 'deepseek', name: 'DeepSeek', baseUrl: 'https://api.deepseek.com', apiKey: '', model: 'deepseek-v4-flash' },
  ]
}

export function Settings() {
  const [models, setModels] = useState<ModelEntry[]>(defaultModels())
  const [saving, setSaving] = useState(false)
  const [savedIndicator, setSavedIndicator] = useState(false)
  const [storageReady, setStorageReady] = useState(false)
  const [ollamaModels, setOllamaModels] = useState<string[]>([])
  const [ollamaAvailable, setOllamaAvailable] = useState(false)
  const isDirty = useRef(false)
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const genConfig = useProjectStore((s) => s.generationConfig)
  const updateGenConfig = useProjectStore((s) => s.updateGenerationConfig)
  const [imageProvider, setImageProvider] = useState('none')
  const [imageApiKeys, setImageApiKeys] = useState<Record<string, string>>({})
  const [imageTesting, setImageTesting] = useState<string | null>(null)
  const [imageTestResults, setImageTestResults] = useState<Record<string, { ok: boolean; message: string; latency_ms: number }>>({})

  useEffect(() => {
    getObject<ModelEntry[]>(STORAGE_KEY).then((saved) => {
      if (saved && saved.length > 0) {
        const cleaned = saved.filter(m => !(m.id === '2' && m.providerId === 'openai' && !m.apiKey))
        if (cleaned.length !== saved.length) {
          setObject(STORAGE_KEY, cleaned)
        }
        setModels(cleaned)
      } else {
        setObject(STORAGE_KEY, defaultModels())
      }
      setStorageReady(true)
    })

    getItem('aippt_image_provider').then(v => {
      if (v) setImageProvider(v)
    })
  }, [])

  useEffect(() => {
    apiConfig.url('/api/v1/ai/check-ollama').then(async (url) => {
      try {
        const resp = await fetch(url)
        if (!resp.ok) return
        const data = await resp.json()
        if (data.available && data.models && data.models.length > 0) {
          setOllamaModels(data.models)
          setOllamaAvailable(true)
        }
      } catch {
        // Ollama 不可用，保持默认列表
      }
    })
  }, [])

  useEffect(() => {
    if (!isDirty.current) {
      isDirty.current = true
      return
    }
    if (!storageReady) return

    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current)
    autoSaveTimer.current = setTimeout(async () => {
      const ok = await setObject(STORAGE_KEY, models)
      if (ok) {
        setSavedIndicator(true)
        setTimeout(() => setSavedIndicator(false), 3000)
      }
    }, 1500)

    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current)
    }
  }, [models, storageReady])

  useEffect(() => {
    if (!storageReady) return
    setItem('aippt_image_provider', imageProvider)
  }, [imageProvider, storageReady])

  const handleDeleteModel = (id: string) => {
    setModels(prev => prev.filter(m => m.id !== id))
  }

  const handleChangeProvider = (id: string, providerId: string) => {
    const prov = getProvider(providerId)
    if (!prov) return
    setModels(prev => prev.map(m =>
      m.id === id ? { ...m, providerId, name: prov.label, baseUrl: prov.baseUrl, model: prov.models[0] } : m
    ))
    setSavedIndicator(false)
  }

  const handleChangeModel = (id: string, model: string) => {
    setModels(prev => prev.map(m => m.id === id ? { ...m, model } : m))
    setSavedIndicator(false)
  }

  const handleChangeApiKey = (id: string, apiKey: string) => {
    setModels(prev => prev.map(m => m.id === id ? { ...m, apiKey } : m))
    setSavedIndicator(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const ok = await setObject(STORAGE_KEY, models)
      if (ok) {
        setSavedIndicator(true)
        setTimeout(() => setSavedIndicator(false), 3000)
        console.debug('[设置] 手动保存成功，共', models.length, '个模型配置')
      }
    } finally {
      setSaving(false)
    }
  }

  const [testingId, setTestingId] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { ok: boolean; message: string }>>({})

  // Prompt editor state
  const [promptContent, setPromptContent] = useState('')
  const [promptLoading, setPromptLoading] = useState(false)
  const [promptSaving, setPromptSaving] = useState(false)
  const [promptResetting, setPromptResetting] = useState(false)
  const [promptSaved, setPromptSaved] = useState(false)
  const [showPromptEditor, setShowPromptEditor] = useState(false)
  const [presets, setPresets] = useState<Array<{
    id: string; name: string; order: number;
    description: string; tags: string[]; suitable_for: string[];
  }>>([])
  const [activePreset, setActivePreset] = useState('')
  const [customOverride, setCustomOverride] = useState(false)
  const [presetLoading, setPresetLoading] = useState(false)
  const [activatingId, setActivatingId] = useState<string | null>(null)

  useEffect(() => {
    if (showPromptEditor) {
      loadPresets()
      if (!promptContent) loadPrompt()
    }
  }, [showPromptEditor])

  const loadPresets = async () => {
    setPresetLoading(true)
    try {
      const res = await fetch(await apiConfig.url('/api/v1/generate/prompt/presets'))
      if (res.ok) {
        const data = await res.json()
        setPresets(data.presets || [])
        setActivePreset(data.active_preset || '')
        setCustomOverride(data.custom_override || false)
      }
    } catch { /* ignore */ }
    finally { setPresetLoading(false) }
  }

  const loadPrompt = async () => {
    setPromptLoading(true)
    try {
      const res = await fetch(await apiConfig.url('/api/v1/generate/prompt/auto-mode'))
      if (res.ok) {
        const data = await res.json()
        setPromptContent(data.content || '')
      }
    } catch { /* ignore */ }
    finally { setPromptLoading(false) }
  }

  const activatePreset = async (presetId: string) => {
    setActivatingId(presetId)
    try {
      const res = await fetch(await apiConfig.url('/api/v1/generate/prompt/presets/activate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset_id: presetId }),
      })
      if (res.ok) {
        setActivePreset(presetId)
        setCustomOverride(false)
        await loadPrompt()
        setPromptSaved(true)
        setTimeout(() => setPromptSaved(false), 3000)
      }
    } finally { setActivatingId(null) }
  }

  const savePrompt = async () => {
    setPromptSaving(true)
    try {
      const res = await fetch(await apiConfig.url('/api/v1/generate/prompt/auto-mode'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: promptContent }),
      })
      if (res.ok) {
        setCustomOverride(true)
        setPromptSaved(true)
        setTimeout(() => setPromptSaved(false), 3000)
      }
    } finally { setPromptSaving(false) }
  }

  const resetPrompt = async () => {
    setPromptResetting(true)
    try {
      const res = await fetch(await apiConfig.url('/api/v1/generate/prompt/auto-mode/reset'), {
        method: 'POST',
      })
      if (res.ok) {
        const data = await res.json()
        setPromptContent(data.content || '')
        setCustomOverride(false)
        setActivePreset(data.active_preset || activePreset)
        setPromptSaved(true)
        setTimeout(() => setPromptSaved(false), 3000)
      }
    } finally { setPromptResetting(false) }
  }

  const classifyNetworkError = (e: any): { reason: string; suggestion: string } => {
    const msg = (e.message || '').toLowerCase()
    const name = (e.name || '').toLowerCase()

    if (msg.includes('connection refused') || msg.includes('err_connection_refused')) {
      return {
        reason: '后端服务未启动',
        suggestion: '请确认 Python 后端已启动在 127.0.0.1:8099，执行: cd backend && python -m api.main',
      }
    }
    if (msg.includes('name_not_resolved') || msg.includes('err_name_not_resolved') || msg.includes('dns')) {
      return {
        reason: 'DNS 解析失败',
        suggestion: '请检查接口地址域名是否正确、网络是否连通，或尝试用 IP 地址替代域名',
      }
    }
    if (msg.includes('timed out') || msg.includes('err_connection_timed_out') || msg.includes('timeout')) {
      return {
        reason: '连接超时',
        suggestion: '目标服务器无法在规定时间内响应，请检查网络代理/VPN 设置，或该服务商是否暂时不可用',
      }
    }
    if (msg.includes('cors') || msg.includes('cross-origin') || name.includes('typeerror') && msg.includes('fetch')) {
      return {
        reason: '跨域或网络阻断',
        suggestion: '可能被浏览器安全策略或防火墙拦截，检查后端 CORS 配置是否允许当前域名',
      }
    }
    if (msg.includes('failed to fetch') || msg.includes('networkerror')) {
      return {
        reason: '无法连接到后端',
        suggestion: '可能原因: ①后端未启动 ②端口被占用 ③防火墙拦截。请先检查后端服务状态',
      }
    }
    if (msg.includes('econnrefused')) {
      return {
        reason: '目标端口未监听',
        suggestion: '接口地址中的端口或服务未启动，请确认目标 API 地址正确且服务正在运行',
      }
    }
    return {
      reason: '未知网络错误',
      suggestion: '请查看控制台详细日志，检查本地网络连接和目标服务状态',
    }
  }

  const testModelConnection = async (entry: ModelEntry) => {
    setTestingId(entry.id)
    setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: '' } }))

    try {
      const backendBase = await apiConfig.url('/api/health')

      let backendOk = false
      try {
        const healthResp = await fetch(backendBase, { method: 'GET' })
        backendOk = healthResp.ok
      } catch {
        backendOk = false
      }

      if (!backendOk) {
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: '❌ 本机后端服务 (127.0.0.1:8099) 未响应，请先启动 Python 后端再重试' } }))
        return
      }

      const baseUrl = await apiConfig.url('/api/v1/ai/connectivity-test')

      const resp = await fetch(baseUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: entry.providerId,
          model: entry.model,
          base_url: entry.baseUrl,
          api_key: entry.apiKey,
        }),
      })

      if (!resp.ok) {
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: `后端服务异常 (HTTP ${resp.status})` } }))
        return
      }

      let result: { ok: boolean; message: string }
      try {
        result = await resp.json()
      } catch {
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: '后端返回格式异常' } }))
        return
      }

      if (result.ok) {
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: true, message: result.message || '连接成功' } }))
      } else {
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: result.message || '连接失败' } }))
      }
    } catch (e: any) {
      const { reason, suggestion } = classifyNetworkError(e)
      setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: `${reason}\n${suggestion}` } }))
    } finally {
      setTestingId(null)
    }
  }

  const testImageConnection = async () => {
    if (!imageProvider || imageProvider === 'none' || imageProvider === 'comfyui') return
    setImageTesting(imageProvider)
    setImageTestResults(prev => ({ ...prev, [imageProvider]: { ok: false, message: '测试中...', latency_ms: 0 } }))

    try {
      const apiKey = imageApiKeys[imageProvider] || ''

      const res = await fetch(await apiConfig.url('/api/v1/media/image-conn-test'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: imageProvider, api_key: apiKey }),
      })

      if (res.ok) {
        const data = await res.json()
        setImageTestResults(prev => ({ ...prev, [imageProvider]: data }))
      } else {
        setImageTestResults(prev => ({ ...prev, [imageProvider]: { ok: false, message: `后端异常 HTTP ${res.status}`, latency_ms: 0 } }))
      }
    } catch (e: any) {
      setImageTestResults(prev => ({ ...prev, [imageProvider]: { ok: false, message: `网络错误: ${e.message?.slice(0, 100)}`, latency_ms: 0 } }))
    } finally {
      setImageTesting(null)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">设置</h1>

      <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300">AI 模型</h2>
        </div>

        <div className="space-y-3">
          {models.map((entry) => {
            return (
              <div key={entry.id} className="p-4 border border-gray-200 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{entry.name}</span>
                  <button onClick={() => handleDeleteModel(entry.id)} className="text-gray-400 hover:text-red-500">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-3 items-start">
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">AI 供应商</label>
                    <select
                      className="input-field text-sm"
                      value={entry.providerId}
                      onChange={(e) => handleChangeProvider(entry.id, e.target.value)}
                    >
                      {providers.map(p => (
                        <option key={p.id} value={p.id}>{p.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">接口地址</label>
                    <input
                      className="input-field text-sm"
                      value={entry.baseUrl}
                      readOnly={entry.providerId !== 'ollama' && entry.providerId !== 'custom'}
                      onChange={(e) => {
                        if (entry.providerId === 'ollama' || entry.providerId === 'custom') {
                          setModels(prev => prev.map(m => m.id === entry.id ? { ...m, baseUrl: e.target.value } : m))
                          setSavedIndicator(false)
                        }
                      }}
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">模型名称</label>
                    <select
                      className="input-field text-sm"
                      value={entry.model}
                      onChange={(e) => handleChangeModel(entry.id, e.target.value)}
                    >
                      {(entry.providerId === 'ollama'
                        ? getOllamaModelList(ollamaModels, entry)
                        : (providers.find(p => p.id === entry.providerId)?.models || [])
                      ).map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex items-end gap-3">
                  <div className="flex-1">
                    <label className="text-xs text-gray-500 block mb-1">API Key</label>
                    <input
                      type="password"
                      className="input-field text-sm"
                      value={entry.apiKey}
                      onChange={(e) => handleChangeApiKey(entry.id, e.target.value)}
                      placeholder="sk-..."
                    />
                  </div>
                  <button
                    onClick={() => testModelConnection(entry)}
                    disabled={testingId === entry.id}
                    className="btn-secondary text-xs h-8 px-3 flex items-center gap-1 shrink-0"
                  >
                    {testingId === entry.id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Wifi className="w-3 h-3" />
                    )}
                    连通测试
                  </button>
                  {testResults[entry.id] && !testingId && (
                    <span className={`text-xs shrink-0 ${testResults[entry.id].ok ? 'text-green-600' : 'text-red-500'}`}>
                      {testResults[entry.id].ok ? (
                        <CheckCircle className="w-4 h-4 inline" />
                      ) : (
                        <WifiOff className="w-4 h-4 inline" />
                      )}
                    </span>
                  )}
                </div>

                {testResults[entry.id] && !testingId && (
                  testResults[entry.id].ok ? (
                    <p className="mt-1 text-xs text-green-600">✅ 连接成功 — API Key 有效，模型可用</p>
                  ) : (
                    <div className="mt-2 p-2 rounded bg-red-50 border border-red-200">
                      <p className="text-xs text-red-700 font-medium">❌ {testResults[entry.id].message}</p>
                      <p className="text-xs text-red-500 mt-1">
                        提示：请检查 API Key 是否正确、网络是否连通，或切换其他供应商测试
                      </p>
                    </div>
                  )
                )}
              </div>
            )
          })}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <CheckCircle className="w-4 h-4 text-blue-600 mt-0.5" />
            <div>
              <p className="text-sm text-blue-800 font-medium">离线模式</p>
              <p className="text-xs text-blue-600 mt-1">
                {ollamaAvailable
                  ? `检测到 Ollama，${ollamaModels.length} 个本地模型可用`
                  : '未检测到 Ollama 服务，启动 Ollama 后刷新页面可自动识别本地模型'}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">生成默认配置</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 block mb-1">默认语言</label>
            <select className="input-field text-sm" value={genConfig.language}
              onChange={(e) => updateGenConfig({ language: e.target.value })}>
              <option value="zh-CN">中文 (zh-CN)</option>
              <option value="en-US">English (en-US)</option>
              <option value="ja-JP">日本語 (ja-JP)</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">默认幻灯片数量</label>
            <input type="number" className="input-field text-sm" value={genConfig.slideCount}
              onChange={(e) => updateGenConfig({ slideCount: parseInt(e.target.value, 10) || 10 })}
              min={5} max={50} />
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">随机度</label>
            <input type="range" min="0" max="2" step="0.1" value={genConfig.temperature}
              onChange={(e) => updateGenConfig({ temperature: parseFloat(e.target.value) })}
              className="w-full" />
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">默认模板</label>
            <select className="input-field text-sm" value={genConfig.template}
              onChange={(e) => updateGenConfig({ template: e.target.value })}>
              <option value="professional-blue">专业蓝</option>
              <option value="dark-modern">暗色现代</option>
              <option value="clean-white">简洁白</option>
            </select>
          </div>
        </div>
      </section>

      <section className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-700">AI 生成 Prompt</h2>
            <p className="text-xs text-gray-400 mt-0.5">选择预设或自定义"AI替我做"模式的生成指令</p>
          </div>
          <button
            onClick={() => setShowPromptEditor(!showPromptEditor)}
            className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5"
          >
            <Edit3 className="w-3.5 h-3.5" />
            {showPromptEditor ? '收起' : '配置 Prompt'}
          </button>
        </div>

        {showPromptEditor && (
          <div className="space-y-4 animate-fade-in">
            {/* Preset selector */}
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">选择预设方案</h3>
              {presetLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-400 py-4">
                  <Loader2 className="w-4 h-4 animate-spin" /> 加载预设列表...
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-2">
                  {presets.map((p) => {
                    const isActive = p.id === activePreset && !customOverride
                    return (
                      <button
                        key={p.id}
                        onClick={() => activatePreset(p.id)}
                        disabled={activatingId === p.id}
                        className={`text-left p-3 rounded-lg border-2 transition-all ${
                          isActive
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 hover:border-gray-300 dark:border-gray-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${isActive ? 'bg-blue-500' : 'bg-gray-300'}`} />
                            <span className={`text-sm font-medium ${isActive ? 'text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}>
                              {p.name}
                            </span>
                            {activatingId === p.id && <Loader2 className="w-3 h-3 animate-spin text-blue-500" />}
                          </div>
                          <div className="flex gap-1">
                            {p.tags?.map((t: string) => (
                              <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500">
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1 ml-4">{p.description}</p>
                        {p.suitable_for?.length > 0 && (
                          <p className="text-[10px] text-gray-400 mt-0.5 ml-4">
                            适用：{p.suitable_for.join('、')}
                          </p>
                        )}
                      </button>
                    )
                  })}
                  {/* Custom override indicator */}
                  {customOverride && (
                    <div className="p-3 rounded-lg border-2 border-amber-300 bg-amber-50 dark:bg-amber-900/10">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-amber-500" />
                        <span className="text-sm font-medium text-amber-700 dark:text-amber-300">自定义 Prompt（已修改）</span>
                      </div>
                      <p className="text-xs text-amber-600 mt-1 ml-4">
                        当前使用手动编辑的 Prompt，点击左侧预设可切换回标准方案
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="border-t border-gray-200 dark:border-gray-700" />

            {/* Custom editor */}
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                手动编辑{customOverride ? '（当前生效中）' : '（将覆盖预设）'}
              </h3>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700 mb-3">
                <p className="font-medium mb-1">注意</p>
                <ul className="list-disc list-inside space-y-0.5 text-amber-600">
                  <li>直接修改下方内容会覆盖当前预设，保存后立即生效</li>
                  <li>保留模板变量 {'{input_text}'} {'{system_prompt}'} 等占位符</li>
                  <li>出问题时点击"恢复当前预设"或重新选择一个预设即可</li>
                </ul>
              </div>

              {promptLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-400 py-8 justify-center">
                  <Loader2 className="w-4 h-4 animate-spin" /> 加载中...
                </div>
              ) : (
                <textarea
                  value={promptContent}
                  onChange={(e) => setPromptContent(e.target.value)}
                  className="input-field min-h-[300px] resize-y font-mono text-xs leading-relaxed"
                  placeholder="Prompt 内容加载失败..."
                />
              )}

              <div className="flex items-center justify-between mt-3">
                <button
                  onClick={resetPrompt}
                  disabled={promptResetting}
                  className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5"
                >
                  {promptResetting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
                  恢复当前预设
                </button>

                <div className="flex items-center gap-3">
                  {promptSaved && (
                    <span className="text-sm text-green-600 flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" /> 已保存
                    </span>
                  )}
                  <button
                    onClick={savePrompt}
                    disabled={promptSaving || !promptContent}
                    className="btn-primary text-xs px-4 py-1.5 flex items-center gap-1.5"
                  >
                    {promptSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                    保存自定义 Prompt
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* 图片生成供应商 */}
      <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
        <div>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300">AI 配图生成</h2>
          <p className="text-xs text-gray-400 mt-0.5">生成PPT时可自动为封面/章节/KPI页配图。需配置所选供应商的API Key</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { id: 'none', name: '不使用配图', region: '', desc: '不自动生成图片', keyName: '' },
            { id: 'openai', name: 'DALL·E 3', region: '国际', desc: 'OpenAI 出品，质量最高，约$0.04/张', keyName: 'OPENAI_API_KEY' },
            { id: 'stability', name: 'Stable Diffusion', region: '国际', desc: 'Stability AI，风格多样，约$0.01/张', keyName: 'STABILITY_API_KEY' },
            { id: 'tongyi', name: '通义万相', region: '国内 · 阿里云', desc: '阿里出品，中文理解好，支持1024×1024', keyName: 'DASHSCOPE_API_KEY' },
            { id: 'cogview', name: 'CogView', region: '国内 · 智谱AI', desc: '智谱出品，与GLM模型同源，速度快', keyName: 'ZHIPU_API_KEY' },
            { id: 'ernie', name: '文心一格', region: '国内 · 百度', desc: '百度出品，中文场景效果好，需API Key+Secret Key', keyName: 'BAIDU_API_KEY + BAIDU_SECRET_KEY' },
            { id: 'spark', name: '讯飞星火', region: '国内 · 科大讯飞', desc: '讯飞出品，需APP_ID+API_KEY+API_SECRET', keyName: 'SPARK_API_KEY + SPARK_API_SECRET + SPARK_APP_ID' },
            { id: 'modelscope', name: '魔搭 ModelScope', region: '国内 · 阿里达摩院', desc: '国内最大模型社区，qwen-plus多模态生成', keyName: 'MODELSCOPE_API_KEY' },
            { id: 'comfyui', name: 'ComfyUI 本地', region: '本地部署 💻', desc: '自部署ComfyUI，完全免费无限量，需本地GPU', keyName: 'COMFYUI_URL (默认 http://127.0.0.1:8188)' },
          ].map(provider => {
            const isSelected = imageProvider === provider.id
            return (
              <button
                key={provider.id}
                onClick={() => { setImageProvider(provider.id); setSavedIndicator(false) }}
                className={`p-3 rounded-xl border-2 text-left transition-all ${
                  isSelected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${isSelected ? 'text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}>
                    {provider.name}
                  </span>
                  {provider.region && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      provider.region.startsWith('国内') ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'
                    }`}>{provider.region}</span>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-1">{provider.desc}</p>
                {isSelected && provider.keyName && (
                  <p className="text-[10px] text-blue-500 mt-2 font-mono">需设置: {provider.keyName}</p>
                )}
              </button>
            )
          })}
        </div>

        {/* API Key 配置 + 连通测试 */}
        {imageProvider !== 'none' && imageProvider !== 'comfyui' && (
          <div className="flex items-end gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
            <div className="flex-1">
              <label className="text-xs text-gray-500 block mb-1">
                {imageProvider === 'ernie' ? 'API Key（百度文心）' :
                 imageProvider === 'spark' ? 'API Key（讯飞星火）' :
                 imageProvider === 'stability' ? 'API Key（Stability AI）' : 'API Key'}
              </label>
              <input type="password" className="input-field text-sm"
                value={imageApiKeys[imageProvider] || ''}
                onChange={(e) => setImageApiKeys(prev => ({ ...prev, [imageProvider]: e.target.value }))}
                placeholder="输入 API Key..." />
            </div>
            {imageProvider === 'ernie' && (
              <div className="flex-1">
                <label className="text-xs text-gray-500 block mb-1">Secret Key</label>
                <input type="password" className="input-field text-sm"
                  value={imageApiKeys[`${imageProvider}_secret`] || ''}
                  onChange={(e) => setImageApiKeys(prev => ({ ...prev, [`${imageProvider}_secret`]: e.target.value }))}
                  placeholder="百度 Secret Key" />
              </div>
            )}
            <button onClick={() => testImageConnection()}
              disabled={imageTesting === imageProvider}
              className="btn-secondary text-xs h-8 px-3 flex items-center gap-1 shrink-0">
              {imageTesting === imageProvider ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wifi className="w-3 h-3" />}
              连通测试
            </button>
            {imageTestResults[imageProvider] && imageTesting !== imageProvider && (
              <span className={`text-xs shrink-0 ${imageTestResults[imageProvider].ok ? 'text-green-600' : 'text-red-500'}`}>
                {imageTestResults[imageProvider].ok ? <CheckCircle className="w-4 h-4 inline" /> : <WifiOff className="w-4 h-4 inline" />}
              </span>
            )}
          </div>
        )}

        {imageTestResults[imageProvider] && imageTesting !== imageProvider && (
          <div className={`p-2 rounded text-xs ${imageTestResults[imageProvider].ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {imageTestResults[imageProvider].ok ? '✅ ' : '❌ '}{imageTestResults[imageProvider].message}
            {imageTestResults[imageProvider].latency_ms > 0 && (
              <span className="text-gray-400 ml-2">({imageTestResults[imageProvider].latency_ms.toFixed(0)}ms)</span>
            )}
          </div>
        )}

        {imageProvider !== 'none' && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700">
            <p className="font-medium mb-1">使用说明</p>
            <ul className="list-disc list-inside space-y-0.5 text-amber-600">
              <li>所选供应商的API Key需通过环境变量或配置文件设置</li>
              <li>编辑 .env 文件或系统环境变量，填入对应的 API Key</li>
              <li>图片生成有成本，建议仅在封面和关键数据页使用</li>
              <li>相同内容会自动缓存，不会重复计费</li>
            </ul>
          </div>
        )}

        {imageProvider === 'comfyui' && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-green-800">ComfyUI 本地部署指南</p>
            <ol className="list-decimal list-inside space-y-1 text-green-700">
              <li>下载 ComfyUI：<code className="bg-green-100 px-1 rounded">git clone https://github.com/comfyanonymous/ComfyUI.git</code></li>
              <li>下载 SD XL 模型放入 <code className="bg-green-100 px-1 rounded">models/checkpoints/</code></li>
              <li>启动：<code className="bg-green-100 px-1 rounded">python main.py --listen 0.0.0.0</code></li>
              <li>如需修改地址，设置环境变量 <code className="bg-green-100 px-1 rounded">COMFYUI_URL=http://你的IP:8188</code></li>
            </ol>
            <p className="text-green-600">✅ 优势：完全免费、不限量、数据不外传、可自定义模型和LoRA</p>
            <p className="text-green-600">⚠ 要求： NVIDIA GPU (6GB+ VRAM推荐)</p>
          </div>
        )}

        {imageProvider === 'modelscope' && (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-xs text-indigo-700">
            <p className="font-medium mb-1">魔搭 ModelScope 说明</p>
            <ul className="list-disc list-inside space-y-0.5 text-indigo-600">
              <li>使用阿里云 DashScope API 的多模态生成能力</li>
              <li>底层模型 qwen-plus，同时理解文字和生成图片</li>
              <li>API Key 获取：<code className="bg-indigo-100 px-1 rounded">https://modelscope.cn/my/overview</code></li>
              <li>新用户通常有免费额度</li>
            </ul>
          </div>
        )}
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">导出选项</h2>
        <div className="space-y-2">
          <label className="flex items-center space-x-2">
            <input type="checkbox" checked={genConfig.includeNotes}
              onChange={(e) => updateGenConfig({ includeNotes: e.target.checked })} className="rounded" />
            <span className="text-sm text-gray-700">在 PPTX 中包含演讲备注</span>
          </label>
          <label className="flex items-center space-x-2">
            <input type="checkbox" checked={genConfig.includeAnimation}
              onChange={(e) => updateGenConfig({ includeAnimation: e.target.checked })} className="rounded" />
            <span className="text-sm text-gray-700">在线时包含 OOXML 动画</span>
          </label>
        </div>
      </section>

      <div className="flex justify-end items-center space-x-3">
        {savedIndicator && (
          <span className="text-sm text-green-600 flex items-center gap-1">
            <CheckCircle className="w-4 h-4" />
            已自动保存
          </span>
        )}
        <button onClick={handleSave} disabled={saving} className="btn-primary text-sm">
          {saving ? '保存中...' : '立即保存'}
        </button>
      </div>
    </div>
  )
}
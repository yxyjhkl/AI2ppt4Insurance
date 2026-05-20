import { useState, useEffect, useRef } from 'react'
import { Trash2, CheckCircle, Wifi, WifiOff, Loader2 } from 'lucide-react'
import { apiConfig } from '@/utils/api'
import { getObject, setObject, removeItem } from '@/utils/secureStore'
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

const DEFAULT_OLLAMA_MODELS = [...providers.find(p => p.id === 'ollama')!.models]

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

  useEffect(() => {
    getObject<ModelEntry[]>(STORAGE_KEY).then((saved) => {
      if (saved && saved.length > 0) {
        const cleaned = saved.filter(m => !(m.id === '2' && m.providerId === 'openai' && !m.apiKey))
        if (cleaned.length !== saved.length) {
          setObject(STORAGE_KEY, cleaned)
          console.debug('[设置] 已清理旧版默认 OpenAI 条目，当前', cleaned.length, '个模型配置')
        }
        setModels(cleaned)
        console.debug('[设置] 已从加密存储加载', cleaned.length, '个模型配置')
      } else {
        setObject(STORAGE_KEY, defaultModels())
        console.debug('[设置] 首次使用，初始化为默认配置')
      }
      setStorageReady(true)
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
          console.debug('[设置] 检测到 Ollama 模型:', data.models.join(', '))
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
        console.debug('[设置] 已自动保存', models.length, '个模型配置')
      }
    }, 1500)

    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current)
    }
  }, [models, storageReady])

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
    const TAG = '[连通测试]'
    console.groupCollapsed(`${TAG} ${entry.providerId}/${entry.model}`)
    console.debug(`${TAG} ========== 开始连通测试 ==========`)
    console.debug(`${TAG} 模型ID: ${entry.id}`)
    console.debug(`${TAG} 供应商: ${entry.providerId}`)
    console.debug(`${TAG} 模型名称: ${entry.model}`)
    console.debug(`${TAG} 接口地址: ${entry.baseUrl}`)
    console.debug(`${TAG} API Key 已填写: ${entry.apiKey ? `是 (${entry.apiKey.length}位)` : '否'}`)

    setTestingId(entry.id)
    setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: '' } }))

    try {
      const backendBase = await apiConfig.url('/api/health')
      console.debug(`${TAG} [预检] 检查后端服务: ${backendBase}`)

      let backendOk = false
      try {
        const healthResp = await fetch(backendBase, { method: 'GET' })
        backendOk = healthResp.ok
        console.debug(`${TAG} [预检] 后端 /api/health 返回: HTTP ${healthResp.status}`)
      } catch (he: any) {
        console.error(`${TAG} [预检] 后端 /api/health 不可达: ${he.message}`)
      }

      if (!backendOk) {
        const msg = '❌ 本机后端服务 (127.0.0.1:8099) 未响应，请先启动 Python 后端再重试'
        console.error(`${TAG} ${msg}`)
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: msg } }))
        return
      }

      console.debug(`${TAG} [预检] 后端服务正常，开始测试 AI 模型连通性`)

      const baseUrl = await apiConfig.url('/api/v1/ai/connectivity-test')
      console.debug(`${TAG} [请求] 后端 API 地址: ${baseUrl}`)

      const safeApiKey = entry.apiKey
        ? `${entry.apiKey.slice(0, 4)}...${entry.apiKey.slice(-4)}`
        : '(空)'
      console.debug(`${TAG} [请求] 请求体:`, JSON.stringify({
        provider_id: entry.providerId,
        model: entry.model,
        base_url: entry.baseUrl,
        api_key: safeApiKey,
      }, null, 2))

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

      console.debug(`${TAG} [响应] HTTP 状态码: ${resp.status} ${resp.statusText}`)
      console.debug(`${TAG} [响应] 响应头:`, Object.fromEntries(resp.headers.entries()))

      const respBody = await resp.text()
      console.debug(`${TAG} [响应] 原始响应体: ${respBody}`)

      if (!resp.ok) {
        console.error(`${TAG} ❌ 后端 API 请求失败 (HTTP ${resp.status}): ${respBody}`)
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: `后端服务异常 (HTTP ${resp.status})` } }))
        return
      }

      let result: { ok: boolean; message: string }
      try {
        result = JSON.parse(respBody)
      } catch {
        console.error(`${TAG} ❌ 响应体解析失败: ${respBody}`)
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: '后端返回格式异常' } }))
        return
      }

      if (result.ok) {
        console.info(`${TAG} ✅ 连通测试成功: ${entry.providerId}/${entry.model} — ${result.message}`)
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: true, message: result.message || '连接成功' } }))
      } else {
        console.error(`${TAG} ❌ 连通测试失败: ${result.message}`)
        setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: result.message || '连接失败' } }))
      }
    } catch (e: any) {
      const { reason, suggestion } = classifyNetworkError(e)
      console.error(`${TAG} ❌ 网络异常`)
      console.error(`${TAG} 错误类型: ${e.name}`)
      console.error(`${TAG} 错误消息: ${e.message}`)
      console.error(`${TAG} 诊断原因: ${reason}`)
      console.error(`${TAG} 建议操作: ${suggestion}`)
      if (e.cause) console.error(`${TAG} 错误原因:`, e.cause)
      if (e.stack) console.debug(`${TAG} 调用栈:`, e.stack)
      setTestResults(prev => ({ ...prev, [entry.id]: { ok: false, message: `${reason}\n${suggestion}` } }))
    } finally {
      console.debug(`${TAG} ========== 连通测试结束 ==========`)
      console.groupEnd()
      setTestingId(null)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-gray-800">设置</h1>

      <section className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-700">AI 模型</h2>
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
                      className="input-field text-sm bg-gray-50"
                      value={entry.baseUrl}
                      readOnly
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
              onChange={(e) => updateGenConfig({ slideCount: parseInt(e.target.value) || 10 })}
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
        <h2 className="text-lg font-semibold text-gray-700">导出选项</h2>
        <div className="space-y-2">
          <label className="flex items-center space-x-2">
            <input type="checkbox" checked={genConfig.includeNotes}
              onChange={(e) => updateGenConfig({ includeNotes: e.target.checked })} className="rounded" />
            <span className="text-sm text-gray-700">在 PPTX 中包含演讲备注</span>
          </label>
          <label className="flex items-center space-x-2">
            <input type="checkbox" checked={genConfig.includeImages}
              onChange={(e) => updateGenConfig({ includeImages: e.target.checked })} className="rounded" />
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
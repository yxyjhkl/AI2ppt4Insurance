import { Rocket, Target, Handshake, Zap } from 'lucide-react'

export type WorkflowMode = 'auto' | 'guided' | 'cocreate'

interface Props {
  selected: WorkflowMode | null
  onChange: (mode: WorkflowMode) => void
  aiMode: string
  onAiModeChange: (mode: string) => void
  ollamaDetected: boolean
}

const MODES = [
  {
    id: 'auto' as WorkflowMode,
    label: 'AI 替我做',
    subtitle: '全自动出稿',
    icon: Rocket,
    color: 'blue',
    desc: '给一份材料或一个主题，AI 全程自动生成精美 PPT，中间无需人工介入。',
    steps: '输入内容 → 一键生成 → 进入编辑器',
    suitable: '赶时间 / 材料完整 / 信任 AI 产出',
    timeHint: '≈ 30秒-2分钟',
  },
  {
    id: 'guided' as WorkflowMode,
    label: 'AI 帮我做',
    subtitle: '按需定制',
    icon: Target,
    color: 'green',
    desc: '给材料并设定要求（受众/风格/必含内容），AI 先出大纲让你确认，确认后生成完整 PPT。',
    steps: '输入内容 + 要求 → 审核大纲 → 确认 → 生成 → 编辑',
    suitable: '有明确需求 / 需要控制方向 / 重要汇报',
    timeHint: '≈ 1-3分钟',
  },
  {
    id: 'cocreate' as WorkflowMode,
    label: 'AI 陪我做',
    subtitle: '逐步共创 精细打磨',
    icon: Handshake,
    color: 'purple',
    desc: '每一步都暴露给你：大纲可逐页编辑 → 内容可逐页微调 → 模板可在生成前切换。你是导演，AI 是执行。',
    steps: '输入内容 → 大纲(逐页编辑) → 确认 → 内容(逐页编辑) → 选模板 → 生成',
    suitable: '精细打磨 / 重要汇报 / 需要完全掌控',
    timeHint: '≈ 3-5分钟',
  },
]

export function WorkflowModeSelector({ selected, onChange, aiMode, onAiModeChange, ollamaDetected }: Props) {
  const showAiPicker = selected !== null

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
          <Zap className="w-4 h-4 text-blue-600 dark:text-blue-300" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">选择工作模式</h2>
          <p className="text-xs text-gray-500">三种深度，按需选择</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {MODES.map(m => {
          const Icon = m.icon
          const isSelected = selected === m.id
          const colors: Record<string, { border: string; bg: string; badge: string; text: string }> = {
            blue: { border: 'border-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20', badge: 'bg-blue-500', text: 'text-blue-600' },
            green: { border: 'border-green-500', bg: 'bg-green-50 dark:bg-green-900/20', badge: 'bg-green-500', text: 'text-green-600' },
            purple: { border: 'border-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20', badge: 'bg-purple-500', text: 'text-purple-600' },
          }
          const c = colors[m.color]

          return (
            <button key={m.id} onClick={() => onChange(m.id)}
              className={`relative overflow-hidden rounded-xl border-2 p-5 text-left transition-all hover:shadow-md ${
                isSelected
                  ? `${c.border} ${c.bg}`
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-3 mb-3">
                <Icon className={`w-8 h-8 ${isSelected ? c.text : 'text-gray-400'}`} />
                <div>
                  <h3 className="font-semibold text-gray-800 dark:text-gray-100">{m.label}</h3>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full text-white ${c.badge}`}>{m.subtitle}</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 leading-relaxed">{m.desc}</p>
              <div className="text-[10px] text-gray-400 space-y-0.5">
                <div className="flex items-center gap-1">
                  <span className="text-gray-300">▸</span> 流程：{m.steps}
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-gray-300">▸</span> 适合：{m.suitable}
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-gray-300">▸</span> 耗时：{m.timeHint}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {showAiPicker && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
              <Zap className="w-3 h-3 text-green-600 dark:text-green-300" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">选择 AI 引擎</h3>
              <p className="text-xs text-gray-400">点击下方选项，选择生成方式</p>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'ai_network', label: '云端 AI', desc: '效果最佳，需配置 API Key', icon: '☁️', color: 'blue' },
              { id: 'local_ollama', label: `本地 Ollama${ollamaDetected ? '' : '(未检测)'}`, desc: '完全本地运行，不上传数据', icon: '💻', color: 'green' },
              { id: 'rule_engine', label: '离线规则', desc: '无需网络，纯本地算法', icon: '📋', color: 'purple' },
            ].map(opt => {
              const colors: Record<string, { border: string; bg: string; active: string; text: string }> = {
                blue: { border: 'border-blue-200 hover:border-blue-400', bg: 'bg-blue-50/50', active: 'ring-2 ring-blue-500 bg-blue-50', text: 'text-blue-600' },
                green: { border: 'border-green-200 hover:border-green-400', bg: 'bg-green-50/50', active: 'ring-2 ring-green-500 bg-green-50', text: 'text-green-600' },
                purple: { border: 'border-purple-200 hover:border-purple-400', bg: 'bg-purple-50/50', active: 'ring-2 ring-purple-500 bg-purple-50', text: 'text-purple-600' },
              }
              const c = colors[opt.color]
              const isSelected = aiMode === opt.id
              const isDisabled = opt.id === 'local_ollama' && !ollamaDetected
              
              return (
                <button
                  key={opt.id}
                  onClick={() => !isDisabled && onAiModeChange(opt.id)}
                  disabled={isDisabled}
                  className={`relative p-4 rounded-xl border-2 text-left transition-all hover:shadow-sm ${
                    isSelected ? c.active : `${c.border} ${c.bg}`
                  } disabled:opacity-40 disabled:cursor-not-allowed`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl">{opt.icon}</span>
                    <span className={`font-semibold ${isSelected ? c.text : 'text-gray-700 dark:text-gray-200'}`}>
                      {opt.label}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{opt.desc}</p>
                  {isSelected && (
                    <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-green-500" />
                  )}
                </button>
              )
            })}
          </div>
          
          <div className="text-center">
            <span className="text-xs text-gray-400">
              ⚠️ 提示：选择后点击下方步骤继续，当前选择：
              <span className="text-primary-500 font-medium ml-1">
                {aiMode === 'ai_network' ? '云端 AI' : aiMode === 'local_ollama' ? '本地 Ollama' : '离线规则'}
              </span>
            </span>
          </div>
        </section>
      )}
    </section>
  )
}

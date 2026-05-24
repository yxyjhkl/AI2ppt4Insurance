import { useState } from 'react'
import { ChevronDown, ChevronUp, Users, Clock, Palette, Eye, AlertCircle } from 'lucide-react'

export interface Requirements {
  audience: string
  duration: string
  tone: string
  mustInclude: string
  avoidTopics: string
}

interface Props {
  value: Requirements
  onChange: (req: Requirements) => void
}

const PRESETS: { id: string; label: string; icon: typeof Users; options: { value: string; label: string; desc: string }[] }[] = [
  {
    id: 'audience', label: '受众', icon: Users, options: [
      { value: 'executives', label: '管理层', desc: '聚焦结论和决策建议' },
      { value: 'team', label: '团队', desc: '聚焦执行方案和指标' },
      { value: 'clients', label: '客户/外部', desc: '聚焦价值和案例展示' },
      { value: 'all', label: '全员', desc: '兼顾战略和执行' },
    ]
  },
  {
    id: 'duration', label: '时长', icon: Clock, options: [
      { value: '5min', label: '5 分钟', desc: '约 5-8 页' },
      { value: '15min', label: '15 分钟', desc: '约 8-12 页' },
      { value: '30min', label: '30 分钟', desc: '约 12-20 页' },
      { value: '45min', label: '45 分钟+', desc: '约 20-30 页' },
    ]
  },
  {
    id: 'tone', label: '风格', icon: Palette, options: [
      { value: 'professional', label: '严谨专业', desc: '数据驱动、逻辑严密' },
      { value: 'motivating', label: '激励动员', desc: '有感染力、目标导向' },
      { value: 'warm', label: '温暖亲和', desc: '客户视角、故事化' },
      { value: 'modern', label: '现代简洁', desc: '极简风格、视觉冲击' },
    ]
  },
]

const MUST_INCLUDES = [
  '核心KPI数据', '同比环比对比', '机构排名', '成功案例',
  '改进措施/行动方案', '组织架构图', '预算/资源需求', '市场趋势',
  '产品卖点/话术', '客户见证', '风险提示', '下一步计划',
]

export function RequirementsPanel({ value, onChange }: Props) {
  const [expanded, setExpanded] = useState(false)

  const update = (key: keyof Requirements, val: string) => {
    onChange({ ...value, [key]: val })
  }

  const toggleMustInclude = (item: string) => {
    const current = value.mustInclude ? value.mustInclude.split(', ') : []
    const next = current.includes(item)
      ? current.filter(i => i !== item)
      : [...current, item]
    update('mustInclude', next.join(', '))
  }

  return (
    <section className="card p-4 space-y-3">
      <button onClick={() => setExpanded(!expanded)} className="flex items-center justify-between w-full text-left">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-primary-500" />
          <span className="text-sm font-semibold text-gray-600 uppercase tracking-wider">详细需求（可选）</span>
          {Object.values(value).some(v => v) && (
            <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-[10px] rounded-full">已设置</span>
          )}
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
      </button>

      {expanded && (
        <div className="space-y-3 pt-2 border-t border-gray-100">
          <p className="text-xs text-gray-400">设定后 AI 将根据需求自动调整内容侧重和页数</p>

          {PRESETS.map(p => {
            const Icon = p.icon
            return (
              <div key={p.id}>
                <label className="text-xs text-gray-500 flex items-center gap-1 mb-1.5">
                  <Icon className="w-3 h-3" />{p.label}
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {p.options.map(opt => (
                    <button key={opt.value} onClick={() => update(p.id as keyof Requirements, opt.value)}
                      className={`p-2 rounded text-left border transition-colors ${
                        value[p.id as keyof Requirements] === opt.value
                          ? 'border-primary-300 bg-primary-50'
                          : 'border-gray-100 hover:border-gray-200 bg-white'
                      }`}>
                      <div className="text-xs font-medium text-gray-700">{opt.label}</div>
                      <div className="text-[10px] text-gray-400">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            )
          })}

          <div>
            <label className="text-xs text-gray-500 flex items-center gap-1 mb-1.5">
              <AlertCircle className="w-3 h-3" />必含内容（可多选）
            </label>
            <div className="flex flex-wrap gap-1">
              {MUST_INCLUDES.map(item => (
                <button key={item} onClick={() => toggleMustInclude(item)}
                  className={`px-2 py-0.5 rounded text-[10px] border transition-colors ${
                    value.mustInclude?.includes(item)
                      ? 'border-primary-300 bg-primary-50 text-primary-700'
                      : 'border-gray-100 text-gray-500 hover:border-gray-200'
                  }`}>
                  {item}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">需要避免的话题/内容</label>
            <input className="input-field text-xs" value={value.avoidTopics}
              onChange={(e) => update('avoidTopics', e.target.value)}
              placeholder="如: 不要出现竞品名称、不要展示亏损数据" />
          </div>
        </div>
      )}
    </section>
  )
}

import { useState } from 'react'
import { Check, X, RefreshCw, Loader2, ChevronDown, ChevronUp } from 'lucide-react'

export interface OutlineItem {
  index: number
  layout_type: string
  title: string
  description: string
  key_points: string[]
}

interface Props {
  title: string
  slides: OutlineItem[]
  generating: boolean
  onConfirm: () => void
  onRegenerate: () => void
  onCancel: () => void
  onEditSlide: (idx: number, field: string, value: string) => void
}

const layoutLabels: Record<string, string> = {
  cover: '封面', chapter: '章节', content: '内容', content_table: '表格',
  content_two_col: '双栏', content_three_col: '三栏', content_compare: '对比',
  content_kpi: 'KPI', content_code: '代码', ending: '结尾',
}

const layoutColors: Record<string, string> = {
  cover: 'bg-purple-100 text-purple-700', chapter: 'bg-blue-100 text-blue-700',
  content_table: 'bg-green-100 text-green-700', content_two_col: 'bg-cyan-100 text-cyan-700',
  content_compare: 'bg-orange-100 text-orange-700', content_kpi: 'bg-red-100 text-red-700',
  ending: 'bg-amber-100 text-amber-700',
}

export function OutlineReview({ title, slides, generating, onConfirm, onRegenerate, onCancel, onEditSlide }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)
  const [editingIdx, setEditingIdx] = useState<number | null>(null)
  const [editValue, setEditValue] = useState('')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl mx-4 max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">审核演示大纲</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              AI 已生成 {slides.length} 页大纲，请审核确认后再生成完整内容
            </p>
          </div>
          <button onClick={onCancel} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="flex-1 overflow-auto px-6 py-4 space-y-2">
          <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-100">
            <span className="text-sm font-medium text-gray-700">标题：</span>
            {editingIdx === -1 ? (
              <input
                className="flex-1 text-sm px-2 py-1 border border-primary-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-400"
                value={editValue}
                autoFocus
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={() => { onEditSlide(-1, 'title', editValue); setEditingIdx(null) }}
                onKeyDown={(e) => { if (e.key === 'Enter') { onEditSlide(-1, 'title', editValue); setEditingIdx(null) } if (e.key === 'Escape') setEditingIdx(null) }}
              />
            ) : (
              <span
                className="flex-1 text-sm font-semibold text-gray-800 cursor-pointer hover:text-primary-600"
                onClick={() => { setEditingIdx(-1); setEditValue(title) }}
              >
                {title || '(点击编辑标题)'}
              </span>
            )}
          </div>

          {slides.map((slide, i) => {
            const isExpanded = expandedIdx === i
            const colorClass = layoutColors[slide.layout_type] || 'bg-gray-100 text-gray-600'
            return (
              <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
                <div
                  className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-gray-50"
                  onClick={() => setExpandedIdx(isExpanded ? null : i)}
                >
                  <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${colorClass}`}>
                    {layoutLabels[slide.layout_type] || slide.layout_type}
                  </span>
                  {editingIdx === i ? (
                    <input
                      className="flex-1 text-sm px-1 py-0.5 border border-primary-300 rounded focus:outline-none"
                      value={editValue}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={() => { onEditSlide(i, 'title', editValue); setEditingIdx(null) }}
                      onKeyDown={(e) => { if (e.key === 'Enter') { onEditSlide(i, 'title', editValue); setEditingIdx(null) } if (e.key === 'Escape') setEditingIdx(null) }}
                    />
                  ) : (
                    <span
                      className="flex-1 text-sm font-medium text-gray-700"
                      onClick={(e) => { e.stopPropagation(); setEditingIdx(i); setEditValue(slide.title) }}
                    >
                      {slide.title}
                    </span>
                  )}
                  <span className="text-xs text-gray-400 shrink-0">{slide.key_points.length} 要点</span>
                  {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
                </div>
                {isExpanded && (
                  <div className="px-3 pb-3 border-t border-gray-100 bg-gray-50">
                    <p className="text-xs text-gray-500 mt-2">{slide.description}</p>
                    {slide.key_points.length > 0 && (
                      <ul className="mt-1.5 space-y-0.5">
                        {slide.key_points.map((kp, j) => (
                          <li key={j} className="text-xs text-gray-600 flex gap-2">
                            <span className="text-gray-300">•</span>
                            {kp}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200 bg-gray-50 rounded-b-xl">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>共 {slides.length} 页</span>
            <span className="text-gray-300">|</span>
            <span>点击展开查看详情，点击标题可编辑</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onCancel} className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1">
              <X className="w-3 h-3" />取消
            </button>
            <button onClick={onRegenerate} disabled={generating} className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1">
              {generating ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}重新生成
            </button>
            <button onClick={onConfirm} disabled={generating} className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1">
              <Check className="w-3 h-3" />确认并生成
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

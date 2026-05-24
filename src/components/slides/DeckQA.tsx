import { AlertCircle, AlertTriangle, Info, CheckCircle, ChevronDown, ChevronRight, Eye } from 'lucide-react'
import { useState } from 'react'
import type { QAItem } from '@/types'

interface DeckQAProps {
  results: QAItem[]
  onSelectSlide: (index: number) => void
}

export function DeckQA({ results, onSelectSlide }: DeckQAProps) {
  const [expanded, setExpanded] = useState(true)
  const [visualExpanded, setVisualExpanded] = useState(true)

  if (!results || results.length === 0) {
    return (
      <div className="p-4 text-center">
        <CheckCircle className="w-6 h-6 mx-auto mb-1 text-green-500" />
        <p className="text-xs text-gray-500">未发现问题</p>
      </div>
    )
  }

  const visualItems = results.filter(r => r.category === 'visual_check')
  const contentItems = results.filter(r => r.category !== 'visual_check')
  const errors = contentItems.filter(r => r.level === 'P0')
  const warnings = contentItems.filter(r => r.level === 'P1')
  const infos = contentItems.filter(r => r.level === 'P2' || r.level === 'P3')

  return (
    <div className="space-y-2">
      {/* Visual check section */}
      {visualItems.length > 0 && (
        <div>
          <button onClick={() => setVisualExpanded(!visualExpanded)}
            className="flex items-center justify-between w-full text-sm font-medium text-gray-700 mb-1">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-purple-500" />
              <span>视觉检查</span>
              <span className="px-1 py-0.5 bg-purple-100 text-purple-600 text-[10px] rounded font-bold">
                {visualItems.length}项
              </span>
            </div>
            {visualExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
          {visualExpanded && (
            <div className="space-y-1 max-h-40 overflow-auto">
              {visualItems.map((item, i) => (
                <div key={`vis-${i}`}
                  className="flex items-start space-x-2 p-2 rounded hover:bg-white bg-purple-50/50">
                  <Eye className="w-3.5 h-3.5 text-purple-500 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold text-purple-500 px-1 rounded border border-purple-200">
                        {item.level || 'P2'}
                      </span>
                      <span className="text-xs text-gray-700">{item.message}</span>
                    </div>
                    <div className="flex items-center space-x-2 mt-0.5">
                      {item.slide > 0 && (
                        <button onClick={() => onSelectSlide(item.slide - 1)}
                          className="text-[10px] text-primary-500 hover:text-primary-700 underline">
                          第 {item.slide} 页
                        </button>
                      )}
                      {item.detail && (
                        <span className="text-[10px] text-purple-400">{item.detail}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {contentItems.length > 0 && <div className="border-t border-gray-200 my-2" />}
        </div>
      )}

      {/* Content QA section */}
      {contentItems.length > 0 && (
        <>
          <button onClick={() => setExpanded(!expanded)}
            className="flex items-center justify-between w-full text-sm font-medium text-gray-700">
            <div className="flex items-center space-x-2">
              <span>内容质检</span>
              <div className="flex items-center space-x-1">
                {errors.length > 0 && <span className="px-1 py-0.5 bg-red-100 text-red-600 text-[10px] rounded font-bold">P0({errors.length})</span>}
                {warnings.length > 0 && <span className="px-1 py-0.5 bg-amber-100 text-amber-600 text-[10px] rounded font-bold">P1({warnings.length})</span>}
                {infos.length > 0 && <span className="px-1 py-0.5 bg-blue-100 text-blue-500 text-[10px] rounded">P2/P3({infos.length})</span>}
              </div>
            </div>
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>

          {expanded && (
            <div className="space-y-1 max-h-60 overflow-auto">
              {errors.map((item, i) => (
                <QARow key={`err-${i}`} item={item} onSelectSlide={onSelectSlide} />
              ))}
              {warnings.map((item, i) => (
                <QARow key={`warn-${i}`} item={item} onSelectSlide={onSelectSlide} />
              ))}
              {infos.map((item, i) => (
                <QARow key={`info-${i}`} item={item} onSelectSlide={onSelectSlide} />
              ))}
            </div>
          )}
        </>
      )}

      {/* All-pass case for content-only */}
      {contentItems.length > 0 && errors.length === 0 && warnings.length === 0 && (
        visualItems.length === 0 ? (
          <div className="p-4 text-center">
            <CheckCircle className="w-6 h-6 mx-auto mb-1 text-green-500" />
            <p className="text-xs text-gray-500">全部通过 ({infos.length}项建议)</p>
          </div>
        ) : null
      )}
    </div>
  )
}

function QARow({ item, onSelectSlide }: { item: QAItem; onSelectSlide: (i: number) => void }) {
  const levelColors: Record<string, { icon: typeof AlertCircle; color: string; bg: string; label: string }> = {
    P0: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-50', label: '阻断' },
    P1: { icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50', label: '警告' },
    P2: { icon: Info, color: 'text-blue-500', bg: 'bg-blue-50', label: '建议' },
    P3: { icon: Info, color: 'text-gray-400', bg: 'bg-gray-50', label: '优化' },
  }
  const lc = levelColors[item.level || 'P2'] || levelColors.P2
  const Icon = lc.icon

  return (
    <div className={`flex items-start space-x-2 p-2 rounded hover:bg-white ${lc.bg}`}>
      <Icon className={`w-3.5 h-3.5 ${lc.color} shrink-0 mt-0.5`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className={`text-[10px] font-bold ${lc.color} px-1 rounded border border-current/20`}>{item.level}</span>
          <span className="text-xs text-gray-700">{item.message}</span>
        </div>
        <div className="flex items-center space-x-2 mt-0.5">
          {item.slide > 0 && (
            <button onClick={() => onSelectSlide(item.slide - 1)}
              className="text-[10px] text-primary-500 hover:text-primary-700 underline">
              第 {item.slide} 页
            </button>
          )}
          <span className="text-[10px] text-gray-400">{item.category}</span>
        </div>
      </div>
    </div>
  )
}

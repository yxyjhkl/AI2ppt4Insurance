import { AlertCircle, AlertTriangle, Info, CheckCircle, ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import type { QAItem } from '@/types'

interface DeckQAProps {
  results: QAItem[]
  onSelectSlide: (index: number) => void
}

export function DeckQA({ results, onSelectSlide }: DeckQAProps) {
  const [expanded, setExpanded] = useState(true)

  if (!results || results.length === 0) {
    return (
      <div className="p-4 text-center">
        <CheckCircle className="w-6 h-6 mx-auto mb-1 text-green-500" />
        <p className="text-xs text-gray-500">未发现问题</p>
      </div>
    )
  }

  const errors = results.filter(r => r.severity === 'error')
  const warnings = results.filter(r => r.severity === 'warning')
  const infos = results.filter(r => r.severity === 'info')

  return (
    <div className="space-y-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-sm font-medium text-gray-700"
      >
        <div className="flex items-center space-x-2">
          <span>内容质检</span>
          <div className="flex items-center space-x-1">
            {errors.length > 0 && <span className="px-1 py-0.5 bg-red-100 text-red-600 text-[10px] rounded">{errors.length}</span>}
            {warnings.length > 0 && <span className="px-1 py-0.5 bg-amber-100 text-amber-600 text-[10px] rounded">{warnings.length}</span>}
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
    </div>
  )
}

function QARow({ item, onSelectSlide }: { item: QAItem; onSelectSlide: (i: number) => void }) {
  const icons = {
    error: <AlertCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />,
    warning: <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />,
    info: <Info className="w-3.5 h-3.5 text-blue-500 shrink-0" />,
  }

  return (
    <div className="flex items-start space-x-2 p-2 rounded hover:bg-gray-50">
      {icons[item.severity]}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-700">{item.message}</p>
        <div className="flex items-center space-x-2 mt-0.5">
          {item.slide > 0 && (
            <button
              onClick={() => onSelectSlide(item.slide - 1)}
              className="text-[10px] text-primary-500 hover:text-primary-700 underline"
            >
              第 {item.slide} 页
            </button>
          )}
          <span className="text-[10px] text-gray-400">{item.category}</span>
        </div>
      </div>
    </div>
  )
}
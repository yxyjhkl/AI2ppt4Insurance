import { useState, useCallback } from 'react'
import { GripVertical, Plus, Trash2 } from 'lucide-react'
import type { SlideData } from '@/types'

interface OutlineEditorProps {
  slides: SlideData[]
  selectedIndex: number
  onSelect: (index: number) => void
  onReorder: (from: number, to: number) => void
  onDelete: (index: number) => void
  onAdd: (afterIndex: number) => void
}

export function OutlineEditor({ slides, selectedIndex, onSelect, onReorder, onDelete, onAdd }: OutlineEditorProps) {
  const [dragIndex, setDragIndex] = useState<number | null>(null)

  const handleDragStart = useCallback((e: React.DragEvent, i: number) => {
    setDragIndex(i)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(i))
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, i: number) => {
    e.preventDefault()
    if (dragIndex !== null && dragIndex !== i) {
      onReorder(dragIndex, i)
      setDragIndex(i)
    }
  }, [dragIndex, onReorder])

  const handleDragEnd = useCallback(() => {
    setDragIndex(null)
  }, [])

  const layoutLabels: Record<string, string> = {
    cover: '封面', chapter: '章节', content: '内容',
    content_two_col: '双栏', content_three_col: '三栏',
    content_table: '表格', content_code: '代码',
    content_quote: '引用', content_compare: '对比',
    ending: '结尾', toc: '目录',
  }

  const layoutColors: Record<string, string> = {
    cover: 'bg-purple-100 text-purple-700',
    chapter: 'bg-blue-100 text-blue-700',
    ending: 'bg-amber-100 text-amber-700',
    toc: 'bg-teal-100 text-teal-700',
  }

  return (
    <div className="space-y-1">
      {slides.map((slide, i) => {
        const isSelected = selectedIndex === i
        const isDragging = dragIndex === i
        const colorClass = layoutColors[slide.layout_type] || 'bg-gray-100 text-gray-600'

        return (
          <div
            key={i}
            draggable
            onDragStart={(e) => handleDragStart(e, i)}
            onDragOver={(e) => handleDragOver(e, i)}
            onDragEnd={handleDragEnd}
            onClick={() => onSelect(i)}
            className={`group flex items-start p-2.5 rounded-lg cursor-pointer border transition-all ${
              isSelected
                ? 'border-primary-500 bg-primary-50 shadow-sm'
                : 'border-transparent hover:border-gray-200 hover:bg-gray-50'
            } ${isDragging ? 'opacity-50' : ''}`}
          >
            <div className="flex items-center pt-0.5 mr-2">
              <GripVertical className="w-3.5 h-3.5 text-gray-300 cursor-grab opacity-0 group-hover:opacity-100 transition-opacity" />
              <span className="text-xs text-gray-400 w-5 text-right -ml-3.5">{slide.page_number}</span>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${colorClass}`}>
                  {layoutLabels[slide.layout_type] || slide.layout_type}
                </span>
                <span className="text-xs text-gray-400 truncate">
                  {slide.body_items?.length || 0} 项
                </span>
              </div>
              <p className="text-sm font-medium text-gray-800 truncate mt-0.5">
                {slide.title || '(无标题)'}
              </p>
            </div>

            <div className="flex items-center space-x-0.5 opacity-0 group-hover:opacity-100 transition-opacity ml-1">
              <button onClick={(e) => { e.stopPropagation(); onAdd(i) }} className="p-1 hover:bg-gray-200 rounded" title="在后面添加">
                <Plus className="w-3 h-3 text-gray-500" />
              </button>
              <button onClick={(e) => { e.stopPropagation(); onDelete(i) }} className="p-1 hover:bg-red-100 rounded" title="删除">
                <Trash2 className="w-3 h-3 text-red-400" />
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

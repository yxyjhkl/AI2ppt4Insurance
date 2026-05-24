import { useState, useCallback, useRef } from 'react'
import { Type, Square, Image, Table2, Plus, GripVertical, PanelTop, Minus, Upload } from 'lucide-react'

interface ElementTemplate {
  type: 'text' | 'shape' | 'image' | 'table'
  label: string
  icon: typeof Type
  width: number
  height: number
  content: string
  style: Record<string, any>
}

const templates: ElementTemplate[] = [
  { type: 'text', label: '标题', icon: Type, width: 400, height: 50,
    content: '标题文本',
    style: { fontSize: 32, fontWeight: 'bold', color: '#1e40af' } },
  { type: 'text', label: '正文', icon: Type, width: 400, height: 120,
    content: '正文内容',
    style: { fontSize: 18, color: '#374151' } },
  { type: 'text', label: '项目列表', icon: PanelTop, width: 400, height: 150,
    content: '• 项目一\n• 项目二\n• 项目三',
    style: { fontSize: 16, color: '#4b5563' } },
  { type: 'image', label: '图片', icon: Image, width: 200, height: 200,
    content: '', style: {} },
  { type: 'shape', label: '矩形', icon: Square, width: 120, height: 80,
    content: 'rectangle',
    style: { fillColor: '#dbeafe', borderRadius: 4 } },
  { type: 'shape', label: '圆形', icon: Square, width: 100, height: 100,
    content: 'circle',
    style: { fillColor: '#fef3c7' } },
  { type: 'shape', label: '菱形', icon: Square, width: 100, height: 100,
    content: 'diamond',
    style: { fillColor: '#d1fae5' } },
  { type: 'shape', label: '三角形', icon: Square, width: 100, height: 90,
    content: 'triangle',
    style: { fillColor: '#fce7f3' } },
  { type: 'table', label: '表格', icon: Table2, width: 400, height: 200,
    content: '| 列1 | 列2 | 列3 |\n| A | B | C |\n| D | E | F |',
    style: { fontSize: 14 } },
]

export function ElementToolbar() {
  const [showMore, setShowMore] = useState(false)
  const imageInputRef = useRef<HTMLInputElement>(null)

  const handleDragStart = useCallback((e: React.DragEvent, tmpl: ElementTemplate) => {
    e.dataTransfer.setData('application/x-canvas-element', JSON.stringify(tmpl))
    e.dataTransfer.effectAllowed = 'copy'

    const ghost = e.currentTarget.cloneNode(true) as HTMLElement
    ghost.style.position = 'absolute'
    ghost.style.top = '-1000px'
    ghost.style.opacity = '0.6'
    ghost.style.width = '120px'
    document.body.appendChild(ghost)
    e.dataTransfer.setDragImage(ghost, 60, 20)
    setTimeout(() => document.body.removeChild(ghost), 0)
  }, [])

  const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string
      window.dispatchEvent(new CustomEvent('image-uploaded', { detail: dataUrl }))
    }
    reader.readAsDataURL(file)
    e.target.value = ''
  }, [])

  const visible = showMore ? templates : templates.slice(0, 5)

  return (
    <div className="flex items-center space-x-1 p-1.5 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
      {visible.map((tmpl, i) => {
        const Icon = tmpl.icon
        return (
          <div
            key={i}
            draggable
            onDragStart={(e) => handleDragStart(e, tmpl)}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md text-xs text-gray-600 hover:bg-gray-100 cursor-grab active:cursor-grabbing border border-transparent hover:border-gray-200 whitespace-nowrap transition-colors"
            title={`拖拽到画布上添加${tmpl.label}`}
          >
            <GripVertical className="w-3 h-3 text-gray-300" />
            <Icon className="w-3.5 h-3.5" />
            <span>{tmpl.label}</span>
          </div>
        )
      })}

      {templates.length > 5 && (
        <button
          onClick={() => setShowMore(!showMore)}
          className="flex items-center px-2 py-1.5 text-xs text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-50"
        >
          {showMore ? <Minus className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
        </button>
      )}

      <div className="ml-2 w-px h-5 bg-gray-200" />

      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleImageUpload}
      />
      <button
        onClick={() => imageInputRef.current?.click()}
        className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md text-xs text-gray-600 hover:bg-blue-50 hover:text-blue-600 border border-transparent hover:border-blue-200 transition-colors"
        title="上传图片"
      >
        <Upload className="w-3.5 h-3.5" />
        <span>图片上传</span>
      </button>

      <div className="ml-auto text-[10px] text-gray-400 pr-1">
        拖拽添加到画布 · 粘贴截图
      </div>
    </div>
  )
}
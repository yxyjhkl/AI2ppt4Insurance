import { useCallback, useRef, useEffect, useState } from 'react'
import { Upload, AlignStartVertical, AlignCenterVertical, AlignEndVertical, AlignStartHorizontal, AlignCenterHorizontal, AlignEndHorizontal, BringToFront, SendToBack, ChevronUp, ChevronDown, ZoomIn, ZoomOut } from 'lucide-react'
import { CanvasElement } from './CanvasElement'
import type { CanvasElement as CanvasElementType, SlideData } from '@/types'

interface Props {
  slide: SlideData | null
  elements: CanvasElementType[]
  selectedElement: string | null
  scale: number
  onSelectElement: (id: string | null) => void
  onUpdateElement: (id: string, updates: Partial<CanvasElementType>) => void
  onAddElement: (element: CanvasElementType) => void
  onDeleteElement: (id: string) => void
  onElementsChange: (elements: CanvasElementType[]) => void
  onDoubleClickElement: (id: string) => void
  onScaleChange?: (scale: number) => void
}

let _idCounter = 0
function genId() { return `el_${++_idCounter}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}` }

export function CanvasEditor({
  slide, elements, selectedElement, scale,
  onSelectElement, onUpdateElement,
  onAddElement, onDeleteElement, onElementsChange,
  onDoubleClickElement, onScaleChange,
}: Props) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const clipboardRef = useRef<CanvasElementType | null>(null)
  const [snapGuides, setSnapGuides] = useState<{ x: number | null; y: number | null }>({ x: null, y: null })

  useEffect(() => { _idCounter = 0 }, [])

  const handleCanvasClick = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current || (e.target as HTMLElement).classList.contains('canvas-bg')) {
      onSelectElement(null)
      setSnapGuides({ x: null, y: null })
    }
  }, [onSelectElement])

  const getSelected = useCallback(() => elements.find(e => e.id === selectedElement) || null, [elements, selectedElement])
  const maxZ = elements.reduce((m, e) => Math.max(m, e.zIndex), 0)

  const dupElement = useCallback((el: CanvasElementType, offsetX = 30, offsetY = 30) => {
    const newEl: CanvasElementType = {
      ...el,
      id: genId(),
      x: el.x + offsetX,
      y: el.y + offsetY,
      zIndex: maxZ + 1,
    }
    onUpdateElement(el.id, { zIndex: maxZ + 1 })
    onAddElement(newEl)
    return newEl.id
  }, [maxZ, onUpdateElement, onAddElement])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const data = e.dataTransfer.getData('application/x-canvas-element')
    if (!data || !canvasRef.current) return
    try {
      const template = JSON.parse(data)
      const rect = canvasRef.current.getBoundingClientRect()
      const x = (e.clientX - rect.left) / scale
      const y = (e.clientY - rect.top) / scale
      onAddElement({
        id: genId(),
        type: template.type,
        x, y,
        width: template.width || 200,
        height: template.height || 60,
        rotation: 0, opacity: 100,
        zIndex: maxZ + 1,
        content: template.content || '',
        style: { ...template.style },
      })
    } catch { /* ignore */ }
  }, [scale, maxZ, onAddElement])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }, [])

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current || (e.target as HTMLElement).classList.contains('canvas-bg')) {
      fileInputRef.current?.click()
    }
  }, [])

  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const el = document.activeElement
      if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || (el as HTMLElement).contentEditable === 'true')) return
      const items = e.clipboardData?.items
      if (!items) return

      let hasImage = false
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          hasImage = true
          e.preventDefault()
          const file = items[i].getAsFile()
          if (!file) continue
          const reader = new FileReader()
          reader.onload = (ev) => {
            onAddElement({
              id: genId(),
              type: 'image',
              x: 80, y: 80, width: 300, height: 200,
              rotation: 0, opacity: 100,
              zIndex: maxZ + 1,
              content: ev.target?.result as string,
              style: {},
            })
          }
          reader.readAsDataURL(file)
          break
        }
      }
      if (hasImage) return

      const text = e.clipboardData?.getData('text/plain')
      if (!text) return
      const lines = text.trim().split(/\r?\n/)
      if (lines.length < 2) return

      const hasTab = lines.some(l => l.includes('\t'))
      if (!hasTab) return

      e.preventDefault()
      const rows = lines.map(l => l.split('\t'))
      const maxCols = Math.max(...rows.map(r => r.length))
      const normRows = rows.map(r => {
        while (r.length < maxCols) r.push('')
        return r
      })
      const mdTable = '| ' + normRows.map(r => r.join(' | ')).join(' |\n| ') + ' |'

      onAddElement({
        id: genId(),
        type: 'table',
        x: 60, y: 80,
        width: Math.max(400, maxCols * 140),
        height: Math.min(400, normRows.length * 40 + 40),
        rotation: 0, opacity: 100,
        zIndex: maxZ + 1,
        content: mdTable,
        style: { fontSize: 13 },
      })
    }
    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [maxZ, onAddElement])

  useEffect(() => {
    const handler = (e: Event) => {
      const dataUrl = (e as CustomEvent).detail as string
      onAddElement({
        id: genId(),
        type: 'image',
        x: 100, y: 100,
        width: 300, height: 200,
        rotation: 0, opacity: 100,
        zIndex: maxZ + 1,
        content: dataUrl,
        style: {},
      })
    }
    window.addEventListener('image-uploaded', handler)
    return () => window.removeEventListener('image-uploaded', handler)
  }, [maxZ, onAddElement])

  const handleImageFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string
      onAddElement({
        id: genId(),
        type: 'image',
        x: 100, y: 100,
        width: 300, height: 200,
        rotation: 0, opacity: 100,
        zIndex: maxZ + 1,
        content: dataUrl,
        style: {},
      })
    }
    reader.readAsDataURL(file)
    e.target.value = ''
  }, [maxZ, onAddElement])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const el = document.activeElement
      if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || (el as HTMLElement).contentEditable === 'true')) return

      const sel = getSelected()
      if (sel) {
        if (e.key === 'Delete' || e.key === 'Backspace') {
          onDeleteElement(sel.id)
          return
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
          clipboardRef.current = { ...sel }
          return
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
          if (clipboardRef.current) {
            const newId = dupElement(clipboardRef.current)
            onSelectElement(newId)
          }
          return
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
          const newId = dupElement(sel)
          onSelectElement(newId)
          e.preventDefault()
          return
        }
        if ((e.ctrlKey || e.metaKey) && e.key === ']') {
          onUpdateElement(sel.id, { zIndex: sel.zIndex + 1 })
          onElementsChange(elements.map(e => e.id === sel.id ? { ...e, zIndex: sel.zIndex + 1 } : e))
          return
        }
        if ((e.ctrlKey || e.metaKey) && e.key === '[') {
          onUpdateElement(sel.id, { zIndex: Math.max(0, sel.zIndex - 1) })
          onElementsChange(elements.map(e => e.id === sel.id ? { ...e, zIndex: Math.max(0, sel.zIndex - 1) } : e))
          return
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [getSelected, elements, onDeleteElement, onUpdateElement, onElementsChange, dupElement, onSelectElement])

  const alignElements = useCallback((dir: string) => {
    if (!selectedElement || !canvasRef.current) return
    const sel = getSelected()
    if (!sel) return
    const rect = canvasRef.current.getBoundingClientRect()
    const cw = rect.width / scale
    const ch = rect.height / scale
    const updates: Partial<CanvasElementType> = {}
    if (dir === 'left') updates.x = 0
    if (dir === 'center-h') updates.x = (cw - sel.width) / 2
    if (dir === 'right') updates.x = cw - sel.width
    if (dir === 'top') updates.y = 0
    if (dir === 'center-v') updates.y = (ch - sel.height) / 2
    if (dir === 'bottom') updates.y = ch - sel.height
    onUpdateElement(sel.id, updates)
    onElementsChange(elements.map(e => e.id === sel.id ? { ...e, ...updates } : e))
  }, [selectedElement, getSelected, scale, onUpdateElement, onElementsChange, elements])

  const handleZOrder = useCallback((action: string) => {
    const sel = getSelected()
    if (!sel) return
    if (action === 'front') {
      onUpdateElement(sel.id, { zIndex: maxZ + 1 })
      onElementsChange(elements.map(e => e.id === sel.id ? { ...e, zIndex: maxZ + 1 } : e))
    } else if (action === 'back') {
      const minZ = elements.reduce((m, e) => Math.min(m, e.zIndex), 0)
      onUpdateElement(sel.id, { zIndex: Math.max(0, minZ - 1) })
      onElementsChange(elements.map(e => e.id === sel.id ? { ...e, zIndex: Math.max(0, minZ - 1) } : e))
    } else if (action === 'up') {
      onUpdateElement(sel.id, { zIndex: sel.zIndex + 1 })
      onElementsChange(elements.map(e => e.id === sel.id ? { ...e, zIndex: sel.zIndex + 1 } : e))
    } else if (action === 'down') {
      onUpdateElement(sel.id, { zIndex: Math.max(0, sel.zIndex - 1) })
      onElementsChange(elements.map(e => e.id === sel.id ? { ...e, zIndex: Math.max(0, sel.zIndex - 1) } : e))
    }
  }, [getSelected, elements, maxZ, onUpdateElement, onElementsChange])

  const handleZoom = useCallback((delta: number) => {
    const newScale = Math.min(2, Math.max(0.3, scale + delta))
    onScaleChange?.(newScale)
  }, [scale, onScaleChange])

  const handleCanvasWheel = useCallback((e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault()
      handleZoom(-e.deltaY * 0.001)
    }
  }, [handleZoom])

  const selectedElData = getSelected()

  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-800 p-4 overflow-auto" onWheel={handleCanvasWheel}>
      <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleImageFileSelect} />

      <div className="flex items-center justify-between w-full max-w-[960px] mb-2 px-1 gap-2">
        <div className="flex items-center space-x-1">
          <button onClick={() => fileInputRef.current?.click()} className="flex items-center space-x-1 px-2 py-1 rounded text-xs text-gray-600 hover:bg-white hover:shadow-sm border border-transparent hover:border-gray-200" title="上传图片">
            <Upload className="w-3 h-3" /><span>图片</span>
          </button>
          <span className="w-px h-4 bg-gray-300" />
          <button onClick={() => handleZOrder('front')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="置顶 (Ctrl+])">
            <BringToFront className="w-3 h-3 text-gray-500" />
          </button>
          <button onClick={() => handleZOrder('up')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="上移一层">
            <ChevronUp className="w-3 h-3 text-gray-500" />
          </button>
          <button onClick={() => handleZOrder('down')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="下移一层">
            <ChevronDown className="w-3 h-3 text-gray-500" />
          </button>
          <button onClick={() => handleZOrder('back')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="置底 (Ctrl+[)">
            <SendToBack className="w-3 h-3 text-gray-500" />
          </button>
          <span className="w-px h-4 bg-gray-300" />
          <button onClick={() => alignElements('left')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="左对齐">
            <AlignStartHorizontal className="w-3 h-3 text-gray-500" />
          </button>
          <button onClick={() => alignElements('center-h')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="水平居中">
            <AlignCenterHorizontal className="w-3 h-3 text-gray-500" />
          </button>
          <button onClick={() => alignElements('right')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="右对齐">
            <AlignEndHorizontal className="w-3 h-3 text-gray-500" />
          </button>
          <span className="w-px h-4 bg-gray-300" />
          <button onClick={() => alignElements('top')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="顶对齐">
            <AlignStartVertical className="w-3 h-3 text-gray-500" />
          </button>
          <button onClick={() => alignElements('center-v')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="垂直居中">
            <AlignCenterVertical className="w-3 h-3 text-gray-500" />
          </button>
          <button onClick={() => alignElements('bottom')} disabled={!selectedElData} className="p-1 rounded hover:bg-white disabled:opacity-30" title="底对齐">
            <AlignEndVertical className="w-3 h-3 text-gray-500" />
          </button>
        </div>
        <div className="flex items-center space-x-1 text-[10px] text-gray-400">
          <button onClick={() => handleZoom(-0.1)} disabled={scale <= 0.3} className="p-1 rounded hover:bg-white disabled:opacity-20"><ZoomOut className="w-3 h-3" /></button>
          <span className="w-8 text-center font-mono">{Math.round(scale * 100)}%</span>
          <button onClick={() => handleZoom(0.1)} disabled={scale >= 2} className="p-1 rounded hover:bg-white disabled:opacity-20"><ZoomIn className="w-3 h-3" /></button>
          <span className="mx-1">|</span>
          <kbd className="px-1 py-0.5 bg-gray-200 rounded text-gray-500">Ctrl+C/V/D</kbd>
          <span>复制</span>
          <span className="mx-1">|</span>
          <kbd className="px-1 py-0.5 bg-gray-200 rounded text-gray-500">Ctrl+[/]</kbd>
          <span>层级</span>
        </div>
      </div>

      <div ref={canvasRef}
        className="canvas-bg bg-white shadow-2xl rounded-lg relative overflow-hidden cursor-pointer"
        style={{ width: '100%', maxWidth: 960, aspectRatio: '16 / 9', transform: `scale(${scale})`, transformOrigin: 'top center', marginBottom: scale < 1 ? `${-960 * 0.5625 * (1 - scale)}px` : undefined }}
        onClick={handleCanvasClick} onDoubleClick={handleDoubleClick} onDrop={handleDrop} onDragOver={handleDragOver}
        title="双击上传图片 · 拖拽元素到画布 · Ctrl+滚轮缩放"
      >
        {slide?.svg_preview && (
          <iframe srcDoc={slide.svg_preview} sandbox="allow-same-origin" className="absolute inset-0 w-full h-full pointer-events-none" style={{ border: 'none', zIndex: 0 }} title="Slide background" />
        )}

        {snapGuides.x !== null && (
          <div style={{ position: 'absolute', left: snapGuides.x, top: 0, width: 1, height: '100%', background: '#ef4444', zIndex: 9999, pointerEvents: 'none' }} />
        )}
        {snapGuides.y !== null && (
          <div style={{ position: 'absolute', left: 0, top: snapGuides.y, width: '100%', height: 1, background: '#ef4444', zIndex: 9999, pointerEvents: 'none' }} />
        )}

        {[...elements].sort((a, b) => a.zIndex - b.zIndex).map(el => (
          <CanvasElement
            key={el.id} element={el}
            isSelected={selectedElement === el.id}
            isHovered={false}
            scale={scale}
            allElements={elements}
            onSelect={onSelectElement}
            onMove={(id, x, y) => onUpdateElement(id, { x, y })}
            onResize={(id, w, h) => onUpdateElement(id, { width: w, height: h })}
            onMoveEnd={(id, x, y) => onElementsChange(elements.map(e => e.id === id ? { ...e, x, y } : e))}
            onResizeEnd={(id, w, h) => onElementsChange(elements.map(e => e.id === id ? { ...e, width: w, height: h } : e))}
            onUpdate={(id, updates) => onUpdateElement(id, updates)}
            onDoubleClick={onDoubleClickElement}
            onDelete={onDeleteElement}
            onSnap={(x, y) => setSnapGuides({ x, y })}
          />
        ))}

        {!slide && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">未选择幻灯片</div>
        )}
        {elements.length === 0 && slide && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center text-gray-300">
              <div className="w-16 h-16 mx-auto mb-3 rounded-2xl border-2 border-dashed border-gray-300 flex items-center justify-center">
                <Upload className="w-6 h-6 text-gray-300" />
              </div>
              <p className="text-base font-medium mb-1">从工具栏拖拽元素到此处</p>
              <p className="text-xs text-gray-400">双击上传图片 · Ctrl+V 粘贴 · Ctrl+C/V 复制</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

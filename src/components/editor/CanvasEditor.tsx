import { useState, useCallback, useRef, useEffect } from 'react'
import { CanvasElement } from './CanvasElement'
import type { CanvasElement as CanvasElementType, SlideData } from '@/types'

interface Props {
  slide: SlideData | null
  elements: CanvasElementType[]
  selectedElement: string | null
  hoveredElement: string | null
  scale: number
  onSelectElement: (id: string | null) => void
  onHoverElement: (id: string | null) => void
  onUpdateElement: (id: string, updates: Partial<CanvasElementType>) => void
  onAddElement: (element: CanvasElementType) => void
  onDeleteElement: (id: string) => void
  onElementsChange: (elements: CanvasElementType[]) => void
  onDoubleClickElement: (id: string) => void
}

let _idCounter = 0
function genId() { return `el_${++_idCounter}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}` }

export function CanvasEditor({
  slide, elements, selectedElement, hoveredElement, scale,
  onSelectElement, onHoverElement, onUpdateElement,
  onAddElement, onDeleteElement, onElementsChange,
  onDoubleClickElement,
}: Props) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [canvasSize, setCanvasSize] = useState({ w: 960, h: 540 })

  useEffect(() => {
    _idCounter = 0
  }, [])

  useEffect(() => {
    if (!canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    setCanvasSize({ w: rect.width, h: rect.height })
  }, [slide])

  const handleCanvasClick = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current || (e.target as HTMLElement).classList.contains('canvas-bg')) {
      onSelectElement(null)
    }
  }, [onSelectElement])

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
        rotation: 0,
        opacity: 100,
        zIndex: elements.length,
        content: template.content || '',
        style: { ...template.style },
      })
    } catch { /* ignore */ }
  }, [scale, elements.length, onAddElement])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }, [])

  return (
    <div className="flex-1 flex items-center justify-center bg-gray-100 p-4 overflow-auto">
      <div
        ref={canvasRef}
        className="canvas-bg bg-white shadow-2xl rounded-lg relative overflow-hidden"
        style={{
          width: '100%',
          maxWidth: 960,
          aspectRatio: '16 / 9',
        }}
        onClick={handleCanvasClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        {/* SVG background */}
        {slide?.svg_preview && (
          <iframe
            srcDoc={slide.svg_preview}
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ border: 'none', zIndex: 0 }}
            title="Slide background"
          />
        )}

        {/* Canvas elements */}
        {[...elements]
          .sort((a, b) => a.zIndex - b.zIndex)
          .map(el => (
            <CanvasElement
              key={el.id}
              element={el}
              isSelected={selectedElement === el.id}
              isHovered={hoveredElement === el.id}
              scale={scale}
              onSelect={onSelectElement}
              onMove={(id, x, y) => onUpdateElement(id, { x, y })}
              onResize={(id, w, h) => onUpdateElement(id, { width: w, height: h })}
              onMoveEnd={(id, x, y) => {
                onElementsChange(elements.map(e => e.id === id ? { ...e, x, y } : e))
              }}
              onResizeEnd={(id, w, h) => {
                onElementsChange(elements.map(e => e.id === id ? { ...e, width: w, height: h } : e))
              }}
              onDoubleClick={onDoubleClickElement}
              onDelete={onDeleteElement}
            />
          ))}

        {/* Empty state */}
        {!slide && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
            No slide selected
          </div>
        )}

        {/* Drop zone hint */}
        {elements.length === 0 && slide && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center text-gray-300">
              <p className="text-lg mb-1">Drag elements here</p>
              <p className="text-xs">or use the toolbar above to add content</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

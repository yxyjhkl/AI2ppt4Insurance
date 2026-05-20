import { useState, useCallback, useRef, useEffect } from 'react'
import type { CanvasElement as CanvasElementType } from '@/types'

interface Props {
  element: CanvasElementType
  isSelected: boolean
  isHovered: boolean
  scale: number
  onSelect: (id: string) => void
  onMove: (id: string, x: number, y: number) => void
  onResize: (id: string, w: number, h: number) => void
  onMoveEnd: (id: string, x: number, y: number) => void
  onResizeEnd: (id: string, w: number, h: number) => void
  onDoubleClick: (id: string) => void
  onDelete: (id: string) => void
}

export function CanvasElement({
  element, isSelected, isHovered, scale,
  onSelect, onMove, onResize, onMoveEnd, onResizeEnd,
  onDoubleClick, onDelete,
}: Props) {
  const [dragStart, setDragStart] = useState<{ x: number; y: number; elX: number; elY: number } | null>(null)
  const [resizeDir, setResizeDir] = useState<string | null>(null)
  const [resizeStart, setResizeStart] = useState<{ x: number; y: number; elW: number; elH: number; elX: number; elY: number } | null>(null)
  const elRef = useRef<HTMLDivElement>(null)

  const dragStartRef = useRef(dragStart)
  dragStartRef.current = dragStart
  const resizeStartRef = useRef(resizeStart)
  resizeStartRef.current = resizeStart

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    onSelect(element.id)

    setDragStart({
      x: e.clientX, y: e.clientY,
      elX: element.x, elY: element.y,
    })
  }, [element.id, element.x, element.y, onSelect])

  const handleResizeStart = useCallback((e: React.MouseEvent, dir: string) => {
    e.stopPropagation()
    e.preventDefault()
    onSelect(element.id)
    setResizeDir(dir)
    setResizeStart({
      x: e.clientX, y: e.clientY,
      elW: element.width, elH: element.height,
      elX: element.x, elY: element.y,
    })
  }, [element.id, element.width, element.height, element.x, element.y, onSelect])

  const handleGlobalMove = useCallback((e: MouseEvent) => {
    const ds = dragStartRef.current
    if (!ds) return
    const dx = (e.clientX - ds.x) / scale
    const dy = (e.clientY - ds.y) / scale
    onMove(element.id, ds.elX + dx, ds.elY + dy)
  }, [scale, element.id, onMove])

  const handleGlobalResize = useCallback((e: MouseEvent) => {
    const rs = resizeStartRef.current
    if (!rs || !resizeDir) return
    const dx = (e.clientX - rs.x) / scale
    const dy = (e.clientY - rs.y) / scale

    let { elW, elH, elX, elY } = rs

    if (resizeDir.includes('e')) elW = Math.max(40, elW + dx)
    if (resizeDir.includes('w')) { elW = Math.max(40, elW - dx); elX = elX + dx }
    if (resizeDir.includes('s')) elH = Math.max(30, elH + dy)
    if (resizeDir.includes('n')) { elH = Math.max(30, elH - dy); elY = elY + dy }

    onResize(element.id, elW, elH)
    if (resizeDir.includes('w') || resizeDir.includes('n')) {
      onMove(element.id, elX, elY)
    }
  }, [resizeDir, scale, element.id, onResize, onMove])

  const handleGlobalUp = useCallback(() => {
    if (dragStartRef.current) {
      onMoveEnd(element.id, element.x, element.y)
      setDragStart(null)
    }
    if (resizeStartRef.current) {
      onResizeEnd(element.id, element.width, element.height)
      setResizeDir(null)
      setResizeStart(null)
    }
  }, [element.id, element.x, element.y, element.width, element.height, onMoveEnd, onResizeEnd])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
      onDelete(element.id)
    }
  }, [element.id, onDelete])

  useEffect(() => {
    if (!dragStart && !resizeStart) return
    const moveHandler = dragStart ? handleGlobalMove : handleGlobalResize
    const upHandler = handleGlobalUp
    window.addEventListener('mousemove', moveHandler)
    window.addEventListener('mouseup', upHandler)
    return () => {
      window.removeEventListener('mousemove', moveHandler)
      window.removeEventListener('mouseup', upHandler)
    }
  }, [dragStart, resizeStart, handleGlobalMove, handleGlobalResize, handleGlobalUp])

  if (dragStart || resizeStart) {
    return (
      <div
        ref={elRef}
        style={{
          position: 'absolute',
          left: element.x, top: element.y,
          width: element.width, height: element.height,
          opacity: element.opacity / 100,
          zIndex: element.zIndex,
          outline: '2px solid #3b82f6',
          outlineOffset: -1,
          cursor: dragStart ? 'grabbing' : 'default',
        }}
      >
        <ElementContent element={element} />
      </div>
    )
  }

  const handles = ['nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w']

  return (
    <div
      ref={elRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      style={{
        position: 'absolute',
        left: element.x, top: element.y,
        width: element.width, height: element.height,
        opacity: element.opacity / 100,
        zIndex: element.zIndex,
        transform: `rotate(${element.rotation}deg)`,
        cursor: 'grab',
        outline: isSelected ? '2px solid #3b82f6' : isHovered ? '1px dashed #94a3b8' : 'none',
        outlineOffset: -1,
        borderRadius: element.style.borderRadius || 0,
        backgroundColor: element.style.backgroundColor || 'transparent',
        border: element.style.borderWidth ? `${element.style.borderWidth}px solid ${element.style.borderColor || '#ccc'}` : 'none',
      }}
      onMouseDown={handleMouseDown}
      onDoubleClick={() => onDoubleClick(element.id)}
      onClick={(e) => { e.stopPropagation(); onSelect(element.id) }}
    >
      <ElementContent element={element} />

      {isSelected && handles.map(dir => (
        <div
          key={dir}
          onMouseDown={(e) => handleResizeStart(e, dir)}
          style={{
            position: 'absolute',
            width: dir.length === 1 ? '100%' : '8px',
            height: dir.length === 1 ? '8px' : '8px',
            ...(dir.includes('n') ? { top: -4 } : { bottom: -4 }),
            ...(dir.includes('w') ? { left: -4 } : dir.includes('e') ? { right: -4 } : dir.length === 1 ? {} : { left: '50%', marginLeft: -4 }),
            ...(dir.length === 1 && dir === 'n' ? { left: 4, right: 4, width: 'auto' } : {}),
            ...(dir.length === 1 && dir === 's' ? { left: 4, right: 4, width: 'auto' } : {}),
            ...(dir.length === 1 && dir === 'w' ? { top: 4, bottom: 4, height: 'auto' } : {}),
            ...(dir.length === 1 && dir === 'e' ? { top: 4, bottom: 4, height: 'auto' } : {}),
            backgroundColor: 'white',
            border: '1px solid #3b82f6',
            cursor: dir === 'nw' || dir === 'se' ? 'nwse-resize'
                  : dir === 'ne' || dir === 'sw' ? 'nesw-resize'
                  : dir === 'n' || dir === 's' ? 'ns-resize'
                  : 'ew-resize',
            zIndex: 10,
          }}
        />
      ))}
    </div>
  )
}

function ElementContent({ element }: { element: CanvasElementType }) {
  if (element.type === 'image') {
    return (
      <img
        src={element.content || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23e5e7eb"/><text x="50" y="55" text-anchor="middle" fill="%239ca3af" font-size="12">图片</text></svg>'}
        alt=""
        style={{ width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }}
        draggable={false}
      />
    )
  }

  if (element.type === 'shape') {
    const shapeStyle: React.CSSProperties = {
      width: '100%', height: '100%',
      background: element.style.fillColor || '#e5e7eb',
      border: '1px solid #d1d5db',
    }
    if (element.content === 'circle') shapeStyle.borderRadius = '50%'
    if (element.content === 'diamond') {
      return (
        <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
          <polygon points="50,5 95,50 50,95 5,50"
            fill={element.style.fillColor || '#e5e7eb'}
            stroke="#d1d5db" strokeWidth="1" />
        </svg>
      )
    }
    if (element.content === 'triangle') {
      return (
        <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
          <polygon points="50,5 95,95 5,95"
            fill={element.style.fillColor || '#e5e7eb'}
            stroke="#d1d5db" strokeWidth="1" />
        </svg>
      )
    }
    return <div style={shapeStyle} />
  }

  if (element.type === 'table') {
    const rows = element.content.split('\n').slice(0, 6)
    return (
      <div style={{ width: '100%', height: '100%', overflow: 'hidden', fontSize: Math.min(element.style.fontSize || 12, element.height / rows.length * 0.4) }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.split('|').filter(Boolean).map((cell, j) => (
                <td key={j} style={{
                  border: '1px solid #d1d5db',
                  padding: '2px 4px',
                  fontSize: 'inherit',
                  background: i === 0 ? '#f3f4f6' : 'white',
                }}>
                  {cell.trim()}
                </td>
              ))}
            </tr>
          ))}
        </table>
      </div>
    )
  }

  const style: React.CSSProperties = {
    width: '100%', height: '100%',
    fontFamily: element.style.fontFamily || 'inherit',
    fontSize: element.style.fontSize || 16,
    fontWeight: element.style.fontWeight || 'normal',
    fontStyle: element.style.fontStyle || 'normal',
    color: element.style.color || '#1f2937',
    textAlign: element.style.textAlign || 'left',
    padding: '4px 6px',
    overflow: 'hidden',
    wordBreak: 'break-word',
    cursor: 'text',
    whiteSpace: 'pre-wrap',
    display: 'flex',
    alignItems: element.style.textAlign === 'center' ? 'center' : 'flex-start',
    justifyContent: element.style.textAlign === 'center' ? 'center' : 'flex-start',
  }

  return <div style={style}>{element.content || '文本'}</div>
}

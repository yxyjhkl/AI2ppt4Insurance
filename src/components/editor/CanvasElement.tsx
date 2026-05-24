import { useState, useCallback, useRef, useEffect } from 'react'
import type { CanvasElement as CanvasElementType } from '@/types'

interface Props {
  element: CanvasElementType
  isSelected: boolean
  isHovered: boolean
  scale: number
  allElements: CanvasElementType[]
  onSelect: (id: string) => void
  onMove: (id: string, x: number, y: number) => void
  onResize: (id: string, w: number, h: number) => void
  onMoveEnd: (id: string, x: number, y: number) => void
  onResizeEnd: (id: string, w: number, h: number) => void
  onUpdate: (id: string, updates: Partial<CanvasElementType>) => void
  onDoubleClick: (id: string) => void
  onDelete: (id: string) => void
  onSnap: (x: number | null, y: number | null) => void
}

export function CanvasElement({
  element, isSelected, isHovered, scale, allElements,
  onSelect, onMove, onResize, onMoveEnd, onResizeEnd,
  onUpdate, onDoubleClick, onDelete, onSnap,
}: Props) {
  const [dragStart, setDragStart] = useState<{ x: number; y: number; elX: number; elY: number } | null>(null)
  const [resizeDir, setResizeDir] = useState<string | null>(null)
  const [resizeStart, setResizeStart] = useState<{ x: number; y: number; elW: number; elH: number; elX: number; elY: number } | null>(null)
  const [inlineEditing, setInlineEditing] = useState(false)
  const [inlineText, setInlineText] = useState('')
  const elRef = useRef<HTMLDivElement>(null)
  const editRef = useRef<HTMLTextAreaElement>(null)
  const elementRef = useRef(element)
  elementRef.current = element
  const dragStartRef = useRef(dragStart)
  dragStartRef.current = dragStart
  const resizeStartRef = useRef(resizeStart)
  resizeStartRef.current = resizeStart

  const locked = element.locked

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    if (locked) return
    onSelect(element.id)
    setDragStart({ x: e.clientX, y: e.clientY, elX: element.x, elY: element.y })
  }, [element.id, element.x, element.y, locked, onSelect])

  const handleResizeStart = useCallback((e: React.MouseEvent, dir: string) => {
    e.stopPropagation()
    e.preventDefault()
    if (locked) return
    onSelect(element.id)
    setResizeDir(dir)
    setResizeStart({ x: e.clientX, y: e.clientY, elW: element.width, elH: element.height, elX: element.x, elY: element.y })
  }, [element.id, element.width, element.height, element.x, element.y, locked, onSelect])

  const handleDoubleClickElem = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    if (locked) return
    if (element.type === 'text') {
      setInlineText(element.content)
      setInlineEditing(true)
      setTimeout(() => editRef.current?.focus(), 0)
    }
    onDoubleClick(element.id)
  }, [element, locked, onDoubleClick])

  const handleInlineBlur = useCallback(() => {
    setInlineEditing(false)
    onUpdate(elementRef.current.id, { content: inlineText })
  }, [onUpdate, inlineText])

  const handleInlineKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      setInlineEditing(false)
      onUpdate(elementRef.current.id, { content: inlineText })
    }
    if (e.key === 'Escape') {
      setInlineText(elementRef.current.content)
      setInlineEditing(false)
    }
  }, [onUpdate, inlineText])

  useEffect(() => {
    if (inlineEditing && editRef.current) {
      editRef.current.style.height = 'auto'
      editRef.current.style.height = editRef.current.scrollHeight + 'px'
    }
  }, [inlineText, inlineEditing])

  const computeSnap = useCallback((x: number, y: number, w: number, h: number) => {
    const threshold = 5 / scale
    const cx = x + w / 2
    const cy = y + h / 2
    let snapX: number | null = null
    let snapY: number | null = null

    for (const other of allElements) {
      if (other.id === element.id) continue
      const ox = other.x, oy = other.y, ow = other.width, oh = other.height
      if (Math.abs(x - ox) < threshold) snapX = ox
      if (Math.abs(x + w - (ox + ow)) < threshold) snapX = ox + ow - w
      if (Math.abs(y - oy) < threshold) snapY = oy
      if (Math.abs(y + h - (oy + oh)) < threshold) snapY = oy + oh - h
      if (Math.abs(cx - (ox + ow / 2)) < threshold * 2) snapX = ox + ow / 2 - w / 2
      if (Math.abs(cy - (oy + oh / 2)) < threshold * 2) snapY = oy + oh / 2 - h / 2
    }
    onSnap(snapX, snapY)
    return { x: snapX !== null ? snapX : x, y: snapY !== null ? snapY : y }
  }, [element.id, scale, allElements, onSnap])

  const handleGlobalMove = useCallback((e: MouseEvent) => {
    const ds = dragStartRef.current
    if (!ds) return
    const dx = (e.clientX - ds.x) / scale
    const dy = (e.clientY - ds.y) / scale
    const newX = ds.elX + dx
    const newY = ds.elY + dy
    const snapped = computeSnap(newX, newY, elementRef.current.width, elementRef.current.height)
    onMove(elementRef.current.id, snapped.x, snapped.y)
  }, [scale, onMove, computeSnap])

  const handleGlobalResize = useCallback((e: MouseEvent) => {
    const rs = resizeStartRef.current
    const dir = resizeDir
    if (!rs || !dir) return
    const shiftHeld = e.shiftKey
    const dx = (e.clientX - rs.x) / scale
    const dy = (e.clientY - rs.y) / scale
    let { elW, elH, elX, elY } = rs
    const aspectRatio = rs.elW / rs.elH

    if (dir.includes('e')) elW = Math.max(20, elW + dx)
    if (dir.includes('w')) { elW = Math.max(20, elW - dx); elX = rs.elX + (rs.elW - elW) }
    if (dir.includes('s')) elH = Math.max(20, elH + dy)
    if (dir.includes('n')) { elH = Math.max(20, elH - dy); elY = rs.elY + (rs.elH - elH) }

    if (shiftHeld && elementRef.current.type === 'image') {
      if (dir.includes('e') || dir.includes('w')) elH = elW / aspectRatio
      else if (dir.includes('s') || dir.includes('n')) elW = elH * aspectRatio
    }

    onResize(elementRef.current.id, elW, elH)
    if (dir.includes('w') || dir.includes('n')) {
      onMove(elementRef.current.id, elX, elY)
    }
  }, [resizeDir, scale, onResize, onMove])

  const handleGlobalUp = useCallback(() => {
    const el = elementRef.current
    if (dragStartRef.current) {
      const snapped = computeSnap(el.x, el.y, el.width, el.height)
      onMoveEnd(el.id, snapped.x, snapped.y)
      setDragStart(null)
      onSnap(null, null)
    }
    if (resizeStartRef.current) {
      onResizeEnd(el.id, el.width, el.height)
      setResizeDir(null)
      setResizeStart(null)
    }
  }, [onMoveEnd, onResizeEnd, computeSnap, onSnap])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
      onDelete(element.id)
    }
  }, [element.id, onDelete])

  useEffect(() => {
    if (!dragStart && !resizeStart) return
    window.addEventListener('mousemove', dragStart ? handleGlobalMove : handleGlobalResize)
    window.addEventListener('mouseup', handleGlobalUp)
    return () => {
      window.removeEventListener('mousemove', dragStart ? handleGlobalMove : handleGlobalResize)
      window.removeEventListener('mouseup', handleGlobalUp)
    }
  }, [dragStart, resizeStart, handleGlobalMove, handleGlobalResize, handleGlobalUp])

  const handles = ['nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w']

  return (
    <div ref={elRef} tabIndex={0} onKeyDown={handleKeyDown}
      style={{
        position: 'absolute', left: element.x, top: element.y,
        width: element.width, height: element.height,
        opacity: element.opacity / 100, zIndex: element.zIndex,
        transform: `rotate(${element.rotation}deg)`,
        cursor: locked ? 'default' : (dragStart ? 'grabbing' : 'grab'),
        outline: isSelected ? '2px solid #3b82f6' : isHovered ? '1px dashed #94a3b8' : 'none',
        outlineOffset: -1,
        borderRadius: element.style.borderRadius || 0,
        backgroundColor: element.style.backgroundColor || 'transparent',
        border: element.style.borderWidth ? `${element.style.borderWidth}px solid ${element.style.borderColor || '#ccc'}` : 'none',
      }}
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClickElem}
      onClick={(e) => { e.stopPropagation(); onSelect(element.id) }}
    >
      {inlineEditing && element.type === 'text' ? (
        <textarea
          ref={editRef}
          className="w-full h-full p-1 text-xs border-2 border-blue-400 rounded resize-none focus:outline-none overflow-hidden"
          value={inlineText}
          onChange={(e) => {
            setInlineText(e.target.value)
          }}
          onBlur={handleInlineBlur}
          onKeyDown={handleInlineKeyDown}
          style={{
            fontFamily: element.style.fontFamily || 'inherit',
            fontSize: element.style.fontSize || 16,
            fontWeight: element.style.fontWeight || 'normal',
            color: element.style.color || '#1f2937',
            textAlign: element.style.textAlign || 'left',
          }}
        />
      ) : (
        <ElementContent element={element} />
      )}

      {locked && isSelected && (
        <div style={{ position: 'absolute', top: 2, right: 2, fontSize: 10, color: '#f59e0b', zIndex: 20, pointerEvents: 'none' }}>🔒</div>
      )}

      {isSelected && !locked && !inlineEditing && handles.map(dir => (
        <div key={dir} onMouseDown={(e) => handleResizeStart(e, dir)}
          style={{
            position: 'absolute', width: dir.length === 1 ? (dir === 'n' || dir === 's' ? '100%' : 8) : 8,
            height: dir.length === 1 ? (dir === 'e' || dir === 'w' ? '100%' : 8) : 8,
            ...(dir.includes('n') ? { top: -4 } : { bottom: -4 }),
            ...(dir.includes('w') ? { left: -4 } : dir.includes('e') ? { right: -4 } : { left: '50%', marginLeft: -4 }),
            backgroundColor: 'white', border: '1px solid #3b82f6',
            cursor: dir === 'nw' || dir === 'se' ? 'nwse-resize' : dir === 'ne' || dir === 'sw' ? 'nesw-resize' : dir === 'n' || dir === 's' ? 'ns-resize' : 'ew-resize',
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
      <img src={element.content || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23e5e7eb"/><text x="50" y="55" text-anchor="middle" fill="%239ca3af" font-size="12">图片</text></svg>'}
        alt="" style={{ width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }} draggable={false} />
    )
  }
  if (element.type === 'shape') {
    const shapeStyle: React.CSSProperties = { width: '100%', height: '100%', background: element.style.fillColor || '#e5e7eb', border: '1px solid #d1d5db' }
    if (element.content === 'circle') shapeStyle.borderRadius = '50%'
    if (element.content === 'diamond') return <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}><polygon points="50,5 95,50 50,95 5,50" fill={element.style.fillColor || '#e5e7eb'} stroke="#d1d5db" strokeWidth="1" /></svg>
    if (element.content === 'triangle') return <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}><polygon points="50,5 95,95 5,95" fill={element.style.fillColor || '#e5e7eb'} stroke="#d1d5db" strokeWidth="1" /></svg>
    return <div style={shapeStyle} />
  }
  if (element.type === 'table') {
    const rows = element.content.split('\n')
      .filter(r => !/^\|[-|\s]+\|$/.test(r))
      .slice(0, 10)
    const fontSize = Math.min(element.style.fontSize || 12, element.height / rows.length * 0.4)
    return (
      <div style={{ width: '100%', height: '100%', overflow: 'hidden', fontSize }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          {rows.map((row, i) => (
            <tr key={i}>{row.split('|').filter(Boolean).map((cell, j) => (
              <td key={j} style={{ border: '1px solid #d1d5db', padding: '2px 4px', fontSize: 'inherit', background: i === 0 ? '#f3f4f6' : 'white' }}>{cell.trim()}</td>
            ))}</tr>
          ))}
        </table>
      </div>
    )
  }
  return (
    <div style={{
      width: '100%', height: '100%', fontFamily: element.style.fontFamily || 'inherit',
      fontSize: element.style.fontSize || 16, fontWeight: element.style.fontWeight || 'normal',
      fontStyle: element.style.fontStyle || 'normal', color: element.style.color || '#1f2937',
      textAlign: element.style.textAlign || 'left', padding: '4px 6px', overflow: 'hidden',
      wordBreak: 'break-word', whiteSpace: 'pre-wrap',
      display: 'flex', alignItems: element.style.textAlign === 'center' ? 'center' : 'flex-start',
      justifyContent: element.style.textAlign === 'center' ? 'center' : 'flex-start',
    }}>
      {element.content || '文本'}
    </div>
  )
}

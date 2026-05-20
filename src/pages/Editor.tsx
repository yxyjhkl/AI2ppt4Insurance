import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  Play, Download, ChevronLeft, ChevronRight, Layout, FileText,
  CheckSquare, Presentation, Undo2, Redo2, Eye, EyeOff, RefreshCw, X, Loader2
} from 'lucide-react'
import { OutlineEditor } from '@/components/slides/OutlineEditor'
import { SpeakerNotes } from '@/components/slides/SpeakerNotes'
import { DeckQA } from '@/components/slides/DeckQA'
import { CanvasEditor } from '@/components/editor/CanvasEditor'
import { ElementToolbar } from '@/components/editor/ElementToolbar'
import { PropertiesPanel } from '@/components/editor/PropertiesPanel'
import { useUndoRedo } from '@/hooks/useUndoRedo'
import { apiConfig, createAbortableFetch } from '@/utils/api'
import { useProjectStore } from '@/stores/projectStore'
import type { SlideData, CanvasElement, QAItem } from '@/types'

export function Editor() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const lastGeneration = useProjectStore((s) => s.lastGeneration)
  const setLastGeneration = useProjectStore((s) => s.setLastGeneration)
  const generationContentRef = useRef<string>('')
  const generationSceneRef = useRef<string>('report')
  const [slides, setSlides] = useState<SlideData[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [qaResults, setQaResults] = useState<QAItem[]>([])
  const [mode, setMode] = useState<string>('')
  const [modeMessage, setModeMessage] = useState<string>('')
  const [projectTitle, setProjectTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [rightPanel, setRightPanel] = useState<'properties' | 'notes' | 'qa'>('properties')
  const [selectedElement, setSelectedElement] = useState<string | null>(null)
  const [hoveredElement, setHoveredElement] = useState<string | null>(null)
  const [showCanvas, setShowCanvas] = useState(true)
  const [canvasScale] = useState(1)
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false)
  const [regenerateContent, setRegenerateContent] = useState('')

  const elementsHistory = useUndoRedo<CanvasElement[]>(
    slides[selectedIndex]?.elements || [],
    30
  )

  useEffect(() => {
    const raw = sessionStorage.getItem('pending_ppt_data')
    if (raw) {
      try {
        const data = JSON.parse(raw)
        setSlides((data.slides || []).map((s: SlideData) => ({ ...s, elements: s.elements || [] })))
        setQaResults(data.qa_results || [])
        setMode(data.mode || 'offline')
        setModeMessage(data.message || '')
        setProjectTitle(data.title || '未命名')
        sessionStorage.removeItem('pending_ppt_data')
        return
      } catch (e) {
        console.error('Failed to load pending PPT data:', e)
      }
    }

    const project = useProjectStore.getState().currentProject
    if (project && project.slides.length > 0 && slides.length === 0) {
      setSlides(project.slides.map((s, i) => ({
        page_number: i + 1,
        layout_type: s.layoutType,
        title: s.title,
        subtitle: null,
        body_items: s.content ? [{ type: 'list_item' as const, text: s.content, level: 1 }] : [],
        images: [], tables: [], code_block: null,
        notes: s.notes || '',
        svg_preview: s.svgContent || '',
        elements: [],
      })))
      setProjectTitle(project.name)
    }
  }, [])

  useEffect(() => {
    if (lastGeneration && lastGeneration.slides.length > 0) {
      setSlides(lastGeneration.slides.map((s) => ({ ...s, elements: s.elements || [] })))
      setQaResults(lastGeneration.qaResults || [])
      setMode(lastGeneration.mode || 'offline')
      setModeMessage(lastGeneration.message || '')
      setProjectTitle(lastGeneration.title || '未命名')
      setSelectedIndex(0)
      generationContentRef.current = lastGeneration.content || ''
      generationSceneRef.current = lastGeneration.scene || 'report'
      setLastGeneration(null)
    }
  }, [])

  useEffect(() => {
    if (slides[selectedIndex]) {
      elementsHistory.reset(slides[selectedIndex].elements || [])
    }
  }, [selectedIndex, slides])

  useEffect(() => {
    updateSlideElements(elementsHistory.present)
  }, [elementsHistory.present])

  const updateSlideElements = useCallback((newElements: CanvasElement[]) => {
    setSlides(prev => prev.map((s, i) =>
      i === selectedIndex ? { ...s, elements: newElements } : s
    ))
  }, [selectedIndex])

  const handleElementsChange = useCallback((elements: CanvasElement[]) => {
    elementsHistory.set(elements)
    updateSlideElements(elements)
  }, [elementsHistory, updateSlideElements])

  const handleAddElement = useCallback((el: CanvasElement) => {
    const current = elementsHistory.present
    const updated = [...current, el]
    elementsHistory.set(updated)
    updateSlideElements(updated)
    setSelectedElement(el.id)
  }, [elementsHistory, updateSlideElements])

  const handleUpdateElement = useCallback((id: string, updates: Partial<CanvasElement>) => {
    const current = elementsHistory.present
    const updated = current.map(e => e.id === id ? { ...e, ...updates } : e)
    elementsHistory.setWithoutHistory(updated)
    updateSlideElements(updated)
  }, [elementsHistory, updateSlideElements])

  const handleDeleteElement = useCallback((id: string) => {
    const current = elementsHistory.present
    const updated = current.filter(e => e.id !== id)
    elementsHistory.set(updated)
    updateSlideElements(updated)
    setSelectedElement(null)
  }, [elementsHistory, updateSlideElements])

  const handleDoubleClickElement = useCallback((id: string) => {
    setRightPanel('properties')
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault()
        if (e.shiftKey) {
          elementsHistory.redo()
        } else if (elementsHistory.canUndo) {
          elementsHistory.undo()
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [elementsHistory.canUndo, elementsHistory.canRedo, elementsHistory.undo, elementsHistory.redo])

  const handleRegenerate = useCallback(async () => {
    const content = regenerateContent || generationContentRef.current
    if (!content.trim()) return
    setLoading(true)
    setShowRegenerateDialog(false)
    const regenAbort = new AbortController()
    const regenFetch = createAbortableFetch(regenAbort.signal)
    try {
      const res = await regenFetch(await apiConfig.url('/api/v1/generate/pptx'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scene: generationSceneRef.current || searchParams.get('scene') || 'report',
          content,
          template: searchParams.get('template') || 'professional-blue',
          ai_mode: 'auto',
          canvas_format: '16:9',
          language: 'zh-CN',
          model: null,
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSlides((data.slides || []).map((s: SlideData) => ({ ...s, elements: [] })))
      setQaResults(data.qa_results || [])
      setMode(data.mode || 'offline')
      setModeMessage(data.message || '')
      setProjectTitle(data.title || '未命名')
      setSelectedIndex(0)
      generationContentRef.current = content
    } catch (err) {
      console.error('Regeneration failed:', err)
    } finally {
      setLoading(false)
    }
  }, [regenerateContent, searchParams])

  const handleUpdateSlide = useCallback((index: number, updates: Partial<SlideData>) => {
    setSlides(prev => prev.map((s, i) => i === index ? { ...s, ...updates } : s))
  }, [])

  const handleReorder = useCallback((from: number, to: number) => {
    setSlides(prev => {
      const next = [...prev]
      const [moved] = next.splice(from, 1)
      next.splice(to, 0, moved)
      return next.map((s, i) => ({ ...s, page_number: i + 1 }))
    })
  }, [])

  const handleDeleteSlide = useCallback((index: number) => {
    setSlides(prev => {
      const next = prev.filter((_, i) => i !== index)
      return next.map((s, i) => ({ ...s, page_number: i + 1 }))
    })
    if (selectedIndex >= index) setSelectedIndex(Math.max(0, selectedIndex - 1))
  }, [selectedIndex])

  const handleAddSlide = useCallback((afterIndex: number) => {
    const newSlide: SlideData = {
      page_number: afterIndex + 2, layout_type: 'content',
      title: '新幻灯片', subtitle: null, body_items: [],
      images: [], tables: [], code_block: null,
      notes: '', svg_preview: '', elements: [],
    }
    setSlides(prev => {
      const next = [...prev]
      next.splice(afterIndex + 1, 0, newSlide)
      return next.map((s, i) => ({ ...s, page_number: i + 1 }))
    })
    setSelectedIndex(afterIndex + 1)
  }, [])

  const handlePresent = useCallback(() => {
    if (slides.length === 0) return
    sessionStorage.setItem('presenter_slides', JSON.stringify(slides))
    navigate('/presenter')
  }, [slides, navigate])

  const handleExport = useCallback(async () => {
    if (slides.length === 0) return
    setExporting(true)
    const exportAbort = new AbortController()
    const exportFetch = createAbortableFetch(exportAbort.signal)
    try {
      const res = await exportFetch(await apiConfig.url('/api/v1/export/pptx'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slides: slides.map(s => ({
            layout_type: s.layout_type,
            title: s.title,
            subtitle: s.subtitle,
            body_items: s.body_items || [],
            tables: s.tables || [],
            images: s.images || [],
            code_block: s.code_block,
            notes: s.notes || '',
          })),
          template: searchParams.get('template') || 'professional-blue',
          canvas_format: '16:9',
          project_title: projectTitle || '演示文稿',
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const pptxB64 = data.pptx_base64
      if (pptxB64) {
        const byteString = atob(pptxB64)
        const ab = new ArrayBuffer(byteString.length)
        const ia = new Uint8Array(ab)
        for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i)
        const blob = new Blob([ab], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${projectTitle || '演示文稿'}.pptx`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('导出失败:', err)
    } finally {
      setExporting(false)
    }
  }, [slides, searchParams, projectTitle])

  const updateNotes = useCallback((notes: string) => {
    handleUpdateSlide(selectedIndex, { notes })
  }, [selectedIndex, handleUpdateSlide])

  const currentSlide = slides[selectedIndex] || null
  const currentElements = elementsHistory.present
  const selectedElData = currentElements.find(e => e.id === selectedElement) || null

  return (
    <div className="flex h-full">
      {/* Left: Slide outline */}
      <aside className="w-56 shrink-0 flex flex-col border-r border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          <span className="text-xs font-semibold text-gray-500 uppercase">幻灯片</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${mode === 'ai' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}
            title={modeMessage}>
            {mode === 'ai' ? 'AI' : mode || '离线'}</span>
        </div>
        <div className="flex-1 overflow-auto p-2">
          <OutlineEditor
            slides={slides}
            selectedIndex={selectedIndex}
            onSelect={(i) => { setSelectedIndex(i); setSelectedElement(null) }}
            onReorder={handleReorder}
            onDelete={handleDeleteSlide}
            onAdd={handleAddSlide}
          />
        </div>
      </aside>

      {/* Center: Canvas */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-3 py-1 border-b border-gray-200 bg-white">
          <div className="flex items-center space-x-1">
            <button onClick={() => elementsHistory.undo()}
              disabled={!elementsHistory.canUndo}
              className="p-1.5 hover:bg-gray-100 rounded disabled:opacity-30" title="撤销 (Ctrl+Z)">
              <Undo2 className="w-4 h-4 text-gray-600" />
            </button>
            <button onClick={() => elementsHistory.redo()}
              disabled={!elementsHistory.canRedo}
              className="p-1.5 hover:bg-gray-100 rounded disabled:opacity-30" title="重做 (Ctrl+Shift+Z)">
              <Redo2 className="w-4 h-4 text-gray-600" />
            </button>
            <div className="w-px h-5 bg-gray-200 mx-1" />
            <button onClick={() => setShowCanvas(!showCanvas)}
              className={`p-1.5 rounded ${showCanvas ? 'bg-gray-100' : 'hover:bg-gray-100'}`} title="切换画布">
              {showCanvas ? <Eye className="w-4 h-4 text-gray-600" /> : <EyeOff className="w-4 h-4 text-gray-600" />}
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400">{slides.length > 0 ? `${selectedIndex + 1} / ${slides.length}` : ''}</span>
            <button
              onClick={() => {
                setRegenerateContent(generationContentRef.current)
                setShowRegenerateDialog(true)
              }}
              disabled={loading}
              className="btn-secondary text-xs px-2 py-1 flex items-center space-x-1"
              title="重新生成"
            >
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
              <span>重新生成</span>
            </button>
            <button onClick={handleExport} disabled={exporting || slides.length === 0} className="btn-primary text-xs px-2 py-1 flex items-center space-x-1 disabled:opacity-50">
              {exporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
              <span>{exporting ? '导出中...' : '导出 PPTX'}</span>
            </button>
            <button onClick={handlePresent} disabled={slides.length === 0}
              className="btn-secondary text-xs px-2 py-1 flex items-center space-x-1 disabled:opacity-30">
              <Presentation className="w-3 h-3" /><span>演示</span>
            </button>
          </div>
        </div>

        {/* Element toolbar */}
        {showCanvas && <ElementToolbar />}

        {/* Canvas area */}
        <div className="flex-1 flex">
          {showCanvas ? (
            <CanvasEditor
              slide={currentSlide}
              elements={currentElements}
              selectedElement={selectedElement}
              hoveredElement={hoveredElement}
              scale={canvasScale}
              onSelectElement={setSelectedElement}
              onHoverElement={setHoveredElement}
              onUpdateElement={handleUpdateElement}
              onAddElement={handleAddElement}
              onDeleteElement={handleDeleteElement}
              onElementsChange={handleElementsChange}
              onDoubleClickElement={handleDoubleClickElement}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-100">
              <div className="text-center text-gray-400 text-sm">
                <p className="text-lg mb-1">{currentSlide?.title || '无幻灯片'}</p>
                {currentSlide?.subtitle && <p className="text-gray-300">{currentSlide.subtitle}</p>}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right: Properties / Notes / QA */}
      <aside className="w-64 shrink-0 flex flex-col border-l border-gray-200 bg-white">
        <div className="flex border-b border-gray-200">
          {[
            {id: 'properties', icon: Layout, label: '元素' },
            { id: 'notes', icon: FileText, label: '备注' },
            { id: 'qa', icon: CheckSquare, label: '质检' },
          ].map(tab => (
            <button key={tab.id}
              onClick={() => setRightPanel(tab.id as typeof rightPanel)}
              className={`flex-1 flex items-center justify-center space-x-1 py-2 text-xs font-medium border-b-2 transition-colors ${
                rightPanel === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-400 hover:text-gray-600'
              }`}>
              <tab.icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-auto">
          {rightPanel === 'properties' && selectedElData && (
            <PropertiesPanel
              element={selectedElData}
              onUpdate={(updates) => handleUpdateElement(selectedElData.id, updates)}
              onDelete={() => handleDeleteElement(selectedElData.id)}
            />
          )}

          {rightPanel === 'properties' && !selectedElData && currentSlide && (
            <div className="p-4 space-y-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">标题</label>
                <input className="input-field text-sm" value={currentSlide.title}
                  onChange={(e) => handleUpdateSlide(selectedIndex, { title: e.target.value })} />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">布局</label>
                <select className="input-field text-sm" value={currentSlide.layout_type}
                  onChange={(e) => handleUpdateSlide(selectedIndex, { layout_type: e.target.value })}>
                  {['cover','chapter','content','content_two_col','content_table','content_code','content_quote','ending'].map(lt => (
                    <option key={lt} value={lt}>{lt === 'cover' ? '封面' : lt === 'chapter' ? '章节' : lt === 'content' ? '内容' : lt === 'content_two_col' ? '双栏' : lt === 'content_three_col' ? '三栏' : lt === 'content_table' ? '表格' : lt === 'content_code' ? '代码' : lt === 'content_quote' ? '引用' : lt === 'content_compare' ? '对比' : lt === 'ending' ? '结尾' : lt === 'toc' ? '目录' : lt.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>
              {currentSlide.body_items.length > 0 && (
                <div>
                  <label className="text-xs text-gray-500 block mb-1">正文 ({currentSlide.body_items.length})</label>
                  <div className="max-h-32 overflow-auto space-y-0.5">
                    {currentSlide.body_items.map((item, i) => (
                      <div key={i} className="text-[11px] p-1 bg-gray-50 rounded">
                        <span className="text-gray-400 mr-1">{item.type === 'list_item' ? '•' : '¶'}</span>
                        <span className="text-gray-600">{item.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {!selectedElData && (
                <div className="text-center text-gray-400 text-xs pt-4 border-t border-gray-100">
                  选中文档上的元素以编辑其属性
                </div>
              )}
            </div>
          )}

          {rightPanel === 'notes' && (
            <SpeakerNotes slide={currentSlide} onUpdateNotes={updateNotes} />
          )}

          {rightPanel === 'qa' && (
            <DeckQA results={qaResults} onSelectSlide={(i) => setSelectedIndex(i)} />
          )}
        </div>
      </aside>

      {showRegenerateDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">重新生成演示文稿</h3>
              <button onClick={() => setShowRegenerateDialog(false)}
                className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600 block mb-1">输入内容</label>
              <textarea
                value={regenerateContent}
                onChange={(e) => setRegenerateContent(e.target.value)}
                className="input-field min-h-[150px] resize-y"
                placeholder="输入或粘贴内容，支持 Markdown 格式..."
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button onClick={() => setShowRegenerateDialog(false)}
                className="btn-secondary text-sm px-4 py-2">
                取消
              </button>
              <button onClick={handleRegenerate}
                disabled={!regenerateContent.trim() || loading}
                className="btn-primary text-sm px-4 py-2 flex items-center space-x-2 disabled:opacity-50">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                <span>生成</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

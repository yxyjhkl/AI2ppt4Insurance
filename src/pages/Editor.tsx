/**
 * 编辑器页面 —— 幻灯片查看/编辑/导出/增强的核心界面
 *
 * 三栏布局：左侧大纲(OutlineEditor) | 中间预览/画布(SlidePreview/CanvasEditor) | 右侧面板(属性/备注/质检)
 *
 * 导出处理程序块（4个导出路径）：
 *   handleExport → POST /api/v1/export/pptx → 下载.pptx
 *   handleExportPdf → POST /api/v1/export (format=pdf) → 下载.pdf
 *   handleExportPngs → POST /api/v1/export (format=pngs) → 下载.zip
 *   handleTTS → POST /api/v1/media/tts-narrate → 下载.mp3旁白
 *   状态保护：同一时间只允许一个导出操作(exporting=true)，支持AbortController中断
 *
 * 资料补充(handleSupplement)：
 *   POST /api/v1/generate/supplement，将现有slides发回后端
 *   LLM在原内容基础上补充数据/案例/流程（不删除原有内容，新增项标记【补充】）
 *   支持6种补充类型：智能综合/补充数据/补充案例/补充流程/补充对比/自定义指令
 *   返回enhanced_slides合并到当前slides的body_items中
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  Download, Layout, FileText, FileOutput, Image, Mic, Database,
  CheckSquare, Presentation, Undo2, Redo2, Eye, EyeOff, RefreshCw, X, Loader2
} from 'lucide-react'
import { OutlineEditor } from '@/components/slides/OutlineEditor'
import { SlidePreview } from '@/components/slides/SlidePreview'
import { SpeakerNotes } from '@/components/slides/SpeakerNotes'
import { DeckQA } from '@/components/slides/DeckQA'
import { CanvasEditor } from '@/components/editor/CanvasEditor'
import { ElementToolbar } from '@/components/editor/ElementToolbar'
import { PropertiesPanel } from '@/components/editor/PropertiesPanel'
import { useUndoRedo } from '@/hooks/useUndoRedo'
import { apiConfig, createAbortableFetch } from '@/utils/api'
import { getObject } from '@/utils/secureStore'
import { useProjectStore } from '@/stores/projectStore'
import { downloadBase64 } from '@/utils/download'
import type { SlideData, CanvasElement, QAItem } from '@/types'

export function Editor() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const lastGeneration = useProjectStore((s) => s.lastGeneration)
  const setLastGeneration = useProjectStore((s) => s.setLastGeneration)
  const generationContentRef = useRef<string>('')
  const generationSceneRef = useRef<string>('report')
  const abortRef = useRef<AbortController | null>(null)
  const mountedRef = useRef(true)
  const initRef = useRef(false)
  const [slideVersion, setSlideVersion] = useState(0)
  const [slides, setSlides] = useState<SlideData[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [qaResults, setQaResults] = useState<QAItem[]>([])
  const [mode, setMode] = useState<string>('')
  const [modeMessage, setModeMessage] = useState<string>('')
  const [projectTitle, setProjectTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')
  const [rightPanel, setRightPanel] = useState<'properties' | 'notes' | 'qa'>('properties')
  const [selectedElement, setSelectedElement] = useState<string | null>(null)
  const [showCanvas, setShowCanvas] = useState(false)
  const [canvasScale, setCanvasScale] = useState(1)
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false)
  const [regenerateContent, setRegenerateContent] = useState('')
  const [showSupplementDialog, setShowSupplementDialog] = useState(false)
  const [supplementType, setSupplementType] = useState('auto')
  const [supplementInstruction, setSupplementInstruction] = useState('')
  const [supplementing, setSupplementing] = useState(false)

  const elementsHistory = useUndoRedo<CanvasElement[]>(
    slides[selectedIndex]?.elements || [],
    30
  )

  // 幻灯片级撤销/重做（改标题、删页、排序、布局等）
  const slideHistoryRef = useRef<SlideData[][]>([])
  const slideHistoryIdxRef = useRef(-1)
  const MAX_SLIDE_HISTORY = 50

  const pushSlideHistory = useCallback((newSlides: SlideData[]) => {
    const history = slideHistoryRef.current
    const idx = slideHistoryIdxRef.current
    // 截断后续历史（如果用户在撤销后做了新操作）
    const newHistory = history.slice(0, idx + 1)
    newHistory.push(newSlides)
    if (newHistory.length > MAX_SLIDE_HISTORY) newHistory.shift()
    slideHistoryRef.current = newHistory
    slideHistoryIdxRef.current = newHistory.length - 1
  }, [])

  const undoSlides = useCallback(() => {
    const idx = slideHistoryIdxRef.current
    if (idx <= 0) return
    slideHistoryIdxRef.current = idx - 1
    setSlides(slideHistoryRef.current[idx - 1].map((s, i) => ({ ...s, page_number: i + 1 })))
  }, [])

  const redoSlides = useCallback(() => {
    const history = slideHistoryRef.current
    const idx = slideHistoryIdxRef.current
    if (idx >= history.length - 1) return
    slideHistoryIdxRef.current = idx + 1
    setSlides(history[idx + 1].map((s, i) => ({ ...s, page_number: i + 1 })))
  }, [])

  const canUndoSlides = slideHistoryIdxRef.current > 0
  const canRedoSlides = slideHistoryIdxRef.current < slideHistoryRef.current.length - 1

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      abortRef.current?.abort()
    }
  }, [])

  useEffect(() => {
    // 优先从 lastGeneration 加载（从 Dashboard 生成后跳转过来）
    if (lastGeneration && lastGeneration.slides.length > 0) {
      setSlides(lastGeneration.slides.map((s: SlideData) => ({ ...s, elements: s.elements || [] })))
      setQaResults(lastGeneration.qaResults || [])
      setMode(lastGeneration.mode || 'offline')
      setModeMessage(lastGeneration.message || '')
      setProjectTitle(lastGeneration.title || '未命名')
      setSelectedIndex(0)
      generationContentRef.current = lastGeneration.content || ''
      generationSceneRef.current = lastGeneration.scene || 'report'
      setLastGeneration(null)
      return
    }

    // 如果没有 lastGeneration，尝试从 currentProject 加载（直接打开已有项目）
    const project = useProjectStore.getState().currentProject
    if (project && project.slides.length > 0) {
      setSlides(project.slides.map((s, i) => ({
        page_number: i + 1,
        layout_type: s.layoutType,
        title: s.title,
        subtitle: null,
        body_items: s.bodyItems && s.bodyItems.length > 0
          ? s.bodyItems
          : s.content
            ? [{ type: 'list_item' as const, text: s.content, level: 1 }]
            : [],
        images: [], tables: [], code_block: null,
        notes: s.notes || '',
        svg_preview: s.svgContent || '',
        elements: s.elements || [],
      })))
      setProjectTitle(project.name)
    }
  }, [lastGeneration, setLastGeneration])

  useEffect(() => {
    if (slides[selectedIndex] && (initRef.current || slideVersion > 0)) {
      elementsHistory.reset(slides[selectedIndex].elements || [])
    }
  }, [selectedIndex, slideVersion])

  useEffect(() => {
    if (slides.length > 0 && !initRef.current) {
      initRef.current = true
      if (slides[selectedIndex]) {
        elementsHistory.reset(slides[selectedIndex].elements || [])
      }
      // 初始化幻灯片历史
      slideHistoryRef.current = [slides.map(s => ({ ...s }))]
      slideHistoryIdxRef.current = 0
    }
  }, [slides.length])

  const saveToProjectStore = useCallback(() => {
    if (slides.length === 0) return
    const project = useProjectStore.getState().currentProject
    if (!project) return
    const store = useProjectStore.getState()
    store.setCurrentProject({
      ...project,
      name: projectTitle,
      slides: slides.map((s, i) => ({
        id: `slide_${i}`,
        index: i,
        layoutType: s.layout_type as any,
        title: s.title,
        content: (s.body_items || []).map((b: any) => b.text).join('\n'),
        bodyItems: s.body_items || [],
        notes: s.notes || '',
        svgContent: s.svg_preview || '',
        elements: s.elements || [],
      })),
      updatedAt: new Date().toISOString(),
    })
  }, [slides, projectTitle])

  useEffect(() => {
    if (slides.length === 0) return
    const timer = setTimeout(saveToProjectStore, 3000)
    return () => clearTimeout(timer)
  }, [slides, projectTitle, saveToProjectStore])

  useEffect(() => {
    const handler = () => saveToProjectStore()
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [saveToProjectStore])

  // 编辑后自动刷新 SVG 预览，保持预览与导出一致
  const previewRefreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastRefreshedHash = useRef<Record<number, string>>({})

  useEffect(() => {
    if (slides.length === 0) return
    if (selectedIndex < 0 || selectedIndex >= slides.length) return
    const currentSlide = slides[selectedIndex]
    if (!currentSlide) return

    // 计算当前页内容的哈希，避免相同内容重复刷新
    const contentHash = JSON.stringify({
      layout_type: currentSlide.layout_type,
      title: currentSlide.title,
      body_items: currentSlide.body_items,
      tables: currentSlide.tables,
    })
    if (lastRefreshedHash.current[selectedIndex] === contentHash) return

    if (previewRefreshTimer.current) clearTimeout(previewRefreshTimer.current)
    previewRefreshTimer.current = setTimeout(async () => {
      try {
        const res = await fetch(await apiConfig.url('/api/v1/generate/refresh-preview'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            slide: {
              page_number: currentSlide.page_number,
              layout_type: currentSlide.layout_type,
              title: currentSlide.title,
              subtitle: currentSlide.subtitle,
              body_items: currentSlide.body_items || [],
              tables: currentSlide.tables || [],
              images: currentSlide.images || [],
              code_block: currentSlide.code_block,
              notes: currentSlide.notes || '',
            },
            template: searchParams.get('template') || 'professional-blue',
            canvas_format: useProjectStore.getState().generationConfig.canvasFormat || '16:9',
          }),
        })
        if (res.ok) {
          const data = await res.json()
          if (data.svg) {
            lastRefreshedHash.current[selectedIndex] = contentHash
            setSlides(prev => prev.map((s, i) =>
              i === selectedIndex ? { ...s, svg_preview: data.svg } : s
            ))
          }
        }
      } catch {
        // 后端不可用时静默跳过，预览保持旧版本
      }
    }, 800)

    return () => {
      if (previewRefreshTimer.current) clearTimeout(previewRefreshTimer.current)
    }
  }, [slides, selectedIndex])  // eslint-disable-line react-hooks/exhaustive-deps

  const updateSlideElements = useCallback((newElements: CanvasElement[]) => {
    setSlides(prev => prev.map((s, i) =>
      i === selectedIndex ? { ...s, elements: newElements } : s
    ))
  }, [selectedIndex])

  const updateSlideElementsRef = useRef(updateSlideElements)
  updateSlideElementsRef.current = updateSlideElements
  useEffect(() => {
    updateSlideElementsRef.current(elementsHistory.present)
  }, [elementsHistory.present])

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

  const zIndexRef = useRef(0)
  zIndexRef.current = elementsHistory.present.length

  const handleAddElementRef = useRef(handleAddElement)
  handleAddElementRef.current = handleAddElement

  useEffect(() => {
    if (!showCanvas) return
    const handler = (e: Event) => {
      const customEvent = e as CustomEvent
      const dataUrl = customEvent.detail
      const newElement: CanvasElement = {
        id: `el_img_${Date.now()}`,
        type: 'image',
        x: 100, y: 100,
        width: 300, height: 200,
        rotation: 0, opacity: 100, zIndex: zIndexRef.current,
        content: dataUrl,
        style: {},
      }
      handleAddElementRef.current(newElement)
    }
    window.addEventListener('image-uploaded', handler)
    return () => window.removeEventListener('image-uploaded', handler)
  }, [showCanvas])

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

  const handleDoubleClickElement = useCallback((_id: string) => {
    setRightPanel('properties')
  }, [])

  const elementsHistoryRef = useRef(elementsHistory)
  elementsHistoryRef.current = elementsHistory

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault()
        if (e.shiftKey) {
          if (canRedoSlides) { redoSlides(); return }
          elementsHistoryRef.current.redo()
        } else {
          if (canUndoSlides && !selectedElement) { undoSlides(); return }
          elementsHistoryRef.current.undo()
        }
      }
      // Ctrl+Shift+↑/↓ 移动幻灯片顺序
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        e.preventDefault()
        if (e.key === 'ArrowUp' && selectedIndex > 0) {
          handleReorder(selectedIndex, selectedIndex - 1)
          setSelectedIndex(selectedIndex - 1)
        } else if (e.key === 'ArrowDown' && selectedIndex < slides.length - 1) {
          handleReorder(selectedIndex, selectedIndex + 1)
          setSelectedIndex(selectedIndex + 1)
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [canUndoSlides, canRedoSlides, undoSlides, redoSlides, selectedElement, slides.length, selectedIndex, handleReorder])

  const handleRegenerate = useCallback(async () => {
    const content = regenerateContent || generationContentRef.current
    if (!content.trim()) return
    setLoading(true)
    setShowRegenerateDialog(false)
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    const regenFetch = createAbortableFetch(abortRef.current.signal)
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
          model: useProjectStore.getState().generationConfig.model || null,
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
      setSlideVersion(v => v + 1)
      generationContentRef.current = content
    } catch (err) {
      console.error('Regeneration failed:', err)
    } finally {
      setLoading(false)
    }
  }, [regenerateContent, searchParams])

  const handleUpdateSlide = useCallback((index: number, updates: Partial<SlideData>) => {
    setSlides(prev => {
      const next = prev.map((s, i) => i === index ? { ...s, ...updates } : s)
      pushSlideHistory(next)
      return next
    })
  }, [pushSlideHistory])

  const handleReorder = useCallback((from: number, to: number) => {
    setSlides(prev => {
      const next = [...prev]
      const [moved] = next.splice(from, 1)
      next.splice(to, 0, moved)
      const renumbered = next.map((s, i) => ({ ...s, page_number: i + 1 }))
      pushSlideHistory(renumbered)
      return renumbered
    })
  }, [pushSlideHistory])

  const handleDeleteSlide = useCallback((index: number) => {
    setSlides(prev => {
      const next = prev.filter((_, i) => i !== index)
      const renumbered = next.map((s, i) => ({ ...s, page_number: i + 1 }))
      pushSlideHistory(renumbered)
      return renumbered
    })
    setSelectedIndex(prev => {
      if (prev >= index) return Math.max(0, prev - 1)
      return prev
    })
  }, [pushSlideHistory])

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
      const renumbered = next.map((s, i) => ({ ...s, page_number: i + 1 }))
      pushSlideHistory(renumbered)
      return renumbered
    })
    setSelectedIndex(afterIndex + 1)
  }, [pushSlideHistory])

  const handlePresent = useCallback(() => {
    if (slides.length === 0) return
    setLastGeneration({
      slides,
      qaResults,
      mode,
      message: modeMessage,
      title: projectTitle,
      content: generationContentRef.current,
      scene: generationSceneRef.current,
    })
    navigate('/presenter')
  }, [slides, navigate, setLastGeneration, qaResults, mode, modeMessage, projectTitle])

  const handleExport = useCallback(async () => {
    if (slides.length === 0 || exporting) return
    setExporting(true)
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    const exportFetch = createAbortableFetch(abortRef.current.signal)
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
            // 添加canvas元素（图片等）
            canvas_elements: (s.elements || []).map(el => ({
              type: el.type,
              x: el.x,
              y: el.y,
              width: el.width,
              height: el.height,
              content: el.content,
              style: el.style,
            })),
          })),
          template: searchParams.get('template') || 'professional-blue',
          canvas_format: useProjectStore.getState().generationConfig.canvasFormat || '16:9',
          project_title: projectTitle || '演示文稿',
        }),
      })
      if (!res.ok) throw new Error(`导出服务异常 (HTTP ${res.status})`)
      const data = await res.json()
      const pptxB64 = data.pptx_base64
      if (pptxB64) {
        downloadBase64(pptxB64, `${projectTitle || '演示文稿'}.pptx`,
          'application/vnd.openxmlformats-officedocument.presentationml.presentation')
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : '导出失败，请重试')
      setTimeout(() => setExportError(''), 5000)
    } finally {
      setExporting(false)
    }
  }, [slides, searchParams, projectTitle])

  const handleExportPdf = useCallback(async () => {
    if (slides.length === 0 || exporting) return
    setExporting(true)
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    const exportFetch = createAbortableFetch(abortRef.current.signal)
    try {
      const svgSlides = slides.map(s => ({
        svg_preview: s.svg_preview || '',
      }))
      const res = await exportFetch(await apiConfig.url('/api/v1/export'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: 'pdf',
          slides: svgSlides,
          titles: slides.map(s => s.title),
          width: 1280,
          height: 720,
        }),
      })
      if (!res.ok) throw new Error(`导出服务异常 (HTTP ${res.status})`)
      const data = await res.json()
      const pdfB64 = data.data_base64
      if (pdfB64) {
        const byteString = atob(pdfB64)
        const ab = new ArrayBuffer(byteString.length)
        const ia = new Uint8Array(ab)
        for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i)
        const blob = new Blob([ab], { type: 'application/pdf' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${projectTitle || '演示文稿'}.pdf`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'PDF 导出失败，请重试')
      setTimeout(() => setExportError(''), 5000)
    } finally {
      setExporting(false)
    }
  }, [slides, projectTitle])

  const handleExportPngs = useCallback(async () => {
    if (slides.length === 0 || exporting) return
    setExporting(true)
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    const exportFetch = createAbortableFetch(abortRef.current.signal)
    try {
      const svgSlides = slides.map(s => ({
        svg_preview: s.svg_preview || '',
      }))
      const res = await exportFetch(await apiConfig.url('/api/v1/export'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: 'pngs',
          slides: svgSlides,
          titles: slides.map(s => s.title),
          width: 1280,
          height: 720,
        }),
      })
      if (!res.ok) throw new Error(`导出服务异常 (HTTP ${res.status})`)
      const data = await res.json()
      const zipB64 = data.data_base64
      if (zipB64) {
        const byteString = atob(zipB64)
        const ab = new ArrayBuffer(byteString.length)
        const ia = new Uint8Array(ab)
        for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i)
        const blob = new Blob([ab], { type: 'application/zip' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${projectTitle || '演示文稿'}_分页PNG.zip`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'PNG 导出失败，请重试')
      setTimeout(() => setExportError(''), 5000)
    } finally {
      setExporting(false)
    }
  }, [slides, projectTitle])

  const handleTTS = useCallback(async () => {
    if (slides.length === 0 || exporting) return
    setExporting(true)
    try {
      const notes = slides.map(s => s.notes || '').filter(n => n.trim())
      if (notes.length === 0) {
        setExportError('没有可用的演讲备注，请先在编辑器中添加备注')
        setTimeout(() => setExportError(''), 5000)
        setExporting(false)
        return
      }
      const res = await fetch(await apiConfig.url('/api/v1/media/tts-narrate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes }),
      })
      if (!res.ok) throw new Error(`TTS 生成失败 (HTTP ${res.status})`)
      const data = await res.json()
      const audioB64 = data.audio_base64
      if (audioB64) {
        const byteString = atob(audioB64)
        const ab = new ArrayBuffer(byteString.length)
        const ia = new Uint8Array(ab)
        for (let i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i)
        const blob = new Blob([ab], { type: 'audio/mp3' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${projectTitle || '旁白'}_旁白.mp3`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'TTS 失败，请重试')
      setTimeout(() => setExportError(''), 5000)
    } finally {
      setExporting(false)
    }
  }, [slides, projectTitle])

  const handleSupplement = useCallback(async () => {
    if (slides.length === 0) return
    setSupplementing(true)
    setShowSupplementDialog(false)
    try {
      let modelId = useProjectStore.getState().generationConfig.model || null
      try {
        const saved = await getObject<{ model?: string; apiKey?: string; baseUrl?: string }[]>('aippt_models')
        if (saved && saved.length > 0) {
          const found = saved.find(m => m.apiKey && m.apiKey !== 'ollama')
          if (found?.model) modelId = found.model
          else if (saved[0]?.model) modelId = saved[0].model
        }
      } catch {}
      const res = await fetch(await apiConfig.url('/api/v1/generate/supplement'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slides: slides.map(s => ({
            layout_type: s.layout_type,
            title: s.title,
            body_items: s.body_items || [],
          })),
          supplement_type: supplementType,
          instruction: supplementInstruction,
          model: modelId,
        }),
      })
      if (!res.ok) throw new Error(`资料补充失败 (HTTP ${res.status})`)
      const data = await res.json()
      const enhanced = data.enhanced_slides || []
      if (enhanced.length > 0) {
        setSlides(prev => prev.map((s, i) => {
          const eSlide = enhanced[i]
          if (!eSlide) return s
          return {
            ...s,
            body_items: eSlide.body_items || s.body_items,
          }
        }))
        setModeMessage(data.message || '资料已补充')
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : '资料补充失败')
      setTimeout(() => setExportError(''), 5000)
    } finally {
      setSupplementing(false)
    }
  }, [slides, supplementType, supplementInstruction])

  const updateNotes = useCallback((notes: string) => {
    handleUpdateSlide(selectedIndex, { notes })
  }, [selectedIndex, handleUpdateSlide])

  const currentSlide = slides[selectedIndex] || null
  const currentElements = elementsHistory.present
  const selectedElData = currentElements.find(e => e.id === selectedElement) || null

  // 方向键微移选中元素
  useEffect(() => {
    if (!selectedElement || !showCanvas) return
    const handler = (e: KeyboardEvent) => {
      const step = e.shiftKey ? 10 : 1
      let dx = 0, dy = 0
      if (e.key === 'ArrowUp') dy = -step
      else if (e.key === 'ArrowDown') dy = step
      else if (e.key === 'ArrowLeft') dx = -step
      else if (e.key === 'ArrowRight') dx = step
      if (dx || dy) {
        e.preventDefault()
        const el = currentElements.find(el => el.id === selectedElement)
        if (el) {
          handleUpdateElement(selectedElement, { x: el.x + dx, y: el.y + dy })
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [selectedElement, showCanvas, currentElements, handleUpdateElement])

  return (
    <div className="flex h-full">
      {/* Left: Slide outline */}
      <aside className="w-56 shrink-0 flex flex-col border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">幻灯片</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${mode === 'ai' || mode === 'online' || mode?.startsWith('ollama') ? 'bg-green-100 text-green-700' : mode === 'transcript' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'}`}
            title={modeMessage}>
            {mode === 'ai' || mode === 'online' ? 'AI' : mode?.startsWith('ollama') ? '本地AI' : mode === 'transcript' ? '会议转写' : mode || '离线'}</span>
        </div>
        <div className="flex-1 overflow-auto p-2">
          <OutlineEditor
            slides={slides}
            selectedIndex={selectedIndex}
            onSelect={(i) => { setSelectedIndex(i); setSelectedElement(null) }}
            onReorder={handleReorder}
            onDelete={handleDeleteSlide}
            onAdd={handleAddSlide}
            onUpdateSlide={handleUpdateSlide}
          />
        </div>
      </aside>

      {/* Center: Canvas */}
      <div className="flex-1 flex flex-col min-w-0 bg-gray-50 dark:bg-gray-800">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-3 py-1 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex items-center space-x-1">
            <button onClick={() => { if (canUndoSlides && !selectedElement) { undoSlides() } else { elementsHistory.undo() } }}
              disabled={!canUndoSlides && !elementsHistory.canUndo}
              className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded disabled:opacity-30" title="撤销 (Ctrl+Z)">
              <Undo2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </button>
            <button onClick={() => { if (canRedoSlides && !selectedElement) { redoSlides() } else { elementsHistory.redo() } }}
              disabled={!canRedoSlides && !elementsHistory.canRedo}
              className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded disabled:opacity-30" title="重做 (Ctrl+Shift+Z)">
              <Redo2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </button>
            <div className="w-px h-5 bg-gray-200 dark:bg-gray-700 mx-1" />
            <button onClick={() => setShowCanvas(!showCanvas)}
              className={`p-1.5 rounded ${showCanvas ? 'bg-gray-100 dark:bg-gray-800' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}`} title="切换画布">
              {showCanvas ? <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" /> : <EyeOff className="w-4 h-4 text-gray-600 dark:text-gray-400" />}
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400 dark:text-gray-500">{slides.length > 0 ? `${selectedIndex + 1} / ${slides.length}` : ''}</span>
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
            <button
              onClick={() => setShowSupplementDialog(true)}
              disabled={supplementing || slides.length === 0}
              className="btn-secondary text-xs px-2 py-1 flex items-center space-x-1"
              title="AI 补充数据、案例、流程等内容"
            >
              {supplementing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Database className="w-3 h-3" />}
              <span>{supplementing ? '补充中...' : '资料补充'}</span>
            </button>
            <button onClick={handleExport} disabled={exporting || slides.length === 0} className="btn-primary text-xs px-2 py-1 flex items-center space-x-1 disabled:opacity-50">
              {exporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
              <span>{exporting ? '导出中...' : '导出 PPTX'}</span>
            </button>
            <button onClick={handleExportPdf} disabled={exporting || slides.length === 0} className="btn-secondary text-xs px-2 py-1 flex items-center space-x-1 disabled:opacity-30">
              <FileOutput className="w-3 h-3" /><span>导出 PDF</span>
            </button>
            <button onClick={handleExportPngs} disabled={exporting || slides.length === 0} className="btn-secondary text-xs px-2 py-1 flex items-center space-x-1 disabled:opacity-30">
              <Image className="w-3 h-3" /><span>导出 PNG</span>
            </button>
            <button onClick={handleTTS} disabled={exporting || slides.length === 0} className="btn-secondary text-xs px-2 py-1 flex items-center space-x-1 disabled:opacity-30" title="为演讲备注生成语音旁白">
              <Mic className="w-3 h-3" /><span>旁白</span>
            </button>
            <button onClick={handlePresent} disabled={slides.length === 0}
              className="btn-secondary text-xs px-2 py-1 flex items-center space-x-1 disabled:opacity-30">
              <Presentation className="w-3 h-3" />              <span>演示</span>
            </button>
          </div>
          {exportError && (
            <div className="mt-2 text-xs text-red-500 bg-red-50 border border-red-200 rounded px-2 py-1">
              {exportError}
            </div>
          )}
        </div>

        {showCanvas && <ElementToolbar />}

        {/* Canvas area */}
        <div className="flex-1 flex">
          {showCanvas ? (
            <CanvasEditor
              slide={currentSlide}
              elements={currentElements}
              selectedElement={selectedElement}
              scale={canvasScale}
              onSelectElement={setSelectedElement}
              onUpdateElement={handleUpdateElement}
              onAddElement={handleAddElement}
              onDeleteElement={handleDeleteElement}
              onElementsChange={handleElementsChange}
              onDoubleClickElement={handleDoubleClickElement}
              onScaleChange={setCanvasScale}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-100 p-4">
              <SlidePreview
                svgContent={currentSlide?.svg_preview}
                title={currentSlide?.title}
                subtitle={currentSlide?.subtitle}
                layoutType={currentSlide?.layout_type}
                className="shadow-lg"
              />
            </div>
          )}
        </div>
      </div>

      {/* Right: Properties / Notes / QA */}
      <aside className="w-64 shrink-0 flex flex-col border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex border-b border-gray-200 dark:border-gray-700">
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
                  {['cover','toc','chapter','content','content_two_col','content_three_col','content_table','content_code','content_quote','content_compare','content_kpi','content_matrix','content_timeline','content_waterfall','content_gauge','content_ranking','content_funnel','ending'].map(lt => (
                    <option key={lt} value={lt}>{lt === 'cover' ? '封面' : lt === 'chapter' ? '章节' : lt === 'content' ? '内容' : lt === 'content_two_col' ? '双栏' : lt === 'content_three_col' ? '三栏' : lt === 'content_table' ? '表格' : lt === 'content_code' ? '代码' : lt === 'content_quote' ? '引用' : lt === 'content_compare' ? '对比' : lt === 'content_kpi' ? 'KPI' : lt === 'content_matrix' ? '矩阵' : lt === 'content_timeline' ? '时间轴' : lt === 'content_waterfall' ? '瀑布' : lt === 'content_gauge' ? '仪表盘' : lt === 'content_ranking' ? '排行' : lt === 'content_funnel' ? '漏斗' : lt === 'ending' ? '结尾' : lt === 'toc' ? '目录' : lt.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>
              {currentSlide.body_items.length > 0 && (
                <div>
                  <label className="text-xs text-gray-500 block mb-1">
                    正文内容 ({currentSlide.body_items.length} 项 · 点击编辑)
                  </label>
                  <div className="max-h-64 overflow-auto space-y-1">
                    {currentSlide.body_items.map((item, i) => (
                      <div key={i} className="flex items-start gap-1">
                        <span className="text-gray-300 mt-1.5 shrink-0 text-[10px]">
                          {item.type === 'list_item' ? '•' : '¶'}
                        </span>
                        <textarea
                          className="flex-1 text-[11px] p-1.5 bg-gray-50 border border-gray-200 rounded resize-none min-h-[28px] focus:outline-none focus:ring-1 focus:ring-primary-300 focus:bg-white"
                          value={item.text}
                          rows={1}
                          onChange={(e) => {
                            const newItems = [...currentSlide.body_items]
                            newItems[i] = { ...newItems[i], text: e.target.value }
                            handleUpdateSlide(selectedIndex, { body_items: newItems })
                          }}
                        />
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

      {showSupplementDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">AI 资料补充</h3>
              <button onClick={() => setShowSupplementDialog(false)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <p className="text-xs text-gray-500">AI 将保留原有内容，在此基础上补充数据、案例、流程或对比分析。补充项将以【补充】标记。</p>

            <div>
              <label className="text-sm font-medium text-gray-600 block mb-2">补充类型</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'auto', label: '智能综合', desc: '自动判断缺什么补什么' },
                  { id: 'data', label: '补充数据', desc: '添加指标、数字、统计' },
                  { id: 'case', label: '补充案例', desc: '添加业务场景和实例' },
                  { id: 'process', label: '补充流程', desc: '添加步骤、时间节点' },
                  { id: 'compare', label: '补充对比', desc: '添加同比/环比/对标' },
                  { id: 'custom', label: '自定义', desc: '自行描述补充需求' },
                ].map(t => (
                  <button key={t.id} onClick={() => setSupplementType(t.id)}
                    className={`p-2.5 rounded-lg border-2 text-left transition-all ${
                      supplementType === t.id ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
                    }`}>
                    <div className={`text-xs font-medium ${supplementType === t.id ? 'text-primary-700' : 'text-gray-700'}`}>{t.label}</div>
                    <div className="text-[10px] text-gray-400 mt-0.5">{t.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {supplementType === 'custom' && (
              <div>
                <label className="text-sm font-medium text-gray-600 block mb-1">自定义指令</label>
                <textarea className="input-field min-h-[80px] resize-y text-xs" value={supplementInstruction}
                  onChange={(e) => setSupplementInstruction(e.target.value)}
                  placeholder="例如：为每页补充近3年的趋势数据，加上行业平均水平做对比..." />
              </div>
            )}

            <div className="flex justify-between items-center text-xs text-gray-400">
              <span>将增强 {slides.length} 页幻灯片</span>
              <span>原有内容不会被删除</span>
            </div>

            <div className="flex justify-end space-x-3">
              <button onClick={() => setShowSupplementDialog(false)} className="btn-secondary text-sm px-4 py-2">取消</button>
              <button onClick={handleSupplement} disabled={supplementing}
                className="btn-primary text-sm px-4 py-2 flex items-center space-x-2 disabled:opacity-50">
                {supplementing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
                <span>{supplementing ? 'AI 补充中...' : '开始补充'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronLeft, ChevronRight, X,
  Clock, Mic, FileText, Maximize2, Video, Square
} from 'lucide-react'
import type { SlideData } from '@/types'
import { useProjectStore } from '@/stores/projectStore'

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export function Presenter() {
  const navigate = useNavigate()
  const [slides, setSlides] = useState<SlideData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showNotes, setShowNotes] = useState(true)
  const [elapsed, setElapsed] = useState(0)
  const [timerRunning, setTimerRunning] = useState(true)
  const [speakerView, setSpeakerView] = useState(false)
  const [showThumbnails, setShowThumbnails] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [recording, setRecording] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const cameraStreamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    const generation = useProjectStore.getState().lastGeneration
    if (generation?.slides && generation.slides.length > 0) {
      setSlides(generation.slides)
      try {
        sessionStorage.setItem('presenter_slides', JSON.stringify(generation.slides))
      } catch {}
      return
    }
    try {
      const stored = sessionStorage.getItem('presenter_slides')
      if (stored) {
        setSlides(JSON.parse(stored))
        return
      }
    } catch {}
  }, [])

  useEffect(() => {
    if (timerRunning) {
      timerRef.current = setInterval(() => {
        setElapsed(t => t + 1)
      }, 1000)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [timerRunning])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
        e.preventDefault()
        setCurrentIndex(i => Math.min(slides.length - 1, i + 1))
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault()
        setCurrentIndex(i => Math.max(0, i - 1))
      } else if (e.key === 'Escape') {
        if (showThumbnails) {
          setShowThumbnails(false)
        } else {
          exitPresenter()
        }
      } else if (e.key === 'g' || e.key === 'G') {
        setShowThumbnails(v => !v)
      } else if (e.key === 'n' || e.key === 'N') {
        setShowNotes(s => !s)
      } else if (e.key === 'f' || e.key === 'F') {
        toggleFullscreen()
      } else if (e.key === 't' || e.key === 'T') {
        setTimerRunning(r => !r)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [slides.length])

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }, [])

  const exitPresenter = useCallback(() => {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
    navigate(-1)
  }, [navigate])

  const startRecording = useCallback(async () => {
    try {
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: { displaySurface: 'browser' },
        audio: true,
      })
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
      let combined = displayStream
      try {
        const camStream = await navigator.mediaDevices.getUserMedia({ video: { width: 200, height: 150 }, audio: false })
        cameraStreamRef.current = camStream
        const dest = ctx.createMediaStreamDestination()
        displayStream.getAudioTracks().forEach(t => {
          const src = ctx.createMediaStreamSource(new MediaStream([t]))
          src.connect(dest)
        })
        const camTrack = camStream.getVideoTracks()[0]
        if (camTrack) combined = new MediaStream([...displayStream.getVideoTracks(), camTrack, ...dest.stream.getAudioTracks()])
      } catch { /* no camera */ }
      const recorder = new MediaRecorder(combined, { mimeType: 'video/webm' })
      chunksRef.current = []
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url; a.download = `演示录制_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.webm`
        a.click(); URL.revokeObjectURL(url)
        displayStream.getTracks().forEach(t => t.stop())
        if (cameraStreamRef.current) cameraStreamRef.current.getTracks().forEach(t => t.stop())
        ctx.close().catch(() => {})
      }
      recorder.start()
      mediaRecorderRef.current = recorder
      setRecording(true)
    } catch (err) {
      console.error('录制失败:', err)
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
      setRecording(false)
    }
  }, [])

  const currentSlide = slides[currentIndex]
  const nextSlide = slides[currentIndex + 1]

  if (!slides.length) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-900 text-white">
        <p className="text-lg">没有幻灯片可演示。<button onClick={exitPresenter} className="underline text-blue-400">返回</button></p>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-black text-white">
      {/* Presenter toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700 shrink-0">
        <div className="flex items-center space-x-4">
          <button onClick={exitPresenter} className="p-1.5 hover:bg-gray-700 rounded" title="退出 (Esc)">
            <X className="w-4 h-4" />
          </button>
          <span className="text-sm text-gray-400">第 {currentIndex + 1} / {slides.length} 页</span>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 text-sm">
            <Clock className="w-3.5 h-3.5 text-gray-400" />
            <span className={`font-mono ${elapsed > 600 ? 'text-yellow-400' : 'text-gray-300'}`}>
              {formatTime(elapsed)}
            </span>
            <button onClick={() => setTimerRunning(r => !r)} className="ml-1 text-xs text-gray-500 hover:text-white">
              {timerRunning ? '暂停' : '继续'}
            </button>
          </div>
          {recording ? (
            <button onClick={stopRecording} className="flex items-center space-x-1 px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-xs font-medium animate-pulse" title="停止录制">
              <Square className="w-3 h-3 fill-current" /><span>停止</span>
            </button>
          ) : (
            <button onClick={startRecording} className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700 text-xs text-gray-400" title="录制演示 (含音频+摄像头)">
              <Video className="w-3.5 h-3.5" /><span>录制</span>
            </button>
          )}
          <button onClick={() => setShowNotes(s => !s)} className={`p-1.5 rounded ${showNotes ? 'bg-blue-600' : 'hover:bg-gray-700'}`} title="切换备注 (N)">
            <FileText className="w-4 h-4" />
          </button>
          <button onClick={() => setSpeakerView(v => !v)} className={`p-1.5 rounded text-xs ${speakerView ? 'bg-green-600' : 'hover:bg-gray-700 text-gray-400'}`} title="演讲者视图（双屏）">
            <Mic className="w-4 h-4" />
          </button>
          <button onClick={toggleFullscreen} className="p-1.5 hover:bg-gray-700 rounded" title="全屏 (F)">
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main presenter area */}
      <div className={`flex-1 flex overflow-hidden ${speakerView ? 'flex-col' : ''}`}>
        {speakerView ? (
          /* 演讲者视图：上半=幻灯片，下半=备注+计时器+下一页 */
          <>
            <div className="flex-1 flex items-center justify-center bg-gray-800 p-2 relative min-h-0">
              <div className="h-full flex items-center justify-center" style={{ aspectRatio: '16/9' }}>
                {currentSlide?.svg_preview ? (
                  <iframe srcDoc={currentSlide.svg_preview} className="w-full h-full rounded shadow-xl" style={{ border: 'none', pointerEvents: 'none' }} title={`第 ${currentIndex + 1} 页`} sandbox="allow-same-origin" />
                ) : (
                  <div className="text-center text-gray-500"><p className="text-4xl font-bold mb-2">{currentSlide?.title || '幻灯片'}</p></div>
                )}
              </div>
            </div>
            <div className="h-48 bg-gray-900 border-t border-gray-700 flex divide-x divide-gray-700 shrink-0">
              <div className="flex-1 p-4 overflow-auto">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">演讲备注</span>
                  <span className="text-xs text-gray-500">{currentIndex + 1}/{slides.length}</span>
                </div>
                <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{currentSlide?.notes || '此页暂无备注'}</p>
              </div>
              <div className="w-64 p-4 flex flex-col items-center justify-center space-y-3 shrink-0">
                <Clock className="w-6 h-6 text-gray-400" />
                <span className={`text-3xl font-mono font-bold ${elapsed > 600 ? 'text-yellow-400' : 'text-white'}`}>{formatTime(elapsed)}</span>
                <button onClick={() => setTimerRunning(r => !r)} className="text-xs text-gray-500 hover:text-white">{timerRunning ? '⏸ 暂停' : '▶ 继续'}</button>
                {nextSlide && (
                  <div className="w-full mt-2">
                    <span className="text-[10px] text-gray-500">下一页</span>
                    <div className="text-xs text-gray-300 mt-0.5 truncate">{nextSlide.title}</div>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          /* 普通演示视图 */
          <>
          <button
            onClick={() => setCurrentIndex(i => Math.max(0, i - 1))}
            disabled={currentIndex === 0}
            className="absolute left-2 p-2 bg-black/30 hover:bg-black/50 rounded-full disabled:opacity-20 z-10"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>

          <div className="w-full h-full max-w-[calc(100vh*16/9)] max-h-full flex items-center justify-center">
            {currentSlide?.svg_preview ? (
              <iframe
                srcDoc={currentSlide.svg_preview}
                className="w-full h-full rounded shadow-2xl"
                style={{ border: 'none', pointerEvents: 'none' }}
                title={`第 ${currentIndex + 1} 页`}
                sandbox="allow-same-origin"
              />
            ) : (
              <div className="text-center text-gray-500">
                <p className="text-4xl font-bold mb-2">{currentSlide?.title || '幻灯片'}</p>
                {currentSlide?.subtitle && <p className="text-xl text-gray-400">{currentSlide.subtitle}</p>}
              </div>
            )}
          </div>

          <button
            onClick={() => setCurrentIndex(i => Math.min(slides.length - 1, i + 1))}
            disabled={currentIndex >= slides.length - 1}
            className="absolute right-2 p-2 bg-black/30 hover:bg-black/50 rounded-full disabled:opacity-20 z-10"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        </div>

        {/* Notes panel (right side) */}
        {showNotes && (
          <div className="w-96 bg-gray-900 border-l border-gray-700 flex flex-col">
            {/* Current slide notes */}
            <div className="flex-1 p-4 overflow-auto">
              <div className="flex items-center space-x-2 mb-3 text-sm text-gray-400">
                <Mic className="w-4 h-4" />
                <span>演讲备注</span>
              </div>
              <p className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
                {currentSlide?.notes || '此页暂无备注'}
              </p>
            </div>

            {/* Next slide preview */}
            {nextSlide && (
              <div className="p-4 border-t border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">下一页: 第 {currentIndex + 2} 页</span>
                </div>
                <div className="h-28 bg-gray-800 rounded-lg overflow-hidden">
                  {nextSlide.svg_preview ? (
                    <iframe
                      srcDoc={nextSlide.svg_preview}
                      className="w-full h-full opacity-70"
                      style={{ border: 'none', pointerEvents: 'none', transform: 'scale(0.5)', transformOrigin: 'top left' }}
                      title={`第 ${currentIndex + 2} 页`}
                      sandbox="allow-same-origin"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500 text-xs">
                      {nextSlide.title || '下一页'}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-700">
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / slides.length) * 100}%` }}
        />
      </div>

      {/* 缩略图索引 (ESC/G键) */}
      {showThumbnails && (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col" onClick={() => setShowThumbnails(false)}>
          <div className="flex items-center justify-between px-6 py-3 bg-gray-900 shrink-0">
            <span className="text-sm text-gray-400">所有幻灯片 · 点击跳转 · 按G或ESC关闭</span>
            <span className="text-xs text-gray-500">{slides.length} 页</span>
          </div>
          <div className="flex-1 overflow-auto p-6">
            <div className="grid grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4 max-w-7xl mx-auto">
              {slides.map((s, i) => (
                <div
                  key={i}
                  onClick={(e) => { e.stopPropagation(); setCurrentIndex(i); setShowThumbnails(false) }}
                  className={`cursor-pointer rounded-lg overflow-hidden border-2 transition-all hover:scale-105 ${
                    i === currentIndex ? 'border-blue-500 ring-2 ring-blue-400 shadow-lg' : 'border-gray-700 hover:border-gray-400'
                  }`}
                >
                  <div className="bg-gray-800 aspect-video flex items-center justify-center overflow-hidden">
                    {s.svg_preview ? (
                      <iframe srcDoc={s.svg_preview} className="w-full h-full pointer-events-none" style={{ border: 'none', transform: 'scale(0.3)', transformOrigin: 'top left', width: '333%', height: '333%' }} title={`缩略图 ${i + 1}`} sandbox="allow-same-origin" />
                    ) : (
                      <span className="text-gray-600 text-xs">{s.title || `第${i + 1}页`}</span>
                    )}
                  </div>
                  <div className="px-2 py-1.5 bg-gray-900">
                    <div className="text-[10px] text-gray-400 truncate">{i + 1}. {s.title || '无标题'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronLeft, ChevronRight, X, Monitor, Settings2,
  Clock, Mic, FileText, Maximize2, Minimize2
} from 'lucide-react'
import type { SlideData } from '@/types'

const BACKEND_URL = 'http://127.0.0.1:8099'

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export function Presenter() {
  const navigate = useNavigate()
  const [slides, setSlides] = useState<SlideData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(true)
  const [showNotes, setShowNotes] = useState(true)
  const [elapsed, setElapsed] = useState(0)
  const [timerRunning, setTimerRunning] = useState(true)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const data = sessionStorage.getItem('presenter_slides')
    if (data) {
      try {
        setSlides(JSON.parse(data))
      } catch { /* ignore */ }
    }
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
        exitPresenter()
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
      setIsFullscreen(true)
    } else {
      document.exitFullscreen().catch(() => {})
      setIsFullscreen(false)
    }
  }, [])

  const exitPresenter = useCallback(() => {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
    navigate(-1)
  }, [navigate])

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
          <button onClick={() => setShowNotes(s => !s)} className={`p-1.5 rounded ${showNotes ? 'bg-blue-600' : 'hover:bg-gray-700'}`} title="切换备注 (N)">
            <FileText className="w-4 h-4" />
          </button>
          <button onClick={toggleFullscreen} className="p-1.5 hover:bg-gray-700 rounded" title="全屏 (F)">
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main presenter area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Current slide */}
        <div className="flex-1 flex items-center justify-center bg-gray-800 p-4 relative">
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
    </div>
  )
}

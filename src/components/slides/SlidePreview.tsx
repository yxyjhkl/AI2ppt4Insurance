import { useMemo } from 'react'

interface SlidePreviewProps {
  svgContent?: string
  title?: string
  subtitle?: string | null
  layoutType?: string
  className?: string
  width?: number
}

export function SlidePreview({ svgContent, title, subtitle, layoutType, className = '', width = 960 }: SlidePreviewProps) {
  const aspectRatio = useMemo(() => {
    if (!svgContent) return 16 / 9
    const match = svgContent.match(/viewBox="0 0 (\d+) (\d+)"/)
    if (match) {
      const [, w, h] = match.map(Number)
      return w / h
    }
    return 16 / 9
  }, [svgContent])

  const height = Math.round(width / aspectRatio)

  if (svgContent) {
    return (
      <div
        className={`bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden ${className}`}
        style={{ width, height }}
      >
        <iframe
          srcDoc={svgContent}
          className="w-full h-full"
          title={`幻灯片预览 - ${title || ''}`}
          sandbox="allow-same-origin"
          style={{ border: 'none' }}
        />
      </div>
    )
  }

  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 shadow-sm flex flex-col items-center justify-center ${className}`}
      style={{ width, height }}
    >
      <div className="text-center px-8">
        <p className="text-lg font-semibold text-gray-700">{title || '无内容'}</p>
        {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
        {layoutType && (
          <span className="inline-block mt-2 px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
            {layoutType.replace(/_/g, ' ')}
          </span>
        )}
      </div>
    </div>
  )
}

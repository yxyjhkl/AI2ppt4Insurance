import { Mic, FileText } from 'lucide-react'
import type { SlideData } from '@/types'

interface SpeakerNotesProps {
  slide: SlideData | null
  onUpdateNotes: (notes: string) => void
}

export function SpeakerNotes({ slide, onUpdateNotes }: SpeakerNotesProps) {
  if (!slide) {
    return (
      <div className="p-4 text-center text-gray-400 text-sm">
        <Mic className="w-6 h-6 mx-auto mb-2 opacity-50" />
        选中幻灯片以编辑演讲备注
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Mic className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">演讲备注</span>
        </div>
        <span className="text-xs text-gray-400">第 {slide.page_number} 页</span>
      </div>

      <textarea
        value={slide.notes || ''}
        onChange={(e) => onUpdateNotes(e.target.value)}
        placeholder="在此输入演讲备注..."
        className="w-full min-h-[120px] p-3 text-sm border border-gray-200 rounded-lg resize-y focus:outline-none focus:ring-1 focus:ring-primary-400"
      />

      {slide.notes && (
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
          <div className="flex items-center space-x-1.5 mb-2">
            <FileText className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-xs font-medium text-blue-700">预览</span>
          </div>
          <p className="text-xs text-blue-800 leading-relaxed whitespace-pre-wrap">
            {slide.notes}
          </p>
        </div>
      )}
    </div>
  )
}
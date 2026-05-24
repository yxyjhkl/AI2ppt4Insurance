import { useState } from 'react'
import type { InsuranceMeetingType } from '@/types'
import { INSURANCE_MEETING_LABELS, INSURANCE_MEETING_DESC, INSURANCE_MEETING_PROMPTS } from '@/types'

export function InsuranceMeetingSelector({
  meetingType,
  onSelect,
}: {
  meetingType: InsuranceMeetingType
  onSelect: (mt: InsuranceMeetingType) => void
}) {
  const [hoveredMt, setHoveredMt] = useState<InsuranceMeetingType | null>(null)

  return (
    <section className="card p-6 space-y-4">
      <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">1B. 选择会议类型</h2>
      <p className="text-sm text-gray-500">请选择保险行业会议类型，系统将使用对应的专业模板和提示词：</p>
      <div className="grid grid-cols-2 gap-3">
        {(Object.keys(INSURANCE_MEETING_LABELS) as InsuranceMeetingType[]).map((mt) => {
          const info = INSURANCE_MEETING_PROMPTS[mt]
          const isHovered = hoveredMt === mt
          return (
            <button
              key={mt}
              onClick={() => onSelect(mt)}
              onMouseEnter={() => setHoveredMt(mt)}
              onMouseLeave={() => setHoveredMt(null)}
              className={`relative p-3 rounded-lg border-2 text-left transition-all ${
                meetingType === mt
                  ? 'border-amber-500 bg-amber-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className={`text-sm font-medium ${meetingType === mt ? 'text-amber-700' : 'text-gray-700'}`}>
                {INSURANCE_MEETING_LABELS[mt]}
              </div>
              <div className="text-xs text-gray-400 mt-0.5">{INSURANCE_MEETING_DESC[mt]}</div>

              {isHovered && info && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 w-80 p-3 rounded-lg bg-gray-900 text-white shadow-xl text-left animate-in slide-in-from-bottom-2 duration-150 pointer-events-none">
                  <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-700">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-medium">AI 角色</span>
                    <span className="text-xs text-gray-300">{info.role}</span>
                  </div>
                  <div className="flex items-start gap-2 mb-2">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-medium shrink-0 mt-0.5">任务</span>
                    <span className="text-xs text-gray-300 leading-relaxed">{info.task}</span>
                  </div>
                  <div className="flex items-start gap-2 mb-2">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-green-500/20 text-green-300 font-medium shrink-0 mt-0.5">结构</span>
                    <span className="text-xs text-gray-300 leading-relaxed">{info.structure}</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-medium shrink-0 mt-0.5">设计</span>
                    <span className="text-xs text-gray-300 leading-relaxed">{info.design}</span>
                  </div>
                  <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-gray-900 rotate-45" />
                </div>
              )}
            </button>
          )
        })}
      </div>
    </section>
  )
}

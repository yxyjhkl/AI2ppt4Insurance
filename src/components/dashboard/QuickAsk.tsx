import { useState } from 'react'
import { X, ArrowRight, Sparkles } from 'lucide-react'

interface QuickAskProps {
  onComplete: (answers: QuickAnswers) => void
  onSkip: () => void
}

export interface QuickAnswers {
  audience: string
  duration: string
  tone: string
  focus: string
}

const QUESTIONS = [
  {
    id: 'audience' as const,
    question: '听众是谁？',
    subtitle: '了解听众背景，AI会调整内容深度和语言风格',
    options: [
      { value: 'executives', label: '管理层/决策者', icon: '👔' },
      { value: 'team', label: '团队成员/同事', icon: '👥' },
      { value: 'clients', label: '客户/外部伙伴', icon: '🤝' },
      { value: 'general', label: '混合听众/不确定', icon: '🎯' },
    ],
  },
  {
    id: 'duration' as const,
    question: '预计演示时长？',
    subtitle: '帮助AI控制页数和内容密度',
    options: [
      { value: '5min', label: '5分钟（闪电讲）', icon: '⚡' },
      { value: '15min', label: '10-15分钟（标准）', icon: '⏱' },
      { value: '30min', label: '20-30分钟（深度）', icon: '📊' },
      { value: '60min', label: '45-60分钟（完整）', icon: '🎙' },
    ],
  },
  {
    id: 'tone' as const,
    question: '期望的风格基调？',
    subtitle: 'AI会据此调整措辞和视觉风格',
    options: [
      { value: 'professional', label: '严谨专业', icon: '💼' },
      { value: 'motivating', label: '激励动员', icon: '🔥' },
      { value: 'warm', label: '温暖亲和', icon: '🌸' },
      { value: 'modern', label: '现代简洁', icon: '✨' },
    ],
  },
  {
    id: 'focus' as const,
    question: '最重要的关注点？',
    subtitle: 'AI会在生成时重点突出这个方向',
    options: [
      { value: 'data', label: '数据与分析', icon: '📈' },
      { value: 'story', label: '故事与案例', icon: '📖' },
      { value: 'action', label: '行动与决策', icon: '🎯' },
      { value: 'vision', label: '愿景与方向', icon: '🔭' },
    ],
  },
]

export function QuickAsk({ onComplete, onSkip }: QuickAskProps) {
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<QuickAnswers>({
    audience: '', duration: '', tone: '', focus: '',
  })
  const [animating, setAnimating] = useState(false)

  const current = QUESTIONS[step]
  const isLast = step === QUESTIONS.length - 1

  const handleSelect = (value: string) => {
    setAnswers(prev => ({ ...prev, [current.id]: value }))
    if (isLast) {
      setAnimating(true)
      setTimeout(() => onComplete(answers), 400)
    } else {
      setAnimating(true)
      setTimeout(() => {
        setStep(s => s + 1)
        setAnimating(false)
      }, 250)
    }
  }

  return (
    <div className={`card p-6 border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/10 transition-all duration-300 ${animating ? 'opacity-0 scale-95' : 'opacity-100'}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-500" />
          <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">
            快速了解你的需求（{step + 1}/{QUESTIONS.length}）
          </span>
        </div>
        <button onClick={onSkip} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
          跳过 <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {/* 进度条 */}
      <div className="flex gap-1 mb-5">
        {QUESTIONS.map((_, i) => (
          <div key={i} className={`h-1 flex-1 rounded-full transition-all ${i < step ? 'bg-blue-500' : i === step ? 'bg-blue-300' : 'bg-gray-200'}`} />
        ))}
      </div>

      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-1">{current.question}</h3>
      <p className="text-xs text-gray-500 mb-4">{current.subtitle}</p>

      <div className="grid grid-cols-2 gap-2">
        {current.options.map(opt => {
          const isSelected = (answers as any)[current.id] === opt.value
          return (
            <button
              key={opt.value}
              onClick={() => handleSelect(opt.value)}
              className={`flex items-center gap-3 p-3 rounded-xl border-2 text-left transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 shadow-sm'
                  : 'border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-500'
              }`}
            >
              <span className="text-2xl">{opt.icon}</span>
              <span className={`text-sm font-medium ${isSelected ? 'text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}>
                {opt.label}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

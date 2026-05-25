import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Loader2, X } from 'lucide-react'
import { apiConfig } from '@/utils/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  slides: any[]
  onSlidesUpdate: (slides: any[]) => void
  onClose: () => void
}

export function ChatEditor({ slides, onSlidesUpdate, onClose }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好！我是PPT编辑助手。你可以用自然语言告诉我怎么修改幻灯片，比如：\n• "把第3页标题改成Q2目标"\n• "第5页换成表格布局"\n• "整体风格更活泼一点"\n• "在第2页加一张数据对比图"' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const res = await fetch(await apiConfig.url('/api/v1/ai/chat-edit'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instruction: userMsg,
          slides: slides.map((s: any) => ({
            page_number: s.page_number,
            layout_type: s.layout_type,
            title: s.title,
            body_items: s.body_items || [],
            notes: s.notes || '',
          })),
        }),
      })

      if (res.ok) {
        const data = await res.json()
        const reply = data.reply || '已完成修改'
        setMessages(prev => [...prev, { role: 'assistant', content: reply }])
        if (data.updated_slides && data.updated_slides.length > 0) {
          onSlidesUpdate(data.updated_slides)
        }
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，修改失败，请重试或换个说法。' }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '网络错误，请检查后端连接后重试。' }])
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    '标题加数据', '换成表格布局', '风格活泼一点', '补充案例', '精简内容',
  ]

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col" style={{ maxHeight: '500px' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-500" />
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">AI 编辑助手</span>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded">
          <X className="w-4 h-4 text-gray-400" />
        </button>
      </div>

      {/* Messages */}
      <div ref={chatRef} className="flex-1 overflow-auto px-4 py-3 space-y-3 min-h-0">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
              msg.role === 'user'
                ? 'bg-blue-500 text-white rounded-br-sm'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-bl-sm'
            }`} style={{ whiteSpace: 'pre-wrap' }}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 text-xs text-gray-400 flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" /> 正在修改...
            </div>
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="px-4 py-2 flex gap-1.5 overflow-x-auto border-t border-gray-100 dark:border-gray-700 shrink-0">
        {quickActions.map(action => (
          <button
            key={action}
            onClick={() => setInput(action)}
            className="text-[10px] px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-blue-900 dark:hover:text-blue-400 whitespace-nowrap transition-colors shrink-0"
          >
            {action}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-4 py-3 border-t border-gray-100 dark:border-gray-700 shrink-0">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="告诉我怎么修改..."
          className="flex-1 text-xs px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="p-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-40 transition-colors"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}

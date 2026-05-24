import { useState } from 'react'
import { Check, Sparkles } from 'lucide-react'
import { promptCategories } from '@/data/prompts'

export function PromptSelector({
  selectedPrompt,
  onSelectPrompt,
}: {
  selectedPrompt: string | null
  onSelectPrompt: (prompt: string | null) => void
}) {
  const [useCustomPrompt, setUseCustomPrompt] = useState<boolean | null>(null)
  const [promptCategory, setPromptCategory] = useState('report')

  return (
    <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
      <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">4. 选择提示词（可选）</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">是否需要自己选择提示词？不选择将使用默认生成策略。</p>
      <div className="flex space-x-3">
        <button onClick={() => { setUseCustomPrompt(false); onSelectPrompt(null) }}
          className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
            useCustomPrompt === false
              ? 'border-primary-500 bg-primary-50 text-primary-700'
              : 'border-gray-200 text-gray-500 hover:border-gray-300'
          }`}>
          <Check className="w-4 h-4 mr-1.5" />
          使用默认策略
        </button>
        <button onClick={() => setUseCustomPrompt(true)}
          className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
            useCustomPrompt === true
              ? 'border-primary-500 bg-primary-50 text-primary-700'
              : 'border-gray-200 text-gray-500 hover:border-gray-300'
          }`}>
          <Sparkles className="w-4 h-4 mr-1.5" />
          自己选择提示词
        </button>
      </div>

      {useCustomPrompt && (
        <div className="pt-3 space-y-3 border-t border-gray-100">
          <div className="flex space-x-1 border-b border-gray-200">
            {promptCategories.map((cat) => (
              <button key={cat.id} onClick={() => setPromptCategory(cat.id)}
                className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                  promptCategory === cat.id
                    ? 'border-primary-600 text-primary-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}>
                {cat.label}
              </button>
            ))}
          </div>
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {(promptCategories.find((c) => c.id === promptCategory)?.prompts || []).map((prompt, i) => (
              <div key={i} onClick={() => onSelectPrompt(prompt.content)}
                className={`card p-3 cursor-pointer border-2 transition-colors ${
                  selectedPrompt === prompt.content
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-transparent hover:border-gray-200'
                }`}>
                <div className="flex items-center space-x-2 mb-1">
                  <Sparkles className="w-3.5 h-3.5 text-yellow-500" />
                  <h4 className="text-sm font-semibold text-gray-700">{prompt.title}</h4>
                  {selectedPrompt === prompt.content && (
                    <span className="px-1.5 py-0.5 bg-primary-600 text-white text-xs rounded-full">已选</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 leading-relaxed">{prompt.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

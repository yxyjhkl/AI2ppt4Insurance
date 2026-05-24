import { Loader2, Sparkles, List, Rocket } from 'lucide-react'
import { useProjectStore } from '@/stores/projectStore'

export function GenerateBar({
  generating, inputText, error,
  onGenerate, onGenerateOutline, outlineGenerating, autoMode,
}: {
  generating: boolean
  inputText: string
  error: string
  onGenerate: () => void
  onGenerateOutline?: () => void
  outlineGenerating?: boolean
  autoMode?: boolean
}) {
  const slideCount = useProjectStore((s) => s.generationConfig.slideCount)

  // AI替我做模式 - 极简布局
  if (autoMode) {
    return (
      <div className="flex flex-col items-center justify-center py-6 space-y-4">
        {error && (
          <div className="w-full text-center text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">
            {error}
          </div>
        )}
        <button
          onClick={onGenerate}
          disabled={generating || !inputText.trim()}
          className="w-full max-w-md bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center space-x-3 text-lg"
        >
          {generating ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              <span>AI 正在为您生成精美 PPT...</span>
            </>
          ) : (
            <>
              <Rocket className="w-6 h-6" />
              <span>🚀 一键生成精美 PPT</span>
            </>
          )}
        </button>
        {!generating && !inputText.trim() && (
          <p className="text-sm text-gray-400">请上传文档或输入内容</p>
        )}
        {generating && (
          <p className="text-sm text-blue-500 animate-pulse">正在分析材料、自动排版、生成精美演示文稿...</p>
        )}
      </div>
    )
  }

  // 完整模式 - 保留所有选项
  return (
    <section className="flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <label className="text-sm text-gray-600">幻灯片数量:</label>
        <input type="range" min="5" max="30"
          value={slideCount}
          onChange={(e) => useProjectStore.getState().updateGenerationConfig({ slideCount: parseInt(e.target.value) })}
          className="w-32" />
        <span className="text-sm text-gray-700">{slideCount}</span>
      </div>
      <div className="flex items-center space-x-3">
        {error && <span className="text-sm text-red-500">{error}</span>}
        {onGenerateOutline && (
          <button onClick={onGenerateOutline} disabled={generating || outlineGenerating || !inputText.trim()}
            className="btn-secondary text-xs px-3 py-1.5 flex items-center space-x-1.5 disabled:opacity-50">
            {outlineGenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <List className="w-3.5 h-3.5" />}
            <span>{outlineGenerating ? '生成大纲中...' : '生成大纲'}</span>
          </button>
        )}
        <button onClick={onGenerate} disabled={generating || !inputText.trim()}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50">
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          <span>{generating ? '生成中...' : '生成 PPT'}</span>
        </button>
      </div>
    </section>
  )
}

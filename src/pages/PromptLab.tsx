import { useState } from 'react'
import { Copy, Sparkles, Bookmark, Search, X, Save, Trash2 } from 'lucide-react'
import { promptCategories, addPrompt, removePrompt, type Prompt } from '@/data/prompts'

export function PromptLab() {
  const [activeCategory, setActiveCategory] = useState('report')
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [newPrompt, setNewPrompt] = useState({ title: '', content: '', category: 'report' })
  const [deleteConfirm, setDeleteConfirm] = useState<{ categoryId: string; prompt: Prompt } | null>(null)

  const prompts = promptCategories.find((c) => c.id === activeCategory)?.prompts || []

  const filtered = prompts.filter(
    (p) =>
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.content.toLowerCase().includes(search.toLowerCase())
  )

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const handleSavePrompt = () => {
    if (!newPrompt.title.trim() || !newPrompt.content.trim()) return
    
    addPrompt(newPrompt.category, newPrompt.title, newPrompt.content)
    
    setShowModal(false)
    setNewPrompt({ title: '', content: '', category: 'report' })
    setActiveCategory(newPrompt.category)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">提示词库</h1>
        <button className="btn-primary flex items-center space-x-1" onClick={() => setShowModal(true)}>
          <Sparkles className="w-4 h-4" />
          <span>新建自定义提示词</span>
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索提示词..."
          className="input-field pl-10"
        />
      </div>

      <div className="flex space-x-1 border-b border-gray-200">
        {promptCategories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeCategory === cat.id
                ? 'border-primary-600 text-primary-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtered.map((prompt) => (
            <div key={`${prompt.title}-${prompt.content.slice(0, 30)}`} className="card p-4 group">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-yellow-500" />
                  <h3 className="text-sm font-semibold text-gray-700">{prompt.title}</h3>
                </div>
                <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => copyToClipboard(prompt.content)}
                    className="p-1 hover:bg-gray-100 rounded"
                    title="复制"
                  >
                    <Copy className="w-4 h-4 text-gray-400" />
                  </button>
                  <button className="p-1 hover:bg-gray-100 rounded" title="保存">
                    <Bookmark className="w-4 h-4 text-gray-400" />
                  </button>
                  <button
                    onClick={() => {
                      setDeleteConfirm({ categoryId: activeCategory, prompt })
                    }}
                    className="p-1 hover:bg-red-50 rounded"
                    title="删除"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed">{prompt.content}</p>
            </div>
          ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-lg mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-800">新建自定义提示词</h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">提示词名称</label>
                <input
                  type="text"
                  value={newPrompt.title}
                  onChange={(e) => setNewPrompt({ ...newPrompt, title: e.target.value })}
                  placeholder="输入提示词名称..."
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
                <select
                  value={newPrompt.category}
                  onChange={(e) => setNewPrompt({ ...newPrompt, category: e.target.value })}
                  className="input-field"
                >
                  {promptCategories.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">提示词内容</label>
                <textarea
                  value={newPrompt.content}
                  onChange={(e) => setNewPrompt({ ...newPrompt, content: e.target.value })}
                  placeholder="输入提示词内容..."
                  className="input-field min-h-[150px] resize-y"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSavePrompt}
                disabled={!newPrompt.title.trim() || !newPrompt.content.trim()}
                className="btn-primary flex items-center space-x-2 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>保存</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm mx-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">确认删除</h2>
              <button
                onClick={() => setDeleteConfirm(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              确定要删除提示词「{deleteConfirm.prompt.title}」吗？此操作无法撤销。
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => {
                  removePrompt(deleteConfirm.categoryId, deleteConfirm.prompt)
                  setDeleteConfirm(null)
                }}
                className="px-4 py-2 text-sm bg-red-500 text-white hover:bg-red-600 rounded-lg transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
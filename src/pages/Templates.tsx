import { useState } from 'react'
import { Search, Plus, Upload } from 'lucide-react'
import { useProjectStore } from '@/stores/projectStore'

const mockTemplates = [
  { id: 'professional-blue', name: '专业蓝', category: '报告', preview: '#1e40af' },
  { id: 'dark-modern', name: '暗色现代', category: '科技', preview: '#111827' },
  { id: 'clean-white', name: '简洁白', category: '教育', preview: '#f8fafc' },
  { id: 'gradient-sunset', name: '渐变日落', category: '创意', preview: '#7c3aed' },
  { id: 'corporate-navy', name: '商务藏青', category: '提案', preview: '#1e3a5f' },
  { id: 'nature-green', name: '自然绿', category: '教育', preview: '#166534' },
]

const categories = ['全部', '报告', '教育', '提案', '创意', '科技']

export function Templates() {
  const [category, setCategory] = useState('全部')
  const [search, setSearch] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [importing, setImporting] = useState(false)
  const [importError, setImportError] = useState('')
  const updateConfig = useProjectStore((s) => s.updateGenerationConfig)

  const filtered = mockTemplates.filter(
    (t) =>
      (category === '全部' || t.category === category) &&
      t.name.toLowerCase().includes(search.toLowerCase())
  )

  const handleSelectTemplate = (id: string) => {
    setSelectedTemplate(id)
    updateConfig({ template: id })
  }

  const handleImportPptx = async () => {
    try {
      setImportError('')
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.pptx'
      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (!file) return
        setImporting(true)
        try {
          const formData = new FormData()
          formData.append('file', file)
          const res = await fetch('http://127.0.0.1:8099/api/v1/templates/import', { method: 'POST', body: formData })
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          const data = await res.json()
          setSelectedTemplate(data.id)
          updateConfig({ template: data.id })
        } catch (err: any) {
          setImportError(err.message || '导入失败')
        } finally {
          setImporting(false)
        }
      }
      input.click()
    } catch (err: any) {
      setImportError(err.message)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">模板</h1>
        <button onClick={handleImportPptx} disabled={importing} className="btn-primary flex items-center space-x-1">
          {importing ? <span>导入中...</span> : <><Upload className="w-4 h-4" /><span>从 PPTX 导入</span></>}
        </button>
      </div>

      {importError && (
        <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">{importError}</div>
      )}

      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索模板..."
            className="input-field pl-10"
          />
        </div>
        <div className="flex space-x-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                category === cat
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {filtered.map((t) => (
          <div
            key={t.id}
            onClick={() => handleSelectTemplate(t.id)}
            className={`card p-0 overflow-hidden group cursor-pointer border-2 transition-colors ${
              selectedTemplate === t.id ? 'border-primary-500' : 'border-transparent hover:border-gray-300'
            }`}
          >
            <div
              className="h-32 flex items-center justify-center relative"
              style={{ backgroundColor: t.preview }}
            >
              <span className="text-white text-opacity-30 text-sm">预览</span>
              {selectedTemplate === t.id && (
                <span className="absolute top-2 right-2 px-2 py-0.5 bg-primary-600 text-white text-xs rounded-full">已选</span>
              )}
            </div>
            <div className="p-3">
              <div className="text-sm font-medium text-gray-700">{t.name}</div>
              <div className="text-xs text-gray-400 mt-0.5">{t.category}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
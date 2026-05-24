import { useState, useEffect } from 'react'
import { Search, Upload, Trash2 } from 'lucide-react'
import { useProjectStore } from '@/stores/projectStore'
import { apiConfig } from '@/utils/api'

interface Template {
  id: string
  name: string
  category: string
  preview_svg?: string
  source: string
}

const categories = ['全部', '报告', '教育', '提案', '创意', '科技', '保险', '其他']

export function Templates() {
  const [category, setCategory] = useState('全部')
  const [search, setSearch] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [importing, setImporting] = useState(false)
  const [importError, setImportError] = useState('')
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const updateConfig = useProjectStore((s) => s.updateGenerationConfig)

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const baseUrl = await apiConfig.baseUrl
      const res = await fetch(await apiConfig.url('/api/v1/templates/'))
      if (res.ok) {
        const data = await res.json()
        const mapped = data.map((t: any) => ({
          id: t.id,
          name: t.name || t.id,
          category: t.category || '其他',
          preview_svg: t.preview_svg ? `${baseUrl}${t.preview_svg}` : '',
          source: t.source || 'built-in',
        }))
        setTemplates(mapped)
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err)
    } finally {
      setLoading(false)
    }
  }

  const filtered = templates.filter(
    (t) =>
      (category === '全部' || t.category === category) &&
      t.name.toLowerCase().includes(search.toLowerCase())
  )

  const handleSelectTemplate = (id: string) => {
    setSelectedTemplate(id)
    updateConfig({ template: id })
  }

  const handleDeleteTemplate = async (id: string) => {
    if (!confirm(`确定要删除模板 "${id}" 吗？此操作不可撤销。`)) {
      return
    }
    try {
      const res = await fetch(await apiConfig.url(`/api/v1/templates/${id}`), {
        method: 'DELETE',
      })
      if (res.ok) {
        fetchTemplates()
        if (selectedTemplate === id) {
          setSelectedTemplate(null)
        }
      } else {
        const data = await res.json()
        alert(data.message || '删除失败')
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '删除失败')
    }
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
          const res = await fetch(await apiConfig.url('/api/v1/templates/import'), { method: 'POST', body: formData })
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          const data = await res.json()
          setSelectedTemplate(data.id)
          updateConfig({ template: data.id })
        } catch (err: unknown) {
          setImportError(err instanceof Error ? err.message : '导入失败')
        } finally {
          setImporting(false)
        }
      }
      input.click()
    } catch (err: unknown) {
      setImportError(err instanceof Error ? err.message : String(err))
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">模板</h1>
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
        {loading ? (
          <div className="col-span-3 text-center py-12">加载中...</div>
        ) : filtered.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-gray-500">暂无模板</div>
        ) : (
          filtered.map((t) => (
            <div
              key={t.id}
              className={`card p-0 overflow-hidden border-2 transition-all ${
                selectedTemplate === t.id ? 'border-primary-500 shadow-md' : 'border-transparent hover:border-gray-300 hover:shadow-sm'
              }`}
            >
              <div className="h-32 flex items-center justify-center relative bg-gray-50 overflow-hidden">
                {t.preview_svg ? (
                  <img
                    src={t.preview_svg}
                    alt={t.name}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <span className="text-gray-300 text-sm">暂无预览</span>
                )}
                {selectedTemplate === t.id && (
                  <span className="absolute top-2 right-2 px-2 py-0.5 bg-primary-600 text-white text-xs rounded-full shadow-sm">已选</span>
                )}
                {t.source === 'custom' && (
                  <span className="absolute top-2 left-2 px-2 py-0.5 bg-green-500 text-white text-xs rounded-full shadow-sm">自定义</span>
                )}
                {t.source === 'custom' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteTemplate(t.id)
                    }}
                    className="absolute bottom-2 right-2 p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors shadow-sm opacity-70 hover:opacity-100"
                    title="删除模板"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
                <div
                  onClick={() => handleSelectTemplate(t.id)}
                  className="absolute inset-0 cursor-pointer"
                />
              </div>
              <div className="p-3">
                <div className="text-sm font-medium text-gray-700">{t.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">{t.category}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
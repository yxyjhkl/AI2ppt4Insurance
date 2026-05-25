import { useState, useEffect } from 'react'
import { Search, Upload, Trash2, X, Maximize2 } from 'lucide-react'
import { useProjectStore } from '@/stores/projectStore'
import { apiConfig } from '@/utils/api'

interface Template {
  id: string
  name: string
  category: string
  preview_svg?: string
  source: string
  description?: string
}

const categories = ['全部', '报告', '教育', '提案', '创意', '科技', '保险', '其他']

export function Templates() {
  const [category, setCategory] = useState('全部')
  const [search, setSearch] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null)
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
          description: t.description || '',
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

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
        {loading ? (
          <div className="col-span-3 text-center py-12 text-gray-400">加载中...</div>
        ) : filtered.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-gray-400">暂无模板</div>
        ) : (
          filtered.map((t) => (
            <div
              key={t.id}
              className={`card p-0 overflow-hidden border-2 transition-all cursor-pointer group ${
                selectedTemplate === t.id ? 'border-primary-500 shadow-lg ring-2 ring-primary-200' : 'border-gray-200 hover:border-gray-400 hover:shadow-md'
              }`}
              onClick={() => handleSelectTemplate(t.id)}
            >
              {/* 预览图 */}
              <div className="relative bg-gray-100 dark:bg-gray-800" style={{ aspectRatio: '4/3' }}>
                {t.preview_svg ? (
                  <img
                    src={t.preview_svg}
                    alt={t.name}
                    className="w-full h-full object-contain p-2"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300 text-sm">暂无预览</div>
                )}
                {/* 放大按钮 */}
                <button
                  onClick={(e) => { e.stopPropagation(); setPreviewTemplate(t) }}
                  className="absolute top-2 right-2 p-1.5 bg-white/90 hover:bg-white rounded-lg shadow-sm opacity-0 group-hover:opacity-100 transition-all"
                  title="查看大图"
                >
                  <Maximize2 className="w-3.5 h-3.5 text-gray-500" />
                </button>
                {/* 已选标记 */}
                {selectedTemplate === t.id && (
                  <span className="absolute top-2 left-2 px-2 py-0.5 bg-primary-600 text-white text-[10px] font-medium rounded-full shadow-sm">当前使用</span>
                )}
                {t.source === 'custom' && (
                  <span className="absolute bottom-2 left-2 px-2 py-0.5 bg-green-500 text-white text-[10px] font-medium rounded-full shadow-sm">自定义</span>
                )}
              </div>
              {/* 信息栏 */}
              <div className="p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t.name}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{t.category}{t.description ? ` · ${t.description}` : ''}</div>
                  </div>
                  {t.source === 'custom' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteTemplate(t.id) }}
                      className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="删除模板"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 大图预览弹窗 */}
      {previewTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-8" onClick={() => setPreviewTemplate(null)}>
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-gray-700">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{previewTemplate.name}</h3>
                <p className="text-xs text-gray-500">{previewTemplate.category}{previewTemplate.description ? ` · ${previewTemplate.description}` : ''}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { handleSelectTemplate(previewTemplate.id); setPreviewTemplate(null) }}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                    selectedTemplate === previewTemplate.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-primary-600 text-white hover:bg-primary-700'
                  }`}
                >
                  {selectedTemplate === previewTemplate.id ? '已选用' : '使用此模板'}
                </button>
                <button onClick={() => setPreviewTemplate(null)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
            </div>
            <div className="flex-1 flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-800 overflow-auto">
              {previewTemplate.preview_svg ? (
                <img src={previewTemplate.preview_svg} alt={previewTemplate.name} className="max-w-full max-h-full object-contain rounded-lg shadow-lg" />
              ) : (
                <span className="text-gray-400">暂无预览图</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
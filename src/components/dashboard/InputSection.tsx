import { useState, useCallback } from 'react'
import { Type, Upload, Globe, X, AlertCircle, Loader2, Table2, Lightbulb, Copy, ChevronDown, ChevronUp } from 'lucide-react'
import { apiConfig } from '@/utils/api'
import type { SceneType, InsuranceMeetingType } from '@/types'
import { SCENE_INPUT_GUIDES, INSURANCE_MEETING_INPUT_GUIDES } from '@/data/inputGuides'

const inputMethods = [
  { id: 'text', label: '输入主题', icon: Type },
  { id: 'file', label: '上传文件', icon: Upload },
  { id: 'url', label: '粘贴 URL', icon: Globe },
]

export function InputSection(props: {
  selectedScene: SceneType
  meetingType?: InsuranceMeetingType
  inputText: string
  onInputChange: (text: string) => void
  onGenerate: () => void
  onFileUploaded?: () => void
  onExcelUploaded?: (data: { filepath: string; file_id: string; filename: string }) => void
}) {
  const { selectedScene, meetingType, inputText, onInputChange, onGenerate, onFileUploaded, onExcelUploaded } = props
  const [inputMethod, setInputMethod] = useState('text')
  const [excelUploading, setExcelUploading] = useState(false)
  const [excelUploadError, setExcelUploadError] = useState('')
  const [excelData, setExcelData] = useState<{
    file_id: string
    filepath: string
    filename: string
    preview: string
    sheet_names: string[]
    row_count: number
    headers: Record<string, string[]>
    summary: string
  } | null>(null)
  const [localError, setLocalError] = useState('')
  const [showExamples, setShowExamples] = useState(false)
  
  // 获取当前场景的输入引导
  const getCurrentGuide = () => {
    if (selectedScene === 'insurance' && meetingType) {
      return INSURANCE_MEETING_INPUT_GUIDES[meetingType]
    }
    return SCENE_INPUT_GUIDES[selectedScene]
  }
  
  const guide = getCurrentGuide()

  const handleExcelUpload = useCallback(async (file: File) => {
    setExcelUploading(true)
    setLocalError('')
    setExcelUploadError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(await apiConfig.url('/api/v1/convert/excel'), {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(errData.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setExcelData({ ...data, headers: {}, summary: data.preview })
      onInputChange(data.preview || `Excel文件: ${data.filename}, ${data.row_count}行数据`)
      onExcelUploaded?.({ filepath: data.filepath, file_id: data.file_id, filename: data.filename })
      onFileUploaded?.()
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Excel上传失败'
      setLocalError(errMsg)
      setExcelUploadError(errMsg)
    } finally {
      setExcelUploading(false)
    }
  }, [onInputChange, onFileUploaded, onExcelUploaded])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      onGenerate()
    }
  }

  return (
    <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
      <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">2. 输入内容</h2>
      
      {/* 输入提示卡片 */}
      {inputMethod === 'text' && guide.tips.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <Lightbulb className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-amber-800 mb-2">输入建议</h3>
              <ul className="space-y-1">
                {guide.tips.map((tip, idx) => (
                  <li key={idx} className="text-sm text-amber-700">{tip}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex space-x-2 mb-3">
        {inputMethods.map((m) => (
          <button
            key={m.id}
            onClick={() => setInputMethod(m.id)}
            className={`flex items-center px-3 py-1.5 rounded-md text-sm transition-colors ${
              inputMethod === m.id
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            <m.icon className="w-4 h-4 mr-1.5" />
            {m.label}
          </button>
        ))}
      </div>

      {inputMethod === 'text' && (
        <div className="space-y-3">
          <textarea
            value={inputText}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={guide.placeholder}
            className="input-field min-h-[200px] resize-y"
          />
          
          {/* 示例按钮 */}
          {guide.examples.length > 0 && (
            <button
              type="button"
              onClick={() => setShowExamples(!showExamples)}
              className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 transition-colors"
            >
              {showExamples ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              {showExamples ? '隐藏示例' : '查看输入示例'}
            </button>
          )}
          
          {/* 示例展示 */}
          {showExamples && guide.examples.length > 0 && (
            <div className="space-y-3">
              {guide.examples.map((example, idx) => (
                <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between gap-3">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap flex-1 overflow-x-auto">
                      {example}
                    </pre>
                    <button
                      type="button"
                      onClick={() => {
                        onInputChange(example)
                        setShowExamples(false)
                      }}
                      className="flex-shrink-0 p-1.5 text-gray-500 hover:text-primary-600 hover:bg-gray-100 rounded transition-colors"
                      title="使用此示例"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {inputMethod === 'file' && selectedScene !== 'insurance' && (
        <label className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary-400 cursor-pointer transition-colors block">
          <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm text-gray-500">
              {selectedScene === 'enhance'
                ? '上传需要 AI 润色优化的 PPTX 文件'
                : '拖放 PDF、DOCX、MD、TXT、PPTX、XMind 或点击浏览'}
            </p>
          {selectedScene === 'enhance' && (
            <p className="text-xs text-gray-400 mt-1">AI 将保留原内容核心信息，优化标题、丰富数据、升级视觉结构</p>
          )}
          <input type="file" accept={selectedScene === 'enhance' ? '.pptx' : '.pdf,.docx,.md,.txt,.pptx,.xmind'} className="hidden" onChange={async (e) => {
            const file = e.target.files?.[0]
            if (!file) return
            try {
              const formData = new FormData()
              formData.append('file', file)
              const res = await fetch(await apiConfig.url('/api/v1/convert/file'), { method: 'POST', body: formData })
              if (!res.ok) throw new Error(`HTTP ${res.status}`)
              const data = await res.json()
              onInputChange(data.markdown || '')
              onFileUploaded?.()
              setInputMethod('text')
            } catch (err: unknown) {
              setLocalError(err instanceof Error ? err.message : '文件转换失败')
            }
          }} />
        </label>
      )}

      {inputMethod === 'file' && selectedScene === 'insurance' && (
        <div className="space-y-3">
          {excelUploadError && (
            <div className="flex items-center space-x-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{excelUploadError}</span>
              <button onClick={() => setExcelUploadError('')} className="ml-auto text-red-400 hover:text-red-600">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          <label className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors block ${
            excelUploading ? 'border-amber-300 bg-amber-50' : excelData ? 'border-green-400 bg-green-50' : 'border-gray-300 hover:border-primary-400 cursor-pointer'
          }`}>
            {excelUploading ? (
              <div className="space-y-2">
                <Loader2 className="w-8 h-8 mx-auto animate-spin text-amber-500" />
                <p className="text-sm text-amber-600">正在解析 Excel 文件...</p>
              </div>
            ) : excelData ? (
              <div className="space-y-2">
                <Table2 className="w-8 h-8 mx-auto text-green-500" />
                <p className="text-sm font-medium text-green-700">{excelData.filename}</p>
                <p className="text-xs text-green-600">
                  {excelData.sheet_names?.join(', ')} | {excelData.row_count} 行数据
                </p>
                <p className="text-xs text-green-500">点击可重新上传</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="w-8 h-8 mx-auto text-gray-400" />
                <p className="text-sm text-gray-500">拖放 Excel、PDF、DOCX、MD、TXT、XMind 或点击浏览</p>
                <p className="text-xs text-gray-400">Excel 将自动解析并匹配到模板</p>
              </div>
            )}
            <input type="file" accept=".xlsx,.xls,.pdf,.docx,.md,.txt,.xmind" className="hidden"
              disabled={excelUploading}
              onChange={async (e) => {
                const file = e.target.files?.[0]
                if (!file) return
                const ext = file.name.split('.').pop()?.toLowerCase()
                if (ext === 'xlsx' || ext === 'xls') {
                  await handleExcelUpload(file)
                } else {
                  setExcelUploading(true)
                  setExcelUploadError('')
                  try {
                    const formData = new FormData()
                    formData.append('file', file)
                    const res = await fetch(await apiConfig.url('/api/v1/convert/file'), { method: 'POST', body: formData })
                    if (!res.ok) {
                      const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
                      throw new Error(errData.detail || `HTTP ${res.status}`)
                    }
                    const data = await res.json()
                    onInputChange(data.markdown || '')
                    onFileUploaded?.()
                    setInputMethod('text')
                  } catch (err: unknown) {
                    const errMsg = err instanceof Error ? err.message : '文件转换失败'
                    setExcelUploadError(errMsg)
                  } finally {
                    setExcelUploading(false)
                  }
                }
              }}
            />
          </label>
          {excelData && (
            <details className="bg-gray-50 rounded-lg p-3">
              <summary className="text-sm font-medium text-gray-600 cursor-pointer">数据预览</summary>
              <pre className="text-xs text-gray-500 mt-2 overflow-x-auto max-h-48 whitespace-pre-wrap">{excelData.preview}</pre>
            </details>
          )}
        </div>
      )}

      {inputMethod === 'url' && (
        <div className="flex space-x-2">
          <input type="url" placeholder="https://example.com/article"
            className="input-field flex-1" value={inputText}
            onChange={(e) => onInputChange(e.target.value)} />
          <button onClick={async () => {
            if (!inputText.trim()) return
            try {
              const res = await fetch(await apiConfig.url('/api/v1/convert/url'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: inputText }),
              })
              if (!res.ok) throw new Error(`HTTP ${res.status}`)
              const data = await res.json()
              onInputChange(data.markdown || '')
              onFileUploaded?.()
            } catch (err: unknown) {
              setLocalError(err instanceof Error ? err.message : 'URL 抓取失败')
            }
          }} className="btn-primary text-sm px-3">抓取</button>
        </div>
      )}
      {localError && <p className="text-sm text-red-500">{localError}</p>}
    </section>
  )
}

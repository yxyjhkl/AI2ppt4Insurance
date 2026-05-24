import { useState } from 'react'
import { Check, Sparkles } from 'lucide-react'

const templateCategories = ['全部', '报告', '保险', '提案', '科技', '创意', '教育']

export function TemplateSelector({
  templates,
  loadingTemplates,
  customTemplateId,
  onSelectTemplate,
  onToggle,
}: {
  templates: { id: string; name: string; category: string; preview_svg?: string }[]
  loadingTemplates: boolean
  customTemplateId: string | null
  onSelectTemplate: (id: string) => void
  onToggle: (useCustom: boolean) => void
}) {
  const [useCustomTemplate, setUseCustomTemplate] = useState<boolean | null>(null)
  const [templateCategory, setTemplateCategory] = useState('全部')

  const handleToggle = (val: boolean) => {
    setUseCustomTemplate(val)
    onToggle(val)
  }

  return (
    <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
      <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">3. 选择模板（可选）</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">是否需要自己选择模板？不选择将使用默认模板。</p>
      <div className="flex space-x-3">
        <button onClick={() => handleToggle(false)}
          className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
            useCustomTemplate === false
              ? 'border-primary-500 bg-primary-50 text-primary-700'
              : 'border-gray-200 text-gray-500 hover:border-gray-300'
          }`}>
          <Check className="w-4 h-4 mr-1.5" />
          使用默认模板
        </button>
        <button onClick={() => handleToggle(true)}
          className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
            useCustomTemplate === true
              ? 'border-primary-500 bg-primary-50 text-primary-700'
              : 'border-gray-200 text-gray-500 hover:border-gray-300'
          }`}>
          <Sparkles className="w-4 h-4 mr-1.5" />
          自己选择模板
        </button>
      </div>

      {useCustomTemplate && (
        <div className="pt-3 space-y-3 border-t border-gray-100">
          <div className="flex space-x-2">
            {templateCategories.map((cat) => (
              <button key={cat} onClick={() => setTemplateCategory(cat)}
                className={`px-3 py-1 rounded-md text-xs transition-colors ${
                  templateCategory === cat
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:bg-gray-100'
                }`}>
                {cat}
              </button>
            ))}
          </div>
          {loadingTemplates ? (
            <div className="grid grid-cols-3 gap-3">
              {[1,2,3].map(i => (
                <div key={i} className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                  <div className="h-20 skeleton" />
                  <div className="p-2 space-y-1.5">
                    <div className="h-3 w-2/3 skeleton" />
                    <div className="h-2.5 w-1/3 skeleton" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {templates.filter((t) => templateCategory === '全部' || t.category === templateCategory)
                .map((t) => (
                  <div key={t.id} onClick={() => onSelectTemplate(t.id)}
                    className={`card p-0 overflow-hidden cursor-pointer border-2 transition-colors ${
                      customTemplateId === t.id ? 'border-primary-500' : 'border-transparent hover:border-gray-300'
                    }`}>
                    <div className="h-20 flex items-center justify-center relative bg-gray-50">
                      {t.preview_svg ? (
                        <img src={t.preview_svg} alt={t.name} className="w-full h-full object-cover" loading="lazy" />
                      ) : (
                        <span className="text-gray-300 text-xs">无预览</span>
                      )}
                      {customTemplateId === t.id && (
                        <span className="absolute top-1.5 right-1.5 px-1.5 py-0.5 bg-primary-600 text-white text-xs rounded-full">已选</span>
                      )}
                    </div>
                    <div className="p-2">
                      <div className="text-xs font-medium text-gray-700">{t.name}</div>
                      <div className="text-xs text-gray-400">{t.category}</div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}

/**
 * 仪表盘页面 —— AI演示文稿生成的入口
 *
 * 三种工作模式（工作流 + AI模式 的组合）：
 *   1. 全自动(auto)：一键生成，跳过大纲确认
 *   2. 引导式(guided)：先确认AI大纲再生成 → 更可控
 *   3. 共创式(cocreate)：大纲+需求面板 → 精细控制
 *
 * AI模式选择（独立于工作流）：
 *   - ai_network：云端大模型(gpt-4o/deepseek/gemini等)，需配置API Key
 *   - local_ollama：本地Ollama部署(如qwen/llama)，完全离线
 *   - rule_engine：离线规则引擎，零依赖，适合无AI环境
 *
 * handleGenerate 核心流程：
 *   1. 根据selectedMode解析 ai_mode 参数(online/offline)
 *   2. 从SecureStore加载选中模型的API Key配置
 *   3. 将配置注入后端 /api/v1/ai/configure
 *   4. 调用 POST /api/v1/generate/pptx 提交生成任务
 *   5. 后端通过WebSocket推送进度 → ProgressModal展示
 *   6. 返回后设置lastGeneration和currentProject → 跳转Editor
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, X, AlertCircle, Loader2, FileUp, Sparkles } from 'lucide-react'
import { useProjectStore } from '@/stores/projectStore'
import { apiConfig, createAbortableFetch } from '@/utils/api'
import { getObject } from '@/utils/secureStore'
import type { SceneType, InsuranceMeetingType, LayoutType } from '@/types'
import { ProgressModal } from '@/components/ProgressModal'
import { OutlineReview, type OutlineItem } from '@/components/dashboard/OutlineReview'
import { SceneSelector } from '@/components/dashboard/SceneSelector'
import { WorkflowModeSelector, type WorkflowMode } from '@/components/dashboard/WorkflowModeSelector'
import { RequirementsPanel, type Requirements } from '@/components/dashboard/RequirementsPanel'
import { InsuranceMeetingSelector } from '@/components/dashboard/InsuranceMeetingSelector'
import { InputSection } from '@/components/dashboard/InputSection'
import { TemplateSelector } from '@/components/dashboard/TemplateSelector'
import { StyleSelector } from '@/components/dashboard/StyleSelector'
import { PromptSelector } from '@/components/dashboard/PromptSelector'
import { ModelSelector } from '@/components/dashboard/ModelSelector'
import { GenerateBar } from '@/components/dashboard/GenerateBar'

type GenerationMode = 'ai_network' | 'local_ollama' | 'rule_engine' | null

export function Dashboard() {
  const navigate = useNavigate()
  const abortRef = useRef<AbortController | null>(null)
  const mountedRef = useRef(true)
  const fileJustUploadedRef = useRef(false)
  const autoTriggeredRef = useRef(false)
  const [selectedScene, setSelectedScene] = useState<SceneType>('report')
  const [meetingType, setMeetingType] = useState<InsuranceMeetingType>('business_review')
  const [inputText, setInputText] = useState('')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  const [useCustomTemplate, setUseCustomTemplate] = useState(false)
  const [customTemplateId, setCustomTemplateId] = useState<string | null>(null)

  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null)

  const [customStyle, setCustomStyle] = useState('')

  const [excelFilepath, setExcelFilepath] = useState<string | null>(null)

  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null)

  const [templates, setTemplates] = useState<{ id: string; name: string; category: string; preview_svg?: string }[]>([])
  const [loadingTemplates, setLoadingTemplates] = useState(true)

  const [showProgress, setShowProgress] = useState(false)
  const [currentTaskId, setCurrentTaskId] = useState('')

  const [ollamaDetected, setOllamaDetected] = useState(false)
  const [ollamaLocalModels, setOllamaLocalModels] = useState<string[]>([])
  const [ollamaChecking, setOllamaChecking] = useState(false)
  const [selectedModelId, setSelectedModelId] = useState('')
  const [storedModels, setStoredModels] = useState<{ model: string; apiKey: string; baseUrl: string; name: string }[]>([])

  const [selectedMode, setSelectedMode] = useState<GenerationMode>(null)
  const [workflowMode, setWorkflowMode] = useState<WorkflowMode | null>(null)

  const [showOutlineReview, setShowOutlineReview] = useState(false)
  const [outlineTitle, setOutlineTitle] = useState('')
  const [outlineSlides, setOutlineSlides] = useState<OutlineItem[]>([])
  const [outlineGenerating, setOutlineGenerating] = useState(false)

  const [requirements, setRequirements] = useState<Requirements>({
    audience: '', duration: '', tone: '', mustInclude: '', avoidTopics: '',
  })

  const originalContentRef = useRef('')

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      abortRef.current?.abort()
    }
  }, [])

  const handleFileUploaded = useCallback(() => {
    fileJustUploadedRef.current = true
  }, [])

  useEffect(() => {
    autoTriggeredRef.current = false
    fileJustUploadedRef.current = false
  }, [workflowMode])

  useEffect(() => {
    const init = async () => {
      setLoadingTemplates(true)
      try {
        const [tplRes, ollamaRes] = await Promise.all([
          fetch(await apiConfig.url('/api/v1/templates')),
          fetch(await apiConfig.url('/api/v1/ai/check-ollama')),
        ])
        if (tplRes.ok) {
          const tplData: { id: string; name?: string; category?: string; preview_svg?: string }[] = await tplRes.json()
          setTemplates(tplData.map((t) => ({
            id: t.id,
            name: t.name || t.id,
            category: t.category || '通用',
            preview_svg: t.preview_svg || '',
          })))
        }
        if (ollamaRes.ok) {
          const data = await ollamaRes.json()
          if (data.available && data.models?.length > 0) {
            setOllamaDetected(true)
            setOllamaLocalModels(data.models)
          }
        }
      } catch {
      } finally {
        setLoadingTemplates(false)
        setOllamaChecking(false)
      }
    }
    init()
  }, [])

  useEffect(() => {
    let cancelled = false
    getObject<{ model?: string; apiKey?: string; baseUrl?: string; name?: string }[]>('aippt_models').then(async (saved) => {
      if (cancelled) return
      if (saved && saved.length > 0) {
        const mapped = saved.map((m, i) => ({
          model: m.model || '',
          apiKey: m.apiKey || '',
          baseUrl: m.baseUrl || '',
          name: m.name || m.model || `Model ${i + 1}`,
        }))
        setStoredModels(mapped)
        if (selectedMode === 'ai_network') {
          // AI网络模式：选择第一个云端模型
          const cloudModel = mapped.find(m => m.apiKey && m.apiKey !== 'ollama')
          if (cloudModel?.model) {
            setSelectedModelId(cloudModel.model)
          } else if (mapped[0]?.model) {
            setSelectedModelId(mapped[0].model)
          }
        } else if (selectedMode === 'local_ollama' && ollamaLocalModels.length > 0) {
          setSelectedModelId(`ollama/${ollamaLocalModels[0]}`)
        }
      } else if (selectedMode === 'local_ollama' && ollamaLocalModels.length > 0) {
        setSelectedModelId(`ollama/${ollamaLocalModels[0]}`)
      }
    })
    return () => { cancelled = true }
  }, [ollamaLocalModels, selectedMode])

  // 当模式切换时，更新模型选择
  useEffect(() => {
    if (selectedMode === 'ai_network' && storedModels.length > 0) {
      const cloudModel = storedModels.find(m => m.apiKey && m.apiKey !== 'ollama')
      if (cloudModel?.model) {
        setSelectedModelId(cloudModel.model)
      } else if (storedModels[0]?.model) {
        setSelectedModelId(storedModels[0].model)
      }
    } else if (selectedMode === 'local_ollama' && ollamaLocalModels.length > 0) {
      setSelectedModelId(`ollama/${ollamaLocalModels[0]}`)
    }
  }, [selectedMode, storedModels, ollamaLocalModels])

  const autoGenRef = useRef<() => void>(() => {})

  useEffect(() => {
    if (
      workflowMode === 'auto' &&
      selectedMode &&
      fileJustUploadedRef.current &&
      inputText.trim() &&
      !autoTriggeredRef.current &&
      !generating
    ) {
      autoTriggeredRef.current = true
      fileJustUploadedRef.current = false
      setNotification({ type: 'info', message: '文档解析完成，正在自动生成 PPT...' })
      const timer = setTimeout(() => {
        setNotification(null)
        autoGenRef.current()
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [inputText, workflowMode, selectedMode, generating])

  const config = useProjectStore((s) => s.generationConfig)
  const setCurrentProject = useProjectStore((s) => s.setCurrentProject)
  const setLastGeneration = useProjectStore((s) => s.setLastGeneration)
  const projects = useProjectStore((s) => s.projects)

  const handleGenerateOutline = useCallback(async () => {
    if (!inputText.trim()) return
    setOutlineGenerating(true)
    try {
      const body = {
        scene: selectedScene,
        meeting_type: selectedScene === 'insurance' ? meetingType : null,
        content: inputText,
        model: selectedModelId || config.model || 'gpt-4o',
        language: config.language,
      }
      const res = await fetch(await apiConfig.url('/api/v1/generate/outline'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setOutlineTitle(data.title || '未命名')
      setOutlineSlides(data.slides || [])
      setShowOutlineReview(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '大纲生成失败')
    } finally {
      setOutlineGenerating(false)
    }
  }, [inputText, selectedScene, meetingType, selectedModelId, config])

  const handleEditOutlineSlide = useCallback((idx: number, field: string, value: string) => {
    if (idx === -1) {
      setOutlineTitle(value)
    } else {
      setOutlineSlides(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s))
    }
  }, [])

  const handleConfirmOutline = useCallback(() => {
    setShowOutlineReview(false)
    originalContentRef.current = inputText
    const outlineText = `【演示标题】${outlineTitle}\n\n` +
      outlineSlides.map(s =>
        `## ${s.title} [${s.layout_type}]\n${s.description}\n${s.key_points.map(k => `- ${k}`).join('\n')}`
      ).join('\n\n')

    if (workflowMode === 'cocreate') {
      // Cocreate模式：确认后直接生成，进入编辑器逐页微调
      setInputText(outlineText)
      setNotification({ type: 'info', message: `大纲已确认，正在生成 ${outlineSlides.length} 页PPT，进入编辑器后您可逐页微调...` })
      setTimeout(() => {
        setNotification(null)
        // 直接触发生成
        const genBtn = document.querySelector('[data-gen-btn]') as HTMLButtonElement
        if (genBtn) genBtn.click()
      }, 300)
    } else {
      // Guided模式：设置大纲文本，用户手动点击生成
      setInputText(outlineText)
      setNotification({ type: 'success', message: `大纲已确认（${outlineSlides.length}页）。请点击"生成PPT"按钮完成生成。` })
      setTimeout(() => setNotification(null), 6000)
    }
  }, [outlineTitle, outlineSlides, inputText, workflowMode])

  const handleGenerate = useCallback(async () => {
    if (generating || !inputText.trim()) return

    setGenerating(true)
    setError('')

    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    const abortableFetch = createAbortableFetch(abortRef.current.signal)

    const effectiveTemplate = useCustomTemplate && customTemplateId ? customTemplateId : config.template
    const finalContent = selectedPrompt
      ? `【生成指令】${selectedPrompt}\n\n【内容】${inputText}`
      : inputText

    const reqParts: string[] = []
    if (requirements.audience) {
      reqParts.push(`【受众】${requirements.audience === 'executives' ? '管理层' : requirements.audience === 'team' ? '团队' : requirements.audience === 'clients' ? '客户' : '全员'}`)
    }
    if (requirements.duration) {
      reqParts.push(`【时长】${requirements.duration}`)
    }
    if (requirements.tone) {
      reqParts.push(`【风格】${requirements.tone === 'professional' ? '严谨专业' : requirements.tone === 'motivating' ? '激励动员' : requirements.tone === 'warm' ? '温暖亲和' : '现代简洁'}`)
    }
    if (requirements.mustInclude) {
      reqParts.push(`【必含】${requirements.mustInclude}`)
    }
    if (requirements.avoidTopics) {
      reqParts.push(`【避免】${requirements.avoidTopics}`)
    }
    const requirementsText = reqParts.length > 0 ? '\n\n' + reqParts.join('\n') : ''
    const finalContentWithReqs = finalContent + requirementsText

    try {
      let ai_mode: 'online' | 'offline' = 'offline'
      let currentModelId = ''

      if (selectedMode === 'ai_network') {
        ai_mode = 'online'
        currentModelId = selectedModelId || config.model || 'gpt-4o'
      } else if (selectedMode === 'local_ollama') {
        ai_mode = 'online'
        currentModelId = selectedModelId || (ollamaLocalModels.length > 0 ? `ollama/${ollamaLocalModels[0]}` : '')
      } else {
        ai_mode = 'offline'
      }

      const savedModels = await getObject<{ model?: string; apiKey?: string; baseUrl?: string; name?: string }[]>('aippt_models')
      const selectedModel = savedModels?.find(m => m.model === currentModelId)
      if (selectedModel?.apiKey && (selectedModel.apiKey !== 'ollama' || selectedModel.baseUrl)) {
        await fetch(await apiConfig.url('/api/v1/ai/configure'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model_id: currentModelId, api_key: selectedModel.apiKey, base_url: selectedModel.baseUrl }),
        }).catch((e) => { console.warn('[Dashboard] API key configure failed:', e) })
      }

      const taskId = `task_${Math.random().toString(36).substring(2, 10)}`
      setCurrentTaskId(taskId)
      setShowProgress(true)

      const body = {
        scene: selectedScene,
        meeting_type: selectedScene === 'insurance' ? meetingType : null,
        content: finalContentWithReqs,
        custom_style: customStyle || null,
        template: effectiveTemplate,
        model: currentModelId,
        slide_count: config.slideCount,
        language: config.language,
        include_notes: config.includeNotes,
        include_images: config.includeImages,
        include_animation: config.includeAnimation,
        temperature: config.temperature,
        ai_mode: ai_mode,
        auto_mode: workflowMode === 'auto',
        canvas_format: config.canvasFormat || '16:9',
        task_id: taskId,
        excel_filepath: excelFilepath,
        requirements: Object.keys(requirements).some(k => (requirements as any)[k])
          ? requirements : null,
      }

      const res = await abortableFetch(await apiConfig.url('/api/v1/generate/pptx'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(errData.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      if (!mountedRef.current) return

      // 如果AI回退到离线模式，提示用户
      if (data.mode === 'offline' && (selectedMode === 'ai_network' || selectedMode === 'local_ollama')) {
        setNotification({ type: 'info', message: 'AI 生成失败，已自动切换为离线模式。效果可能不如预期，可在设置中检查 API Key 后重试。' })
        setTimeout(() => setNotification(null), 8000)
      }

      setLastGeneration({
        slides: data.slides || [],
        qaResults: data.qa_results || [],
        mode: data.mode || 'offline',
        message: data.message || '',
        title: data.title || '未命名',
        content: inputText,
        scene: selectedScene,
      })

      setCurrentProject({
        id: data.project_id,
        name: data.title,
        scene: selectedScene,
        slides: (data.slides as { layout_type: string; title: string; body_items?: { type: string; text: string; level: number }[]; notes?: string; svg_preview?: string }[] | undefined)?.map((s, i: number) => ({
          id: `slide_${i}`,
          index: i,
          layoutType: s.layout_type as LayoutType,
          title: s.title,
          content: s.body_items?.map((b) => b.text).join('\n') || '',
          bodyItems: s.body_items || [],
          notes: s.notes || '',
          svgContent: s.svg_preview || data.preview_slides?.[i] || '',
        })) || [],
        templateId: data.template_id,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        version: 1,
      })

      navigate(`/editor/new?scene=${selectedScene}&template=${effectiveTemplate}&project=${data.project_id}`)
      if (mountedRef.current) {
        setShowProgress(false)
        setGenerating(false)
      }
    } catch (err: unknown) {
      if (!mountedRef.current) return
      autoTriggeredRef.current = false
      setShowProgress(false)
      setError(err instanceof Error ? err.message : '生成失败')
      setGenerating(false)
    }
  }, [inputText, selectedScene, meetingType, selectedPrompt, useCustomTemplate, customTemplateId, customStyle, config, navigate, setCurrentProject, setLastGeneration, selectedModelId, selectedMode, ollamaDetected, ollamaLocalModels, generating, requirements])

  autoGenRef.current = handleGenerate

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <section className="animate-fade-in">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1">新建演示文稿</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">AI 从您的内容生成可编辑的 PPTX</p>
      </section>

      {projects.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">最近项目</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {projects.slice(0, 6).map((project) => (
              <div
                key={project.id}
                onClick={() => {
                  setCurrentProject(project)
                  navigate(`/editor/${project.id}?scene=${project.scene}&template=${project.templateId}`)
                }}
                className="card p-4 cursor-pointer hover:shadow-md hover:border-primary-300 dark:hover:border-primary-600 transition-all group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">{project.name}</h3>
                    <p className="text-xs text-gray-400 mt-1">
                      {project.slides.length} 页 · {new Date(project.updatedAt).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      useProjectStore.getState().setProjects(projects.filter(p => p.id !== project.id))
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-50 rounded transition-all"
                    title="删除项目"
                  >
                    <svg className="w-3.5 h-3.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 生成中骨架屏 */}
      {generating && (
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          <div className="h-32 bg-gray-100 dark:bg-gray-800 rounded-xl" />
          <div className="flex gap-3">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-20" />
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-20" />
          </div>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg" style={{ width: `${85 - i * 10}%` }} />
            ))}
          </div>
        </div>
      )}

      {notification && (
        <div className={`flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium animate-in slide-in-from-top-2 ${
          notification.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' :
          notification.type === 'error' ? 'bg-red-50 border border-red-200 text-red-800' :
          'bg-blue-50 border border-blue-200 text-blue-800'
        }`}>
          <div className="flex items-center space-x-2">
            {notification.type === 'success' ? <Check className="w-5 h-5 text-green-500" /> :
             notification.type === 'error' ? <AlertCircle className="w-5 h-5 text-red-500" /> :
             <Loader2 className="w-5 h-5 text-blue-500" />}
            <span>{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-gray-400 hover:text-gray-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <WorkflowModeSelector
        selected={workflowMode}
        onChange={setWorkflowMode}
        aiMode={selectedMode || 'ai_network'}
        onAiModeChange={(m) => setSelectedMode(m as GenerationMode)}
        ollamaDetected={ollamaDetected}
      />

      {selectedMode === null && (
        <div className="text-center py-8 text-sm text-gray-400">← 请先选择一个工作模式</div>
      )}

      {workflowMode && selectedMode && (
        <>
          {/* AI替我做模式 - 极简界面 */}
          {workflowMode === 'auto' ? (
            <>
              {/* AI替我做模式 - 极简界面：场景/模板自动识别 */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-800 rounded-2xl p-6 border-2 border-blue-100 dark:border-blue-900">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
                    <FileUp className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">上传您的材料</h3>
                    <p className="text-sm text-gray-500">支持 Word、PDF、TXT 等，AI 自动识别场景并生成精美 PPT</p>
                  </div>
                </div>
                <InputSection
                  selectedScene={selectedScene}
                  meetingType={meetingType}
                  inputText={inputText}
                  onInputChange={setInputText}
                  onGenerate={handleGenerate}
                  onFileUploaded={handleFileUploaded}
                  onExcelUploaded={(data) => setExcelFilepath(data.filepath)}
                />
              </div>

              <div className="text-center py-3">
                <div className="inline-flex items-center gap-2 bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-full text-sm text-gray-500">
                  <Sparkles className="w-4 h-4 text-blue-500" />
                  <span>AI 自动识别场景、选择模板、确定页数，无需手动配置</span>
                </div>
              </div>

              <GenerateBar
                generating={generating}
                inputText={inputText}
                error={error}
                onGenerate={handleGenerate}
                onGenerateOutline={undefined}
                outlineGenerating={outlineGenerating}
                autoMode={true}
              />
            </>
          ) : (
            <>
              {/* 完整模式 - 保留所有选项 */}
              <SceneSelector selectedScene={selectedScene} onSelect={setSelectedScene} />

              {selectedScene === 'insurance' && (
                <InsuranceMeetingSelector meetingType={meetingType} onSelect={setMeetingType} />
              )}

              <InputSection
                selectedScene={selectedScene}
                meetingType={meetingType}
                inputText={inputText}
                onInputChange={setInputText}
                onGenerate={handleGenerate}
                onFileUploaded={handleFileUploaded}
                onExcelUploaded={(data) => setExcelFilepath(data.filepath)}
              />

              {originalContentRef.current && (
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-gray-400">当前显示的是大纲格式。</span>
                  <button
                    onClick={() => {
                      setInputText(originalContentRef.current)
                      originalContentRef.current = ''
                      setNotification({ type: 'info', message: '已恢复原始输入内容' })
                      setTimeout(() => setNotification(null), 3000)
                    }}
                    className="text-primary-600 hover:text-primary-700 underline"
                  >
                    恢复原始内容
                  </button>
                </div>
              )}

              <RequirementsPanel value={requirements} onChange={setRequirements} />

              <TemplateSelector
                templates={templates}
                loadingTemplates={loadingTemplates}
                customTemplateId={customTemplateId}
                onSelectTemplate={(id) => setCustomTemplateId(id)}
                onToggle={(val) => setUseCustomTemplate(val)}
              />

              <StyleSelector customStyle={customStyle} onChange={setCustomStyle} />
              <PromptSelector selectedPrompt={selectedPrompt} onSelectPrompt={setSelectedPrompt} />

              {(selectedMode === 'ai_network' || selectedMode === 'local_ollama') && (
                <ModelSelector
                  mode={selectedMode}
                  ollamaChecking={ollamaChecking}
                  ollamaDetected={ollamaDetected}
                  ollamaLocalModels={ollamaLocalModels}
                  storedModels={storedModels}
                  selectedModelId={selectedModelId}
                  onSelect={setSelectedModelId}
                />
              )}

              <GenerateBar
                generating={generating}
                inputText={inputText}
                error={error}
                onGenerate={handleGenerate}
                onGenerateOutline={handleGenerateOutline}
                outlineGenerating={outlineGenerating}
                autoMode={false}
              />
            </>
          )}

          <ProgressModal
            isOpen={showProgress}
            onClose={() => setShowProgress(false)}
            taskId={currentTaskId}
          />

          {showOutlineReview && (
            <OutlineReview
              title={outlineTitle}
              slides={outlineSlides}
              generating={outlineGenerating}
              onConfirm={handleConfirmOutline}
              onRegenerate={handleGenerateOutline}
              onCancel={() => setShowOutlineReview(false)}
              onEditSlide={handleEditOutlineSlide}
            />
          )}
        </>
      )}
    </div>
  )
}

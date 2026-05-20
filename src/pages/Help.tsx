import {
  Sparkles, FileText, LayoutTemplate, Cpu, Download, Monitor, Zap,
  FileUp, Globe, WifiOff, Keyboard, Shield, RefreshCw, Save,
} from 'lucide-react'

const features = [
  {
    icon: Sparkles,
    title: 'AI 智能生成',
    desc: '接入 DeepSeek、GPT-4o、Claude 等十余种主流大模型，输入主题或粘贴内容即可一键生成专业演示文稿。API Key 安全加密存储于本地，生成请求不传输密钥。',
  },
  {
    icon: Cpu,
    title: '离线规则引擎',
    desc: '无需 AI 服务也能生成 PPT。内置智能分段算法，自动拆分文本、匹配布局、填充内容，联网/断网均可使用。',
  },
  {
    icon: Shield,
    title: '保险行业模板',
    desc: '内置业务复盘、领导指示、启动会、产说会、创说会、经营复盘、述职、培训等 10 种保险会议模板，支持 Excel 数据驱动填充。',
  },
  {
    icon: LayoutTemplate,
    title: '20+ 视觉主题',
    desc: '内置专业蓝、暗色现代、简洁白、赛博霓虹等 21 套完整主题。模板列表从后端动态获取，新增主题自动出现。',
  },
  {
    icon: FileUp,
    title: '多格式输入',
    desc: '支持直接输入文本、上传 PDF / DOCX / MD / TXT 文件、输入网页 URL 自动抓取，保险场景支持上传 Excel 自动匹配。',
  },
  {
    icon: Download,
    title: '所见即所得导出',
    desc: '导出 PPTX 时使用编辑器中的当前数据直接拼装，而非重新生成，确保导出结果与预览完全一致。',
  },
  {
    icon: Save,
    title: '自动持久化',
    desc: '项目列表、生成配置自动保存到本地存储，页面刷新或关闭后重新打开，数据不丢失。',
  },
  {
    icon: WifiOff,
    title: '离线可用',
    desc: '检测到本地 Ollama 服务时自动启用离线模式，完全本地运行，数据不上传。Ollama + 规则引擎双重离线保障。',
  },
]

const usageSteps = [
  {
    step: 1,
    title: '配置 AI 模型',
    desc: '首次使用前往「设置」页面添加 AI 模型（支持 DeepSeek、GPT、Claude 等），输入 API Key 并点击「连通测试」验证。Key 安全存储于本地，不随请求发送。',
  },
  {
    step: 2,
    title: '选择场景与会议类型',
    desc: '在仪表盘选择场景（报告/教育/提案/转换/研讨/保险）。选择保险场景后还需指定会议类型（如业务复盘会、产品说明会等），系统自动匹配专业提示词和模板。',
  },
  {
    step: 3,
    title: '输入内容',
    desc: '输入主题描述或粘贴 Markdown 大纲。也可上传 PDF/DOCX 文件自动转换，或输入网页链接抓取内容。保险场景可上传 Excel，系统自动解析并映射到对应模板。',
  },
  {
    step: 4,
    title: '选择模板与提示词（可选）',
    desc: '可从 20+ 内置主题中选择视觉效果，或使用默认模板。高级用户可选择特定的提示词策略（如金字塔原理、SCQA 框架等）。',
  },
  {
    step: 5,
    title: '点击生成',
    desc: '点击「生成 PPT」按钮（Ctrl+Enter），系统调用 AI 或规则引擎生成结构化幻灯片，展示 SVG 预览。生成时可随时关闭页面，请求会自动取消。',
  },
  {
    step: 6,
    title: '编辑调整',
    desc: '在编辑器中可拖拽元素位置、调整大小、修改文字。支持撤销/重做（Ctrl+Z / Ctrl+Shift+Z），切换备注和质检面板。',
  },
  {
    step: 7,
    title: '导出 PPTX',
    desc: '满意后点击「导出 PPTX」按钮，系统使用当前编辑器中的幻灯片数据直接生成原生 PPTX 文件，而非重新调用 AI，保证一致性。',
  },
]

const shortcuts = [
  { keys: 'Ctrl + Enter', desc: '快速生成演示文稿' },
  { keys: 'Ctrl + Z', desc: '撤销上一步操作' },
  { keys: 'Ctrl + Shift + Z', desc: '重做已撤销操作' },
  { keys: 'Delete / Backspace', desc: '删除选中的画布元素' },
  { keys: '方向键 ↑↓', desc: '切换上一张/下一张幻灯片' },
  { keys: '方向键 ← →', desc: '演示模式下翻页' },
  { keys: 'Esc', desc: '退出演示模式 / 取消选中元素' },
  { keys: 'F', desc: '演示模式切换全屏' },
  { keys: 'N', desc: '演示模式显示/隐藏备注' },
  { keys: 'T', desc: '演示模式暂停/继续计时器' },
]

export function Help() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-8">
      <section>
        <h1 className="text-2xl font-bold text-gray-800 mb-1">帮助与指南</h1>
        <p className="text-sm text-gray-500">
          AIPPTXPLUS — AI 驱动的智能演示文稿生成工具 | v1.0.0
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary-600" />
          核心亮点
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {features.map((feat) => {
            const Icon = feat.icon
            return (
              <div key={feat.title} className="card p-4 flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-primary-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-700">{feat.title}</h3>
                  <p className="text-xs text-gray-500 mt-1 leading-relaxed">{feat.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Monitor className="w-5 h-5 text-primary-600" />
          使用方法
        </h2>
        <div className="space-y-4">
          {usageSteps.map((item) => (
            <div key={item.step} className="card p-4 flex items-start gap-4">
              <div className="w-7 h-7 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-bold shrink-0">
                {item.step}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-700">{item.title}</h3>
                <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Globe className="w-5 h-5 text-primary-600" />
          支持的 AI 模型
        </h2>
        <div className="card p-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            支持 <strong>DeepSeek</strong>（深度求索）、<strong>通义千问</strong>（阿里云）、
            <strong>豆包</strong>（火山引擎）、<strong>智谱 GLM</strong>、<strong>Moonshot</strong>（月之暗面）、
            <strong>讯飞星火</strong>、<strong>腾讯混元</strong>、<strong>文心一言</strong>（百度）、
            <strong>OpenAI GPT-4o</strong>、<strong>Anthropic Claude</strong>、<strong>Google Gemini</strong>、
            <strong>Ollama</strong>（本地部署）等十余种模型。
          </p>
          <ul className="mt-2 space-y-1 text-sm text-gray-500">
            <li>• 在「设置」页面添加模型，API Key 通过加密通道传入后端内存存储，不会落盘或随生成请求传输</li>
            <li>• 点击「连通测试」按钮验证连接状态，后端会逐步诊断 DNS/TCP/HTTP 各层</li>
            <li>• 检测到本地 Ollama 服务后自动展示可用模型列表，无需配置 API Key</li>
          </ul>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-600" />
          保险数据驱动模式
        </h2>
        <div className="card p-4 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            选择「保险」场景后，系统进入数据驱动模式，支持 Excel 上传自动填充会议模板：
          </p>
          <ul className="space-y-1 text-sm text-gray-500">
            <li>• 上传 Excel 文件自动解析工作表和数据行</li>
            <li>• 模糊匹配列名到模板字段（支持多命名习惯）</li>
            <li>• 自动进行数据校验（数值一致性、百分比范围等）</li>
            <li>• 可选调用 AI 生成分析评述文本（如对标诊断）</li>
            <li>• 10 种保险会议模板：业务复盘、领导指示、启动会、产说会、创说会、服务权益、经营复盘、述职、培训、落后述职</li>
          </ul>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Keyboard className="w-5 h-5 text-primary-600" />
          快捷键
        </h2>
        <div className="card p-4">
          <div className="space-y-2">
            {shortcuts.map((item) => (
              <div key={item.keys} className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{item.desc}</span>
                <code className="px-2 py-0.5 bg-gray-100 rounded text-xs font-mono text-gray-700">
                  {item.keys}
                </code>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="text-right text-sm text-gray-500 pt-4 border-t border-gray-200">
        <p>作者：何克霖</p>
        <p>福建 龙岩</p>
        <p>2026.05</p>
      </div>
    </div>
  )
}
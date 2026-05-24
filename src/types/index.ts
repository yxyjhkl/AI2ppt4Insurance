declare global {
  interface Window {
    electronAPI?: {
      openFile: (filters: { name: string; extensions: string[] }[]) => Promise<{ canceled: boolean; filePaths: string[] }>
      saveFile: (filters: { name: string; extensions: string[] }[]) => Promise<{ canceled: boolean; filePath: string }>
      getBackendUrl: () => Promise<string>
      onFileOpened: (callback: (filePath: string) => void) => void
      onNewProject: (callback: () => void) => void
      onBackendStatus: (callback: (status: { status: string; message?: string }) => void) => void
      getBackendStatus: () => Promise<{ ready: boolean }>
      removeAllListeners: (channel: string) => void
      secureStore?: {
        set: (key: string, value: string) => Promise<boolean>
        get: (key: string) => Promise<string | null>
        delete: (key: string) => Promise<boolean>
        has: (key: string) => Promise<boolean>
      }
    }
  }
}

export type SceneType = 'report' | 'education' | 'proposal' | 'transform' | 'brainstorm' | 'insurance' | 'enhance'

export type InsuranceMeetingType =
  | 'business_review'
  | 'leadership_instruction'
  | 'business_launch'
  | 'product_seminar'
  | 'entrepreneur_seminar'
  | 'service_rights'
  | 'operation_review'
  | 'business_report'
  | 'product_training'
  | 'underperformer_review'

export const INSURANCE_MEETING_LABELS: Record<InsuranceMeetingType, string> = {
  business_review: '业务对标复盘会',
  leadership_instruction: '领导会议总结与指示',
  business_launch: '业务启动会（战役启动）',
  product_seminar: '产品说明会（产说会）',
  entrepreneur_seminar: '创业说明会（创说会）',
  service_rights: '服务权益说明会',
  operation_review: '经营复盘会',
  business_report: '绩优分享会',
  product_training: '产品培训',
  underperformer_review: '落后述职会',
}

export const INSURANCE_MEETING_DESC: Record<InsuranceMeetingType, string> = {
  business_review: '先进与落后对标复盘，数据驱动的问题诊断',
  leadership_instruction: '领导讲话、方向指示、战略部署',
  business_launch: '战役启动、目标分解、激励动员',
  product_seminar: '产品路演、卖点展示、促单转化',
  entrepreneur_seminar: '事业机会、收入模型、成长路径',
  service_rights: '服务介绍、权益说明、客户沟通',
  operation_review: '经营数据分析、问题诊断、改进措施',
  business_report: '业绩汇报、工作述职、能力展示',
  product_training: '产品知识、话术培训、通关考核',
  underperformer_review: '问题剖析、改进承诺、帮扶方案',
}

export interface InsuranceMeetingPromptInfo {
  label: string
  desc: string
  role: string
  task: string
  structure: string
  design: string
}

export const INSURANCE_MEETING_PROMPTS: Record<InsuranceMeetingType, InsuranceMeetingPromptInfo> = {
  business_review: {
    label: '业务对标复盘会',
    desc: '先进与落后对标复盘，数据驱动的问题诊断与改进方案',
    role: '保险行业数据分析师与对标改进顾问，精通保费/件数/继续率/活动率/人均产能/投产比等多维度指标评估',
    task: '分析业务数据或会议纪要，覆盖业绩达成、队伍KPI、投产效率等核心维度，同时展示先进机构亮点经验与落后机构问题诊断',
    structure: '封面 → 议程 → KPI仪表盘 → 队伍KPI → 投产效率 → 继续率/内涵价值 → 荣誉对标 → 问题诊断 → 改进措施 → 承诺追踪 → 总结',
    design: '深蓝#1a365d主色 + 金色点缀；🟢(前30%)/🟡(30-70%)/🔴(后30%)排行标注；柱状图对比+折线图趋势',
  },
  leadership_instruction: {
    label: '领导会议总结与指示',
    desc: '领导讲话、方向指示、战略部署的传达与任务分解',
    role: '保险行业战略传达与任务分解专家，擅长将领导讲话转化为结构化战略传达材料',
    task: '精准提炼领导核心思想3-5条，将战略方向分解为可执行的部门级任务，设置明确时间节点和责任人，保留领导金句',
    structure: '封面 → 核心精神(金句引用) → 三大战略方向 → 形势分析 → 核心指标 → 重点任务部署 → 资源配置 → 执行保障 → 动员总结',
    design: '沉稳蓝#1e3a5f主色 + 金色点缀；金句用content_quote大号斜体；任务表格含序号/名称/标准/部门/时限/优先级',
  },
  business_launch: {
    label: '业务启动会（战役启动）',
    desc: '战役启动、目标分解、激励动员、军令状签署',
    role: '保险行业战役启动策划专家，擅长将业务目标转化为有战斗力的战役方案',
    task: '渲染战役背景与紧迫感，科学分解总目标到团队/个人，设计竞赛规则与激励方案，制定推进节奏与检视节点',
    structure: '封面(战役名称+口号) → 战前形势 → 目标分解 → 三大战区 → 竞赛规则 → 激励方案(KPI卡片) → 推进节奏 → 军令状 → 动员总结',
    design: '红色#c53030主色(战役氛围) + 金色点缀；目标数字大号字体突出；🚀⚡🔥战役符号；目标之和=总目标',
  },
  product_seminar: {
    label: '产品说明会（产说会）',
    desc: '产品路演、卖点展示、场景化说明、促单转化',
    role: '保险产品营销与路演专家，擅长将复杂保险产品转化为客户语言，通过场景化案例和利益量化打动客户',
    task: '用客户痛点开场，产品利益需量化，至少3个真实场景案例，明确行动呼吁与限时权益，实现从"讲产品"到"讲需求"',
    structure: '封面(产品+卖点) → 客户痛点共鸣 → 市场趋势 → 三大优势 → 保障方案对比 → 客户案例 → 收益测算(KPI) → 限时权益 → 行动号召',
    design: '暖金色#d4a843主色 + 睿智蓝辅色；✅标记优势📊标记数据；保障方案表格对比利益差异；案例标注"以实际保单为准"',
  },
  entrepreneur_seminar: {
    label: '创业说明会（创说会）',
    desc: '事业机会、收入模型、成长路径、团队文化展示',
    role: '保险行业人才招募与事业规划专家，擅长将保险事业机会转化为有吸引力的职业发展故事',
    task: '展示行业前景与市场空间，用真实收入模型演示职业发展路径，至少2个不同背景的成功案例，明确加入流程与支持体系',
    structure: '封面 → 传统vs保险行业对比 → 市场空间(KPI) → 收入成长路径(1/3/5年) → 成功案例 → 三级培训体系 → 团队文化 → 加入流程(4步) → 行动号召',
    design: '活力橙#ea580c主色 + 深蓝辅色；收入大号+KPI卡片；⬆️📈趋势符号；收入标注"仅供参考"；案例脱敏处理',
  },
  service_rights: {
    label: '服务权益说明会',
    desc: '服务介绍、权益说明、客户沟通、服务升级推荐',
    role: '保险客户服务与权益管理专家，擅长将复杂服务权益条款转化为客户易于理解的权益清单',
    task: '用客户语言介绍权益，每种权益配1个真实使用场景，服务升级前后对比，明确权益使用方式与激活条件',
    structure: '封面(VIP质感) → 服务体系全景(健康/出行/生活) → 健康管理 → 出行保障 → 生活服务 → 升级对比 → 使用指南 → 客户见证(金句) → 开启指引',
    design: '尊贵金#b8860b主色 + 深蓝辅色VIP质感；✨🌟尊贵符号；左右分栏对比差异项；金色表头高端感',
  },
  operation_review: {
    label: '经营复盘会',
    desc: '经营数据分析、问题诊断、改进措施、预算调整',
    role: '保险行业经营分析与财务顾问，擅长从财务和运营双重视角审视经营结果，识别费差损溢、投产比异常和现金流风险',
    task: '用KPI仪表盘展示整体经营健康度，利润表逐项分析，识别TOP3利润黑洞并提出止血方案，给出下一周期预算调整建议',
    structure: '封面 → 经营KPI全景 → 收入分析 → 赔付分析 → 费用预算vs实际 → 利润穿透 → TOP3问题诊断 → 改进方案 → 预算调整 → 关键决策',
    design: '财务蓝#1e40af主色 + 警示红负面；KPI大号数字+⬆️⬇️趋势箭头；超支项红色标注；金额精确到千元；区分固定/变动费用',
  },
  business_report: {
    label: '绩优分享会',
    desc: '业绩汇报、工作述职、典范案例分享、经验推广',
    role: '保险行业绩优典范萃取专家，擅长从绩优人员工作中提炼可复制的成功方法论',
    task: '用数据展示绩优成果，萃取3个可复制关键动作/方法，展示客户经营和服务流程，给出转型建议供他人借鉴',
    structure: '封面(荣誉头衔) → 荣誉档案(KPI) → 成长历程 → 核心方法论一 → 核心方法论二 → 客户经营体系 → 标准化工作流 → 心态金句 → 总结邀请',
    design: '成就金#d4a843主色 + 深蓝辅色；⭐🏆荣誉符号；方法论左右分栏(理论+案例)；数据经本人确认；方法具体可操作',
  },
  product_training: {
    label: '产品培训',
    desc: '产品知识、话术培训、通关考核、场景演练',
    role: '保险产品培训师与话术设计师，擅长将复杂产品条款转化为代理人即学即用的话术模板',
    task: '产品核心要素一页讲清，与竞品关键差异对比，至少5个真实场景开口话术，5个常见客户异议及应对，通关考核标准明确',
    structure: '封面 → 产品画像(一页全) → 三大卖点 → 竞品对比 → 目标客群 → 场景话术 → 异议处理 → 促成技巧 → 通关考核 → 关键记忆点',
    design: '专业绿#0f766e主色；💡话术要点⚠️常见误区；"客户说→我们答"对照格式；🟢合格/🟡待改进/🔴不合格；合规要求',
  },
  underperformer_review: {
    label: '落后述职会',
    desc: '问题剖析、改进承诺、帮扶方案、业绩提升计划',
    role: '保险行业绩效改进顾问，擅长客观诊断业绩落后原因，区分能力问题与态度问题，保护个人尊严同时推动改进',
    task: '客观展示业绩差距(本人/团队均值/合格线三维对比)，从活动量/技能/心态三维诊断根因，制定30/60/90天阶梯改进计划，明确帮扶方案',
    structure: '封面 → 差距分析(三维对比) → 趋势分析(6个月) → 活动量诊断 → 技能诊断评分 → 根因剖析 → 阶梯改进计划 → 帮扶方案(双轨) → 承诺签字',
    design: '理性蓝#2563eb主色；柱状图差距对比；🟢改善/🟡持平/🔴下滑标注；改进目标SMART原则；保护个人尊严避免羞辱性表述',
  },
}

export type ExportFormat = 'pptx' | 'pdf' | 'png' | 'html'

export interface Project {
  id: string
  name: string
  scene: SceneType
  slides: Slide[]
  templateId: string
  createdAt: string
  updatedAt: string
  version: number
}

export interface CachedGeneration {
  slides: SlideData[]
  qaResults: QAItem[]
  mode: string
  message: string
  title: string
  content: string
  scene: string
}

export interface Slide {
  id: string
  index: number
  layoutType: LayoutType
  title: string
  content: string
  notes: string
  svgContent?: string
  elements?: CanvasElement[]
  bodyItems?: { type: string; text: string; level: number }[]
}

/**
 * 幻灯片布局类型（17种） —— 核心DSL，决定了每页的渲染方式
 *
 * 结构类（2种）：
 *   cover     - 封面页：大标题+副标题+装饰，仅第一页
 *   ending    - 结束页：感谢/总结/下一步，仅最后一页
 *   chapter   - 章节分隔：深色背景+大标题，分隔大主题（每10页建议1-2个）
 *   toc       - 目录页：编号列表，展示全局结构
 *
 * 文本类（3种）：
 *   content           - 通用内容：编号卡片列表，最常用布局（默认兜底）
 *   content_quote     - 引用页：居中大号引文+来源，适合金句/名人名言
 *   content_code      - 代码页：暗色终端风格，适合技术展示/代码片段
 *
 * 数据类（5种）：
 *   content_table     - 表格页：Markdown表格，斑马纹，状态emoji着色
 *   content_kpi       - KPI仪表盘：大号数字卡片(最多4列8个)，百分比进度条
 *   content_gauge     - 仪表盘：环形进度环，多KPI达成率可视化
 *   content_waterfall - 瀑布图：分步数值变化（如保费→佣金→利润）
 *   content_ranking   - 排行榜：横向柱状条，金银铜牌，适合业绩排行
 *
 * 对比类（2种）：
 *   content_two_col   - 双栏对比：左右分栏，适合A-vs-B、优缺点
 *   content_three_col - 三栏框架：三大支柱/三维度，如战略-运营-财务
 *
 * 分析类（3种）：
 *   content_compare   - 前后对比：Before/After卡片，自动计算变化率
 *   content_matrix    - 2×2矩阵：SWOT分析/BCG矩阵等四象限框架
 *   content_funnel    - 漏斗图：销售管道/客户转化阶段可视化
 *
 * 时间类（1种）：
 *   content_timeline  - 时间轴：左右交替节点，适合项目路线图/里程碑
 */
export type LayoutType =
  | 'cover'
  | 'toc'
  | 'chapter'
  | 'content'
  | 'content_two_col'
  | 'content_three_col'
  | 'content_table'
  | 'content_code'
  | 'content_quote'
  | 'content_compare'
  | 'content_kpi'
  | 'content_matrix'
  | 'content_timeline'
  | 'content_waterfall'
  | 'content_gauge'
  | 'content_ranking'
  | 'content_funnel'
  | 'ending'

export interface Template {
  id: string
  name: string
  category: string
  preview: string
  colors: ColorScheme
  fonts: FontPair
  layouts: Partial<Record<LayoutType, string>>
}

export interface ColorScheme {
  primary: string
  secondary: string
  accent: string
  background: string
  text: string
}

export interface FontPair {
  title: string
  body: string
}

export interface AIModel {
  id: string
  name: string
  provider: 'openai' | 'anthropic' | 'gemini' | 'deepseek' | 'qwen' | 'zhipu' | 'ollama' | 'custom'
  baseUrl: string
  apiKey: string
  models: string[]
}

export interface GenerationConfig {
  scene: SceneType
  meetingType: InsuranceMeetingType | null
  template: string
  model: string
  slideCount: number
  language: string
  includeNotes: boolean
  includeImages: boolean
  includeAnimation: boolean
  temperature: number
  canvasFormat: string
}

export interface NetworkStatus {
  online: boolean
  ollamaAvailable: boolean
  backendReady: boolean
}

export interface GenerationResult {
    project_id: string
    title: string
    scene: string
    template_id: string
    mode: string
    message: string
    slide_count: number
    slides: SlideData[]
    qa_results: QAItem[]
    preview_slides: string[]
    file_id?: string
}

export interface SlideData {
  page_number: number
  layout_type: string
  title: string
  subtitle: string | null
  body_items: { type: string; text: string; level: number }[]
  images: { src: string; alt: string }[]
  tables: { markdown: string }[]
  code_block: string | null
  notes: string
  svg_preview: string
  elements?: CanvasElement[]
}

export interface EditorState {
  slides: SlideData[]
  selectedSlide: number
  selectedElement: string | null
  hoveredElement: string | null
  canvasScale: number
  history: EditorHistory[]
  historyIndex: number
}

export interface EditorHistory {
  slides: SlideData[]
  selectedSlide: number
}

export interface QAItem {
  severity: 'error' | 'warning' | 'info'
  level?: 'P0' | 'P1' | 'P2' | 'P3'
  category: string
  slide: number
  message: string
  detail: string | null
}

export type CanvasElementType = 'text' | 'image' | 'shape' | 'table'

export type EntranceEffectName =
  | 'none'
  | 'fadeIn'
  | 'flyInLeft' | 'flyInRight' | 'flyInTop' | 'flyInBottom'
  | 'flyInTopLeft' | 'flyInTopRight' | 'flyInBottomLeft' | 'flyInBottomRight'
  | 'zoomIn' | 'zoomOutBounce'
  | 'wipeLeft' | 'wipeRight' | 'wipeUp' | 'wipeDown'
  | 'splitHorizontalIn' | 'splitVerticalIn'
  | 'boxIn' | 'boxOut'
  | 'circleIn' | 'diamondIn' | 'plusIn'
  | 'wedgeIn' | 'stripsLeftUp' | 'stripsRightDown'
  | 'randomBarsHorizontal' | 'randomBarsVertical'
  | 'checkerboardAcross' | 'checkerboardDown'
  | 'dissolveIn'
  | 'appear'
  | 'floatIn' | 'floatUp' | 'floatDown'
  | 'spinIn' | 'swivelIn' | 'swishIn'
  | 'growShrink'
  | 'curveUp' | 'curveDown'
  | 'compassIn' | 'glideIn'
  | 'foldIn'
  | 'pinWheel'
  | 'bounceIn' | 'bounceLeft' | 'bounceRight' | 'bounceUp' | 'bounceDown'
  | 'peekIn'
  | 'crawlInLeft' | 'crawlInRight' | 'crawlInUp' | 'crawlInDown'
  | 'wheel4Spoke'

export const ENTRANCE_EFFECT_LABELS: Record<EntranceEffectName, string> = {
  none: '无动画',
  fadeIn: '淡入',
  flyInLeft: '飞入-左', flyInRight: '飞入-右', flyInTop: '飞入-上', flyInBottom: '飞入-下',
  flyInTopLeft: '飞入-左上', flyInTopRight: '飞入-右上', flyInBottomLeft: '飞入-左下', flyInBottomRight: '飞入-右下',
  zoomIn: '放大进入', zoomOutBounce: '缩小弹入',
  wipeLeft: '擦除-左', wipeRight: '擦除-右', wipeUp: '擦除-上', wipeDown: '擦除-下',
  splitHorizontalIn: '水平分割', splitVerticalIn: '垂直分割',
  boxIn: '盒状进入', boxOut: '盒状展开', circleIn: '圆形进入', diamondIn: '菱形进入', plusIn: '十字进入',
  wedgeIn: '楔形进入', stripsLeftUp: '条纹-左上', stripsRightDown: '条纹-右下',
  randomBarsHorizontal: '随机横条', randomBarsVertical: '随机竖条',
  checkerboardAcross: '棋盘-横向', checkerboardDown: '棋盘-纵向',
  dissolveIn: '溶解',
  appear: '出现',
  floatIn: '浮入', floatUp: '上浮', floatDown: '下浮',
  spinIn: '旋转进入', swivelIn: '翻转进入', swishIn: '挥鞭进入',
  growShrink: '放大缩小',
  curveUp: '曲线向上', curveDown: '曲线向下',
  compassIn: '指南针', glideIn: '滑翔',
  foldIn: '折叠',
  pinWheel: '风车',
  bounceIn: '弹跳', bounceLeft: '弹跳-左', bounceRight: '弹跳-右', bounceUp: '弹跳-上', bounceDown: '弹跳-下',
  peekIn: '窥视',
  crawlInLeft: '爬行-左', crawlInRight: '爬行-右', crawlInUp: '爬行-上', crawlInDown: '爬行-下',
  wheel4Spoke: '轮子-4辐',
}

export interface CanvasElement {
  id: string
  type: CanvasElementType
  x: number
  y: number
  width: number
  height: number
  rotation: number
  opacity: number
  zIndex: number
  locked?: boolean
  content: string
  animation?: EntranceEffectName
  style: {
    fontFamily?: string
    fontSize?: number
    fontWeight?: string
    fontStyle?: string
    color?: string
    backgroundColor?: string
    borderColor?: string
    borderWidth?: number
    borderRadius?: number
    fillColor?: string
    textAlign?: 'left' | 'center' | 'right'
  }
}

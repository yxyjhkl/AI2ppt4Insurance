export {}

declare global {
  interface Window {
    electronAPI?: {
      openFile: (filters: { name: string; extensions: string[] }[]) => Promise<{ canceled: boolean; filePaths: string[] }>
      saveFile: (filters: { name: string; extensions: string[] }[]) => Promise<{ canceled: boolean; filePath: string }>
      getBackendUrl: () => Promise<string>
      onFileOpened: (callback: (filePath: string) => void) => void
      onNewProject: (callback: () => void) => void
      secureStore?: {
        set: (key: string, value: string) => Promise<boolean>
        get: (key: string) => Promise<string | null>
        delete: (key: string) => Promise<boolean>
        has: (key: string) => Promise<boolean>
      }
    }
  }
}

export type SceneType = 'report' | 'education' | 'proposal' | 'transform' | 'brainstorm' | 'insurance'

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
  business_report: '业务述职会',
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
}

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

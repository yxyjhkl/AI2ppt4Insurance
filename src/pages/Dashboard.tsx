import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Globe, Type, Sparkles, Upload, Loader2, Check, Shield, FileSpreadsheet, Table2, X, AlertCircle } from 'lucide-react'
import { useProjectStore } from '@/stores/projectStore'
import { apiConfig, createAbortableFetch } from '@/utils/api'
import { getObject } from '@/utils/secureStore'
import type { SceneType, InsuranceMeetingType } from '@/types'
import { INSURANCE_MEETING_LABELS, INSURANCE_MEETING_DESC } from '@/types'

const scenes: { type: SceneType; label: string; desc: string; icon: typeof Sparkles }[] = [
  { type: 'report', label: '报告', desc: '年度报告、商业分析、研究报告', icon: FileText },
  { type: 'education', label: '教育', desc: '课件、培训、知识分享', icon: Sparkles },
  { type: 'proposal', label: '提案', desc: '产品规划、项目路演、商业计划', icon: Globe },
  { type: 'transform', label: '转换', desc: '文档、报告、文章转幻灯片', icon: Upload },
  { type: 'brainstorm', label: '研讨', desc: '主题大纲结构设计', icon: Type },
  { type: 'insurance', label: '保险', desc: '保险行业专项会议模板', icon: Shield },
]

const inputMethods = [
  { id: 'text', label: '输入主题', icon: Type },
  { id: 'file', label: '上传文件', icon: Upload },
  { id: 'url', label: '粘贴 URL', icon: Globe },
]

const templateCategories = ['全部', '报告', '保险', '提案', '科技', '创意', '教育']

const CATEGORY_MAP: Record<string, string> = {
  'report': '报告', 'Report': '报告', '保险': '保险', 'Insurance': '保险',
  'proposal': '提案', 'Proposal': '提案', '科技': '科技', 'Tech': '科技',
  'creative': '创意', 'Creative': '创意', '教育': '教育', 'Education': '教育',
}

const promptCategories = [
  {
    id: 'report',
    label: '报告',
    prompts: [
      { title: '金字塔原理结构', content: '使用 MECE 原则组织年度报告。先给出核心结论，再用 3 个论点支撑，每个论点配数据证据。风格：专业、数据驱动。' },
      { title: 'SCQA 框架', content: '使用 SCQA 框架组织商业分析：情境 → 冲突 → 问题 → 答案。每部分需有清晰的数据可视化和关键结论。' },
      { title: '执行摘要前置', content: '先用 1 页执行摘要总结关键发现，再深入分析并配图表。最后给出可执行的建议。' },
      { title: '数据驱动月报', content: '按以下结构生成月度业务报告：核心KPI仪表盘 → 同比/环比趋势分析 → 亮点与不足 → 下月行动计划。每页不超过5条关键信息。' },
      { title: '会议总结模板', content: '将会议内容总结为：会议目标 → 关键决议（不超过5条） → 待办事项（含负责人+截止日期） → 下次会议议程。使用行动导向的语言。' },
    ],
  },
  {
    id: 'education',
    label: '教育',
    prompts: [
      { title: '渐进式学习路径', content: '按以下结构设计课程模块：引入 → 概念 → 示例 → 练习 → 总结。复杂概念搭配类比和可视化图表。' },
      { title: '互动式教学', content: '按以下结构组织培训材料：学习目标 → 前测 → 核心内容（分块） → 小组活动 → 问答 → 后测。' },
      { title: '微课讲稿结构', content: '每节微课控制在5-8页：痛点引入 → 核心概念 → 操作演示 → 常见误区 → 小结练习。每页保留"讲师备注"栏。' },
      { title: '学术答辩模板', content: '按学术答辩标准组织：研究背景与意义 → 文献综述 → 研究方法 → 实验设计与结果 → 创新点总结 → 未来工作。突出原创贡献。' },
    ],
  },
  {
    id: 'proposal',
    label: '提案',
    prompts: [
      { title: '问题-方案-价值', content: '使用 FAB（特性-优势-收益）框架。每页幻灯片应：陈述痛点 → 展示方案 → 量化商业价值。' },
      { title: '故事化路演', content: '按英雄旅程组织路演：现状 → 冲突 → 产品解决方案 → 成功愿景。加入客户案例。' },
      { title: '投资者演示', content: '生成专业投资路演：公司愿景 → 市场机会（TAM/SAM/SOM） → 产品/技术壁垒 → 商业模式 →  traction数据 → 团队背景 → 融资需求与用途。每页突出一个核心数字。' },
      { title: '竞品对标分析', content: '生成竞品分析幻灯片：市场格局总览 → 竞品矩阵（功能/价格/市场） → 我方差异化优势 → SWOT对比 → 战略建议。使用对比表格和雷达图。' },
      { title: '咨询级商业提案', content: '按顶级咨询公司标准生成：执行摘要 → 当前挑战诊断 → 推荐方案（含实施路线图） → 预期收益量化 → 风险与应对 → 下一步建议。每页底部保留关键结论栏。' },
    ],
  },
  {
    id: 'transform',
    label: '转换',
    prompts: [
      { title: '一对一映射', content: '保留原始文档结构：每个 H1/H2 对应一页幻灯片，段落转为要点。保留所有数据和引用原文。' },
      { title: '执行摘要', content: '将文档压缩至 1/3 长度。仅提取：关键发现、支撑证据（每条最多 3 点）和行动项。' },
      { title: '80/20 精华提取', content: '遵循帕累托原则：识别文档中20%最重要的内容 → 每章提取1-2个核心观点 → 删除重复和冗余 → 保留关键数据 → 重组为5-10页精华版。' },
      { title: '会议纪要转行动清单', content: '将会议纪要转换为：会议主题（1页） → 决议事项（每项1页，含背景+决议+理由） → 行动项跟踪表（负责人/DDL/状态）。' },
    ],
  },
  {
    id: 'brainstorm',
    label: '研讨',
    prompts: [
      { title: '第一性原理', content: '针对主题：拆解至第一性原理 → 重新构建 → 识别关键假设 → 提出创新方案。' },
      { title: '设计思维', content: '围绕以下阶段组织：共情 → 定义 → 构思 → 原型 → 测试。每阶段包含关键问题和预期输出。' },
      { title: '战略规划工作坊', content: '按战略规划流程组织：愿景与使命回顾 → 外部环境分析（PESTEL） → 内部能力评估 → 战略选项生成 → 优先级排序矩阵 → 实施路线图。' },
      { title: '六顶思考帽', content: '按六顶思考帽框架组织：白帽（事实数据） → 红帽（直觉感受） → 黑帽（风险问题） → 黄帽（价值机会） → 绿帽（创新方案） → 蓝帽（总结控制）。' },
    ],
  },
  {
    id: 'business',
    label: '商业',
    prompts: [
      { title: '季度业务复盘', content: '按以下结构生成QBR演示：QOQ关键指标对比 → 收入/成本/利润深度分析 → 业务线红绿灯评估 → 市场环境变化 → 下季度重点举措（3-5项）。使用红黄绿状态标识。' },
      { title: '产品发布会', content: '按苹果式发布会结构：现状痛点（1页） → 产品亮点（1页/功能，最多3个） → 现场演示（流程页） → 定价与上市时间 → One More Thing惊喜环节。每页极简，图片主导。' },
      { title: '组织架构调整', content: '生成组织变革沟通材料：变革背景与必要性 → 新架构全景图 → 各部门职责变化 → 人员安排 → 过渡时间表 → Q&A。语气：坦诚、积极、清晰。' },
    ],
  },
  {
    id: 'insurance',
    label: '保险',
    prompts: [
      { title: '业务对标复盘会', content:
`<role>保险业务数据分析师与对标改进顾问</role>
<task>分析提供的业务数据，生成对标复盘PPT。涵盖业绩达成、队伍KPI、投产效率等多维度。先进分享亮点与优秀做法，落后剖析问题根源与制定改进计划。</task>
<structure_spec>
- 封面（1页）：会议主题、时间、机构名称
- 议程（1页）：对标议程安排
- 直接创造价值（1页）：保费达成、件数达成、增幅
- 队伍KPI（1页）：出勤率、人均产能、活动率
- 投产效率（1页）：费差损溢、总体投产比
- 继续率与内涵价值（1页）：13J/25J继续率、新业务价值
- 荣誉展示（1页）：IDA/MDRT达成、MCI晋级
- 问题诊断（2页）：偏差分析+根本原因
- 改进措施（1页）：具体补救方案与时间表
- 承诺与追踪（1页）：各级承诺+督导机制
- 领导总结与资源承诺（1页）
</structure_spec>
<design_requirements>配色：深蓝#1a365d+金色点缀，专业保险风格。图表：柱状/折线/雷达图用于排名。每页不超过5条摘要信息。</design_requirements>
<constraints>使用数据生成时插入JSON模板中的班级信息。表格数据保留2位小数。</constraints>` },
      { title: '领导会议总结与指示', content:
`<role>保险行业高管助理与战略沟通顾问</role>
<task>基于领导讲话与会议纪要，提炼领导核心思想生成总结PPT。涵盖整体评价、形势判断、指导方针、定量指示和资源承诺。</task>
<structure_spec>
- 封面（1页）：会议主题、日期、机构
- 会议概述（1页）：会议背景与核心议题
- 整体评价（1页）：成绩肯定、问题定性
- 形势分析（1页）：外部宏观环境、行业趋势、竞争态势
- 战略方针（1页）：指导思想、核心原则
- 定量指标（2页）：各条线/各层级分解指标
- 资源承诺（1页）：人力、财务、技术、政策支持
- 责任矩阵（1页）：RACI矩阵明确责任人
- 奖惩机制（1页）：考核标准与挂钩方案
- 动员号召（1页）：感性号召+行动召唤
</structure_spec>
<design_requirements>配色：政务红#c53030+金色点缀，庄重正式。字体：标题使用加粗黑体。</design_requirements>
<constraints>引述领导原话用引号标注。量化指标需精确到具体数字。</constraints>` },
      { title: '业务启动会', content:
`<role>保险业务推动与战役启动策划师</role>
<task>设计战前动员PPT。回顾过往成绩建立信心，展望新战役目标，拆解策略路径，激励团队士气，组织签署承诺。</task>
<structure_spec>
- 封面：XX战役启动大会
- 成绩回顾（1页）：上一战役亮点数据
- 英雄榜（1页）：先进团队/个人表彰
- 新战役全景（1页）：目标、时间、规则
- 目标分解（1页）：各层级目标拆解
- 策略路径（1页）：达成目标的战法
- 激励方案（1页）：奖项设置与奖励标准
- 表态承诺（1页）：各级代表签署军令状
- 领导动员（1页）：战前动员讲话
- 出征仪式（1页）：团队誓师
</structure_spec>
<design_requirements>配色：热烈红色+金色，高能量氛围。使用大号数字突出目标。</design_requirements>
<constraints>目标数据精确。保持激励氛围，避免负面信息。</constraints>` },
      { title: '产品说明会', content:
`<role>保险产品营销策划师</role>
<task>设计面向客户的产品说明会PPT。发掘客户痛点，展示产品解决方案，呈现公司实力，使用促成技巧推动成交。</task>
<structure_spec>
- 封面：产品名称+一句话slogan
- 现状分析（1页）：客户面临的保障缺口与风险
- 解决方案（2页）：产品核心卖点（1页1个）
- 产品实力（2页）：公司偿付能力、理赔数据、市场规模
- 客户案例（1页）：真实理赔案例故事
- 增值服务（1页）：附加权益与服务
- 限时权益（1页）：当期优惠政策对比
- 行动指引（1页）：购买流程、联系方式
- 答疑互动（1页）：常见问题解答
</structure_spec>
<design_requirements>配色：温暖金色+渐变，强调信任感。多使用图片和图表。</design_requirements>
<constraints>避免过度销售话术，保持专业可信。案例需匿名化处理。</constraints>` },
      { title: '创业说明会', content:
`<role>保险行业创业顾问与招募专家</role>
<task>设计面向潜在合伙人的创业说明PPT。展现行业前景、收入模型、成长路径、公司支持体系，激发事业渴望。</task>
<structure_spec>
- 封面：事业邀请主题
- 行业趋势（1页）：保险行业发展数据与红利
- 为什么选择我们（1页）：公司品牌、文化、口碑
- 收入模型（1页）：薪酬制度、晋升阶梯、奖金机制
- 成长路径（1页）：培训体系、职涯规划
- 成功案例（1页）：真实收入案例展示
- 支持体系（1页）：公司提供的展业资源
- 团队文化（1页）：团队氛围与文化活动
- 加入流程（1页）：面试培训安排
- 行动号召（1页）：一对一沟通邀约
</structure_spec>
<design_requirements>配色：活力蓝+金色，现代感。多使用真人照片和视频占位符。</design_requirements>
<constraints>收入展示需注明"过往业绩不保证未来收益"。数据来源标注。</constraints>` },
      { title: '服务权益说明会', content:
`<role>保险客户服务顾问与权益沟通专家</role>
<task>基于服务手册或权益条款，设计服务权益说明PPT。通过清晰的服务分类体系、分层权益对比和典型场景示例，让客户快速理解保障与服务内容。</task>
<structure_spec>
- 封面（1页）：服务权益主题+服务价值概括
- 服务全景图（1页）：健康/出行/生活/金融四大类服务一览
- 健康管理服务（1页）：体检、就医绿通、专家预约、健康档案
- 出行保障服务（1页）：紧急救援、贵宾厅、专车等
- 生活尊享与金融服务（1页）：酒店、高端活动、理财顾问
- VIP等级对比（1页）：银卡/金卡/钻石卡权益差异
- 使用场景示例（1页）：有/无权益的体验对比
- 关键条款提示（1页）：使用条件、有效期、免责说明
- 服务激活与联系（1页）：激活方式、热线、在线渠道
</structure_spec>
<design_requirements>配色：专业蓝#1e40af+翡翠绿。图标区分服务大类。</design_requirements>
<constraints>条款以合同为准。免责条款不可遗漏。</constraints>` },
      { title: '经营复盘会', content:
`<role>保险经营管理顾问与数据分析专家</role>
<task>基于经营数据和业务报表，生成经营复盘PPT。采用PDCA逻辑，数据呈现→对标→诊断→改善→行动，每个结论有数据支撑。</task>
<structure_spec>
- 封面（1页）：复盘周期、机构名称
- KPI仪表盘（1页）：保费达成率、利润率、续保率等核心指标
- 保费达成分析（1页）：分渠道/分产品分析
- 利润结构分析（1页）：收入vs成本构成，费差/死差异/利差异
- 人力效能分析（1页）：人均产能、活动率、留存率
- 标杆对标（1页）：与先进机构多维度对比
- 问题根因诊断（1页）：现象表现→根本原因对应
- 客户经营指标（1页）：新客数、继续率、满意度
- 改善方案（1页）：SMART改进措施+责任人+时间节点
- 下期行动计划（1页）：重点任务+目标承诺
</structure_spec>
<design_requirements>配色：深蓝#1e3a5f+琥珀。🟢达标🟡关注🔴预警标识。</design_requirements>
<constraints>财务数据保留2位小数。问题分析必须基于数据事实。改善方案遵循SMART原则。</constraints>` },
      { title: '业务述职会', content:
`<role>保险绩效评估顾问与述职报告专家</role>
<task>基于述职材料和业绩数据，生成专业述职PPT。采用业绩达成→关键成果→能力成长→不足反思→未来规划框架，逻辑闭环且有数据支撑。</task>
<structure_spec>
- 封面（1页）：述职人姓名、岗位、考核周期
- 业绩达成概览（1页）：核心KPI达成+目标vs实际对比表
- 关键工作成果（2页）：重点项目成果详述，配数据
- 过程管理与团队建设（1页）：日常管理动作+团队建设
- 能力成长（1页）：技能提升、培训、自我突破
- 不足与反思（1页）：真诚反思+STAR分析
- 改进措施（1页）：针对性提升计划+时间表
- 下期规划（1页）：目标分解+关键任务+里程碑
- 支持需求与致谢（1页）
</structure_spec>
<design_requirements>配色：商务蓝+深灰，专业稳重。KPI用大号数字+进度条。</design_requirements>
<constraints>业绩数据真实准确。反思需真诚深刻。规划需可量化执行。</constraints>` },
      { title: '产品培训', content:
`<role>保险资深培训讲师与产品专家</role>
<task>基于产品手册，设计产品培训PPT。采用概念→细节→话术→案例→考核五步法。确保学员能讲清卖点、能处理异议、能独立讲解。</task>
<structure_spec>
- 封面（1页）：培训主题、对象、时长、讲师
- 学习目标（1页）：核心能力清单3-5条
- 产品定位与客群（1页）：产品特色+目标客群画像
- 核心保障详解（2页）：逐条讲解+案例说明
- 投保规则速查（1页）：年龄、保额、健康告知等规则表
- 销售话术训练（1页）：错误话术vs标准话术对比
- 异议处理话术（1页）：5大常见异议标准应对策略
- 竞品对比（1页）：差异化优势矩阵
- 案例演练与通关考核（1页）：场景模拟+通过标准
</structure_spec>
<design_requirements>配色：教育蓝#3b82f6。话术训练左右对比，错误红色/正确绿色。</design_requirements>
<constraints>条款以官方为准。话术遵守合规要求。竞品需匿名化。</constraints>` },
      { title: '落后述职会', content:
`<role>保险绩效改进顾问与教练</role>
<task>基于落后团队/个人数据，生成落后述职PPT。以建设性方式深入分析问题，避免批评式氛围。数据诊断→根因分析→方案共创→帮扶落地。</task>
<structure_spec>
- 封面（1页）：述职人/机构、考核周期
- 数据复盘（1页）：KPI达成+差距总览，🔴标注未达标项
- 差距分析（1页）：目标vs实际逐项对比+差距率
- 主观原因剖析（1页）：意愿层面+能力层面鱼骨图分析
- 客观困难分析（1页）：外部环境、竞争、资源因素
- 短期追赶计划（1页）：按周拆解的量化动作
- 中期提升方案（1页）：按月拆解的能力提升计划
- 帮扶需求（1页）：带教、陪访、培训、资源支持
- 改进承诺书（1页）：量化目标+时间节点+签名
- 督导机制与信心展望（1页）
</structure_spec>
<design_requirements>配色：专业蓝+警示橙。差距用红色标注，改善用绿色。60%篇幅聚焦改进。</design_requirements>
<constraints>分析客观不推卸。方案量化可执行。鼓励收尾。不点名批评个人。</constraints>` },
    ],
  },
]

export function Dashboard() {
  const navigate = useNavigate()
  const [selectedScene, setSelectedScene] = useState<SceneType>('report')
  const [meetingType, setMeetingType] = useState<InsuranceMeetingType>('business_review')
  const [inputMethod, setInputMethod] = useState('text')
  const [inputText, setInputText] = useState('')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  const [useCustomTemplate, setUseCustomTemplate] = useState<boolean | null>(null)
  const [customTemplateId, setCustomTemplateId] = useState<string | null>(null)
  const [templateCategory, setTemplateCategory] = useState('全部')

  const [useCustomPrompt, setUseCustomPrompt] = useState<boolean | null>(null)
  const [promptCategory, setPromptCategory] = useState('report')
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null)

  // 用户自定义风格要求
  const [customStyle, setCustomStyle] = useState('')

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

  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null)

  const showNotification = useCallback((type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message })
    if (type !== 'error') {
      setTimeout(() => setNotification(null), 6000)
    }
  }, [])

  const [templates, setTemplates] = useState<{ id: string; name: string; category: string; preview?: string }[]>([])
  const [loadingTemplates, setLoadingTemplates] = useState(true)

  const [ollamaDetected, setOllamaDetected] = useState(false)
  const [ollamaLocalModels, setOllamaLocalModels] = useState<string[]>([])
  const [ollamaChecking, setOllamaChecking] = useState(false)
  const [selectedModelId, setSelectedModelId] = useState('')
  const [storedModels, setStoredModels] = useState<{ model: string; apiKey: string; baseUrl: string; name: string }[]>([])

  const isValidModel = selectedModelId && storedModels.some(m => m.model === selectedModelId)

  useEffect(() => {
    const init = async () => {
      setLoadingTemplates(true)
      try {
        const [tplRes, ollamaRes] = await Promise.all([
          fetch(await apiConfig.url('/api/v1/templates')),
          fetch(await apiConfig.url('/api/v1/ai/check-ollama')),
        ])
        if (tplRes.ok) {
          const tplData = await tplRes.json()
          setTemplates(tplData.map((t: any) => ({
            id: t.id,
            name: t.name || t.id,
            category: CATEGORY_MAP[t.category?.toLowerCase()] || CATEGORY_MAP[t.category] || '通用',
            preview: t.colors?.primary || '#1e40af',
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
    getObject<{ model?: string; apiKey?: string; baseUrl?: string; name?: string }[]>('aippt_models').then(async (saved) => {
      if (saved && saved.length > 0) {
        const mapped = saved.map((m, i) => ({
          model: m.model || '',
          apiKey: m.apiKey || '',
          baseUrl: m.baseUrl || '',
          name: m.name || m.model || `Model ${i + 1}`,
        }))
        setStoredModels(mapped)
        const first = saved[0]
        if (first?.model) {
          setSelectedModelId(first.model)
        }
        for (const m of mapped) {
          if (m.apiKey && m.apiKey !== 'ollama') {
            fetch(await apiConfig.url('/api/v1/ai/configure'), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ model_id: m.model, api_key: m.apiKey, base_url: m.baseUrl }),
            }).catch(() => {})
          }
        }
      } else if (ollamaLocalModels.length > 0) {
        const ollamaEntry = {
          model: ollamaLocalModels[0],
          apiKey: 'ollama',
          baseUrl: 'http://localhost:11434/v1',
          name: 'Ollama Local',
        }
        setStoredModels([ollamaEntry])
        setSelectedModelId(ollamaLocalModels[0])
      }
    })
  }, [ollamaLocalModels])

  const config = useProjectStore((s) => s.generationConfig)
  const updateConfig = useProjectStore((s) => s.updateGenerationConfig)
  const setCurrentProject = useProjectStore((s) => s.setCurrentProject)
  const setLastGeneration = useProjectStore((s) => s.setLastGeneration)

  const handleGenerate = useCallback(async () => {
    if (!inputText.trim()) return

    setGenerating(true)
    setError('')

    const abortController = new AbortController()
    const abortableFetch = createAbortableFetch(abortController.signal)

    const effectiveTemplate = useCustomTemplate && customTemplateId ? customTemplateId : config.template
    const finalContent = selectedPrompt
      ? `【生成指令】${selectedPrompt}\n\n【内容】${inputText}`
      : inputText

    try {
      const currentModelId = selectedModelId || config.model || 'gpt-4o'

      const body = {
        scene: selectedScene,
        meeting_type: selectedScene === 'insurance' ? meetingType : null,
        content: finalContent,
        custom_style: customStyle || null,
        template: effectiveTemplate,
        model: currentModelId,
        slide_count: config.slideCount,
        language: config.language,
        include_notes: config.includeNotes,
        include_images: config.includeImages,
        temperature: config.temperature,
        ai_mode: 'auto',
        canvas_format: config.canvasFormat || '16:9',
        excel_filepath: selectedScene === 'insurance' && excelData ? excelData.filepath : null,
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
        slides: data.slides?.map((s: any, i: number) => ({
          id: `slide_${i}`,
          index: i,
          layoutType: s.layout_type,
          title: s.title,
          content: s.body_items?.map((b: any) => b.text).join('\n') || '',
          notes: s.notes || '',
          svgContent: s.svg_preview || data.preview_slides?.[i] || '',
        })) || [],
        templateId: data.template_id,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        version: 1,
      })

      sessionStorage.setItem('pending_ppt_data', JSON.stringify({
        slides: data.slides || [],
        qa_results: data.qa_results || [],
        mode: data.mode || 'offline',
        message: data.message || '',
        title: data.title || '未命名',
        project_id: data.project_id,
      }))

      navigate(`/editor/new?scene=${selectedScene}&template=${effectiveTemplate}&project=${data.project_id}`)
    } catch (err: any) {
      setError(err.message || '生成失败')
    } finally {
      setGenerating(false)
    }
  }, [inputText, selectedScene, meetingType, selectedPrompt, useCustomTemplate, customTemplateId, config, navigate, setCurrentProject, setLastGeneration, selectedModelId, excelData])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleGenerate()
    }
  }

  const handleExcelUpload = useCallback(async (file: File) => {
    setExcelUploading(true)
    setError('')
    setExcelUploadError('')
    setNotification(null)
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
      setExcelData({
        ...data,
        headers: {},
        summary: data.preview,
      })
      setInputText(data.preview || `Excel文件: ${data.filename}, ${data.row_count}行数据`)
      showNotification('success', `✅ ${data.filename} 上传成功！解析 ${data.row_count} 行数据，${data.sheet_names?.length || 0} 个工作表`)
    } catch (err: any) {
      const errMsg = err.message || 'Excel上传失败'
      setError(errMsg)
      setExcelUploadError(errMsg)
      showNotification('error', `❌ ${errMsg}`)
    } finally {
      setExcelUploading(false)
    }
  }, [showNotification])

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <section>
        <h1 className="text-2xl font-bold text-gray-800 mb-1">新建演示文稿</h1>
        <p className="text-sm text-gray-500">AI 从您的内容生成可编辑的 PPTX</p>
      </section>

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

      <section className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">1. 选择场景</h2>
        <div className="grid grid-cols-6 gap-3">
          {scenes.map((scene) => {
            const Icon = scene.icon
            const isActive = selectedScene === scene.type
            return (
              <button
                key={scene.type}
                onClick={() => setSelectedScene(scene.type)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  isActive
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <Icon className={`w-5 h-5 mb-2 ${isActive ? 'text-primary-600' : 'text-gray-400'}`} />
                <div className={`text-sm font-medium ${isActive ? 'text-primary-700' : 'text-gray-700'}`}>
                  {scene.label}
                </div>
                <div className="text-xs text-gray-400 mt-0.5">{scene.desc}</div>
              </button>
            )
          })}
        </div>
      </section>

      {selectedScene === 'insurance' && (
        <section className="card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">1B. 选择会议类型</h2>
          <p className="text-sm text-gray-500">请选择保险行业会议类型，系统将使用对应的专业模板和提示词：</p>
          <div className="grid grid-cols-2 gap-3">
            {(Object.keys(INSURANCE_MEETING_LABELS) as InsuranceMeetingType[]).map((mt) => (
              <button
                key={mt}
                onClick={() => setMeetingType(mt)}
                className={`p-3 rounded-lg border-2 text-left transition-all ${
                  meetingType === mt
                    ? 'border-amber-500 bg-amber-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className={`text-sm font-medium ${meetingType === mt ? 'text-amber-700' : 'text-gray-700'}`}>
                  {INSURANCE_MEETING_LABELS[mt]}
                </div>
                <div className="text-xs text-gray-400 mt-0.5">{INSURANCE_MEETING_DESC[mt]}</div>
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">2. 输入内容</h2>
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
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="在此描述演示主题，或粘贴文档内容...\n\n提示：按 Ctrl+Enter（Windows）快速生成"
            className="input-field min-h-[200px] resize-y"
          />
        )}
        {inputMethod === 'file' && selectedScene !== 'insurance' && (
          <label className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary-400 cursor-pointer transition-colors block">
            <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm text-gray-500">拖放 PDF、DOCX、MD、TXT 或点击浏览</p>
            <input type="file" accept=".pdf,.docx,.md,.txt" className="hidden" onChange={async (e) => {
              const file = e.target.files?.[0]
              if (!file) return
              try {
                const formData = new FormData()
                formData.append('file', file)
                const res = await fetch(await apiConfig.url('/api/v1/convert/file'), { method: 'POST', body: formData })
                if (!res.ok) throw new Error(`HTTP ${res.status}`)
                const data = await res.json()
                setInputText(data.markdown || '')
                setInputMethod('text')
              } catch (err: any) {
                setError(err.message || '文件转换失败')
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
                  <p className="text-sm text-gray-500">拖放 Excel、PDF、DOCX、MD、TXT 或点击浏览</p>
                  <p className="text-xs text-gray-400">Excel 将自动解析并匹配到 {INSURANCE_MEETING_LABELS[meetingType]} 模板</p>
                </div>
              )}
              <input
                type="file"
                accept=".xlsx,.xls,.pdf,.docx,.md,.txt"
                className="hidden"
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
                      setInputText(data.markdown || '')
                      setInputMethod('text')
                      showNotification('success', `✅ ${file.name} 已转换为文本内容`)
                    } catch (err: any) {
                      const errMsg = err.message || '文件转换失败'
                      setExcelUploadError(errMsg)
                      showNotification('error', `❌ ${errMsg}`)
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
            <input
              type="url"
              placeholder="https://example.com/article"
              className="input-field flex-1"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
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
                setInputText(data.markdown || '')
              } catch (err: any) {
                setError(err.message || 'URL 抓取失败')
              }
            }} className="btn-primary text-sm px-3">抓取</button>
          </div>
        )}
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">3. 选择模板（可选）</h2>
        <p className="text-sm text-gray-500">是否需要自己选择模板？不选择将使用默认模板。</p>
        <div className="flex space-x-3">
          <button
            onClick={() => setUseCustomTemplate(false)}
            className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
              useCustomTemplate === false
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            <Check className="w-4 h-4 mr-1.5" />
            使用默认模板
          </button>
          <button
            onClick={() => setUseCustomTemplate(true)}
            className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
              useCustomTemplate === true
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            自己选择模板
          </button>
        </div>

        {useCustomTemplate && (
          <div className="pt-3 space-y-3 border-t border-gray-100">
            <div className="flex space-x-2">
              {templateCategories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setTemplateCategory(cat)}
                  className={`px-3 py-1 rounded-md text-xs transition-colors ${
                    templateCategory === cat
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-500 hover:bg-gray-100'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
            {loadingTemplates ? (
              <div className="flex items-center justify-center py-8 text-sm text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />加载模板中...
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-3">
                {templates
                  .filter((t) => templateCategory === '全部' || t.category === templateCategory)
                  .map((t) => (
                    <div
                      key={t.id}
                      onClick={() => {
                        setCustomTemplateId(t.id)
                        updateConfig({ template: t.id })
                      }}
                      className={`card p-0 overflow-hidden cursor-pointer border-2 transition-colors ${
                        customTemplateId === t.id ? 'border-primary-500' : 'border-transparent hover:border-gray-300'
                      }`}
                    >
                      <div
                        className="h-20 flex items-center justify-center relative"
                        style={{ backgroundColor: t.preview || '#1e40af' }}
                      >
                        <span className="text-white text-opacity-30 text-xs">预览</span>
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

      {/* 用户自定义风格要求 */}
      <section className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">自定义风格（可选）</h2>
        <p className="text-sm text-gray-500">描述你想要的风格，如"商务蓝金配色、适合投影"或"小清新书香风、鼠尾草绿+米白底"</p>
        <textarea
          value={customStyle}
          onChange={(e) => setCustomStyle(e.target.value)}
          placeholder="例如：配色为深蓝+金色，标题加粗，每页不超过5个要点..."
          className="input-field h-20 resize-none"
        />
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">4. 选择提示词（可选）</h2>
        <p className="text-sm text-gray-500">是否需要自己选择提示词？不选择将使用默认生成策略。</p>
        <div className="flex space-x-3">
          <button
            onClick={() => { setUseCustomPrompt(false); setSelectedPrompt(null) }}
            className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
              useCustomPrompt === false
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            <Check className="w-4 h-4 mr-1.5" />
            使用默认策略
          </button>
          <button
            onClick={() => setUseCustomPrompt(true)}
            className={`flex items-center px-4 py-2 rounded-lg border-2 text-sm transition-all ${
              useCustomPrompt === true
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            自己选择提示词
          </button>
        </div>

        {useCustomPrompt && (
          <div className="pt-3 space-y-3 border-t border-gray-100">
            <div className="flex space-x-1 border-b border-gray-200">
              {promptCategories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setPromptCategory(cat.id)}
                  className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                    promptCategory === cat.id
                      ? 'border-primary-600 text-primary-700'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {(promptCategories.find((c) => c.id === promptCategory)?.prompts || []).map((prompt, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedPrompt(prompt.content)}
                  className={`card p-3 cursor-pointer border-2 transition-colors ${
                    selectedPrompt === prompt.content
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-transparent hover:border-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <Sparkles className="w-3.5 h-3.5 text-yellow-500" />
                    <h4 className="text-sm font-semibold text-gray-700">{prompt.title}</h4>
                    {selectedPrompt === prompt.content && (
                      <span className="px-1.5 py-0.5 bg-primary-600 text-white text-xs rounded-full">已选</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">{prompt.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">5. 选择模型</h2>
        {ollamaChecking ? (
          <div className="flex items-center space-x-2 text-sm text-amber-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>正在检测本地 Ollama 模型...</span>
          </div>
        ) : ollamaDetected && ollamaLocalModels.length > 0 ? (
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sm text-green-600">
              <Check className="w-4 h-4" />
              <span>检测到 Ollama 本地服务，{ollamaLocalModels.length} 个模型可用</span>
            </div>
            <select
              className="input-field text-sm w-full"
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
            >
              {ollamaLocalModels.map(m => (
                <option key={m} value={m}>{m} (Ollama 本地)</option>
              ))}
              {storedModels.filter(m => !ollamaLocalModels.includes(m.model)).map(m => (
                <option key={m.model} value={m.model}>{m.name}: {m.model}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400">
              当前选择: {selectedModelId || '未选择'} — Ollama 本地模型免费、隐私安全，无需 API Key
            </p>
          </div>
        ) : storedModels.length > 0 ? (
          <div className="space-y-2">
            <select
              className="input-field text-sm w-full"
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
            >
              {storedModels.map(m => (
                <option key={m.model} value={m.model}>{m.name}: {m.model}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400">
              当前选择: {selectedModelId || '未选择'} — 可在「设置」页面添加更多模型
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              {ollamaDetected ? '未检测到模型，请确保 Ollama 已拉取模型 (ollama pull &lt;model&gt;)' : '未检测到 Ollama 服务，也未配置云端模型。'}
            </p>
            <p className="text-xs text-gray-400">
              启动 Ollama 后将自动检测本地模型；或前往「设置」页面添加云端 API 模型
            </p>
          </div>
        )}
      </section>

      <section className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <label className="text-sm text-gray-600">幻灯片数量:</label>
          <input
            type="range"
            min="5"
            max="30"
            value={config.slideCount}
            onChange={(e) => useProjectStore.getState().updateGenerationConfig({ slideCount: parseInt(e.target.value) })}
            className="w-32"
          />
          <span className="text-sm text-gray-700">{config.slideCount}</span>
        </div>
        <div className="flex items-center space-x-3">
          {error && <span className="text-sm text-red-500">{error}</span>}
          <button
            onClick={handleGenerate}
            disabled={generating || !inputText.trim()}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50"
          >
            {generating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>{generating ? '生成中...' : '生成 PPT'}</span>
          </button>
        </div>
      </section>
    </div>
  )
}

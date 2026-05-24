export interface Prompt {
  title: string
  content: string
}

export interface PromptCategory {
  id: string
  label: string
  prompts: Prompt[]
}

export const promptCategories: PromptCategory[] = [
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
      { title: '业务对标复盘会', content: '保险行业对标复盘PPT：覆盖业绩达成、队伍KPI、投产效率、继续率、荣誉展示、问题诊断（偏差+根因）、改进措施、承诺追踪、领导总结。使用🟢🟡🔴状态标注。' },
      { title: '领导会议总结与指示', content: '保险行业领导指示PPT：会议概述、整体评价、形势分析、战略方针、定量指标分解、资源承诺、责任矩阵(RACI)、奖惩机制、动员号召。使用政务红配色。' },
      { title: '业务启动会', content: '保险行业战前动员PPT：成绩回顾、英雄榜表彰、新战役目标、策略路径、激励方案、表态承诺、领导动员、出征仪式。数字要大，氛围要高能量。' },
      { title: '产品说明会', content: '保险产品路演PPT：保障缺口分析、核心卖点展示、公司实力数据、客户案例故事、增值服务权益、限时优惠政策、购买流程指引。保持专业可信。' },
      { title: '创业说明会', content: '保险事业邀请PPT：行业趋势数据、公司品牌口碑、收入模型与晋升阶梯、成长路径与培训、成功案例、公司支持、招募流程。注明收益合规声明。' },
      { title: '服务权益说明会', content: '保险服务权益PPT：服务全景图、核心保障详解、增值服务、使用流程、权益对比、场景示例、关键条款提示、联系方式。避免术语过多。' },
      { title: '经营复盘会', content: '经营分析PPT：核心KPI仪表盘、保费达成分析、利润结构分析、人力效能分析、标杆对标、问题根因诊断、改善方案、行动计划。数据驱动。' },
      { title: '绩优分享会', content: '述职PPT：业绩达成概览、关键成果展示、过程管理、能力成长、不足反思、改进措施、未来规划、支持需求。70%成果+30%反思。' },
      { title: '产品培训', content: '保险产品培训PPT：学习目标、产品定位、保障责任详解、投保规则、话术对比训练（错误vs正确）、竞品对比、案例演练、FAQ、通关考核。' },
      { title: '落后述职会', content: '保险业绩改进PPT：数据复盘、差距分析(target vs actual)、根因剖析（意愿/能力/方法）、客观困难、改进方案、帮扶需求、量化承诺、督导追踪。建设性基调。' },
    ],
  },
]

export function addPrompt(categoryId: string, title: string, content: string): void {
  const category = promptCategories.find((c) => c.id === categoryId)
  if (category) {
    category.prompts.push({ title, content })
  }
}

export function removePrompt(categoryId: string, prompt: Prompt): void {
  const category = promptCategories.find((c) => c.id === categoryId)
  if (category) {
    const idx = category.prompts.indexOf(prompt)
    if (idx !== -1) {
      category.prompts.splice(idx, 1)
    }
  }
}

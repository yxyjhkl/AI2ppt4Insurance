import {
  Download, Monitor, Zap, FileUp, Globe, Keyboard, Shield,
  Briefcase, Settings, Edit3, Play, Rocket, Target, Handshake,
  Sparkles, Mic, Image, Database, RefreshCw,
} from 'lucide-react'
import { INSURANCE_MEETING_PROMPTS, type InsuranceMeetingType } from '@/types'

const shortcuts = [
  { keys: 'Ctrl + Enter', desc: '快速生成演示文稿' },
  { keys: 'Ctrl + Z', desc: '撤销上一步操作' },
  { keys: 'Ctrl + Shift + Z', desc: '重做已撤销操作' },
  { keys: 'Ctrl + C/V/D', desc: '画布元素复制/粘贴/原地复制' },
  { keys: 'Ctrl + ] / [', desc: '画布元素上移/下移一层' },
  { keys: 'Delete / Backspace', desc: '删除选中的画布元素' },
  { keys: 'Shift + 拖拽', desc: '图片等比缩放（保持宽高比）' },
  { keys: '方向键 ↑↓', desc: '编辑器中切换上一张/下一张幻灯片' },
  { keys: '方向键 ← →', desc: '演示模式下翻页' },
  { keys: 'Esc', desc: '退出演示模式 / 取消选中元素' },
  { keys: 'F', desc: '演示模式切换全屏' },
  { keys: 'N', desc: '演示模式显示/隐藏备注' },
  { keys: 'T', desc: '演示模式暂停/继续计时器' },
  { keys: 'B', desc: '演示模式切换静态低功耗模式' },
]

export function Help() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-8">

      <section>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1">InsurDeck 操作指南</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          AI 驱动的智能演示文稿生成工具 · v1.0.0 · 作者：何克霖（福建龙岩）
        </p>
      </section>

      {/* ===== 一、三种工作模式 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary-600" />
          三种工作模式
        </h2>
        <p className="text-sm text-gray-500 mb-4">根据你的时间和控制需求，选择不同深度的工作模式：</p>
        <div className="grid sm:grid-cols-3 gap-3">
          <ModeCard icon={Rocket} title="AI 替我做" subtitle="全自动出稿" color="blue"
            desc="给一份材料或一个主题，AI 全程自动生成精美 PPT，中间无需任何人工干涉。"
            steps={['输入主题/材料', '点击「一键生成」', '自动生成 → 进入编辑器']}
            suitable="赶时间 / 材料完整 / 信任 AI" />
          <ModeCard icon={Target} title="AI 帮我做" subtitle="按需定制" color="green"
            desc="设定受众、风格、时长等要求，AI 先出大纲让你确认，确认后再生成完整 PPT。"
            steps={['输入材料 + 设定需求', 'AI 生成大纲 → 审核确认', '生成完整 PPT → 编辑']}
            suitable="有明确需求 / 重要汇报" />
          <ModeCard icon={Handshake} title="AI 陪我做" subtitle="逐步共创" color="purple"
            desc="每一步都暴露给你：大纲可逐页编辑、内容可逐页微调、模板可切换。你是导演。"
            steps={['输入内容', '大纲逐页编辑确认', '内容逐页微调', '选模板 → 生成']}
            suitable="精细打磨 / 完全掌控" />
        </div>
        <p className="text-xs text-gray-400 mt-3">
          三种模式共享同一个 AI 引擎选择（云端 AI / 本地 Ollama / 离线规则），在选择模式后可以随时切换。
        </p>
      </section>

      {/* ===== 二、快速入门 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Rocket className="w-5 h-5 text-primary-600" />
          快速入门（3 步出 PPT）
        </h2>
        <div className="space-y-3">
          <StepCard num={1} title="选择工作模式 + 场景" icon={Target}>
            在仪表盘选择三种模式之一，然后选择场景：报告/教育/提案/转换/研讨/保险/润色。
            保险场景需进一步选择会议类型（如业务复盘会、产品说明会等10种）。
          </StepCard>
          <StepCard num={2} title="输入内容 + 设定需求（可选）" icon={FileUp}>
            直接粘贴文字/Markdown，或上传 PDF/DOCX/MD/TXT/PPTX 文件，或输入网页 URL 抓取。
            在「AI帮我做」或「AI陪我做」模式下，可展开需求面板设定受众、时长、风格等偏好。
          </StepCard>
          <StepCard num={3} title="生成 → 审核 → 编辑 → 导出" icon={Download}>
            点击「生成PPT」（自动模式为「一键生成」）。在 guided/cocreate 模式下先审核大纲再生成。
            进入编辑器后可以：修改标题/正文、调整布局、添加画布元素（图片/文字/形状/表格）。
            完成后导出为 PPTX / PDF / 分页 PNG 文件。
          </StepCard>
        </div>
      </section>

      {/* ===== 三、编辑器能力 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Edit3 className="w-5 h-5 text-primary-600" />
          编辑器能力一览
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <GuideCard title="内容编辑" items={[
            '点击左侧大纲列表的标题直接编辑',
            '右侧面板编辑当前页的标题、正文、布局类型',
            '每行正文可独立编辑，实时更新',
            '演讲备注独立编辑，导出时写入 PPTX',
          ]} />
          <GuideCard title="画布元素" items={[
            '从工具栏拖拽文本/形状/图片/表格到画布',
            '双击文字元素在画布上直接编辑',
            '拖拽调整位置和大小，Shift+拖拽等比缩放',
            'Ctrl+C/V 复制粘贴，Ctrl+D 原地复制',
          ]} />
          <GuideCard title="元素控制" items={[
            '置顶/上移/下移/置底按钮控制层级',
            '6 个对齐按钮（左中右、顶中底）对齐到画布',
            '拖拽时自动吸附临近元素边缘和中心',
            '锁定元素防止误拖拽，锁定后显示 🔒 角标',
          ]} />
          <GuideCard title="画布操作" items={[
            '+/- 按钮缩放画布（30%~200%）',
            'Ctrl+滚轮缩放',
            '粘贴图片/截图到画布（Ctrl+V）',
            '从 Excel 复制表格数据粘贴到画布',
          ]} />
        </div>
      </section>

      {/* ===== 四、特色功能 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary-600" />
          特色功能
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <FeatureCard icon={RefreshCw} title="PPTX 导入润色"
            desc="上传已有 .pptx 文件 → AI 提取内容 → 优化标题/丰富数据/升级布局 → 输出全新 PPT。选择「润色」场景即可使用。" />
          <FeatureCard icon={Database} title="资料补充"
            desc="对已生成的 PPT，选择补充类型（综合/数据/案例/流程/对比/自定义）→ AI 为每页追加新内容，原有内容不删除。新增项带【补充】标记。" />
          <FeatureCard icon={Image} title="图片搜索"
            desc="支持 Pexels 专业图库搜索高质量图片，也可回退到 DuckDuckGo 搜索，适合为封面页和数据页配图。" />
          <FeatureCard icon={Mic} title="语音旁白"
            desc="点击编辑器中的「旁白」按钮 → 基于所有演讲备注 → edge-tts 合成 MP3 音频 → 下载为演讲配音。" />
          <FeatureCard icon={Play} title="录制演示"
            desc="演示模式下点击「录制」→ 屏幕录制 + 摄像头 PIP + 音频 → 停止后自动下载 WebM 视频。" />
          <FeatureCard icon={Globe} title="多平台封面"
            desc="基于当前主题和标题生成公众号(21:9)、小红书(3:4)、分享卡(1:1)三种规格的封面 SVG。" />
        </div>
      </section>

      {/* ===== 五、AI 模型配置 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5 text-primary-600" />
          AI 模型配置
        </h2>
        <div className="card p-4 space-y-3">
          <p className="text-sm text-gray-600">前往「设置」页面管理 AI 模型。支持 12 种供应商：</p>
          <div className="grid grid-cols-4 gap-2 text-xs text-gray-500">
            <span>DeepSeek</span><span>通义千问</span><span>豆包</span><span>智谱 GLM</span>
            <span>Moonshot</span><span>讯飞星火</span><span>腾讯混元</span><span>文心一言</span>
            <span>OpenAI</span><span>Claude</span><span>Gemini</span><span>Ollama</span>
          </div>
          <ul className="space-y-1 text-xs text-gray-500">
            <li>· API Key 通过 Electron safeStorage 系统级加密存储</li>
            <li>· 点击「连通测试」逐层诊断 DNS→TCP→HTTP→API</li>
            <li>· 生成时仅传输所选模型的密钥到本地后端</li>
            <li>· 配置自动保存（1.5 秒防抖）</li>
          </ul>
        </div>
      </section>

      {/* ===== 六、生成流程 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Monitor className="w-5 h-5 text-primary-600" />
          生成流程
        </h2>
        <div className="card p-4">
          <div className="space-y-2 text-xs font-mono text-gray-600">
            <FlowStep label="1. 路由判断" detail="有 Excel? → 数据驱动 / 有会议纪要? → 转写处理 / 正常 → AI 生成" />
            <FlowStep label="2. AI 规划" detail="加载场景 YAML → 拼接提示词(角色+任务+布局规则+设计约束+few-shot) → 调用大模型" />
            <FlowStep label="3. 解析校验" detail="精确提取 JSON → 布局白名单验证 → 自动补封面/结尾 → 类型规范化" />
            <FlowStep label="4. SVG 渲染" detail="SlideData → SVGFiller → 每页独立 SVG预览（17 种布局）" />
            <FlowStep label="5. PPTX 组装" detail="SlideData → PPTXGenerator → 原生 DrawingML 形状(非图片)" />
            <FlowStep label="6. 质检 P0-P3" detail="P0阻断/ P1警告/ P2建议/ P3优化。连续3页content触发节奏警告" />
          </div>
        </div>
      </section>

      {/* ===== 七、质检系统 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary-600" />
          内容质检（P0-P3 四级）
        </h2>
        <div className="space-y-2 text-sm">
          <QACard level="P0" color="red" label="阻断" desc="必须修复才能导出" items={[
            '幻灯片完全为空', '仅标题无内容', '布局与数据不匹配（如表格布局无表格数据）', '数据布局未检测到任何数字'
          ]} />
          <QACard level="P1" color="amber" label="警告" desc="导出前建议修复" items={[
            '标题重复出现', '内容溢出（>10项或>2000字符）', '缺少封面/结尾', 'content 布局占比 >65%', '连续3页使用 content 布局'
          ]} />
          <QACard level="P2" color="blue" label="建议" desc="可忽略但建议改进" items={[
            '标题过长（>120字符）', '有内容但无演讲备注', '内容密度过低（<30字符）'
          ]} />
          <QACard level="P3" color="gray" label="优化" desc="锦上添花" items={[
            '建议使用 🟢🟡🔴 状态标记', '建议使用【标签】结构化标注'
          ]} />
        </div>
      </section>

      {/* ===== 八、PPTX 导入润色 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-primary-600" />
          PPTX 导入润色
        </h2>
        <div className="card p-4 space-y-3 text-sm text-gray-600">
          <p>选择「润色」场景 → 上传已有 .pptx 文件 → AI 自动：</p>
          <ul className="list-disc list-inside space-y-1 text-xs text-gray-500">
            <li>提取所有页面的文本、表格和备注</li>
            <li>优化标题（加入动作词和量化结果）</li>
            <li>丰富内容（补充数据支撑和因果关系）</li>
            <li>升级布局（自动分配更合适的 layout_type）</li>
            <li>补充缺失的执行摘要、数据对比或行动建议</li>
            <li>提升语言品质（口语化→专业商务语言）</li>
          </ul>
          <p className="text-xs text-gray-400">约束：不编造原文中没有的关键数据，补充内容标注「分析建议」，页数波动 ±30%</p>
        </div>
      </section>

      {/* ===== 九、保险行业模式 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-primary-600" />
          保险行业模式
        </h2>
        <div className="card p-4 space-y-3 text-sm text-gray-600">
          <p>选择「保险」场景 + 指定会议类型后，系统使用专属 AI 角色和行业模板：</p>
          <ul className="list-disc list-inside space-y-1 text-xs text-gray-500">
            <li><strong>10 种预设会议类型</strong>：每种都有专属 AI 角色、任务目标、幻灯片结构、设计规范</li>
            <li><strong>数据驱动模式</strong>：上传 Excel → 自动解析工作表 → 模糊匹配列名 → 填充会议模板</li>
            <li><strong>17 种专业布局</strong>：瀑布图、仪表盘、排行榜、漏斗图、矩阵、时间轴等保险行业高频布局</li>
            <li><strong>专业术语</strong>：内置保费、件数、继续率、活动率、人均产能、投产比等行业指标</li>
            <li><strong>设计宪章</strong>：颜色上限、字体约束、状态编码（前30%🟢/30-70%🟡/后30%🔴）、数据精度、禁止装饰效果</li>
            <li><strong>图片槽位</strong>：封面 16:9、对比图 16:10、KPI 荣誉照 1:1</li>
          </ul>
          <p className="text-xs text-gray-400 mt-2">鼠标悬停在仪表盘的会议类型卡片上可预览 AI 角色和任务。详细参数见下方。</p>
        </div>
      </section>

      {/* ===== 十、保险会议提示词详情 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-primary-600" />
          保险会议 AI 角色详情
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          每种会议类型都有专属的 AI 角色设定。以下为各类型使用的 prompt 参数。
        </p>
        <div className="space-y-4">
          {(Object.keys(INSURANCE_MEETING_PROMPTS) as InsuranceMeetingType[]).map((mt) => {
            const info = INSURANCE_MEETING_PROMPTS[mt]
            return (
              <div key={mt} className="card p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-base font-semibold text-gray-800">{info.label}</span>
                  <span className="text-xs text-gray-400">—</span>
                  <span className="text-xs text-gray-500">{info.desc}</span>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  <PromptRow color="amber" label="角色" text={info.role} />
                  <PromptRow color="blue" label="任务" text={info.task} />
                  <PromptRow color="green" label="结构" text={info.structure} />
                  <PromptRow color="purple" label="设计" text={info.design} />
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* ===== 十一、快捷键 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Keyboard className="w-5 h-5 text-primary-600" />
          快捷键一览
        </h2>
        <div className="card p-4">
          <div className="space-y-2">
            {shortcuts.map((item) => (
              <div key={item.keys} className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{item.desc}</span>
                <code className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono text-gray-700 dark:text-gray-300">
                  {item.keys}
                </code>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== 十二、常见问题 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">常见问题</h2>
        <div className="space-y-3 text-sm">
          <FAQ q="三种模式有什么区别？"
            a="AI替我做：给材料→自动出稿，无人工介入。AI帮我做：给材料+设定要求→审核大纲→生成。AI陪我做：每一步都暴露给你，可逐页编辑大纲和内容再生成。" />
          <FAQ q="生成失败怎么办？"
            a="AI 解析失败会自动重试一次（降低温度提高稳定性）。若仍失败，自动回退到离线规则引擎。也可直接选择离线模式。" />
          <FAQ q="API Key 安全吗？"
            a="密钥通过 Electron safeStorage 系统级加密存储。生成时仅传输所选模型的密钥到本地后端 127.0.0.1，不上传任何外部服务器。" />
          <FAQ q="怎么给已有 PPT 润色？"
            a="选择「润色」场景 → 上传 .pptx → AI 提取内容并优化标题/数据/布局 → 生成优化版 PPT。" />
          <FAQ q="画布元素刷新后会丢失吗？"
            a="不会。画布元素（图片/文字/形状）每 3 秒自动保存到 localStorage。刷新或关闭浏览器重开后元素依然存在。" />
          <FAQ q="可以离线使用吗？"
            a="三种方式：① 本地 Ollama（需提前安装拉取模型）；② 离线规则引擎（无需任何依赖）；③ 以上都不行时回退到纯文本分段。" />
        </div>
      </section>

      <div className="text-right text-sm text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
        作者：何克霖 · 福建龙岩 · 2026.05
      </div>
    </div>
  )
}

function StepCard({ num, title, icon: Icon, children }: { num: number; title: string; icon: React.ComponentType<{ className?: string }>; children: React.ReactNode }) {
  return (
    <div className="card p-4 flex items-start gap-4">
      <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-bold shrink-0">{num}</div>
      <div>
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <Icon className="w-4 h-4 text-primary-500" />{title}
        </h3>
        <div className="text-xs text-gray-500 mt-1">{children}</div>
      </div>
    </div>
  )
}

function ModeCard({ icon: Icon, title, subtitle, color, desc, steps, suitable }: {
  icon: React.ComponentType<{ className?: string }>; title: string; subtitle: string; color: string;
  desc: string; steps: string[]; suitable: string;
}) {
  const colors: Record<string, string> = { blue: 'border-blue-200 bg-blue-50/50', green: 'border-green-200 bg-green-50/50', purple: 'border-purple-200 bg-purple-50/50' }
  const badges: Record<string, string> = { blue: 'bg-blue-500', green: 'bg-green-500', purple: 'bg-purple-500' }
  return (
    <div className={`card p-4 border ${colors[color] || ''}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-6 h-6 rounded ${badges[color] || 'bg-gray-500'} flex items-center justify-center`}>
          <Icon className="w-3.5 h-3.5 text-white" />
        </div>
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        <span className={`text-[10px] px-1.5 py-0.5 rounded-full text-white ${badges[color]}`}>{subtitle}</span>
      </div>
      <p className="text-xs text-gray-500 mb-2">{desc}</p>
      <div className="text-[10px] text-gray-400 space-y-0.5">
        {steps.map((s, i) => <div key={i}>▸ {i + 1}. {s}</div>)}
        <div className="text-gray-300 mt-1">适合：{suitable}</div>
      </div>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, desc }: { icon: React.ComponentType<{ className?: string }>; title: string; desc: string }) {
  return (
    <div className="card p-4 flex items-start gap-3">
      <div className="w-8 h-8 rounded-lg bg-primary-50 dark:bg-primary-900/30 flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4 text-primary-600 dark:text-primary-400" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">{title}</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{desc}</p>
      </div>
    </div>
  )
}

function GuideCard({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="card p-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <ul className="space-y-1 text-xs text-gray-500">
        {items.map((item, i) => <li key={i} className="flex gap-2"><span className="text-gray-300">·</span>{item}</li>)}
      </ul>
    </div>
  )
}

function FlowStep({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="flex gap-3 items-start">
      <span className="font-medium text-gray-700 shrink-0 w-28">{label}</span>
      <span className="text-gray-500">{detail}</span>
    </div>
  )
}

function QACard({ level, color, label, desc, items }: { level: string; color: string; label: string; desc: string; items: string[] }) {
  const colors: Record<string, string> = { red: 'border-red-200 bg-red-50', amber: 'border-amber-200 bg-amber-50', blue: 'border-blue-200 bg-blue-50', gray: 'border-gray-200 bg-gray-50' }
  const badges: Record<string, string> = { red: 'bg-red-100 text-red-700', amber: 'bg-amber-100 text-amber-700', blue: 'bg-blue-100 text-blue-700', gray: 'bg-gray-100 text-gray-600' }
  return (
    <div className={`card p-3 border ${colors[color] || ''}`}>
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${badges[color] || ''}`}>{level} {label}</span>
        <span className="text-xs text-gray-400">{desc}</span>
      </div>
      <ul className="space-y-0.5 text-xs text-gray-600">
        {items.map((item, i) => <li key={i} className="flex gap-2"><span className="text-gray-300">·</span>{item}</li>)}
      </ul>
    </div>
  )
}

function PromptRow({ color, label, text }: { color: string; label: string; text: string }) {
  const colors: Record<string, string> = { amber: 'bg-amber-50 text-amber-600', blue: 'bg-blue-50 text-blue-600', green: 'bg-green-50 text-green-600', purple: 'bg-purple-50 text-purple-600' }
  return (
    <div className="flex items-start gap-2">
      <span className={`text-xs font-medium px-1.5 py-0.5 rounded shrink-0 w-10 text-center ${colors[color] || ''}`}>{label}</span>
      <span className="text-xs text-gray-600 leading-relaxed">{text}</span>
    </div>
  )
}

function FAQ({ q, a }: { q: string; a: string }) {
  return (
    <div className="card p-4">
      <h4 className="text-sm font-medium text-gray-700">{q}</h4>
      <p className="text-xs text-gray-500 mt-1">{a}</p>
    </div>
  )
}

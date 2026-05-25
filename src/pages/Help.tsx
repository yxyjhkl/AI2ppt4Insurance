import {
  Download, Monitor, Zap, FileUp, Globe, Keyboard, Shield, List, Layout,
  Briefcase, Settings, Edit3, Play, Rocket, Target, Handshake,
  Sparkles, Mic, Image, Database, RefreshCw,
} from 'lucide-react'
import { INSURANCE_MEETING_PROMPTS, type InsuranceMeetingType } from '@/types'

const shortcuts = [
  { keys: 'Ctrl + Enter', desc: '快速生成演示文稿' },
  { keys: 'Ctrl + Z', desc: '撤销上一步操作（幻灯片/元素）' },
  { keys: 'Ctrl + Shift + Z', desc: '重做已撤销操作' },
  { keys: 'Ctrl + Shift + ↑↓', desc: '移动当前幻灯片顺序' },
  { keys: 'Ctrl + C/V/D', desc: '画布元素复制/粘贴/原地复制' },
  { keys: 'Ctrl + ] / [', desc: '画布元素上移/下移一层' },
  { keys: 'Delete / Backspace', desc: '删除选中的画布元素' },
  { keys: 'Shift + 拖拽', desc: '图片等比缩放（保持宽高比）' },
  { keys: '方向键 ↑↓←→', desc: '微移选中元素 / 切换幻灯片' },
  { keys: 'Esc', desc: '退出演示模式 / 演示中显示缩略图索引' },
  { keys: 'F', desc: '演示模式切换全屏' },
  { keys: 'G', desc: '演示模式显示/隐藏缩略图网格' },
  { keys: 'N', desc: '演示模式显示/隐藏备注' },
  { keys: 'T', desc: '演示模式暂停/继续计时器' },
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

        {/* 模式对比表格 */}
        <div className="card p-4 mb-4 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-2 font-semibold text-gray-600 w-24"></th>
                <th className="text-left py-2 px-2 font-semibold text-blue-700"><Rocket className="w-3.5 h-3.5 inline mr-1" />AI 替我做</th>
                <th className="text-left py-2 px-2 font-semibold text-green-700"><Target className="w-3.5 h-3.5 inline mr-1" />AI 帮我做</th>
                <th className="text-left py-2 px-2 font-semibold text-purple-700"><Handshake className="w-3.5 h-3.5 inline mr-1" />AI 陪我做</th>
              </tr>
            </thead>
            <tbody className="text-gray-600">
              <tr className="border-b border-gray-100">
                <td className="py-2 px-2 font-medium text-gray-500">场景选择</td>
                <td className="py-2 px-2">AI 自动识别<span className="text-[10px] text-gray-400 ml-1">（含中文关键词）</span></td>
                <td className="py-2 px-2">用户手动选择</td>
                <td className="py-2 px-2">用户手动选择</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 px-2 font-medium text-gray-500">需求面板</td>
                <td className="py-2 px-2 text-gray-400">隐藏（自动推断）</td>
                <td className="py-2 px-2">完整展开</td>
                <td className="py-2 px-2">完整展开</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 px-2 font-medium text-gray-500">模板选择</td>
                <td className="py-2 px-2 text-gray-400">AI 自动匹配</td>
                <td className="py-2 px-2">用户选择</td>
                <td className="py-2 px-2">用户选择</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 px-2 font-medium text-gray-500">大纲审核</td>
                <td className="py-2 px-2 text-gray-400">跳过</td>
                <td className="py-2 px-2">手动点击「生成大纲」→ 审核 → 确认</td>
                <td className="py-2 px-2">手动点击「生成大纲」→ 逐页编辑 → 确认</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 px-2 font-medium text-gray-500">确认后</td>
                <td className="py-2 px-2 text-gray-400">—</td>
                <td className="py-2 px-2">用户手动点击「生成PPT」</td>
                <td className="py-2 px-2"><span className="text-purple-600 font-medium">自动触发生成</span> → 进入编辑器</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 px-2 font-medium text-gray-500">生成过程</td>
                <td className="py-2 px-2">一键生成 + 自动美化</td>
                <td className="py-2 px-2">完整生成（使用选定场景/模板）</td>
                <td className="py-2 px-2">完整生成 → 编辑器逐页微调</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 px-2 font-medium text-gray-500">需求传递</td>
                <td className="py-2 px-2 text-gray-400">内容中拼接</td>
                <td className="py-2 px-2">结构化字段 → AI prompt</td>
                <td className="py-2 px-2">结构化字段 → AI prompt</td>
              </tr>
              <tr>
                <td className="py-2 px-2 font-medium text-gray-500">适合场景</td>
                <td className="py-2 px-2 text-gray-500">赶时间 / 材料完整 / 信任AI</td>
                <td className="py-2 px-2 text-gray-500">有明确需求 / 重要汇报</td>
                <td className="py-2 px-2 text-gray-500">精细打磨 / 完全掌控</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          <ModeCard icon={Rocket} title="AI 替我做" subtitle="全自动出稿" color="blue"
            desc="给一份材料或一个主题，AI 全程自动生成精美 PPT，中间无需任何人工干涉。支持上传文件后自动触发。"
            steps={['输入主题或上传文件', 'AI 自动分析内容类型', '自动选场景/模板/页数', '点击「一键生成」', '进入编辑器']}
            suitable="赶时间 / 材料完整 / 信任 AI" />
          <ModeCard icon={Target} title="AI 帮我做" subtitle="先大纲后生成" color="green"
            desc="设定受众、风格、时长等需求，AI 先出大纲让你逐页审核和编辑，确认后手动点击生成完整 PPT。"
            steps={['输入材料 + 填写需求面板', '点击「生成大纲」', '审核大纲，逐页编辑标题', '确认大纲 → 点击「生成PPT」', '进入编辑器调整']}
            suitable="有明确需求 / 重要汇报" />
          <ModeCard icon={Handshake} title="AI 陪我做" subtitle="确认即生成+逐页微调" color="purple"
            desc="审核大纲并逐页编辑确认后，自动触发生成进入编辑器。在编辑器中可逐页微调标题、正文、布局和画布元素。"
            steps={['输入材料 + 填写需求', '生成大纲 → 逐页编辑', '确认大纲 → 自动生成', '进入编辑器逐页微调', '导出']}
            suitable="精细打磨 / 完全掌控" />
        </div>
        <p className="text-xs text-gray-400 mt-3">
          三种模式共享同一个 AI 引擎选择（云端 AI / 本地 Ollama / 离线规则）。<br />
          <span className="text-gray-400">提示：</span>「AI帮我做」和「AI陪我做」的需求面板（受众/风格/必含/避免）会作为结构化字段传给 AI，而非简单拼接，效果更好。
        </p>
      </section>

      {/* ===== 二、快速入门 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Rocket className="w-5 h-5 text-primary-600" />
          快速入门（3 步出 PPT）
        </h2>
        <div className="space-y-3">
          <StepCard num={1} title="选择工作模式 + AI 引擎" icon={Target}>
            在仪表盘选择三种模式之一：<strong>AI替我做</strong>（全自动）、<strong>AI帮我做</strong>（先大纲后生成）、<strong>AI陪我做</strong>（确认即生成+逐页微调）。
            然后选择 AI 引擎：云端大模型 / 本地 Ollama / 离线规则。
          </StepCard>
          <StepCard num={2} title="输入内容 + 设定需求" icon={FileUp}>
            直接粘贴文字/Markdown，或上传 PDF/DOCX/MD/TXT/PPTX/XMind 文件，或输入网页 URL 抓取，或上传 Excel。
            在「AI帮我做」或「AI陪我做」模式下，可展开需求面板设定受众、时长、风格、必含/避免内容（这些需求会以结构化方式传给AI）。
          </StepCard>
          <StepCard num={3} title="审核大纲（guided/cocreate）" icon={List}>
            在 guided/cocreate 模式下，点击「生成大纲」→ AI 生成大纲 → 逐页审核编辑标题。
            Cocreate 确认后自动生成；Guided 确认后需手动点击「生成PPT」。
            <span className="text-gray-400">（自动模式下此步骤跳过）</span>
          </StepCard>
          <StepCard num={4} title="编辑 → 导出" icon={Download}>
            进入编辑器后可以：修改标题/正文、切换17种布局、添加画布元素（图片/文字/形状/表格）、AI资料补充。
            编辑后 SVG 预览 0.8 秒自动刷新，所见即所得。完成后导出为 PPTX / PDF / 分页 PNG。
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
          <GuideCard title="AI 辅助" items={[
            '点击「AI编辑」打开对话助手，自然语言修改PPT',
            '点击「资料补充」AI为每页追加数据/案例',
            '点击「旁白」生成语音MP3，支持语音克隆',
            '点击「重新生成」修改原始内容后重新出稿',
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
            desc="对已生成的 PPT，选择补充类型（综合/数据/案例/流程/对比/自定义）→ AI 为每页追加新内容，原有内容不删除。" />
          <FeatureCard icon={Image} title="AI 智能配图"
            desc="支持 8 家图片生成供应商（DALL·E 3、通义万相、ComfyUI 本地等），AI 根据每页内容自动生成配图。设置页可选用。" />
          <FeatureCard icon={Sparkles} title="AI 对话式编辑"
            desc="编辑器右下角打开 AI 助手 → 用自然语言修改 PPT：'把第3页标题加数据''换成表格布局'。AI 理解意图并直接修改。" />
          <FeatureCard icon={Mic} title="语音旁白 + 克隆"
            desc="支持 edge-tts 免费合成 + ElevenLabs/MiniMax 语音克隆。为演讲备注生成自然语音旁白 MP3。" />
          <FeatureCard icon={Play} title="录制演示"
            desc="演示模式下点击「录制」→ 屏幕录制 + 摄像头 PIP + 音频 → 停止后自动下载 WebM 视频。" />
          <FeatureCard icon={Globe} title="多平台封面"
            desc="一键生成公众号 21:9 头图、小红书 3:4 竖图、1:1 分享卡片。基于当前主题色自动适配。" />
          <FeatureCard icon={Monitor} title="三种风格预览"
            desc="输入标题后一键生成 3 种风格封面（专业商务蓝/杂志编辑风/瑞士国际主义），看图选用。" />
          <FeatureCard icon={Layout} title="24 套内置模板"
            desc="含新增杂志编辑风(Editorial Magazine)和瑞士国际主义(Swiss International)双设计语言包。全部支持模板预览大图。" />
          <FeatureCard icon={Edit3} title="幻灯片撤销/重做"
            desc="50 步历史栈：改标题/删页/排序/切换布局都可 Ctrl+Z 撤销。元素级和幻灯片级双历史。" />
          <FeatureCard icon={Zap} title="生成缓存"
            desc="相同输入 SHA256 去重，24 小时内不重复调 API。节省费用，加速二次生成。" />
          <FeatureCard icon={FileUp} title="全格式输入"
            desc="支持 PDF/DOCX/MD/TXT/PPTX/XMind/HTML/LaTeX/URL 共 9 种输入格式。Excel 可数据驱动生成。" />
        </div>
      </section>

      {/* ===== 五、AI 配图供应商 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Image className="w-5 h-5 text-primary-600" />
          AI 配图供应商（8家）
        </h2>
        <div className="card p-4 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-2 font-semibold text-gray-600">供应商</th>
                <th className="text-left py-2 px-2 font-semibold text-gray-600">区域</th>
                <th className="text-left py-2 px-2 font-semibold text-gray-600">成本</th>
                <th className="text-left py-2 px-2 font-semibold text-gray-600">所需配置</th>
              </tr>
            </thead>
            <tbody className="text-gray-600">
              {[
                ['DALL·E 3', '🌍 OpenAI', '~$0.04/张', 'OPENAI_API_KEY'],
                ['Stable Diffusion', '🌍 Stability AI', '~$0.01/张', 'STABILITY_API_KEY'],
                ['ComfyUI 本地', '💻 本地部署', '免费无限量', 'COMFYUI_URL + GPU 6GB+'],
                ['通义万相', '🇨🇳 阿里云', '按量计费', 'DASHSCOPE_API_KEY'],
                ['CogView', '🇨🇳 智谱AI', '按量计费', 'ZHIPU_API_KEY'],
                ['文心一格', '🇨🇳 百度', '按量计费', 'BAIDU_API_KEY + SECRET_KEY'],
                ['讯飞星火', '🇨🇳 科大讯飞', '按量计费', 'SPARK 三Key'],
                ['魔搭 ModelScope', '🇨🇳 阿里达摩院', '新用户免费额度', 'MODELSCOPE_API_KEY'],
              ].map((row, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-2 px-2 font-medium">{row[0]}</td>
                  <td className="py-2 px-2">{row[1]}</td>
                  <td className="py-2 px-2">{row[2]}</td>
                  <td className="py-2 px-2 font-mono text-[10px] text-gray-500">{row[3]}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-gray-400 mt-3">在「设置」→「AI 配图生成」中选择供应商。相同内容自动 SHA256 缓存，不重复计费。</p>
        </div>
      </section>

      {/* ===== 语音旁白配置 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Mic className="w-5 h-5 text-primary-600" />
          语音旁白配置
        </h2>
        <div className="card p-4 space-y-4">
          <p className="text-sm text-gray-600">点击编辑器工具栏「旁白」按钮，为演讲备注生成语音 MP3。支持三种引擎：</p>

          {/* 引擎对比表格 */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 font-semibold text-gray-600">引擎</th>
                  <th className="text-left py-2 px-2 font-semibold text-gray-600">音质</th>
                  <th className="text-left py-2 px-2 font-semibold text-gray-600">中文</th>
                  <th className="text-left py-2 px-2 font-semibold text-gray-600">费用</th>
                  <th className="text-left py-2 px-2 font-semibold text-gray-600">配置难度</th>
                </tr>
              </thead>
              <tbody className="text-gray-600">
                {[
                  ['Edge TTS', '★★★', '★★★', '免费', '无需配置'],
                  ['ElevenLabs', '★★★★★', '★★★★', '≈$0.015/千字', '需 API Key'],
                  ['MiniMax', '★★★★', '★★★★★', '按量计费', '需 API Key + Group ID'],
                ].map((row, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-2 px-2 font-medium">{row[0]}</td>
                    <td className="py-2 px-2">{row[1]}</td>
                    <td className="py-2 px-2">{row[2]}</td>
                    <td className="py-2 px-2">{row[3]}</td>
                    <td className="py-2 px-2">{row[4]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Edge TTS */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-green-800">🆓 Edge TTS — 免费·零配置</p>
            <p className="text-green-700">使用微软晓晓语音（zh-CN-XiaoxiaoNeural），自然女声，无需任何设置。</p>
            <p className="text-green-700">选择后直接点击「生成并下载 MP3」即可。</p>
          </div>

          {/* ElevenLabs */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-blue-800">🎙️ ElevenLabs — 最高音质·可克隆真人声音</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-700">
              <li>注册账号：<code className="bg-blue-100 px-1 rounded">https://elevenlabs.io</code></li>
              <li>获取 API Key：头像 → Profile → API Key → 复制</li>
              <li>配置环境变量（.env 文件）：<code className="bg-blue-100 px-1 rounded">ELEVENLABS_API_KEY=sk_xxxx</code></li>
              <li>（可选）克隆音色：Voices → Add Voice → 上传录音 → 获得 Voice ID</li>
            </ol>
            <p className="text-blue-600 mt-1">对话框中填入 Voice ID（留空用默认女声 Rachel），可调整稳定性(0-1)和相似度(0-1)滑块。</p>
          </div>

          {/* MiniMax */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-indigo-800">🇨🇳 MiniMax — 中文最佳·可克隆</p>
            <ol className="list-decimal list-inside space-y-1 text-indigo-700">
              <li>注册账号：<code className="bg-indigo-100 px-1 rounded">https://platform.minimaxi.com</code></li>
              <li>获取 API Key + Group ID：控制台 → 账户管理 → API 密钥</li>
              <li>配置环境变量（.env 文件）：
                <br /><code className="bg-indigo-100 px-1 rounded">MINIMAX_API_KEY=your_key</code>
                <br /><code className="bg-indigo-100 px-1 rounded">MINIMAX_GROUP_ID=your_group_id</code>
              </li>
            </ol>
            <p className="text-indigo-600 mt-1">对话框中填入 Voice ID（如 male-qn-qingse 男声，留空用默认）。</p>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700">
            <p className="font-medium mb-1">💡 提示</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>不设置任何环境变量时，默认使用 Edge TTS（免费）</li>
              <li>旁白基于每页的「演讲备注」生成，生成前请先在编辑器中为每页填写备注</li>
              <li>ElevenLabs 新用户有免费额度，MiniMax 按量计费</li>
            </ul>
          </div>
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

      {/* ===== 九、四大高频场景 ===== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-primary-600" />
          四大高频场景
        </h2>
        <p className="text-sm text-gray-500 mb-4">针对保险行业四大高频工作场景，内置专属 AI 角色和提示词。上传文档后自动识别场景：</p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-2 font-semibold text-gray-600 w-24">场景</th>
                <th className="text-left py-2 px-2 font-semibold text-gray-600">自动识别词</th>
                <th className="text-left py-2 px-2 font-semibold text-gray-600">AI 角色</th>
                <th className="text-left py-2 px-2 font-semibold text-gray-600">特色布局</th>
                <th className="text-left py-2 px-2 font-semibold text-gray-600">推荐结构</th>
              </tr>
            </thead>
            <tbody className="text-gray-600">
              {[
                ['领导会议总结', '领导/会议/部署/传达/纪要/精神', '战略传达专家', '金句引用 + 任务RACI表', '金句→核心精神→任务分解→传达要求'],
                ['个人工作汇报', '周报/月报/述职/一人一策/行事历', '工作汇报专家', 'KPI仪表盘 + 跟进清单', '成果(70%)→问题(20%)→计划(10%)'],
                ['培训课件开发', '课件/培训/话术/通关/新人班', '资深培训师', '正反对比 + 案例演练', '目标→概念→对比→案例→考核'],
                ['优秀经验分享', '标杆/萃取/转介绍/绩优/分享', '经验萃取专家', '荣誉档案 + 方法论卡片', '数据→故事→方法论→工具→行动'],
              ].map((row, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-2 px-2 font-medium">{row[0]}</td>
                  <td className="py-2 px-2 text-[10px] text-gray-500">{row[1]}</td>
                  <td className="py-2 px-2">{row[2]}</td>
                  <td className="py-2 px-2">{row[3]}</td>
                  <td className="py-2 px-2 text-[10px] text-gray-500">{row[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-xs text-gray-400 mt-3">
          每个场景都有专属的 few-shot 示例（含真实保险业务数据），AI 会参照示例的格式、密度和风格生成。<br />
          上传文档后自动关键词匹配，也可在「AI帮我做」或「AI陪我做」模式下手动选择场景。
        </p>
      </section>

      {/* ===== 十、保险行业模式 ===== */}
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
            a={
              <span>
                <strong>AI替我做</strong>：给材料→一键自动出稿，场景/模板/页数全自动识别。<br/>
                <strong>AI帮我做</strong>：给材料+设需求→生成大纲→逐页审核→手动点击生成PPT。<br/>
                <strong>AI陪我做</strong>：给材料+设需求→生成大纲→逐页审核→确认后自动生成→编辑器逐页微调。<br/>
                详见上方对比表格。
              </span> as any
            } />
          <FAQ q="生成失败怎么办？"
            a="AI 解析失败会自动重试一次（降低温度提高稳定性）。若仍失败，自动回退到离线规则引擎。也可直接选择离线模式。" />
          <FAQ q="API Key 安全吗？"
            a="密钥通过 Electron safeStorage 系统级加密存储。生成时仅传输所选模型的密钥到本地后端 127.0.0.1，不上传任何外部服务器。" />
          <FAQ q="怎么给已有 PPT 润色？"
            a="选择「润色」场景 → 上传 .pptx → AI 提取内容并优化标题/数据/布局 → 生成优化版 PPT。" />
          <FAQ q="画布元素刷新后会丢失吗？"
            a="不会。画布元素每 3 秒自动保存到 localStorage，关闭页面前也会即时保存。编辑内容后 SVG 预览 0.8 秒内自动刷新，所见即所得。" />
          <FAQ q="语音旁白怎么用？"
            a="1. 在编辑器右侧面板「备注」中为每页填写演讲内容；2. 点击工具栏「旁白」按钮；3. 在弹出的对话框中选择引擎（Edge TTS 免费 / ElevenLabs 最自然 / MiniMax 中文好）；4. 点击「生成并下载 MP3」。详细配置方法见上方「语音旁白配置」章节。" />
          <FAQ q="可以离线使用吗？"
            a="四种方式：① 本地 Ollama 大模型（需提前安装拉取模型）；② ComfyUI 本地生图（需 GPU 6GB+）；③ 离线规则引擎（零依赖）；④ Edge TTS 旁白（免费）。以上都不行时自动回退。" />
          <FAQ q="Ollama 地址怎么改？"
            a="设置页选择 Ollama 供应商后，接口地址输入框可编辑。支持修改为局域网地址或自定义端口。" />
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

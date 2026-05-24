const stylePresets = [
  { id: 'business', label: '商务', desc: '深蓝+金色，专业正式', color: '#1e40af', style: '配色：深蓝#1e40af+金色#fbbf24，主标题加粗，每页5-7个要点，适合正式场合投影' },
  { id: 'creative', label: '创意', desc: '明亮配色，活力动感', color: '#7c3aed', style: '配色：紫色#7c3aed+橙色#f97316，使用渐变背景，卡片圆角8px，添加入场动画' },
  { id: 'education', label: '教育', desc: '清新蓝绿，清晰易懂', color: '#3b82f6', style: '配色：教育蓝#3b82f6+清新绿#10b981，每页3-5个知识点，添加进度条，字体稍大' },
  { id: 'minimal', label: '简约', desc: '白底黑字，极简留白', color: '#374151', style: '配色：白色背景+深灰文字，使用大量留白，无边框卡片，重点加粗，适合轻薄需求' },
  { id: 'luxury', label: '高端', desc: '黑金配色，奢华质感', color: '#0f172a', style: '配色：深黑#0f172a+金色#fbbf24，使用暗色背景，添加金属质感边框，适合高端场合' },
  { id: 'data', label: '数据', desc: '强调数字，图表优先', color: '#059669', style: '配色：绿色#059669+蓝色#3b82f6，核心KPI大字号，数据精确，表格对齐，使用进度条可视化' },
]

export function StyleSelector({
  customStyle,
  onChange,
}: {
  customStyle: string
  onChange: (style: string) => void
}) {
  return (
    <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
      <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">自定义风格（可选）</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">选择或描述你想要的风格</p>
      <div className="grid grid-cols-3 gap-2">
        {stylePresets.map((preset) => (
          <button key={preset.id} onClick={() => onChange(preset.style)}
            className={`p-2.5 rounded-lg border-2 text-left transition-all ${
              customStyle === preset.style
                ? 'border-primary-500 bg-primary-50'
                : 'border-transparent hover:border-gray-300 bg-gray-50'
            }`}>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: preset.color }} />
              <span className="text-sm font-medium text-gray-700">{preset.label}</span>
            </div>
            <div className="text-xs text-gray-400 mt-1 ml-5">{preset.desc}</div>
          </button>
        ))}
      </div>
      <div className="text-center text-xs text-gray-400">或手动输入风格要求：</div>
      <textarea value={customStyle} onChange={(e) => onChange(e.target.value)}
        placeholder="例如：配色为深蓝+金色，标题加粗，每页不超过5个要点..."
        className="input-field h-16 resize-none" />
    </section>
  )
}

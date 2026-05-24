import { FileText, Globe, Type, Sparkles, Upload, Shield, RefreshCw } from 'lucide-react'
import type { SceneType } from '@/types'

const scenes: { type: SceneType; label: string; desc: string; icon: typeof Sparkles }[] = [
  { type: 'report', label: '报告', desc: '年度汇报 工作总结\n项目展示 市场分析', icon: FileText },
  { type: 'education', label: '教育', desc: '课件制作 培训演示\n知识讲解 课程设计', icon: Sparkles },
  { type: 'proposal', label: '提案', desc: '项目路演 商业计划\n产品介绍 融资方案', icon: Globe },
  { type: 'transform', label: '转换', desc: '文档转换 灯片重塑\n内容重构 格式适配', icon: Upload },
  { type: 'brainstorm', label: '研讨', desc: '头脑风暴 大纲设计\n主题探索 团队协作', icon: Type },
  { type: 'insurance', label: '保险', desc: '会议启动 复盘总结\n分享微课 领导指示', icon: Shield },
  { type: 'enhance', label: '润色', desc: '导入PPTX\nAI优化升级', icon: RefreshCw },
]

export function SceneSelector({
  selectedScene,
  onSelect,
}: {
  selectedScene: SceneType
  onSelect: (scene: SceneType) => void
}) {
  return (
    <section className="card p-6 space-y-4 dark:bg-gray-800 dark:border-gray-700">
      <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">1. 选择场景</h2>
      <div className="grid grid-cols-7 gap-3">
        {scenes.map((scene) => {
          const Icon = scene.icon
          const isActive = selectedScene === scene.type
          return (
            <button
              key={scene.type}
              onClick={() => onSelect(scene.type)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                isActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 bg-white dark:bg-gray-800'
              }`}
            >
              <Icon className={`w-5 h-5 mb-2 ${isActive ? 'text-primary-600' : 'text-gray-400 dark:text-gray-500'}`} />
              <div className={`text-sm font-medium ${isActive ? 'text-primary-700 dark:text-primary-300' : 'text-gray-700 dark:text-gray-300'}`}>
                {scene.label}
              </div>
              <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5 whitespace-pre-line">{scene.desc}</div>
            </button>
          )
        })}
      </div>
    </section>
  )
}

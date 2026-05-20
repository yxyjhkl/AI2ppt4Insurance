import { useProjectStore } from '@/stores/projectStore'

export function TopBar() {
  const currentProject = useProjectStore((s) => s.currentProject)

  return (
    <header className="h-12 bg-white border-b border-gray-200 flex items-center px-4 shrink-0">
      <div className="flex-1 flex items-center space-x-3">
        {currentProject ? (
          <>
            <span className="text-sm font-medium text-gray-700">{currentProject.name}</span>
            <span className="text-xs text-gray-400">|</span>
            <span className="text-xs text-gray-500">
              {currentProject.slides.length} 页
            </span>
          </>
        ) : (
          <span className="text-sm text-gray-400">未打开项目</span>
        )}
      </div>
    </header>
  )
}
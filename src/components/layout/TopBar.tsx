import { Moon, Sun } from 'lucide-react'
import { useProjectStore } from '@/stores/projectStore'
import { useDarkMode } from '@/hooks/useDarkMode'

export function TopBar() {
  const currentProject = useProjectStore((s) => s.currentProject)
  const { dark, toggle } = useDarkMode()

  return (
    <header className="h-12 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center px-4 shrink-0 transition-colors">
      <div className="flex-1 flex items-center space-x-3">
        {currentProject ? (
          <>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{currentProject.name}</span>
            <span className="text-xs text-gray-400 dark:text-gray-500">|</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {currentProject.slides.length} 页
            </span>
          </>
        ) : (
          <span className="text-sm text-gray-400 dark:text-gray-500">未打开项目</span>
        )}
      </div>
      <button
        onClick={toggle}
        className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        title={dark ? '切换亮色模式' : '切换暗黑模式'}
      >
        {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </button>
    </header>
  )
}
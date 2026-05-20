import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Presentation,
  LayoutTemplate,
  Sparkles,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useLocale } from '@/locales'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/editor', icon: Presentation, label: '编辑器' },
  { to: '/templates', icon: LayoutTemplate, label: '模板库' },
  { to: '/prompts', icon: Sparkles, label: '提示词' },
  { to: '/settings', icon: Settings, label: '设置' },
  { to: '/help', icon: HelpCircle, label: '帮助' },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`bg-white border-r border-gray-200 flex flex-col shrink-0 transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-56'
      }`}
    >
      <div className={`h-14 flex items-center border-b border-gray-200 px-4 ${collapsed ? 'justify-center' : 'justify-between'}`}>
        {!collapsed && (
          <div className="flex items-center">
            <Presentation className="w-6 h-6 text-primary-600" />
            <span className="ml-2 font-bold text-gray-800">AI PPT</span>
          </div>
        )}
        {collapsed && <Presentation className="w-6 h-6 text-primary-600" />}
      </div>

      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center px-2 py-2.5 rounded-lg transition-colors duration-150 ${
                collapsed ? 'justify-center' : 'justify-start'
              } ${
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            <item.icon className="w-5 h-5 shrink-0" />
            {!collapsed && <span className="ml-3 text-sm font-medium">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-gray-200 p-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center py-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
          title={collapsed ? '展开侧边栏' : '折叠侧边栏'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span className="ml-2 text-xs">折叠</span>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
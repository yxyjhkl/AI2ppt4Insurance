import { createContext, useContext } from 'react'
import { zhCN, type Locale } from './zh-CN'

const LocaleContext = createContext<Locale>(zhCN)

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  return <LocaleContext.Provider value={zhCN}>{children}</LocaleContext.Provider>
}

export function useLocale(): Locale {
  return useContext(LocaleContext)
}
import { create } from 'zustand'
import type { Project, GenerationConfig, NetworkStatus, CachedGeneration } from '@/types'

const STORAGE_KEY = 'aippt_projects'
const CONFIG_KEY = 'aippt_gen_config'
const STORAGE_VERSION = 1

interface StoredData<T> {
  version: number
  data: T
  timestamp: number
}

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    
    let parsed = JSON.parse(raw)
    
    // 检查是否是版本化的数据
    if (parsed && typeof parsed === 'object' && 'version' in parsed && 'data' in parsed) {
      const stored = parsed as StoredData<T>
      if (stored.version <= STORAGE_VERSION) {
        // 未来可以在这里进行数据迁移
        return stored.data
      }
    }
    
    // 兼容旧格式
    return parsed || fallback
  } catch (e) {
    console.warn(`Failed to load from localStorage (key: ${key}):`, e)
    return fallback
  }
}

function save(key: string, value: unknown) {
  try {
    const data: StoredData<unknown> = {
      version: STORAGE_VERSION,
      data: value,
      timestamp: Date.now()
    }
    localStorage.setItem(key, JSON.stringify(data))
  } catch (e) {
    console.error(`Failed to save to localStorage (key: ${key}):`, e)
    // 静默失败，不影响应用运行
  }
}

export function clearStorage(key: string) {
  try {
    localStorage.removeItem(key)
  } catch {
    // 静默失败
  }
}

export function clearProjects() {
  clearStorage(STORAGE_KEY)
}

export function clearConfig() {
  clearStorage(CONFIG_KEY)
}

interface ProjectStore {
  currentProject: Project | null
  projects: Project[]
  generationConfig: GenerationConfig
  networkStatus: NetworkStatus
  lastGeneration: CachedGeneration | null

  setCurrentProject: (project: Project | null) => void
  setProjects: (projects: Project[]) => void
  updateGenerationConfig: (config: Partial<GenerationConfig>) => void
  setNetworkStatus: (status: NetworkStatus) => void
  setLastGeneration: (data: CachedGeneration | null) => void
  resetAll: () => void
}

const defaultConfig: GenerationConfig = {
  scene: 'report',
  meetingType: null,
  template: 'professional-blue',
  model: 'gpt-4',
  slideCount: 10,
  language: 'zh-CN',
  includeNotes: true,
  includeImages: true,
  includeAnimation: false,
  temperature: 0.7,
  canvasFormat: '16:9',
}

export const useProjectStore = create<ProjectStore>((set) => ({
  currentProject: null,
  projects: load<Project[]>(STORAGE_KEY, []),
  generationConfig: load<GenerationConfig>(CONFIG_KEY, defaultConfig),
  networkStatus: {
    online: navigator.onLine,
    ollamaAvailable: false,
    backendReady: false,
  },
  lastGeneration: null,

  setCurrentProject: (project) => {
    set({ currentProject: project })
    if (project) {
      set((state) => {
        const exists = state.projects.findIndex(p => p.id === project.id)
        const updated = exists >= 0
          ? state.projects.map((p, i) => i === exists ? project : p)
          : [project, ...state.projects]
        save(STORAGE_KEY, updated)
        return { projects: updated }
      })
    }
  },
  setProjects: (projects) => {
    set({ projects })
    save(STORAGE_KEY, projects)
  },
  updateGenerationConfig: (config) =>
    set((state) => {
      const updated = { ...state.generationConfig, ...config }
      save(CONFIG_KEY, updated)
      return { generationConfig: updated }
    }),
  setNetworkStatus: (status) => set({ networkStatus: status }),
  setLastGeneration: (data) => set({ lastGeneration: data }),
  resetAll: () => {
    clearProjects()
    clearConfig()
    set({
      currentProject: null,
      projects: [],
      generationConfig: defaultConfig,
      lastGeneration: null,
    })
  },
}))

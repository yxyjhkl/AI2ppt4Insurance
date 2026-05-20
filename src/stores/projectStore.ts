import { create } from 'zustand'
import type { Project, GenerationConfig, NetworkStatus, CachedGeneration } from '@/types'

const STORAGE_KEY = 'aippt_projects'
const CONFIG_KEY = 'aippt_gen_config'

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}
function save(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch { /* quota exceeded */ }
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
}))
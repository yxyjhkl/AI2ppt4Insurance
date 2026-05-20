import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { Dashboard } from './pages/Dashboard'
import { Editor } from './pages/Editor'
import { Templates } from './pages/Templates'
import { Settings } from './pages/Settings'
import { PromptLab } from './pages/PromptLab'
import { Presenter } from './pages/Presenter'
import { Help } from './pages/Help'

export default function App() {
  return (
    <Routes>
      <Route path="/presenter" element={<Presenter />} />
      <Route path="/*" element={
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/editor/:projectId?" element={<Editor />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/prompts" element={<PromptLab />} />
            <Route path="/help" element={<Help />} />
          </Routes>
        </Layout>
      } />
    </Routes>
  )
}

import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/Layout/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import CourseManage from './pages/CourseManage'
import Chat from './pages/Chat'
import Assignment from './pages/Assignment'
import GradingResult from './pages/GradingResult'
import Analytics from './pages/Analytics'
import Exercises from './pages/Exercises'
import AgentBuilder from './pages/AgentBuilder'
import PlatformConfig from './pages/PlatformConfig'
import { useAuthStore } from './hooks/useAuthStore'

function App() {
  const token = useAuthStore((s) => s.token)

  if (!token) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="courses" element={<CourseManage />} />
        <Route path="chat/:courseId?" element={<Chat />} />
        <Route path="assignments/:courseId?" element={<Assignment />} />
        <Route path="grading/:submissionId" element={<GradingResult />} />
        <Route path="analytics/:courseId?" element={<Analytics />} />
        <Route path="exercises/:courseId?" element={<Exercises />} />
        <Route path="agent-builder" element={<AgentBuilder />} />
        <Route path="platform" element={<PlatformConfig />} />
      </Route>
      <Route path="/login" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App

import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import MainLayout from './components/Layout/MainLayout'
import AppErrorBoundary from './components/common/AppErrorBoundary'
import { useAuthStore } from './hooks/useAuthStore'

const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const CourseManage = lazy(() => import('./pages/CourseManage'))
const Chat = lazy(() => import('./pages/Chat'))
const Assignment = lazy(() => import('./pages/Assignment'))
const GradingResult = lazy(() => import('./pages/GradingResult'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Exercises = lazy(() => import('./pages/Exercises'))
const AgentBuilder = lazy(() => import('./pages/AgentBuilder'))
const PlatformConfig = lazy(() => import('./pages/PlatformConfig'))
const Widget = lazy(() => import('./pages/Widget'))

function PageFallback() {
  return (
    <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 12, color: '#666' }}>页面加载中...</div>
      </div>
    </div>
  )
}

function App() {
  const token = useAuthStore((s) => s.token)

  if (!token) {
    return (
      <AppErrorBoundary>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/widget/chat" element={<Widget />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </Suspense>
      </AppErrorBoundary>
    )
  }

  return (
    <AppErrorBoundary>
      <Suspense fallback={<PageFallback />}>
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
          <Route path="/widget/chat" element={<Widget />} />
        </Routes>
      </Suspense>
    </AppErrorBoundary>
  )
}

export default App

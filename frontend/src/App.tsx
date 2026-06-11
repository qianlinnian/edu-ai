import { Suspense, lazy, type ReactNode } from 'react'
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

function StartupShell() {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(180deg, #f5f8fc 0%, #eaf0f7 100%)',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            width: 52,
            height: 52,
            margin: '0 auto 16px',
            borderRadius: 14,
            background: 'linear-gradient(135deg, #00a8ff, #0078d7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 800,
            fontSize: 24,
            boxShadow: '0 16px 32px rgba(0, 120, 215, 0.18)',
          }}
        >
          E
        </div>
        <Spin size="large" />
        <div style={{ marginTop: 12, color: '#425466', fontWeight: 600 }}>Starting EduAI...</div>
      </div>
    </div>
  )
}

function PageFallback() {
  return (
    <div style={{ minHeight: 280, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 12, color: '#666' }}>页面加载中...</div>
      </div>
    </div>
  )
}

function SuspendedPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageFallback />}>{children}</Suspense>
}

function App() {
  const hasHydrated = useAuthStore((s) => s.hasHydrated)
  const token = useAuthStore((s) => s.token)

  if (!hasHydrated) {
    return <StartupShell />
  }

  if (!token) {
    return (
      <AppErrorBoundary>
        <Routes>
          <Route path="/login" element={<SuspendedPage><Login /></SuspendedPage>} />
          <Route path="/widget/chat" element={<SuspendedPage><Widget /></SuspendedPage>} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AppErrorBoundary>
    )
  }

  return (
    <AppErrorBoundary>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<SuspendedPage><Dashboard /></SuspendedPage>} />
          <Route path="courses" element={<SuspendedPage><CourseManage /></SuspendedPage>} />
          <Route path="chat/:courseId?" element={<SuspendedPage><Chat /></SuspendedPage>} />
          <Route path="assignments/:courseId?" element={<SuspendedPage><Assignment /></SuspendedPage>} />
          <Route path="grading/:submissionId" element={<SuspendedPage><GradingResult /></SuspendedPage>} />
          <Route path="analytics/:courseId?" element={<SuspendedPage><Analytics /></SuspendedPage>} />
          <Route path="exercises/:courseId?" element={<SuspendedPage><Exercises /></SuspendedPage>} />
          <Route path="agent-builder" element={<SuspendedPage><AgentBuilder /></SuspendedPage>} />
          <Route path="platform" element={<SuspendedPage><PlatformConfig /></SuspendedPage>} />
        </Route>
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/widget/chat" element={<SuspendedPage><Widget /></SuspendedPage>} />
      </Routes>
    </AppErrorBoundary>
  )
}

export default App

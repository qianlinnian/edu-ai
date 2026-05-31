import axios from 'axios'
import { useAuthStore } from '../hooks/useAuthStore'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截：自动携带token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401自动登出
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestPath = error.config?.url || ''
    if (error.response?.status === 401 && !requestPath.includes('/auth/login')) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

export function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }

    if (Array.isArray(detail)) {
      const parts = detail
        .map((item) => {
          if (typeof item === 'string') return item
          if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') return item.msg
          return ''
        })
        .filter(Boolean)

      if (parts.length > 0) {
        return parts.join('；')
      }
    }

    if (!error.response) {
      return '网络连接失败，请检查服务或网络后重试'
    }

    if (error.code === 'ECONNABORTED') {
      return '请求超时，请稍后重试'
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  return fallback
}

// ===== Auth API =====
export const authAPI = {
  login: (username: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    return api.post('/auth/login', form)
  },
  register: (data: { username: string; email: string; password: string; full_name: string; role: string }) =>
    api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
}

// ===== Course API =====
export const courseAPI = {
  list: () => api.get('/courses'),
  get: (id: number) => api.get(`/courses/${id}`),
  create: (data: any) => api.post('/courses', data),
  update: (id: number, data: any) => api.put(`/courses/${id}`, data),
  remove: (id: number) => api.delete(`/courses/${id}`),
  listResources: (courseId: number) => api.get(`/courses/${courseId}/resources`),
  downloadResource: (courseId: number, resourceId: number) =>
    api.get(`/courses/${courseId}/resources/${resourceId}/download`, { responseType: 'blob' }),
  uploadResource: (courseId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/courses/${courseId}/resources`, form)
  },
  deleteResource: (courseId: number, resourceId: number) => api.delete(`/courses/${courseId}/resources/${resourceId}`),
  listStudents: (courseId: number) => api.get(`/courses/${courseId}/students`),
  listKnowledgeUnits: (courseId: number) => api.get(`/courses/${courseId}/knowledge-units`),
  createKnowledgeUnit: (courseId: number, data: any) => api.post(`/courses/${courseId}/knowledge-units`, data),
  generateKnowledgeUnits: (courseId: number) => api.post(`/courses/${courseId}/knowledge-units/generate`),
}
// ===== Chat API =====
export const chatAPI = {
  send: (data: { agent_id: number; course_id: number; session_id?: number; message: string }) =>
    api.post('/chat/send', data),
  sendStreamUrl: '/api/v1/chat/send-stream',
  listSessions: (courseId?: number) => api.get('/chat/sessions', { params: { course_id: courseId } }),
  getMessages: (sessionId: number) => api.get(`/chat/sessions/${sessionId}/messages`),
  deleteSession: (sessionId: number) => api.delete(`/chat/sessions/${sessionId}`),
}

// ===== Assignment API =====
export const assignmentAPI = {
  list: (courseId: number) => api.get('/assignments', { params: { course_id: courseId } }),
  create: (data: any) => api.post('/assignments', data),
  listSubmissions: (assignmentId: number) => api.get(`/assignments/${assignmentId}/submissions`),
  submit: (assignmentId: number, content?: string, file?: File) => {
    const form = new FormData()
    if (content) form.append('content', content)
    if (file) form.append('file', file)
    return api.post(`/assignments/${assignmentId}/submit`, form)
  },
  getResult: (submissionId: number) => api.get(`/assignments/submissions/${submissionId}/result`),
  getAnnotations: (submissionId: number) => api.get(`/assignments/submissions/${submissionId}/annotations`),
}

// ===== Analytics API =====
export const analyticsAPI = {
  getStudentMastery: (studentId: number, courseId: number) =>
    api.get(`/analytics/student/${studentId}/mastery`, { params: { course_id: courseId } }),
  getWeakPoints: (studentId: number, courseId: number) =>
    api.get(`/analytics/student/${studentId}/weak-points`, { params: { course_id: courseId } }),
  getClassReport: (courseId: number) => api.get(`/analytics/course/${courseId}/class-report`),
  getAlerts: (courseId?: number) => api.get('/analytics/alerts', { params: { course_id: courseId } }),
}

// ===== Exercise API =====
export const exerciseAPI = {
  generate: (data: any) => api.post('/exercises/generate', data),
  attempt: (data: any) => api.post('/exercises/attempt', data),
  listPool: (courseId: number) => api.get('/exercises/pool', { params: { course_id: courseId } }),
}

// ===== Agent API =====
export const agentAPI = {
  listTemplates: () => api.get('/agents/templates'),
  listInstances: (courseId?: number) => api.get('/agents/instances', { params: { course_id: courseId } }),
  createInstance: (data: any) => api.post('/agents/instances', data),
  createWorkflow: (data: any) => api.post('/agents/workflows', data),
}

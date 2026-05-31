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

export type SSEChunkCallback = (content: string) => void
export type SSEDoneCallback = (sessionId: number, messageId: number) => void
export type SSEErrorCallback = (detail: string) => void

export interface SSECallbacks {
  onChunk: SSEChunkCallback
  onDone: SSEDoneCallback
  onError: SSEErrorCallback
}

export function createAbortController(): AbortController {
  return new AbortController()
}

export function fetchSSE(
  url: string,
  body: Record<string, unknown>,
  callbacks: SSECallbacks,
  abortSignal?: AbortSignal,
  timeoutMs?: number
): void {
  const token = useAuthStore.getState().token

  const controller = new AbortController()
  const timeoutId = timeoutMs ? setTimeout(() => controller.abort(), timeoutMs) : null

  // 监听外部 abort 信号，传递到本地 controller
  if (abortSignal) {
    abortSignal.addEventListener('abort', () => controller.abort())
  }

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal: controller.signal,
  }).then(async (response) => {
    if (timeoutId) clearTimeout(timeoutId)
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
      callbacks.onError(err.detail || `HTTP ${response.status}`)
      return
    }
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const read = () => {
      reader.read().then(({ done, value }) => {
        if (done) return
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data:')) continue
          try {
            const data = JSON.parse(trimmed.slice(5).trim())
            if (data.type === 'chunk') {
              callbacks.onChunk(data.content ?? '')
            } else if (data.type === 'done') {
              callbacks.onDone(data.session_id, data.message_id)
            } else if (data.type === 'error') {
              callbacks.onError(data.detail ?? 'Unknown error')
            }
          } catch {
            // ignore parse error
          }
        }
        read()
      })
    }
    read()
  }).catch((err: Error) => {
    if (timeoutId) clearTimeout(timeoutId)
    if (err.name === 'AbortError') return
    callbacks.onError(err.message || 'Network error')
  })
}

export default api

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

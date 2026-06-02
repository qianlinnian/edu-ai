import axios from 'axios'
import { useAuthStore } from '../hooks/useAuthStore'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

type RequestConfig = {
  headers?: Record<string, string>
  params?: Record<string, unknown>
  responseType?: 'blob'
}

type SSEChunkCallback = (content: string) => void
type SSEDoneCallback = (sessionId: number, messageId: number) => void
type SSEErrorCallback = (detail: string) => void
type SSEAbortCallback = () => void

export interface SSECallbacks {
  onChunk: SSEChunkCallback
  onDone: SSEDoneCallback
  onError: SSEErrorCallback
  onAbort?: SSEAbortCallback
}

function buildAuthConfig(authToken?: string, config: RequestConfig = {}): RequestConfig {
  if (!authToken) return config
  return {
    ...config,
    headers: {
      ...(config.headers ?? {}),
      Authorization: `Bearer ${authToken}`,
    },
  }
}

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestPath = error.config?.url || ''
    const isWidgetPage = typeof window !== 'undefined' && window.location.pathname.startsWith('/widget/')
    if (error.response?.status === 401 && !requestPath.includes('/auth/login') && !isWidgetPage) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export function createAbortController(): AbortController {
  return new AbortController()
}

export function fetchSSE(
  url: string,
  body: Record<string, unknown>,
  callbacks: SSECallbacks,
  abortSignal?: AbortSignal,
  timeoutMs?: number,
  authToken?: string
): void {
  const token = authToken || useAuthStore.getState().token || undefined
  const controller = new AbortController()
  const timeoutId = timeoutMs ? setTimeout(() => controller.abort(), timeoutMs) : null

  if (abortSignal) {
    abortSignal.addEventListener('abort', () => controller.abort(), { once: true })
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

    const reader = response.body?.getReader()
    if (!reader) {
      callbacks.onError('Empty SSE response body')
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    const handleEvent = (rawLine: string) => {
      const trimmed = rawLine.trim()
      if (!trimmed.startsWith('data:')) return false
      try {
        const data = JSON.parse(trimmed.slice(5).trim())
        if (data.type === 'chunk') {
          callbacks.onChunk(data.content ?? '')
          return false
        }
        if (data.type === 'done') {
          callbacks.onDone(data.session_id, data.message_id)
          return true
        }
        if (data.type === 'error') {
          callbacks.onError(data.detail ?? data.error ?? 'Unknown error')
          return true
        }
      } catch {
        // Ignore malformed SSE frames.
      }
      return false
    }

    const read = () => {
      reader.read().then(({ done, value }) => {
        if (done) {
          if (buffer.trim()) {
            handleEvent(buffer)
          }
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (handleEvent(line)) {
            return
          }
        }

        read()
      }).catch((err: Error) => {
        if (err.name === 'AbortError') {
          callbacks.onAbort?.()
          return
        }
        callbacks.onError(err.message || 'Network error')
      })
    }

    read()
  }).catch((err: Error) => {
    if (timeoutId) clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      callbacks.onAbort?.()
      return
    }
    callbacks.onError(err.message || 'Network error')
  })
}

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

export const courseAPI = {
  list: (authToken?: string) => api.get('/courses', buildAuthConfig(authToken)),
  get: (id: number, authToken?: string) => api.get(`/courses/${id}`, buildAuthConfig(authToken)),
  create: (data: any) => api.post('/courses', data),
  update: (id: number, data: any) => api.put(`/courses/${id}`, data),
  remove: (id: number) => api.delete(`/courses/${id}`),
  listResources: (courseId: number, authToken?: string) =>
    api.get(`/courses/${courseId}/resources`, buildAuthConfig(authToken)),
  downloadResource: (courseId: number, resourceId: number, authToken?: string) =>
    api.get(
      `/courses/${courseId}/resources/${resourceId}/download`,
      buildAuthConfig(authToken, { responseType: 'blob' })
    ),
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

export const chatAPI = {
  send: (data: { agent_id: number; course_id: number; session_id?: number; message: string }) =>
    api.post('/chat/send', data),
  sendStreamUrl: '/api/v1/chat/send-stream',
  listSessions: (courseId?: number) => api.get('/chat/sessions', { params: { course_id: courseId } }),
  getMessages: (sessionId: number) => api.get(`/chat/sessions/${sessionId}/messages`),
  deleteSession: (sessionId: number) => api.delete(`/chat/sessions/${sessionId}`),
}

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

export const analyticsAPI = {
  getStudentMastery: (studentId: number, courseId: number) =>
    api.get(`/analytics/student/${studentId}/mastery`, { params: { course_id: courseId } }),
  getWeakPoints: (studentId: number, courseId: number) =>
    api.get(`/analytics/student/${studentId}/weak-points`, { params: { course_id: courseId } }),
  getClassReport: (courseId: number) => api.get(`/analytics/course/${courseId}/class-report`),
  getAlerts: (courseId?: number) => api.get('/analytics/alerts', { params: { course_id: courseId } }),
}

export const exerciseAPI = {
  generate: (data: any) => api.post('/exercises/generate', data),
  attempt: (data: any) => api.post('/exercises/attempt', data),
  listPool: (courseId: number) => api.get('/exercises/pool', { params: { course_id: courseId } }),
}

export const agentAPI = {
  listTemplates: () => api.get('/agents/templates'),
  listInstances: (courseId?: number, authToken?: string) =>
    api.get('/agents/instances', buildAuthConfig(authToken, { params: { course_id: courseId } })),
  getInstance: (id: number) => api.get(`/agents/instances/${id}`),
  createInstance: (data: any) => api.post('/agents/instances', data),
  updateInstance: (id: number, data: any) => api.put(`/agents/instances/${id}`, data),
  publishInstance: (id: number) => api.post(`/agents/instances/${id}/publish`),
  listWorkflows: (agentId: number) => api.get('/agents/workflows', { params: { agent_id: agentId } }),
  getWorkflow: (id: number) => api.get(`/agents/workflows/${id}`),
  createWorkflow: (data: any) => api.post('/agents/workflows', data),
  updateWorkflow: (id: number, data: any) => api.put(`/agents/workflows/${id}`, data),
  publishWorkflow: (id: number) => api.post(`/agents/workflows/${id}/publish`),
  saveAndPublish: async (nodes: any[], edges: any[], agentName: string, courseId: number = 3) => {
    const workflowDAG = { nodes, edges }

    const instanceData = {
      template_id: null,
      course_id: courseId,
      name: agentName,
      description: `由 ${agentName} Agent Builder 创建`,
      system_prompt: '你是一个智能教学助手，负责回答课程相关问题。',
      config: {},
      tools: [],
      llm_provider: 'dashscope',
      llm_model: 'qwen-max',
    }

    const instanceRes = await api.post('/agents/instances', instanceData)
    const agentId = instanceRes.data.id

    const workflowData = {
      agent_id: agentId,
      name: `${agentName} 工作流`,
      description: '由 Agent Builder 生成',
      workflow_dag: workflowDAG,
    }

    const workflowRes = await api.post('/agents/workflows', workflowData)

    return { instanceId: agentId, workflowId: workflowRes.data.id }
  },
}

export const platformAPI = {
  listConnections: () => api.get('/platform/connections'),
  createConnection: (data: any) => api.post('/platform/connections', data),
  launchChaoxing: (data: { course_id: number; launch_ticket: string; role: 'student' | 'teacher' | 'assistant' }) =>
    api.post('/platform/chaoxing/lti-launch', data),
  dingtalkAuth: (params: { code: string; course_id: number; role: 'student' | 'teacher' | 'assistant' }) =>
    api.get('/platform/dingtalk/auth', { params }),
}

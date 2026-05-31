import { useState, useRef, useEffect } from 'react'
import { Input, Button, Avatar, Tag, Select } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined, CloseOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useSearchParams } from 'react-router-dom'
import { fetchSSE, createAbortController, courseAPI, agentAPI } from '../../services/api'

interface CourseItem {
  id: number
  name: string
  code: string
}

interface AgentItem {
  id: number
  name: string
  course_id: number
  is_active: boolean
}

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
}

export default function Widget() {
  const [searchParams] = useSearchParams()
  const courseIdParam = searchParams.get('course') ?? '1'
  const courseId = parseInt(courseIdParam, 10)

  const [courseIdState, setCourseIdState] = useState<number>(courseId)
  const [courseName, setCourseName] = useState('AI助手')
  const [courses, setCourses] = useState<CourseItem[]>([])
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [agents, setAgents] = useState<AgentItem[]>([])
  const [loadingAgents, setLoadingAgents] = useState(false)
  const activeAgentRef = useRef<AgentItem | null>(null)

  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: 'assistant', content: `你好！我是 **${courseName}** 的 AI 助手，有什么可以帮你？` },
  ])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const loadingMsgIdRef = useRef<number>(0)
  const sessionIdRef = useRef<number | null>(null)

  const loadAgents = (cid: number) => {
    setLoadingAgents(true)
    agentAPI.listInstances(cid).then(({ data }: { data: AgentItem[] }) => {
      setAgents(data)
      activeAgentRef.current = data.find((a) => a.is_active) ?? data[0] ?? null
    }).catch(() => {
      setAgents([])
      activeAgentRef.current = null
    }).finally(() => setLoadingAgents(false))
  }

  useEffect(() => {
    setLoadingCourses(true)
    courseAPI.list().then(({ data }) => {
      setCourses(data)
      if (data.length > 0) {
        const matched = data.find((c: CourseItem) => c.id === courseIdState)
        setCourseName(matched?.name ?? 'AI助手')
        loadAgents(courseIdState)
      }
    }).catch(() => {
    }).finally(() => setLoadingCourses(false))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, error])

  const stopStream = () => {
    abortControllerRef.current?.abort()
    setStreaming(false)
  }

  const send = () => {
    const text = input.trim()
    if (!text || streaming) return
    if (!activeAgentRef.current) {
      setError('当前课程没有可用答疑 Agent，请先在 Agent Builder 中创建')
      return
    }
    setInput('')
    setError(null)
    setStreaming(true)

    const uid = Date.now()
    const aid = uid + 1
    loadingMsgIdRef.current = aid
    setMessages(p => [
      ...p,
      { id: uid, role: 'user', content: text },
      { id: aid, role: 'assistant', content: '', loading: true },
    ])

    abortControllerRef.current = createAbortController()
    let cur = ''

    fetchSSE(
      '/api/v1/chat/send-stream',
      {
        agent_id: activeAgentRef.current.id,
        course_id: courseIdState,
        session_id: sessionIdRef.current ?? undefined,
        message: text,
      },
      {
        onChunk: (content: string) => {
          cur += content
          setMessages(p => p.map(m => m.id === loadingMsgIdRef.current ? { ...m, content: cur, loading: false } : m))
        },
        onDone: (sessionId: number, messageId: number) => {
          sessionIdRef.current = sessionId
          setMessages(p => p.map(m => m.id === loadingMsgIdRef.current ? { ...m, id: messageId, loading: false } : m))
          setStreaming(false)
        },
        onError: (detail: string) => {
          const isConfigError =
            (detail && /api.?key|api.?key未配置|API.?key|未设置|not configured/i.test(detail)) ||
            (detail && /provider|llm|模型/i.test(detail) && /未配置|未设置|not.?found|empty|null|undefined/i.test(detail))
          const msg = isConfigError
            ? 'AI 服务配置不完整，请联系管理员配置 LLM API Key（通义千问/DeepSeek/智谱）'
            : detail
              ? `请求失败：${detail}`
              : '后端服务未响应，请检查后端服务是否正常运行'
          setError(msg)
          setMessages(p => p.map(m => m.id === loadingMsgIdRef.current ? { ...m, content: msg, loading: false } : m))
          setStreaming(false)
        },
      },
      abortControllerRef.current.signal
    )
  }

  return (
    <div style={{
      width: '100%', height: '100vh', display: 'flex', flexDirection: 'column',
      background: '#fff', fontFamily: 'system-ui, sans-serif',
    }}>
      {/* 顶栏 */}
      <div style={{
        padding: '10px 14px', background: 'linear-gradient(90deg,#0f1b2d,#1a3a5c)',
        display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0,
      }}>
        <RobotOutlined style={{ color: '#00a8ff', fontSize: 18 }} />
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 14, flex: 1 }}>{courseName} · AI助手</span>
        <Select
          size="small"
          value={courseIdState}
          loading={loadingCourses}
          onChange={(val) => {
            const matched = courses.find(c => c.id === val)
            setCourseName(matched?.name ?? 'AI助手')
            setCourseIdState(val)
            loadAgents(val)
            setMessages([{ id: 1, role: 'assistant', content: `你好！我是 AI 助手，有什么可以帮你？` }])
            sessionIdRef.current = null
          }}
          style={{ width: 130 }}
            options={courses.map((c: CourseItem) => ({ value: c.id, label: c.name }))}
          placeholder="加载中..."
        />
        <Tag color={loadingAgents ? 'processing' : activeAgentRef.current ? 'green' : 'default'} style={{ fontSize: 10 }}>
          {loadingAgents ? '加载中...' : activeAgentRef.current ? activeAgentRef.current.name : '无 Agent'}
        </Tag>
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={{ padding: '6px 12px', background: '#fff2f0', color: '#cf1322', fontSize: 12 }}>
          错误：{error}
        </div>
      )}

      {/* 消息区 */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px' }}>
        {messages.map(msg => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              gap: 8, marginBottom: 14, alignItems: 'flex-start',
            }}
          >
            <Avatar
              size={28}
              style={{ background: msg.role === 'assistant' ? '#00a8ff' : '#6366f1', flexShrink: 0 }}
              icon={msg.role === 'assistant' ? <RobotOutlined /> : <UserOutlined />}
            />
            <div style={{
              maxWidth: '78%',
              background: msg.role === 'user' ? '#6366f1' : '#f4f4f5',
              color: msg.role === 'user' ? '#fff' : '#1a1a1a',
              padding: '8px 12px',
              borderRadius: msg.role === 'user' ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
              fontSize: 13, lineHeight: 1.65,
            }}>
              {msg.loading ? (
                <span style={{ display: 'inline-flex', gap: 3 }}>
                  {[0, 150, 300].map(d => (
                    <span key={d} style={{
                      width: 6, height: 6, borderRadius: '50%', background: '#00a8ff',
                      display: 'inline-block', animation: `bounce 1s ${d}ms infinite`,
                    }} />
                  ))}
                </span>
              ) : msg.role === 'user' ? (
                msg.content
              ) : (
                <ReactMarkdown
                  components={{
                    code({ className, children, ...props }: any) {
                      const match = /language-(\w+)/.exec(className || '')
                      return match ? (
                        <SyntaxHighlighter
                          style={vscDarkPlus as any}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{ borderRadius: 6, margin: '6px 0', fontSize: 12 }}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code style={{ background: '#e4e4e7', padding: '1px 5px', borderRadius: 3, fontSize: '0.9em' }} {...props}>
                          {children}
                        </code>
                      )
                    },
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* 输入区 */}
      <div style={{ padding: '8px 10px 10px', borderTop: '1px solid #f0f0f0', flexShrink: 0 }}>
        <style>{`@keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-5px)}}`}</style>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <Input.TextArea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
            placeholder="输入问题…"
            autoSize={{ minRows: 1, maxRows: 3 }}
            style={{ borderRadius: 8, fontSize: 13, flex: 1 }}
            disabled={streaming}
          />
          {streaming ? (
            <Button
              danger
              icon={<CloseOutlined />}
              onClick={stopStream}
              style={{ height: 36, width: 44, borderRadius: 8 }}
            />
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={send}
              disabled={!input.trim()}
              style={{ height: 36, width: 44, borderRadius: 8, background: 'linear-gradient(90deg,#00a8ff,#0078d7)', border: 'none' }}
            />
          )}
        </div>
      </div>
    </div>
  )
}


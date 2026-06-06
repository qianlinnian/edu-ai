import { useEffect, useMemo, useRef, useState } from 'react'
import { Alert, Avatar, Button, Empty, Input, Select, Tag } from 'antd'
import { CloseOutlined, RobotOutlined, SendOutlined, UserOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useSearchParams } from 'react-router-dom'
import { agentAPI, chatAPI, courseAPI, createAbortController, fetchSSE, getErrorMessage } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

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

function buildWelcomeMessage(courseName: string): Message {
  return {
    id: Date.now(),
    role: 'assistant',
    content: `你好，我是 **${courseName}** 的 AI 助手，有什么可以帮你？`,
  }
}

export default function Widget() {
  const [searchParams] = useSearchParams()
  const queryToken = searchParams.get('token')?.trim() || ''
  const storeToken = useAuthStore((s) => s.token)
  const authToken = queryToken || storeToken || ''
  const courseId = Number(searchParams.get('course') || '1')

  const [courseIdState, setCourseIdState] = useState<number>(courseId)
  const [courseName, setCourseName] = useState('AI 助手')
  const [courses, setCourses] = useState<CourseItem[]>([])
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [agents, setAgents] = useState<AgentItem[]>([])
  const [loadingAgents, setLoadingAgents] = useState(false)
  const [messages, setMessages] = useState<Message[]>([buildWelcomeMessage('AI 助手')])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const abortControllerRef = useRef<AbortController | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const loadingMsgIdRef = useRef<number>(0)
  const sessionIdRef = useRef<number | null>(null)

  const activeAgent = useMemo(
    () => agents.find((item) => item.is_active) ?? agents[0] ?? null,
    [agents]
  )

  const resetConversation = (nextCourseName: string) => {
    setMessages([buildWelcomeMessage(nextCourseName)])
    sessionIdRef.current = null
    setError(null)
  }

  const loadAgents = async (nextCourseId: number) => {
    if (!authToken) return
    setLoadingAgents(true)
    try {
      const { data } = await agentAPI.listInstances(nextCourseId, authToken)
      setAgents(data)
    } catch (err) {
      setAgents([])
      setError(getErrorMessage(err, '加载课程 Agent 失败'))
    } finally {
      setLoadingAgents(false)
    }
  }

  useEffect(() => {
    if (!authToken) {
      setError('缺少嵌入访问令牌，请从平台嵌入入口重新打开。')
      return
    }

    const loadData = async () => {
      setLoadingCourses(true)
      try {
        const [{ data: courseData }, { data: currentCourse }] = await Promise.all([
          courseAPI.list(authToken),
          courseAPI.get(courseIdState, authToken),
        ])
        setCourses(courseData)
        setCourseName(currentCourse.name)
        resetConversation(currentCourse.name)
      } catch (err) {
        setError(getErrorMessage(err, '加载课程信息失败'))
      } finally {
        setLoadingCourses(false)
      }

      await loadAgents(courseIdState)
    }

    void loadData()
  }, [authToken, courseIdState])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, error])

  const stopStream = () => {
    abortControllerRef.current?.abort()
  }

  const send = () => {
    const text = input.trim()
    if (!text || streaming) return
    if (!authToken) {
      setError('缺少嵌入访问令牌，请从平台嵌入入口重新打开。')
      return
    }
    if (!activeAgent) {
      setError('当前课程没有可用的答疑 Agent，请联系教师先发布课程 Agent。')
      return
    }

    setInput('')
    setError(null)
    setStreaming(true)

    const userMessageId = Date.now()
    const loadingMessageId = userMessageId + 1
    loadingMsgIdRef.current = loadingMessageId

    setMessages((prev) => [
      ...prev,
      { id: userMessageId, role: 'user', content: text },
      { id: loadingMessageId, role: 'assistant', content: '', loading: true },
    ])

    abortControllerRef.current = createAbortController()
    let contentBuffer = ''

    fetchSSE(
      chatAPI.sendStreamUrl,
      {
        agent_id: activeAgent.id,
        course_id: courseIdState,
        session_id: sessionIdRef.current ?? undefined,
        message: text,
      },
      {
        onChunk: (chunk) => {
          contentBuffer += chunk
          setMessages((prev) =>
            prev.map((item) =>
              item.id === loadingMsgIdRef.current ? { ...item, content: contentBuffer, loading: false } : item
            )
          )
        },
        onDone: (sessionId, messageId) => {
          sessionIdRef.current = sessionId
          setMessages((prev) =>
            prev.map((item) =>
              item.id === loadingMsgIdRef.current ? { ...item, id: messageId, loading: false } : item
            )
          )
          setStreaming(false)
        },
        onError: (detail) => {
          const messageText = detail || '问答失败，请稍后重试'
          setError(messageText)
          setMessages((prev) =>
            prev.map((item) =>
              item.id === loadingMsgIdRef.current ? { ...item, content: messageText, loading: false } : item
            )
          )
          setStreaming(false)
        },
        onAbort: () => {
          setMessages((prev) =>
            prev.map((item) =>
              item.id === loadingMsgIdRef.current ? { ...item, content: '已取消本次回答。', loading: false } : item
            )
          )
          setStreaming(false)
        },
      },
      abortControllerRef.current.signal,
      undefined,
      authToken
    )
  }

  return (
    <div
      style={{
        width: '100%',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: '#fff',
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <div
        style={{
          padding: '10px 14px',
          background: 'linear-gradient(90deg,#0f1b2d,#1a3a5c)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          flexShrink: 0,
        }}
      >
        <RobotOutlined style={{ color: '#00a8ff', fontSize: 18 }} />
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 14, flex: 1 }}>{courseName} / AI 助手</span>
        <Select
          size="small"
          value={courseIdState}
          loading={loadingCourses}
          onChange={(value) => {
            const nextCourse = courses.find((item) => item.id === value)
            setCourseIdState(value)
            setCourseName(nextCourse?.name ?? 'AI 助手')
            resetConversation(nextCourse?.name ?? 'AI 助手')
          }}
          style={{ width: 150 }}
          options={courses.map((item) => ({ value: item.id, label: item.name }))}
          placeholder="选择课程"
        />
        <Tag color={loadingAgents ? 'processing' : activeAgent ? 'green' : 'default'} style={{ fontSize: 10 }}>
          {loadingAgents ? '加载中' : activeAgent ? activeAgent.name : '无 Agent'}
        </Tag>
      </div>

      {error && (
        <Alert
          type="error"
          showIcon
          message="嵌入问答不可用"
          description={error}
          style={{ margin: 12, marginBottom: 0 }}
        />
      )}

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
        {messages.length === 0 ? (
          <Empty description="暂无消息" />
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                gap: 8,
                marginBottom: 14,
                alignItems: 'flex-start',
              }}
            >
              <Avatar
                size={28}
                style={{ background: message.role === 'assistant' ? '#00a8ff' : '#6366f1', flexShrink: 0 }}
                icon={message.role === 'assistant' ? <RobotOutlined /> : <UserOutlined />}
              />
              <div
                style={{
                  maxWidth: '78%',
                  background: message.role === 'user' ? '#6366f1' : '#f4f4f5',
                  color: message.role === 'user' ? '#fff' : '#1a1a1a',
                  padding: '8px 12px',
                  borderRadius: message.role === 'user' ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                  fontSize: 13,
                  lineHeight: 1.65,
                }}
              >
                {message.loading ? (
                  <span style={{ color: '#777' }}>正在生成回答...</span>
                ) : message.role === 'user' ? (
                  message.content
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
                          <code
                            style={{ background: '#e4e4e7', padding: '1px 5px', borderRadius: 3, fontSize: '0.9em' }}
                            {...props}
                          >
                            {children}
                          </code>
                        )
                      },
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ padding: '8px 10px 10px', borderTop: '1px solid #f0f0f0', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <Input.TextArea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                send()
              }
            }}
            placeholder="输入问题..."
            autoSize={{ minRows: 1, maxRows: 3 }}
            style={{ borderRadius: 8, fontSize: 13, flex: 1 }}
            disabled={streaming || !authToken}
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
              disabled={!input.trim() || !authToken}
              style={{
                height: 36,
                width: 44,
                borderRadius: 8,
                background: 'linear-gradient(90deg,#00a8ff,#0078d7)',
                border: 'none',
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}

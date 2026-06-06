import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { Input, Button, Select, Avatar, Tag, Tooltip, Empty, Alert, message } from 'antd'
import {
  SendOutlined, RobotOutlined, UserOutlined,
  PlusOutlined, DeleteOutlined, CloseOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { agentAPI, chatAPI, courseAPI, fetchSSE, createAbortController, getErrorMessage } from '../../services/api'
import { useSessionStore, type PersistedMessage } from '../../hooks/useChatSession'

// ===== 类型 =====
interface CourseItem {
  id: number
  name: string
  code: string
  description?: string | null
  domain: string
}

interface AgentItem {
  id: number
  name: string
  description?: string | null
  course_id: number
  is_active: boolean
}

interface ServerSession {
  id: number
  title: string
  course_id: number
  created_at: string
}

interface ServerMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  metadata_?: unknown
}

// ===== 组件 =====
export default function Chat() {
  const sessions = useSessionStore((s) => s.sessions)
  const activeId = useSessionStore((s) => s.activeId)
  const setActiveId = useSessionStore((s) => s.setActiveId)
  const upsertSession = useSessionStore((s) => s.upsertSession)
  const updateSession = useSessionStore((s) => s.updateSession)
  const storeRemoveSession = useSessionStore((s) => s.removeSession)
  const setStoreSessions = useSessionStore((s) => s.setSessions)

  const [courses, setCourses] = useState<CourseItem[]>([])
  const [agents, setAgents] = useState<AgentItem[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>()
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [loadingAgents, setLoadingAgents] = useState(false)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const abortControllerRef = useRef<AbortController | null>(null)
  const loadingMsgIdRef = useRef<number>(0)
  const bottomRef = useRef<HTMLDivElement>(null)

  const activeSession = useMemo(
    () => sessions.find((s) => s.localId === activeId) ?? null,
    [sessions, activeId]
  )

  const selectedCourseItem = useMemo(
    () => courses.find((c) => c.id === selectedCourse) ?? null,
    [courses, selectedCourse]
  )

  const selectedAgent = useMemo(
    () => agents.find((a) => a.is_active) ?? agents[0] ?? null,
    [agents]
  )

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeSession?.messages.length])

  // 加载课程
  useEffect(() => {
    setLoadingCourses(true)
    courseAPI
      .list()
      .then(({ data }) => {
        setCourses(data)
        if (data.length > 0 && !selectedCourse) {
          setSelectedCourse(data[0].id)
        }
      })
      .catch((err: unknown) => {
        message.error(getErrorMessage(err, '加载课程列表失败，请检查后端服务是否正常运行'))
      })
      .finally(() => setLoadingCourses(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // 加载 Agent + 合并会话列表（切换课程时）
  useEffect(() => {
    if (!selectedCourseItem) return

    setLoadingAgents(true)
    agentAPI
      .listInstances(selectedCourseItem.id)
      .then(({ data }) => setAgents(data))
      .catch((err: unknown) => {
        message.error(getErrorMessage(err, '加载 Agent 列表失败，请检查后端服务是否正常运行'))
        setAgents([])
      })
      .finally(() => setLoadingAgents(false))

    chatAPI
      .listSessions(selectedCourseItem.id)
      .then(({ data }: { data: ServerSession[] }) => {
        // 从 store 实时读取，防止闭包旧值
        const currentSessions = useSessionStore.getState().sessions
        const serverIds = new Set(data.map((s) => s.id))

        // 保留其他课程的会话 + 本课程的本地会话 + 本课程的服务器会话
        const merged = [
          ...currentSessions.filter((s) => s.courseId !== selectedCourseItem.id),
          ...currentSessions.filter(
            (s) => s.courseId === selectedCourseItem.id && !serverIds.has(Math.abs(s.localId))
          ),
          ...data.map((s) => ({
            localId: -s.id,
            serverSessionId: s.id,
            title: s.title,
            courseId: s.course_id,
            courseName: selectedCourseItem.name,
            messages: [] as PersistedMessage[],
          })),
        ]

        setStoreSessions(merged)

        const localOfThisCourse = merged.filter(
          (s) => s.courseId === selectedCourseItem.id && s.serverSessionId === undefined
        )
        if (localOfThisCourse.length > 0) {
          setActiveId(localOfThisCourse[0].localId)
        } else if (data.length > 0) {
          setActiveId(-data[0].id)
        } else {
          setActiveId(null)
        }
      })
      .catch((err: unknown) => {
        message.error(getErrorMessage(err, '加载会话列表失败，请检查后端服务是否正常运行'))
      })
  }, [selectedCourseItem?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  // 加载历史消息
  useEffect(() => {
    if (!activeId) return
    const session = useSessionStore.getState().sessions.find((s) => s.localId === activeId)
    if (!session || !session.serverSessionId || session.messages.length > 0) return

    chatAPI
      .getMessages(session.serverSessionId)
      .then(({ data }: { data: ServerMessage[] }) => {
        upsertSession({
          ...session,
          messages: data.map((m) => ({ id: m.id, role: m.role as 'user' | 'assistant', content: m.content })),
        })
      })
      .catch((err: unknown) => {
        message.error(getErrorMessage(err, '加载历史消息失败，请检查后端服务是否正常运行'))
        upsertSession({
          ...session,
          messages: [{ id: Date.now(), role: 'assistant', content: '加载历史消息失败，请刷新重试。' }],
        })
      })
  }, [activeId]) // eslint-disable-line react-hooks/exhaustive-deps

  const createSession = useCallback(() => {
    if (!selectedCourseItem) return
    const newSession = {
      localId: Date.now(),
      title: `新对话 · ${selectedCourseItem.name}`,
      courseId: selectedCourseItem.id,
      courseName: selectedCourseItem.name,
      agentId: selectedAgent?.id,
      messages: [
        {
          id: Date.now(),
          role: 'assistant' as const,
          content: `你好！我是 **${selectedCourseItem.name}** 课程助手，请开始提问。`,
        },
      ],
    }
    upsertSession(newSession)
    setActiveId(newSession.localId)
  }, [selectedCourseItem, selectedAgent, upsertSession, setActiveId])

  const removeSession = useCallback(
    async (localId: number, e: React.MouseEvent) => {
      e.stopPropagation()
      const session = useSessionStore.getState().sessions.find((item) => item.localId === localId)
      try {
        if (session?.serverSessionId) {
          await chatAPI.deleteSession(session.serverSessionId)
        }
        storeRemoveSession(localId)
      } catch (err) {
        message.error(getErrorMessage(err, '删除对话失败，请稍后重试'))
      }
    },
    [storeRemoveSession]
  )

  const send = useCallback(() => {
    const text = input.trim()
    if (!text) return

    // 实时读取所有依赖，杜绝任何闭包旧值
    const store = useSessionStore.getState()
    const currentSession = store.sessions.find((s) => s.localId === store.activeId)
    if (!currentSession) return

    const coursesNow = courses
    const agentsNow = agents
    const selCourse = coursesNow.find((c) => c.id === selectedCourse)
    const selAgent = agentsNow.find((a) => a.is_active) ?? agentsNow[0] ?? null
    if (!selCourse || !selAgent) {
      message.warning(!selCourse ? '请先选择课程' : '当前课程还没有可用答疑 Agent，请先在 Agent Builder 中创建')
      return
    }
    if (sending) return

    setInput('')
    setSending(true)

    const userMsgId = Date.now()
    const loadingMsgId = userMsgId + 1
    loadingMsgIdRef.current = loadingMsgId

    upsertSession({
      ...currentSession,
      title: currentSession.serverSessionId ? currentSession.title : text.slice(0, 20),
      agentId: selAgent.id,
      messages: [
        ...currentSession.messages,
        { id: userMsgId, role: 'user' as const, content: text },
        { id: loadingMsgId, role: 'assistant' as const, content: '', loading: true },
      ],
    })

    abortControllerRef.current = createAbortController()

    fetchSSE(
      chatAPI.sendStreamUrl,
      {
        agent_id: selAgent.id,
        course_id: selCourse.id,
        session_id: currentSession.serverSessionId ?? undefined,
        message: text,
      },
      {
        onChunk: (content: string) => {
          const sid = useSessionStore.getState().activeId
          if (sid === null) return
          updateSession(sid, (s) => ({
            ...s,
            messages: s.messages.map((m: PersistedMessage) =>
              m.id === loadingMsgIdRef.current
                ? { ...m, content: (m.content as string) + content, loading: false }
                : m
            ),
          }))
        },
        onDone: (serverSessId: number, msgId: number) => {
          const sid = useSessionStore.getState().activeId
          if (sid !== null) {
            updateSession(sid, (s) => ({
              ...s,
              serverSessionId: serverSessId,
              messages: s.messages.map((m: PersistedMessage) =>
                m.id === loadingMsgIdRef.current ? { ...m, id: msgId, loading: false } : m
              ),
            }))
          }
          abortControllerRef.current = null
          setSending(false)
        },
        onError: (detail: string) => {
          const isConfigError =
            (detail && /api.?key|api.?key未配置|API.?key|未设置|not configured/i.test(detail)) ||
            (detail &&
              /provider|llm|模型/i.test(detail) &&
              /未配置|未设置|not.?found|empty|null|undefined/i.test(detail))

          const errMsg = isConfigError
            ? 'AI 服务配置不完整，请联系管理员配置 LLM API Key（通义千问/DeepSeek/智谱）'
            : detail
              ? `问答失败：${detail}`
              : '后端服务未响应，请检查后端服务是否正常运行'

          const sid = useSessionStore.getState().activeId
          if (sid !== null) {
            updateSession(sid, (s) => ({
              ...s,
              messages: s.messages.map((m: PersistedMessage) =>
                m.id === loadingMsgIdRef.current ? { ...m, content: errMsg, loading: false } : m
              ),
            }))
          }
          message.error(errMsg, 8)
          abortControllerRef.current = null
          setSending(false)
        },
        onAbort: () => {
          const sid = useSessionStore.getState().activeId
          if (sid !== null) {
            updateSession(sid, (s) => ({
              ...s,
              messages: s.messages.map((m: PersistedMessage) =>
                m.id === loadingMsgIdRef.current ? { ...m, content: '已取消本次回答。', loading: false } : m
              ),
            }))
          }
          abortControllerRef.current = null
          setSending(false)
        },
      },
      abortControllerRef.current.signal,
      10_000
    )
  }, [input, sending])

  // 清理
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
    }
  }, [])

  return (
    <div
      style={{
        display: 'flex',
        height: 'calc(100vh - 160px)',
        borderRadius: 12,
        overflow: 'hidden',
        border: '1px solid #f0f0f0',
      }}
    >
      {/* 左侧边栏 */}
      <div
        style={{
          width: 260,
          flexShrink: 0,
          background: '#fafafa',
          borderRight: '1px solid #f0f0f0',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ padding: '12px 12px 8px', borderBottom: '1px solid #f0f0f0' }}>
          <Select
            value={selectedCourse}
            onChange={(val) => {
              setSelectedCourse(val)
              setActiveId(null)
            }}
            options={courses.map((c) => ({ value: c.id, label: `${c.name} (${c.code})` }))}
            style={{ width: '100%', marginBottom: 8 }}
            size="small"
            loading={loadingCourses}
            placeholder="选择课程"
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            size="small"
            onClick={createSession}
            disabled={!selectedCourseItem}
            style={{ borderRadius: 6 }}
          >
            新建对话
          </Button>
        </div>

        <div style={{ padding: 12, borderBottom: '1px solid #f0f0f0' }}>
          {loadingAgents ? (
            <Tag color="processing">正在加载答疑 Agent...</Tag>
          ) : selectedAgent ? (
            <Tag color="green">当前 Agent：{selectedAgent.name}</Tag>
          ) : (
            <Alert
              type="warning"
              showIcon
              message="当前课程还没有可用答疑 Agent"
              description="请老师在Agent构建中创建并发布 Agent，再回到此页面使用。"
            />
          )}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
          {sessions.length === 0 && (
            <div style={{ padding: 16, color: '#bbb', fontSize: 12, textAlign: 'center' }}>暂无对话</div>
          )}
          {sessions.map((session) => (
            <div
              key={session.localId}
              onClick={() => setActiveId(session.localId)}
              style={{
                padding: '10px 12px',
                cursor: 'pointer',
                background: activeId === session.localId ? '#e6f4ff' : 'transparent',
                borderLeft: `3px solid ${activeId === session.localId ? '#00a8ff' : 'transparent'}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: 4,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontWeight: activeId === session.localId ? 600 : 400,
                    fontSize: 13,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {session.title}
                </div>
                <Tag color="blue" style={{ fontSize: 10, marginTop: 4, padding: '0 4px' }}>
                  {session.courseName}
                </Tag>
              </div>
              <Tooltip title="删除">
                <DeleteOutlined
                  style={{ color: '#ccc', fontSize: 12, flexShrink: 0, marginTop: 2 }}
                  onClick={(e) => { void removeSession(session.localId, e) }}
                />
              </Tooltip>
            </div>
          ))}
        </div>
      </div>

      {/* 右侧聊天区 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#fff', minWidth: 0 }}>
        <div
          style={{
            padding: '12px 20px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <RobotOutlined style={{ color: '#00a8ff', fontSize: 18 }} />
          <span style={{ fontWeight: 600, fontSize: 15 }}>
            {activeSession?.courseName ?? '智能答疑'}
          </span>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {!activeSession ? (
            <Empty description="请选择或创建一个对话" style={{ marginTop: 60 }} />
          ) : (
            activeSession.messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  gap: 12,
                  marginBottom: 20,
                  alignItems: 'flex-start',
                }}
              >
                <Avatar
                  size={36}
                  style={{ background: msg.role === 'assistant' ? '#00a8ff' : '#6366f1', flexShrink: 0 }}
                  icon={msg.role === 'assistant' ? <RobotOutlined /> : <UserOutlined />}
                />
                <div style={{ maxWidth: '75%' }}>
                  <div
                    style={{
                      background: msg.role === 'user' ? '#6366f1' : '#f8f9fa',
                      color: msg.role === 'user' ? '#fff' : '#1a1a1a',
                      padding: '10px 16px',
                      borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                      fontSize: 14,
                      lineHeight: 1.7,
                      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                    }}
                  >
                    {'loading' in msg && msg.loading ? (
                      <span style={{ color: '#888' }}>正在生成回答...</span>
                    ) : msg.role === 'user' ? (
                      <span>{msg.content}</span>
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
                                customStyle={{ borderRadius: 8, margin: '8px 0', fontSize: 13 }}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code
                                style={{
                                  background: '#e8e8e8',
                                  padding: '1px 6px',
                                  borderRadius: 4,
                                  fontSize: '0.9em',
                                }}
                                {...props}
                              >
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
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        <div style={{ padding: '12px 20px 16px', borderTop: '1px solid #f0f0f0' }}>
          {!selectedAgent && (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 10 }}
              message="当前课程没有可用答疑 Agent，请课程老师先在 Agent Builder 中创建并发布"
              description="创建后回到此页面，选择对应课程即可使用 AI 问答功能。"
            />
          )}
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <Input.TextArea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  send()
                }
              }}
              placeholder="输入问题… (Enter 发送，Shift+Enter 换行)"
              autoSize={{ minRows: 1, maxRows: 5 }}
              style={{ borderRadius: 10, fontSize: 14, flex: 1 }}
              disabled={sending || !selectedAgent}
            />
            {sending ? (
              <Button
                danger
                icon={<CloseOutlined />}
                onClick={() => abortControllerRef.current?.abort()}
                style={{ height: 40, width: 60, borderRadius: 10 }}
              />
            ) : (
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={send}
                disabled={!input.trim() || !selectedAgent}
                style={{
                  height: 40,
                  width: 60,
                  borderRadius: 10,
                  background: 'linear-gradient(90deg,#00a8ff,#0078d7)',
                  border: 'none',
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

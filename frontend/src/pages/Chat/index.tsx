import { useEffect, useMemo, useRef, useState } from 'react'
import { Input, Button, Select, Avatar, Tag, Tooltip, Empty, Alert, message } from 'antd'
import {
  SendOutlined, RobotOutlined, UserOutlined,
  PlusOutlined, DeleteOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { agentAPI, chatAPI, courseAPI } from '../../services/api'

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

interface MessageItem {
  id: number
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
}

interface SessionItem {
  localId: number
  serverSessionId?: number
  title: string
  courseId: number
  courseName: string
  agentId?: number
  messages: MessageItem[]
}

export default function Chat() {
  const [courses, setCourses] = useState<CourseItem[]>([])
  const [agents, setAgents] = useState<AgentItem[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>()
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [loadingAgents, setLoadingAgents] = useState(false)
  const [sessions, setSessions] = useState<SessionItem[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const activeSession = useMemo(
    () => sessions.find((session) => session.localId === activeId) ?? null,
    [sessions, activeId]
  )

  const selectedCourseItem = useMemo(
    () => courses.find((course) => course.id === selectedCourse) ?? null,
    [courses, selectedCourse]
  )

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.is_active) ?? agents[0] ?? null,
    [agents]
  )

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeSession?.messages.length])

  useEffect(() => {
    const loadCourses = async () => {
      setLoadingCourses(true)
      try {
        const { data } = await courseAPI.list()
        setCourses(data)
        if (data.length > 0) {
          setSelectedCourse((prev) => prev ?? data[0].id)
        }
      } catch (error: any) {
        message.error(error?.response?.data?.detail || '加载课程失败')
      } finally {
        setLoadingCourses(false)
      }
    }
    void loadCourses()
  }, [])

  useEffect(() => {
    if (!selectedCourse) {
      setAgents([])
      return
    }

    const loadAgents = async () => {
      setLoadingAgents(true)
      try {
        const { data } = await agentAPI.listInstances(selectedCourse)
        setAgents(data)
      } catch (error: any) {
        setAgents([])
        message.error(error?.response?.data?.detail || '加载 Agent 失败')
      } finally {
        setLoadingAgents(false)
      }
    }

    void loadAgents()
  }, [selectedCourse])

  useEffect(() => {
    if (!selectedCourseItem) return
    const existing = sessions.find((session) => session.courseId === selectedCourseItem.id)
    if (existing) {
      setActiveId(existing.localId)
      return
    }

    const newSession: SessionItem = {
      localId: Date.now(),
      title: `新对话 · ${selectedCourseItem.name}`,
      courseId: selectedCourseItem.id,
      courseName: selectedCourseItem.name,
      agentId: selectedAgent?.id,
      messages: [
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: `你好！我是 **${selectedCourseItem.name}** 课程助手，请上传资料后开始提问。`,
        },
      ],
    }
    setSessions((prev) => [...prev, newSession])
    setActiveId(newSession.localId)
  }, [selectedCourseItem, selectedAgent?.id])

  const createSession = () => {
    if (!selectedCourseItem) return
    const newSession: SessionItem = {
      localId: Date.now(),
      title: `新对话 · ${selectedCourseItem.name}`,
      courseId: selectedCourseItem.id,
      courseName: selectedCourseItem.name,
      agentId: selectedAgent?.id,
      messages: [
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: `你好！我是 **${selectedCourseItem.name}** 课程助手，请开始提问。`,
        },
      ],
    }
    setSessions((prev) => [...prev, newSession])
    setActiveId(newSession.localId)
  }

  const removeSession = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const next = sessions.filter((session) => session.localId !== id)
    setSessions(next)
    if (activeId === id) {
      setActiveId(next[0]?.localId ?? null)
    }
  }

  const send = async () => {
    const text = input.trim()
    if (!text || sending || !activeSession || !selectedCourseItem) return
    if (!selectedAgent) {
      message.warning('当前课程还没有可用答疑 Agent')
      return
    }

    setInput('')
    setSending(true)

    const userMsg: MessageItem = { id: Date.now(), role: 'user', content: text }
    const loadingMsg: MessageItem = { id: Date.now() + 1, role: 'assistant', content: '', loading: true }

    setSessions((prev) => prev.map((session) =>
      session.localId === activeSession.localId
        ? {
            ...session,
            agentId: selectedAgent.id,
            messages: [...session.messages, userMsg, loadingMsg],
          }
        : session
    ))

    try {
      const { data } = await chatAPI.send({
        agent_id: selectedAgent.id,
        course_id: selectedCourseItem.id,
        session_id: activeSession.serverSessionId,
        message: text,
      })

      setSessions((prev) => prev.map((session) => {
        if (session.localId !== activeSession.localId) return session
        return {
          ...session,
          serverSessionId: data.session_id,
          title: session.serverSessionId ? session.title : text.slice(0, 18),
          messages: session.messages.map((msg) =>
            msg.id === loadingMsg.id
              ? {
                  id: data.message.id,
                  role: 'assistant',
                  content: data.message.content,
                  loading: false,
                }
              : msg
          ),
        }
      }))
    } catch (error: any) {
      const errorText = error?.response?.data?.detail || '问答失败，请稍后重试'
      setSessions((prev) => prev.map((session) => {
        if (session.localId !== activeSession.localId) return session
        return {
          ...session,
          messages: session.messages.map((msg) =>
            msg.id === loadingMsg.id
              ? { ...msg, content: `请求失败：${errorText}`, loading: false }
              : msg
          ),
        }
      }))
      message.error(errorText)
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 160px)', borderRadius: 12, overflow: 'hidden', border: '1px solid #f0f0f0' }}>
      <div style={{ width: 260, flexShrink: 0, background: '#fafafa', borderRight: '1px solid #f0f0f0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 12px 8px', borderBottom: '1px solid #f0f0f0' }}>
          <Select
            value={selectedCourse}
            onChange={setSelectedCourse}
            options={courses.map((course) => ({ value: course.id, label: `${course.name} (${course.code})` }))}
            style={{ width: '100%', marginBottom: 8 }}
            size="small"
            loading={loadingCourses}
            placeholder="选择课程"
          />
          <Button type="primary" icon={<PlusOutlined />} block size="small" onClick={createSession} disabled={!selectedCourseItem} style={{ borderRadius: 6 }}>
            新建对话
          </Button>
        </div>

        <div style={{ padding: 12, borderBottom: '1px solid #f0f0f0' }}>
          {loadingAgents ? (
            <Tag color="processing">正在加载答疑 Agent...</Tag>
          ) : selectedAgent ? (
            <Tag color="green">当前 Agent：{selectedAgent.name}</Tag>
          ) : (
            <Alert type="warning" showIcon message="当前课程还没有可用答疑 Agent" description="这是后端数据问题，不是前端故障。需要先在数据库或后端接口中为该课程创建 Agent 实例。" />
          )}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
          {sessions.length === 0 && <div style={{ padding: 16, color: '#bbb', fontSize: 12, textAlign: 'center' }}>暂无对话</div>}
          {sessions.map((session) => (
            <div
              key={session.localId}
              onClick={() => setActiveId(session.localId)}
              style={{
                padding: '10px 12px', cursor: 'pointer',
                background: activeId === session.localId ? '#e6f4ff' : 'transparent',
                borderLeft: `3px solid ${activeId === session.localId ? '#00a8ff' : 'transparent'}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 4,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: activeId === session.localId ? 600 : 400, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {session.title}
                </div>
                <Tag color="blue" style={{ fontSize: 10, marginTop: 4, padding: '0 4px' }}>{session.courseName}</Tag>
              </div>
              <Tooltip title="删除">
                <DeleteOutlined style={{ color: '#ccc', fontSize: 12, flexShrink: 0, marginTop: 2 }} onClick={(e) => removeSession(session.localId, e)} />
              </Tooltip>
            </div>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#fff', minWidth: 0 }}>
        <div style={{ padding: '12px 20px', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ color: '#00a8ff', fontSize: 18 }} />
          <span style={{ fontWeight: 600, fontSize: 15 }}>{activeSession?.courseName ?? '智能答疑'}</span>
          {selectedAgent && <Tag color="green" style={{ marginLeft: 4, fontSize: 11 }}>真实后端问答</Tag>}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {!activeSession ? (
            <Empty description="请选择或创建一个对话" style={{ marginTop: 60 }} />
          ) : (
            activeSession.messages.map((msg) => (
              <div key={msg.id} style={{ display: 'flex', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', gap: 12, marginBottom: 20, alignItems: 'flex-start' }}>
                <Avatar size={36} style={{ background: msg.role === 'assistant' ? '#00a8ff' : '#6366f1', flexShrink: 0 }} icon={msg.role === 'assistant' ? <RobotOutlined /> : <UserOutlined />} />
                <div style={{ maxWidth: '75%' }}>
                  <div style={{
                    background: msg.role === 'user' ? '#6366f1' : '#f8f9fa',
                    color: msg.role === 'user' ? '#fff' : '#1a1a1a',
                    padding: '10px 16px',
                    borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                    fontSize: 14, lineHeight: 1.7,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                  }}>
                    {msg.loading ? (
                      <span style={{ color: '#888' }}>正在生成回答...</span>
                    ) : msg.role === 'user' ? (
                      <span>{msg.content}</span>
                    ) : (
                      <ReactMarkdown
                        components={{
                          code({ className, children, ...props }: any) {
                            const match = /language-(\w+)/.exec(className || '')
                            return match ? (
                              <SyntaxHighlighter style={vscDarkPlus as any} language={match[1]} PreTag="div" customStyle={{ borderRadius: 8, margin: '8px 0', fontSize: 13 }}>
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code style={{ background: '#e8e8e8', padding: '1px 6px', borderRadius: 4, fontSize: '0.9em' }} {...props}>{children}</code>
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
          {!selectedAgent && <Alert type="warning" showIcon style={{ marginBottom: 10 }} message="当前课程没有可用答疑 Agent，请先在后端为该课程创建 Agent 实例。" description="可通过后端 `/api/v1/agents/instances` 创建，或补充种子数据后再测试问答。" />}
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <Input.TextArea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send() } }}
              placeholder="输入问题… (Enter 发送，Shift+Enter 换行)"
              autoSize={{ minRows: 1, maxRows: 5 }}
              style={{ borderRadius: 10, fontSize: 14, flex: 1 }}
              disabled={sending || !selectedAgent}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={() => void send()}
              loading={sending}
              disabled={!input.trim() || !selectedAgent}
              style={{ height: 40, width: 60, borderRadius: 10, background: 'linear-gradient(90deg,#00a8ff,#0078d7)', border: 'none' }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

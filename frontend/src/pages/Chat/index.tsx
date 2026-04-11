import { useState, useRef, useEffect } from 'react'
import { Input, Button, Select, Avatar, Tag, Tooltip, Empty } from 'antd'
import {
  SendOutlined, RobotOutlined, UserOutlined,
  PlusOutlined, DeleteOutlined, LinkOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources?: { title: string; page: number }[]
  loading?: boolean
}

interface Session {
  id: number
  title: string
  courseId: number
  courseName: string
  messages: Message[]
}

const COURSES = [
  { value: 1, label: 'Python程序设计' },
  { value: 2, label: '数据结构' },
  { value: 3, label: '高等数学' },
]

const INIT_SESSIONS: Session[] = [
  {
    id: 1, title: 'Python基础问答', courseId: 1, courseName: 'Python程序设计',
    messages: [
      { id: 1, role: 'assistant', content: '你好！我是 **Python程序设计** 课程的 AI 助手，有什么问题我可以帮你解答？' },
      { id: 2, role: 'user', content: '什么是列表推导式？' },
      {
        id: 3, role: 'assistant',
        content: `列表推导式（List Comprehension）是 Python 中一种简洁的创建列表的方式。

**基本语法：**
\`\`\`python
[表达式 for 变量 in 可迭代对象 if 条件]
\`\`\`

**示例：**
\`\`\`python
# 生成平方数列表
squares = [x**2 for x in range(5)]
print(squares)  # [0, 1, 4, 9, 16]

# 只保留偶数
evens = [x for x in range(10) if x % 2 == 0]
print(evens)  # [0, 2, 4, 6, 8]
\`\`\`

列表推导式比等价的 for 循环更简洁，执行速度也更快。`,
        sources: [
          { title: '第3章-循环结构.pdf', page: 12 },
          { title: '第1章-基础语法.pdf', page: 28 },
        ],
      },
    ],
  },
]

const MOCK_REPLY = `这是一个很好的问题！根据课程知识库的内容，我来为你详细解答。

在 Python 中，相关概念涉及多个核心知识点：

\`\`\`python
# 示例代码
def example(items):
    """使用列表推导式过滤并转换数据"""
    return [item.upper() for item in items if len(item) > 3]

result = example(['hello', 'hi', 'world', 'ok'])
print(result)  # ['HELLO', 'WORLD']
\`\`\`

如果你还有疑问，欢迎继续追问！`

export default function Chat() {
  const [sessions, setSessions] = useState<Session[]>(INIT_SESSIONS)
  const [activeId, setActiveId] = useState<number>(1)
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<number>(1)
  const bottomRef = useRef<HTMLDivElement>(null)

  const active = sessions.find(s => s.id === activeId)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [active?.messages.length])

  const newSession = () => {
    const course = COURSES.find(c => c.value === selectedCourse)
    const s: Session = {
      id: Date.now(),
      title: `新对话 · ${course?.label}`,
      courseId: selectedCourse,
      courseName: course?.label ?? '',
      messages: [{ id: 1, role: 'assistant', content: `你好！我是 **${course?.label}** 课程的 AI 助手，有什么问题？` }],
    }
    setSessions(p => [...p, s])
    setActiveId(s.id)
  }

  const removeSession = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const next = sessions.filter(s => s.id !== id)
    setSessions(next)
    if (activeId === id) setActiveId(next[0]?.id ?? -1)
  }

  const send = async () => {
    const text = input.trim()
    if (!text || streaming || !active) return
    setInput('')
    setStreaming(true)

    const uid = Date.now()
    const aid = uid + 1
    const userMsg: Message = { id: uid, role: 'user', content: text }
    const asstMsg: Message = { id: aid, role: 'assistant', content: '', loading: true }

    setSessions(p => p.map(s => s.id === activeId ? { ...s, messages: [...s.messages, userMsg, asstMsg] } : s))

    // 模拟流式输出（后端就绪后替换为 SSE: /api/v1/chat/stream）
    let cur = ''
    for (const ch of MOCK_REPLY) {
      await new Promise(r => setTimeout(r, 16))
      cur += ch
      const snap = cur
      setSessions(p => p.map(s => s.id === activeId
        ? { ...s, messages: s.messages.map(m => m.id === aid ? { ...m, content: snap, loading: false } : m) }
        : s
      ))
    }
    setSessions(p => p.map(s => s.id === activeId
      ? { ...s, messages: s.messages.map(m => m.id === aid ? { ...m, sources: [{ title: '第3章-循环结构.pdf', page: 8 }] } : m) }
      : s
    ))
    setStreaming(false)
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 160px)', borderRadius: 12, overflow: 'hidden', border: '1px solid #f0f0f0' }}>

      {/* 左侧会话列表 */}
      <div style={{ width: 240, flexShrink: 0, background: '#fafafa', borderRight: '1px solid #f0f0f0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 12px 8px', borderBottom: '1px solid #f0f0f0' }}>
          <Select value={selectedCourse} onChange={setSelectedCourse} options={COURSES} style={{ width: '100%', marginBottom: 8 }} size="small" />
          <Button type="primary" icon={<PlusOutlined />} block size="small" onClick={newSession} style={{ borderRadius: 6 }}>新建对话</Button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
          {sessions.length === 0 && <div style={{ padding: 16, color: '#bbb', fontSize: 12, textAlign: 'center' }}>暂无对话</div>}
          {sessions.map(s => (
            <div
              key={s.id}
              onClick={() => setActiveId(s.id)}
              style={{
                padding: '10px 12px', cursor: 'pointer',
                background: activeId === s.id ? '#e6f4ff' : 'transparent',
                borderLeft: `3px solid ${activeId === s.id ? '#00a8ff' : 'transparent'}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 4,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: activeId === s.id ? 600 : 400, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  <MessageOutlined style={{ marginRight: 6, color: '#00a8ff' }} />{s.title}
                </div>
                <Tag color="blue" style={{ fontSize: 10, marginTop: 4, padding: '0 4px' }}>{s.courseName}</Tag>
              </div>
              <Tooltip title="删除">
                <DeleteOutlined style={{ color: '#ccc', fontSize: 12, flexShrink: 0, marginTop: 2 }} onClick={e => removeSession(s.id, e)} />
              </Tooltip>
            </div>
          ))}
        </div>
      </div>

      {/* 右侧消息区 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#fff', minWidth: 0 }}>
        <div style={{ padding: '12px 20px', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ color: '#00a8ff', fontSize: 18 }} />
          <span style={{ fontWeight: 600, fontSize: 15 }}>{active?.courseName ?? '智能答疑'}</span>
          {active && <Tag color="green" style={{ marginLeft: 4, fontSize: 11 }}>RAG 增强</Tag>}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {!active
            ? <Empty description="请选择或创建一个对话" style={{ marginTop: 60 }} />
            : active.messages.map(msg => (
              <div
                key={msg.id}
                style={{ display: 'flex', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', gap: 12, marginBottom: 20, alignItems: 'flex-start' }}
              >
                <Avatar
                  size={36}
                  style={{ background: msg.role === 'assistant' ? '#00a8ff' : '#6366f1', flexShrink: 0 }}
                  icon={msg.role === 'assistant' ? <RobotOutlined /> : <UserOutlined />}
                />
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
                      <span style={{ display: 'inline-flex', gap: 4 }}>
                        {[0, 200, 400].map(d => (
                          <span key={d} style={{
                            width: 7, height: 7, borderRadius: '50%', background: '#00a8ff', display: 'inline-block',
                            animation: `bounce 1s ${d}ms infinite`,
                          }} />
                        ))}
                      </span>
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
                              <code style={{ background: '#e8e8e8', padding: '1px 6px', borderRadius: 4, fontSize: '0.9em' }} {...props}>
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
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {msg.sources.map((src, i) => (
                        <Tooltip key={i} title={`${src.title} 第${src.page}页`}>
                          <Tag
                            icon={<LinkOutlined />}
                            style={{ cursor: 'pointer', fontSize: 11, background: '#f0f9ff', border: '1px solid #bae0ff', color: '#0078d7', borderRadius: 6 }}
                          >
                            {src.title} P{src.page}
                          </Tag>
                        </Tooltip>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          }
          <div ref={bottomRef} />
        </div>

        <div style={{ padding: '12px 20px 16px', borderTop: '1px solid #f0f0f0' }}>
          <style>{`
            @keyframes bounce {
              0%,80%,100% { transform: translateY(0); }
              40% { transform: translateY(-6px); }
            }
          `}</style>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <Input.TextArea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder="输入问题… (Enter 发送，Shift+Enter 换行)"
              autoSize={{ minRows: 1, maxRows: 5 }}
              style={{ borderRadius: 10, fontSize: 14, flex: 1 }}
              disabled={streaming}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={send}
              loading={streaming}
              disabled={!input.trim()}
              style={{ height: 40, width: 60, borderRadius: 10, background: 'linear-gradient(90deg,#00a8ff,#0078d7)', border: 'none' }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function MessageOutlined({ style }: { style?: React.CSSProperties }) {
  return <span style={style}>💬</span>
}

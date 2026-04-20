import { useState, useRef, useEffect } from 'react'
import { Input, Button, Avatar, Tag } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useSearchParams } from 'react-router-dom'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
}

const COURSE_NAMES: Record<string, string> = {
  '1': 'Python程序设计',
  '2': '数据结构',
  '3': '高等数学',
}

const MOCK_REPLY = `好的！我来为你解答这个问题。

根据课程知识库的内容：

\`\`\`python
# 示例代码
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("EduAI"))  # Hello, EduAI!
\`\`\`

如还有疑问，随时提问！`

export default function Widget() {
  const [searchParams] = useSearchParams()
  const courseId = searchParams.get('course') ?? '1'
  const courseName = COURSE_NAMES[courseId] ?? '课程助手'

  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: 'assistant', content: `你好！我是 **${courseName}** 的 AI 助手，有什么可以帮你？` },
  ])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const send = async () => {
    const text = input.trim()
    if (!text || streaming) return
    setInput('')
    setStreaming(true)

    const uid = Date.now()
    const aid = uid + 1
    setMessages(p => [
      ...p,
      { id: uid, role: 'user', content: text },
      { id: aid, role: 'assistant', content: '', loading: true },
    ])

    let cur = ''
    for (const ch of MOCK_REPLY) {
      await new Promise(r => setTimeout(r, 18))
      cur += ch
      const snap = cur
      setMessages(p => p.map(m => m.id === aid ? { ...m, content: snap, loading: false } : m))
    }
    setStreaming(false)
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
        <Tag color="green" style={{ fontSize: 10 }}>RAG</Tag>
      </div>

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
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={send}
            loading={streaming}
            disabled={!input.trim()}
            style={{ height: 36, width: 44, borderRadius: 8, background: 'linear-gradient(90deg,#00a8ff,#0078d7)', border: 'none' }}
          />
        </div>
      </div>
    </div>
  )
}


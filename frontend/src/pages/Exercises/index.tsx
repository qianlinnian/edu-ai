import { useState } from 'react'
import { Card, Button, Radio, Space, Tag, Progress, Alert, Divider } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, TrophyOutlined, ReloadOutlined, FireOutlined } from '@ant-design/icons'

interface Question {
  id: number
  text: string
  code?: string
  options: { key: string; label: string }[]
  answer: string
  explanation: string
  knowledge: string
  difficulty: 1 | 2 | 3
}

const QUESTIONS: Question[] = [
  {
    id: 1, text: '以下代码的输出结果是什么？',
    code: 'for i in range(3):\n    print(i, end=" ")',
    options: [{ key: 'A', label: '1 2 3' }, { key: 'B', label: '0 1 2' }, { key: 'C', label: '0 1 2 3' }, { key: 'D', label: '1 2' }],
    answer: 'B',
    explanation: 'range(3) 生成序列 0, 1, 2（不包含3），end=" " 使输出用空格分隔而不是换行。',
    knowledge: '循环结构', difficulty: 1,
  },
  {
    id: 2, text: '下列哪个选项正确定义了递归函数计算阶乘？',
    options: [
      { key: 'A', label: 'def fact(n): return n * fact(n)' },
      { key: 'B', label: 'def fact(n): return n * fact(n-1) if n > 0 else 1' },
      { key: 'C', label: 'def fact(n): return n * fact(n+1)' },
      { key: 'D', label: 'def fact(n): return fact(n) * n' },
    ],
    answer: 'B',
    explanation: '递归函数必须有终止条件（n==0 返回1），选项B正确设置了终止条件并递减n。',
    knowledge: '递归算法', difficulty: 2,
  },
  {
    id: 3, text: 'x = [1,2,3,4,5]，执行 x[1:3] 的结果是？',
    options: [{ key: 'A', label: '[1,2,3]' }, { key: 'B', label: '[2,3,4]' }, { key: 'C', label: '[2,3]' }, { key: 'D', label: '[1,2]' }],
    answer: 'C',
    explanation: '切片 x[1:3] 取索引1到2（不含3）的元素，即 x[1]=2 和 x[2]=3。',
    knowledge: '列表操作', difficulty: 1,
  },
  {
    id: 4, text: '以下关于 Python 函数参数的说法，正确的是？',
    options: [
      { key: 'A', label: '形参是调用函数时传入的值' },
      { key: 'B', label: '实参是函数定义中的参数名' },
      { key: 'C', label: '形参是函数定义中的参数名，实参是调用时传入的值' },
      { key: 'D', label: '形参和实参是同一个概念' },
    ],
    answer: 'C',
    explanation: '形参（parameter）是函数定义中的参数占位符，实参（argument）是调用函数时实际传入的值。',
    knowledge: '函数', difficulty: 1,
  },
  {
    id: 5, text: '下列代码执行后 result 的值是？\n\nresult = [x**2 for x in range(4) if x % 2 == 0]',
    options: [{ key: 'A', label: '[0, 4]' }, { key: 'B', label: '[0, 1, 4, 9]' }, { key: 'C', label: '[4, 16]' }, { key: 'D', label: '[1, 9]' }],
    answer: 'A',
    explanation: 'range(4) 产生 0,1,2,3；过滤偶数得 0,2；平方得 [0, 4]。',
    knowledge: '列表推导式', difficulty: 2,
  },
]

const DIFFICULTY_LABEL: Record<number, string> = { 1: '⭐', 2: '⭐⭐', 3: '⭐⭐⭐' }

export default function Exercises() {
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [answers, setAnswers] = useState<Record<number, { selected: string; correct: boolean }>>({})
  const [finished, setFinished] = useState(false)

  const q = QUESTIONS[current]
  const total = QUESTIONS.length
  const isLast = current === total - 1
  const isCorrect = selected === q.answer

  const handleSubmit = () => {
    if (!selected) return
    setSubmitted(true)
    setAnswers(prev => ({ ...prev, [q.id]: { selected, correct: selected === q.answer } }))
  }

  const handleNext = () => {
    if (isLast) { setFinished(true); return }
    setCurrent(c => c + 1)
    setSelected(null)
    setSubmitted(false)
  }

  const handleRestart = () => {
    setCurrent(0); setSelected(null); setSubmitted(false); setAnswers({}); setFinished(false)
  }

  const correctCount = Object.values(answers).filter(a => a.correct).length

  if (finished) {
    const score = Math.round(correctCount / total * 100)
    return (
      <div>
        <div style={{ marginBottom: 24, fontSize: 20, fontWeight: 700 }}>练习中心</div>
        <Card style={{ borderRadius: 12, textAlign: 'center', padding: '32px 0' }} bordered={false}>
          <TrophyOutlined style={{ fontSize: 64, color: score >= 80 ? '#faad14' : score >= 60 ? '#00a8ff' : '#ff4d4f' }} />
          <div style={{ fontSize: 28, fontWeight: 800, marginTop: 16, color: score >= 80 ? '#52c41a' : score >= 60 ? '#00a8ff' : '#ff4d4f' }}>
            {correctCount}/{total} 题正确 · {score}分
          </div>
          <div style={{ color: '#888', marginTop: 8 }}>
            {score >= 80 ? '优秀！继续保持 🎉' : score >= 60 ? '良好，还有提升空间' : '加油，多加练习！'}
          </div>
          <Divider />
          <div style={{ textAlign: 'left', maxWidth: 480, margin: '0 auto' }}>
            <div style={{ fontWeight: 600, marginBottom: 12 }}>知识点掌握变化</div>
            {[
              { label: '循环结构', before: 30, after: 50 },
              { label: '递归算法', before: 42, after: 55 },
              { label: '列表操作', before: 78, after: 85 },
            ].map(k => (
              <div key={k.label} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                  <span>{k.label}</span>
                  <span style={{ color: '#52c41a' }}>{k.before}% → {k.after}% ↑</span>
                </div>
                <Progress percent={k.after} strokeColor="#52c41a" size="small" />
              </div>
            ))}
          </div>
          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 12 }}>
            <Button icon={<ReloadOutlined />} onClick={handleRestart}>再练一次</Button>
            <Button type="primary" icon={<FireOutlined />}>继续强化练习</Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <span style={{ fontSize: 20, fontWeight: 700 }}>练习中心</span>
        <Tag color="blue" icon={<FireOutlined />}>基于薄弱点：循环结构 · 递归</Tag>
      </div>

      {/* 进度条 */}
      <Card style={{ borderRadius: 12, marginBottom: 16 }} bordered={false}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontWeight: 600 }}>Q{current + 1} / {total}</span>
          <span style={{ color: '#888', fontSize: 13 }}>{DIFFICULTY_LABEL[q.difficulty]} {q.knowledge}</span>
        </div>
        <Progress percent={Math.round(current / total * 100)} strokeColor="#00a8ff" showInfo={false} size="small" />
      </Card>

      {/* 题目 */}
      <Card style={{ borderRadius: 12, marginBottom: 16 }} bordered={false}>
        <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 16, lineHeight: 1.7 }}>{q.text}</div>
        {q.code && (
          <pre style={{
            background: '#1e1e1e', color: '#d4d4d4', padding: '14px 18px',
            borderRadius: 10, fontSize: 14, marginBottom: 16, overflowX: 'auto',
          }}>
            {q.code}
          </pre>
        )}
        <Radio.Group
          value={selected}
          onChange={e => { if (!submitted) setSelected(e.target.value) }}
          style={{ width: '100%' }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            {q.options.map(opt => {
              let bg = 'transparent'
              let border = '1px solid #e8e8e8'
              if (submitted) {
                if (opt.key === q.answer) { bg = '#f6ffed'; border = '1px solid #b7eb8f' }
                else if (opt.key === selected) { bg = '#fff1f0'; border = '1px solid #ffa39e' }
              } else if (opt.key === selected) { bg = '#e6f4ff'; border = '1px solid #91caff' }
              return (
                <div
                  key={opt.key}
                  onClick={() => { if (!submitted) setSelected(opt.key) }}
                  style={{
                    padding: '12px 16px', borderRadius: 10, cursor: submitted ? 'default' : 'pointer',
                    background: bg, border, display: 'flex', alignItems: 'center', gap: 10,
                    transition: 'all 0.15s',
                  }}
                >
                  <Radio value={opt.key} />
                  <span style={{ flex: 1, color: '#1f1f1f' }}><strong>{opt.key}.</strong> {opt.label}</span>
                  {submitted && opt.key === q.answer && <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />}
                  {submitted && opt.key === selected && opt.key !== q.answer && <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />}
                </div>
              )
            })}
          </Space>
        </Radio.Group>

        {submitted && (
          <Alert
            type={isCorrect ? 'success' : 'error'}
            showIcon
            message={isCorrect ? '✅ 回答正确！' : `❌ 正确答案是 ${q.answer}`}
            description={q.explanation}
            style={{ marginTop: 16, borderRadius: 10 }}
          />
        )}
      </Card>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
        {!submitted ? (
          <Button type="primary" disabled={!selected} onClick={handleSubmit}
            style={{ borderRadius: 8, minWidth: 100 }}>提交答案</Button>
        ) : (
          <Button type="primary" onClick={handleNext}
            style={{ borderRadius: 8, minWidth: 100, background: isLast ? '#52c41a' : undefined }}>
            {isLast ? '查看报告 🎯' : '下一题 →'}
          </Button>
        )}
      </div>
    </div>
  )
}

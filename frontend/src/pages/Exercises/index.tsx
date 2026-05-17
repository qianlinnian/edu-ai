import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Empty, Progress, Select, Space, Typography } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined, TrophyOutlined } from '@ant-design/icons'
import { courseAPI, exerciseAPI } from '../../services/api'

type Course = { id: number; name: string; code: string }
type KnowledgeUnit = { id: number; name: string }
type Question = {
  id?: number
  source?: 'pool' | 'generated' | 'mock'
  exercise_id?: number
  generated_exercise_id?: number
  question?: string
  text?: string
  stem?: string
  options?: { key?: string; label?: string; value?: string; text?: string }[] | string[]
  answer?: string
  explanation?: string
  knowledge?: string
  difficulty?: 1 | 2 | 3
}

type AttemptResult = {
  correct?: boolean
  is_correct?: boolean
  score?: number
  feedback?: string
  explanation?: string
  answer?: string
}

const mockQuestions: Question[] = [
  {
    id: 1,
    source: 'mock',
    question: '以下代码的输出结果是什么？',
    options: ['1 2 3', '0 1 2', '0 1 2 3', '1 2'],
    answer: 'B',
    explanation: 'range(3) 生成 0,1,2。',
    knowledge: '循环结构',
    difficulty: 1,
  },
]

const difficultyLabel: Record<number, string> = { 1: '⭐', 2: '⭐⭐', 3: '⭐⭐⭐' }

const normalizeQuestion = (item: any, index: number): Question => {
  const source = item.source === 'generated' ? 'generated' : item.source === 'pool' ? 'pool' : 'pool'
  return {
    id: item.id,
    source,
    exercise_id: source === 'pool' ? item.id : undefined,
    generated_exercise_id: source === 'generated' ? item.id : undefined,
    question: item.question || item.prompt || item.title || item.text || item.stem || `练习题 ${index + 1}`,
    text: item.text,
    stem: item.stem,
    options: Array.isArray(item.options)
      ? item.options
      : Array.isArray(item.choices)
        ? item.choices
        : Array.isArray(item.choice_options)
          ? item.choice_options
          : [],
    answer: item.answer || item.correct_answer,
    explanation: item.explanation || item.analysis || item.feedback,
    knowledge: item.knowledge || item.knowledge_point || item.knowledge_name || (Array.isArray(item.knowledge_point_ids) ? `知识点 ${item.knowledge_point_ids.join(', ')}` : '练习题'),
    difficulty: Number(item.difficulty || 1) as 1 | 2 | 3,
  }
}

const isDisplayableChoiceQuestion = (item: Question) => {
  const text = item.question || item.text || item.stem || ''
  const hasOptions = Array.isArray(item.options) && item.options.length > 0
  const isGeneratedPlaceholder = text.startsWith('Explain the core concept of knowledge points')
  return hasOptions && !isGeneratedPlaceholder
}

export default function Exercises() {
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>()
  const [questions, setQuestions] = useState<Question[]>([])
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [finished, setFinished] = useState(false)
  const [answers, setAnswers] = useState<Record<number, { selected: string; correct: boolean; score: number }>>({})
  const [attemptResult, setAttemptResult] = useState<AttemptResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [usingMock, setUsingMock] = useState(false)

  const q = questions[current]
  const total = questions.length || 1
  const normalizedOptions = useMemo(() => {
    const raw = q?.options || []
    return raw.map((option: any, index: number) => typeof option === 'string'
      ? { key: String.fromCharCode(65 + index), label: option }
      : { key: option.key || option.value || String.fromCharCode(65 + index), label: option.label || option.text || option.value || '' })
  }, [q])

  const resetProgress = () => {
    setCurrent(0)
    setSelected(null)
    setSubmitted(false)
    setFinished(false)
    setAnswers({})
    setAttemptResult(null)
  }

  const loadRealQuestions = async (courseId: number) => {
    const poolRes = await exerciseAPI.listPool(courseId).catch(() => ({ data: [] }))
    const poolQuestions = (Array.isArray(poolRes.data) ? poolRes.data : [])
      .map(normalizeQuestion)
      .filter((item: Question) => isDisplayableChoiceQuestion(item))
    if (poolQuestions.length > 0) {
      setUsingMock(false)
      return poolQuestions
    }

    const knowledgeRes = await courseAPI.listKnowledgeUnits(courseId).catch(() => ({ data: [] }))
    const kpIds = (Array.isArray(knowledgeRes.data) ? knowledgeRes.data : []).map((item: KnowledgeUnit) => item.id)
    if (kpIds.length > 0) {
      const { data } = await exerciseAPI.generate({
        course_id: courseId,
        knowledge_point_ids: kpIds,
        exercise_type: 'choice',
        difficulty: 2,
        count: 1,
      })
      const source = Array.isArray(data) ? data : Array.isArray(data?.exercises) ? data.exercises : []
      const generatedQuestions = source
        .map(normalizeQuestion)
        .filter((item: Question) => isDisplayableChoiceQuestion(item))
      if (generatedQuestions.length > 0) {
        setUsingMock(false)
        return generatedQuestions
      }
    }

    setUsingMock(true)
    return mockQuestions
  }

  const loadCoursesAndQuestions = async (courseIdArg?: number) => {
    setLoading(true)
    try {
      const { data: courseData } = await courseAPI.list().catch(() => ({ data: [] }))
      setCourses(courseData)
      const activeCourseId = courseIdArg || selectedCourseId || courseData?.[0]?.id
      if (!activeCourseId) {
        setQuestions(mockQuestions)
        setUsingMock(true)
        resetProgress()
        return
      }

      setSelectedCourseId(activeCourseId)
      const nextQuestions = await loadRealQuestions(activeCourseId)
      setQuestions(nextQuestions)
      resetProgress()
    } catch {
      setQuestions(mockQuestions)
      setUsingMock(true)
      resetProgress()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void loadCoursesAndQuestions() }, [])

  const handleSubmit = async () => {
    if (!selected || !q) return
    setLoading(true)
    try {
      let result: AttemptResult
      try {
        const { data } = await exerciseAPI.attempt({
          exercise_id: q.exercise_id,
          generated_exercise_id: q.generated_exercise_id,
          student_answer: selected,
        })
        result = data
      } catch {
        const correct = selected === (q.answer || 'A')
        result = { is_correct: correct, score: correct ? 100 : 0, feedback: q.explanation || '暂无反馈', answer: q.answer }
      }
      const correct = Boolean(result.correct ?? result.is_correct)
      setAttemptResult(result)
      setSubmitted(true)
      setAnswers((prev) => ({ ...prev, [q.generated_exercise_id || q.exercise_id || q.id || current]: { selected, correct, score: Number(result.score || 0) } }))
    } finally {
      setLoading(false)
    }
  }

  const handleNext = () => {
    if (current >= total - 1) {
      setFinished(true)
      return
    }
    setCurrent((prev) => prev + 1)
    setSelected(null)
    setSubmitted(false)
    setAttemptResult(null)
  }

  const score = Object.values(answers).length ? Math.round(Object.values(answers).reduce((sum, item) => sum + item.score, 0) / Object.values(answers).length) : 0

  if (!questions.length && !loading) return <Empty description="暂无练习" />

  if (finished) {
    const correctCount = Object.values(answers).filter((item) => item.correct).length
    return (
      <div>
        <Typography.Title level={4}>练习中心</Typography.Title>
        <Card style={{ borderRadius: 12, textAlign: 'center', padding: '32px 0' }}>
          <TrophyOutlined style={{ fontSize: 64, color: score >= 80 ? '#faad14' : score >= 60 ? '#00a8ff' : '#ff4d4f' }} />
          <div style={{ fontSize: 28, fontWeight: 800, marginTop: 16 }}>{correctCount}/{Object.keys(answers).length} 题正确 · {score}分</div>
          <div style={{ color: '#888', marginTop: 8 }}>{score >= 80 ? '优秀！继续保持' : score >= 60 ? '良好，还有提升空间' : '加油，多加练习！'}</div>
          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 12 }}>
            <Button icon={<ReloadOutlined />} onClick={() => void loadCoursesAndQuestions(selectedCourseId)}>再练一次</Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 20 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>练习中心</Typography.Title>
        <Select style={{ width: 240 }} options={courses.map((course) => ({ value: course.id, label: `${course.name}（${course.code}）` }))} value={selectedCourseId} onChange={(value) => { setSelectedCourseId(value); void loadCoursesAndQuestions(value) }} />
      </Space>

      {usingMock && (
        <Alert type="warning" showIcon style={{ marginBottom: 16 }} message="当前课程暂无可用真实选择题，已展示示例题。" />
      )}

      <Card style={{ borderRadius: 12, marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ fontWeight: 600 }}>Q{current + 1} / {total}</span>
          <span style={{ color: '#888' }}>{difficultyLabel[q?.difficulty || 1]} {q?.knowledge || '练习题'}</span>
        </div>
        <Progress percent={Math.round((current / total) * 100)} showInfo={false} />
      </Card>

      <Card style={{ borderRadius: 12, marginBottom: 16 }} loading={loading && !submitted}>
        <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 16, lineHeight: 1.7 }}>{q?.question || q?.text || q?.stem || '暂无题目内容'}</div>
        {normalizedOptions.length === 0 ? (
          <Empty description="当前题目暂无可展示选项，请刷新重试" />
        ) : (
          <Space direction="vertical" style={{ width: '100%' }}>
            {normalizedOptions.map((option) => {
              const correctAnswer = attemptResult?.answer || q?.answer
              const isCorrect = option.key === correctAnswer
              const isSelected = option.key === selected
              let background = 'transparent'
              let border = '1px solid #e8e8e8'
              if (submitted) {
                if (isCorrect) { background = '#f6ffed'; border = '1px solid #b7eb8f' }
                else if (isSelected) { background = '#fff1f0'; border = '1px solid #ffa39e' }
              } else if (isSelected) { background = '#e6f4ff'; border = '1px solid #91caff' }
              return (
                <div key={option.key} onClick={() => { if (!submitted) setSelected(option.key) }} style={{ padding: '12px 16px', borderRadius: 10, cursor: submitted ? 'default' : 'pointer', background, border, display: 'flex', alignItems: 'center', gap: 10 }}>
                  <strong>{option.key}.</strong>
                  <span style={{ flex: 1 }}>{option.label}</span>
                  {submitted && isCorrect && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                  {submitted && isSelected && !isCorrect && <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                </div>
              )
            })}
          </Space>
        )}
        {submitted && (
          <Alert type={Boolean(attemptResult?.correct ?? attemptResult?.is_correct) ? 'success' : 'error'} showIcon style={{ marginTop: 16 }} message={Boolean(attemptResult?.correct ?? attemptResult?.is_correct) ? '回答正确' : `回答错误，正确答案是 ${attemptResult?.answer || q?.answer || ''}`} description={attemptResult?.feedback || attemptResult?.explanation || q?.explanation || '暂无反馈'} />
        )}
      </Card>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
        {!submitted ? <Button type="primary" disabled={!selected || normalizedOptions.length === 0} onClick={() => void handleSubmit()}>提交答案</Button> : <Button type="primary" onClick={handleNext}>{current >= total - 1 ? '查看报告' : '下一题'}</Button>}
      </div>
    </div>
  )
}

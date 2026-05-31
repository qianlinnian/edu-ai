import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Alert, Button, Card, Empty, Progress, Select, Space, Tag, Typography, message } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExperimentOutlined,
  ReloadOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { courseAPI, exerciseAPI } from '../../services/api'

type Course = { id: number; name: string; code: string }
type QuestionSource = 'pool' | 'generated' | 'mock'
type GenerationMethod = 'llm' | 'fallback' | null
type Option = { key: string; label: string }
type Question = {
  id?: number
  source: QuestionSource
  generation_method?: GenerationMethod
  exercise_id?: number
  generated_exercise_id?: number
  question: string
  options: Option[]
  answer?: string
  explanation?: string
  knowledge?: string
  difficulty: number
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
    question: '以下代码的输出结果是什么？for (int i = 0; i < 3; i++) { System.out.print(i + " "); }',
    options: [
      { key: 'A', label: '1 2 3' },
      { key: 'B', label: '0 1 2' },
      { key: 'C', label: '0 1 2 3' },
      { key: 'D', label: '1 2' },
    ],
    answer: 'B',
    explanation: '循环变量 i 从 0 开始，到 i < 3 时结束，因此输出 0、1、2。',
    knowledge: '循环结构',
    difficulty: 1,
  },
]

const difficultyLabel: Record<number, string> = {
  1: '基础',
  2: '适中',
  3: '进阶',
  4: '困难',
  5: '挑战',
}

const normalizeOptions = (raw: any): Option[] => {
  if (!Array.isArray(raw)) return []
  return raw
    .map((option: any, index: number) => {
      const fallbackKey = String.fromCharCode(65 + index)
      if (typeof option === 'string') {
        return { key: fallbackKey, label: option }
      }
      return {
        key: String(option.key || option.value || fallbackKey).toUpperCase().slice(0, 1),
        label: String(option.label || option.text || option.content || option.value || ''),
      }
    })
    .filter((option) => option.label)
}

const normalizeQuestion = (item: any, index: number): Question => {
  const source: QuestionSource = item.source === 'generated' ? 'generated' : item.source === 'mock' ? 'mock' : 'pool'
  const generatedId = item.generated_exercise_id || (source === 'generated' ? item.id : undefined)
  const exerciseId = item.exercise_id || (source === 'pool' ? item.id : undefined)
  const knowledgePointIds = Array.isArray(item.knowledge_point_ids)
    ? item.knowledge_point_ids
    : Array.isArray(item.target_knowledge_points)
      ? item.target_knowledge_points
      : []

  return {
    id: item.id,
    source,
    generation_method: item.generation_method || null,
    exercise_id: exerciseId,
    generated_exercise_id: generatedId,
    question: item.question || item.prompt || item.title || item.text || item.stem || `练习题 ${index + 1}`,
    options: normalizeOptions(item.options || item.choices || item.choice_options),
    answer: item.answer || item.correct_answer,
    explanation: item.explanation || item.analysis || item.feedback,
    knowledge: item.knowledge || item.knowledge_point || item.knowledge_name || (knowledgePointIds.length ? `知识点 ${knowledgePointIds.join(', ')}` : '综合练习'),
    difficulty: Number(item.difficulty || 1),
  }
}

const isDisplayableChoiceQuestion = (item: Question) => item.options.length > 0 && Boolean(item.question)

const getSourceTag = (question?: Question) => {
  if (!question) return null
  if (question.source === 'mock') return <Tag color="default">兜底练习</Tag>
  if (question.source === 'pool') return <Tag color="blue">题库推荐</Tag>
  if (question.generation_method === 'fallback') return <Tag color="orange">兜底练习</Tag>
  return <Tag color="green">AI 生成</Tag>
}

export default function Exercises() {
  const { courseId } = useParams()
  const routeCourseId = courseId ? Number(courseId) : undefined
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>(routeCourseId)
  const [questions, setQuestions] = useState<Question[]>([])
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [finished, setFinished] = useState(false)
  const [answers, setAnswers] = useState<Record<number, { selected: string; correct: boolean; score: number }>>({})
  const [attemptResult, setAttemptResult] = useState<AttemptResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)

  const q = questions[current]
  const total = questions.length || 1
  const normalizedOptions = useMemo(() => q?.options || [], [q])

  const resetProgress = () => {
    setCurrent(0)
    setSelected(null)
    setSubmitted(false)
    setFinished(false)
    setAnswers({})
    setAttemptResult(null)
  }

  const setQuestionSet = (nextQuestions: Question[], nextNotice: string | null) => {
    setQuestions(nextQuestions)
    setNotice(nextNotice)
    resetProgress()
  }

  const loadPoolQuestions = async (courseIdValue: number) => {
    const poolRes = await exerciseAPI.listPool(courseIdValue).catch(() => ({ data: [] }))
    const poolQuestions = (Array.isArray(poolRes.data) ? poolRes.data : [])
      .map(normalizeQuestion)
      .filter(isDisplayableChoiceQuestion)

    if (poolQuestions.length > 0) {
      setQuestionSet(poolQuestions, '当前展示题库推荐练习。点击“根据薄弱点生成练习”可按个人学情生成新题。')
      return
    }

    setQuestionSet(mockQuestions, '当前课程暂无可展示的题库选择题，已展示兜底练习。')
  }

  const loadCoursesAndQuestions = async (courseIdArg?: number) => {
    setLoading(true)
    try {
      const { data: courseData } = await courseAPI.list().catch(() => ({ data: [] }))
      const nextCourses = Array.isArray(courseData) ? courseData : []
      setCourses(nextCourses)
      const activeCourseId = courseIdArg || selectedCourseId || routeCourseId || nextCourses[0]?.id
      if (!activeCourseId) {
        setQuestionSet(mockQuestions, '暂无可用课程，已展示兜底练习。')
        return
      }

      setSelectedCourseId(activeCourseId)
      await loadPoolQuestions(activeCourseId)
    } catch {
      setQuestionSet(mockQuestions, '练习数据加载失败，已展示兜底练习。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadCoursesAndQuestions(routeCourseId)
  }, [routeCourseId])

  const handleGenerateByWeakPoints = async () => {
    if (!selectedCourseId) return
    setGenerating(true)
    setNotice('AI 正在根据你的学情生成练习...')
    try {
      const { data } = await exerciseAPI.generate({
        course_id: selectedCourseId,
        knowledge_point_ids: [],
        exercise_type: 'choice',
        difficulty: 2,
        count: 3,
        use_llm: true,
      })
      const source = Array.isArray(data) ? data : Array.isArray(data?.exercises) ? data.exercises : []
      const generatedQuestions: Question[] = source.map(normalizeQuestion).filter(isDisplayableChoiceQuestion)

      if (generatedQuestions.length === 0) {
        message.warning('生成接口未返回可展示的选择题，已保留当前练习。')
        setNotice('生成接口未返回可展示的选择题，当前仍展示原练习。')
        return
      }

      const hasLlm = generatedQuestions.some((item) => item.source === 'generated' && item.generation_method === 'llm')
      const hasFallback = generatedQuestions.some((item) => item.source === 'generated' && item.generation_method === 'fallback')
      const hasPool = generatedQuestions.some((item) => item.source === 'pool')
      const nextNotice = hasLlm
        ? '已生成 AI 个性化练习，作答会写入生成题作答记录并更新学情。'
        : hasFallback
          ? 'AI 生成不可用，后端已提供兜底练习以保持流程可用。'
          : hasPool
            ? '后端按薄弱点返回了题库推荐练习。'
            : null
      setQuestionSet(generatedQuestions, nextNotice)
    } catch {
      message.error('AI 生成练习失败，请稍后重试。')
      setNotice('AI 生成练习失败，当前仍展示原练习。')
    } finally {
      setGenerating(false)
    }
  }

  const handleSubmit = async () => {
    if (!selected || !q) return
    setLoading(true)
    try {
      let result: AttemptResult
      try {
        const payload = q.generated_exercise_id
          ? { generated_exercise_id: q.generated_exercise_id, student_answer: selected }
          : { exercise_id: q.exercise_id, student_answer: selected }
        const { data } = await exerciseAPI.attempt(payload)
        result = data
      } catch {
        const correct = selected === (q.answer || 'A')
        result = { is_correct: correct, score: correct ? 100 : 0, feedback: q.explanation || '暂无反馈', answer: q.answer }
      }

      const correct = Boolean(result.correct ?? result.is_correct)
      setAttemptResult(result)
      setSubmitted(true)
      setAnswers((prev) => ({
        ...prev,
        [q.generated_exercise_id || q.exercise_id || q.id || current]: {
          selected,
          correct,
          score: Number(result.score || 0),
        },
      }))
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

  const score = Object.values(answers).length
    ? Math.round(Object.values(answers).reduce((sum, item) => sum + item.score, 0) / Object.values(answers).length)
    : 0

  if (!questions.length && !loading) return <Empty description="暂无练习" />

  if (finished) {
    const correctCount = Object.values(answers).filter((item) => item.correct).length
    return (
      <div>
        <Typography.Title level={4}>练习中心</Typography.Title>
        <Card style={{ borderRadius: 8, textAlign: 'center', padding: '32px 0' }}>
          <TrophyOutlined style={{ fontSize: 64, color: score >= 80 ? '#faad14' : score >= 60 ? '#1677ff' : '#ff4d4f' }} />
          <div style={{ fontSize: 28, fontWeight: 800, marginTop: 16 }}>
            {correctCount}/{Object.keys(answers).length} 题正确 · {score} 分
          </div>
          <div style={{ color: '#666', marginTop: 8 }}>
            {score >= 80 ? '掌握情况良好，继续保持。' : score >= 60 ? '基础可用，建议继续补强薄弱点。' : '建议回到薄弱知识点复习后再练习。'}
          </div>
          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 12 }}>
            <Button icon={<ReloadOutlined />} onClick={() => void loadCoursesAndQuestions(selectedCourseId)}>再练一次</Button>
            <Button type="primary" icon={<ExperimentOutlined />} loading={generating} onClick={() => void handleGenerateByWeakPoints()}>
              根据薄弱点生成练习
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 20 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>练习中心</Typography.Title>
        <Space wrap>
          <Select
            style={{ width: 260 }}
            options={courses.map((course) => ({ value: course.id, label: `${course.name}（${course.code}）` }))}
            value={selectedCourseId}
            onChange={(value) => {
              setSelectedCourseId(value)
              void loadCoursesAndQuestions(value)
            }}
          />
          <Button type="primary" icon={<ExperimentOutlined />} loading={generating} onClick={() => void handleGenerateByWeakPoints()}>
            根据薄弱点生成练习
          </Button>
        </Space>
      </Space>

      {notice && (
        <Alert
          type={q?.source === 'generated' && q.generation_method === 'fallback' ? 'warning' : 'info'}
          showIcon
          style={{ marginBottom: 16 }}
          message={notice}
        />
      )}

      <Card style={{ borderRadius: 8, marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 8, flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 600 }}>Q{current + 1} / {total}</span>
          <Space wrap size={6}>
            {getSourceTag(q)}
            <Tag>{difficultyLabel[q?.difficulty || 1] || `难度 ${q?.difficulty || 1}`}</Tag>
            <span style={{ color: '#666' }}>{q?.knowledge || '综合练习'}</span>
          </Space>
        </div>
        <Progress percent={Math.round(((current + (submitted ? 1 : 0)) / total) * 100)} showInfo={false} />
      </Card>

      <Card style={{ borderRadius: 8, marginBottom: 16 }} loading={loading && !submitted}>
        <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 16, lineHeight: 1.7 }}>{q?.question || '暂无题目内容'}</div>
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
                if (isCorrect) {
                  background = '#f6ffed'
                  border = '1px solid #b7eb8f'
                } else if (isSelected) {
                  background = '#fff1f0'
                  border = '1px solid #ffa39e'
                }
              } else if (isSelected) {
                background = '#e6f4ff'
                border = '1px solid #91caff'
              }
              return (
                <div
                  key={option.key}
                  onClick={() => {
                    if (!submitted) setSelected(option.key)
                  }}
                  style={{ padding: '12px 16px', borderRadius: 8, cursor: submitted ? 'default' : 'pointer', background, border, display: 'flex', alignItems: 'center', gap: 10 }}
                >
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
          <Alert
            type={Boolean(attemptResult?.correct ?? attemptResult?.is_correct) ? 'success' : 'error'}
            showIcon
            style={{ marginTop: 16 }}
            message={Boolean(attemptResult?.correct ?? attemptResult?.is_correct) ? '回答正确' : `回答错误${attemptResult?.answer || q?.answer ? `，正确答案是 ${attemptResult?.answer || q?.answer}` : ''}`}
            description={attemptResult?.feedback || attemptResult?.explanation || q?.explanation || '暂无反馈'}
          />
        )}
      </Card>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
        {!submitted ? (
          <Button type="primary" disabled={!selected || normalizedOptions.length === 0} loading={loading} onClick={() => void handleSubmit()}>
            提交答案
          </Button>
        ) : (
          <Button type="primary" onClick={handleNext}>{current >= total - 1 ? '查看报告' : '下一题'}</Button>
        )}
      </div>
    </div>
  )
}

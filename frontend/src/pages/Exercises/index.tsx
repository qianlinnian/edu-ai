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
import { courseAPI, exerciseAPI, getErrorMessage } from '../../services/api'

type Course = { id: number; name: string; code: string }
type QuestionSource = 'pool' | 'generated'
type GenerationMethod = 'llm' | 'fallback' | 'pool_recommendation' | null
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
  is_correct?: boolean
  score?: number
  feedback?: string
  answer?: string
  alerts_refreshed?: number
}

type TargetKnowledgePoint = {
  knowledge_unit_id: number
  name: string
  mastery_score: number
  attempt_count: number
}

type GenerateResponse = {
  exercises: any[]
  source: string
  generation_method: GenerationMethod
  target_knowledge_points: TargetKnowledgePoint[]
  source_summary: { llm: number; pool: number; fallback: number }
  fallback_used: boolean
}

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
  const source: QuestionSource = item.source === 'generated' ? 'generated' : 'pool'
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
  if (question.source === 'pool') return <Tag color="blue">题库推荐</Tag>
  if (question.generation_method === 'fallback') return <Tag color="orange">后端兜底生成</Tag>
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
  const [errorText, setErrorText] = useState<string | null>(null)
  const [targetKnowledgePoints, setTargetKnowledgePoints] = useState<TargetKnowledgePoint[]>([])

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

  const setQuestionSet = (nextQuestions: Question[], nextNotice: string | null, weakPoints: TargetKnowledgePoint[] = []) => {
    setQuestions(nextQuestions)
    setNotice(nextNotice)
    setTargetKnowledgePoints(weakPoints)
    setErrorText(null)
    resetProgress()
  }

  const loadPoolQuestions = async (courseIdValue: number) => {
    const { data } = await exerciseAPI.listPool(courseIdValue)
    const poolQuestions = (Array.isArray(data) ? data : [])
      .map(normalizeQuestion)
      .filter(isDisplayableChoiceQuestion)

    if (poolQuestions.length > 0) {
      setQuestionSet(poolQuestions, '当前展示题库推荐练习。点击“根据薄弱点生成练习”会优先使用你的薄弱知识点生成或推荐新题。')
      return
    }

    setQuestionSet([], '当前课程暂无可展示的题库练习。你可以直接根据薄弱点生成练习。')
  }

  const loadCoursesAndQuestions = async (courseIdArg?: number) => {
    setLoading(true)
    setErrorText(null)
    try {
      const { data: courseData } = await courseAPI.list()
      const nextCourses = Array.isArray(courseData) ? courseData : []
      setCourses(nextCourses)
      const activeCourseId = courseIdArg || selectedCourseId || routeCourseId || nextCourses[0]?.id
      if (!activeCourseId) {
        setQuestionSet([], '暂无可用课程，当前无法加载练习。')
        return
      }

      setSelectedCourseId(activeCourseId)
      await loadPoolQuestions(activeCourseId)
    } catch (error) {
      setQuestions([])
      setTargetKnowledgePoints([])
      setNotice(null)
      setErrorText(getErrorMessage(error, '练习数据加载失败'))
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
    setNotice('正在根据你的掌握度、预警和薄弱知识点生成练习...')
    setErrorText(null)
    try {
      const { data } = await exerciseAPI.generate({
        course_id: selectedCourseId,
        knowledge_point_ids: [],
        exercise_type: 'choice',
        difficulty: 2,
        count: 3,
        use_llm: true,
      })
      const payload = data as GenerateResponse
      const generatedQuestions: Question[] = (Array.isArray(payload.exercises) ? payload.exercises : [])
        .map(normalizeQuestion)
        .filter(isDisplayableChoiceQuestion)

      if (generatedQuestions.length === 0) {
        setQuestions([])
        setTargetKnowledgePoints(payload.target_knowledge_points || [])
        setNotice('后端未返回可展示的选择题，当前保持空态。')
        return
      }

      const summary = payload.source_summary || { llm: 0, pool: 0, fallback: 0 }
      const nextNotice = summary.llm > 0
        ? '已根据薄弱知识点生成 AI 个性化练习。作答后会更新 mastery，并刷新 learning alerts。'
        : summary.fallback > 0
          ? 'LLM 生成不可用，后端已返回兜底练习以保持闭环可用。'
          : '后端已按薄弱知识点返回题库推荐练习。'
      setQuestionSet(generatedQuestions, nextNotice, payload.target_knowledge_points || [])
    } catch (error) {
      setErrorText(getErrorMessage(error, '生成练习失败'))
      setNotice(null)
    } finally {
      setGenerating(false)
    }
  }

  const handleSubmit = async () => {
    if (!selected || !q) return
    setLoading(true)
    setErrorText(null)
    try {
      const payload = q.generated_exercise_id
        ? { generated_exercise_id: q.generated_exercise_id, student_answer: selected }
        : { exercise_id: q.exercise_id, student_answer: selected }
      const { data } = await exerciseAPI.attempt(payload)
      const result = data as AttemptResult

      const correct = Boolean(result.is_correct)
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

      if ((result.alerts_refreshed || 0) > 0) {
        setNotice(`本次作答已刷新 ${result.alerts_refreshed} 条学习预警，可前往学情页查看。`)
      }
    } catch (error) {
      const detail = getErrorMessage(error, '提交作答失败')
      setErrorText(detail)
      message.error(detail)
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

  if (!loading && !questions.length) {
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

        {errorText && <Alert type="error" showIcon style={{ marginBottom: 16 }} message={errorText} />}
        {notice && <Alert type="info" showIcon style={{ marginBottom: 16 }} message={notice} />}
        <Empty description="暂无可展示练习" />
      </div>
    )
  }

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

      {errorText && <Alert type="error" showIcon style={{ marginBottom: 16 }} message={errorText} />}
      {notice && <Alert type="info" showIcon style={{ marginBottom: 16 }} message={notice} />}

      {targetKnowledgePoints.length > 0 && (
        <Card style={{ borderRadius: 8, marginBottom: 16 }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>本次练习聚焦的薄弱点</div>
          <Space wrap>
            {targetKnowledgePoints.map((item) => (
              <Tag key={item.knowledge_unit_id} color={item.mastery_score < 0.25 ? 'error' : 'warning'}>
                {item.name} · 掌握度 {Math.round(item.mastery_score * 100)}%
              </Tag>
            ))}
          </Space>
        </Card>
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
        {submitted && (
          <Alert
            type={Boolean(attemptResult?.is_correct) ? 'success' : 'error'}
            showIcon
            style={{ marginTop: 16 }}
            message={Boolean(attemptResult?.is_correct) ? '回答正确' : `回答错误${attemptResult?.answer || q?.answer ? `，正确答案是 ${attemptResult?.answer || q?.answer}` : ''}`}
            description={attemptResult?.feedback || q?.explanation || '暂无反馈'}
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

import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  Progress,
  Radio,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import { FireOutlined, ReloadOutlined, TrophyOutlined } from '@ant-design/icons'
import { courseAPI, exerciseAPI, getCourseAgentCapability, getErrorMessage, type CourseAgentCapability } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type CourseItem = {
  id: number
  name: string
  code: string
}

type ExerciseOption = {
  key: string
  label: string
}

type ExerciseItem = {
  id: number
  source?: 'pool' | 'generated'
  generation_method?: 'llm' | 'pool_recommendation' | 'fallback'
  type?: string
  question: string
  options?: Array<ExerciseOption | string> | null
  difficulty?: number
  knowledge_point_ids?: number[]
  knowledge_point_names?: string[]
  generated_exercise_id?: number
}

type GenerationResponse = {
  exercises: ExerciseItem[]
  source: string
  generation_method: string
  target_knowledge_points: {
    knowledge_unit_id: number
    name: string
    mastery_score: number
    attempt_count: number
  }[]
  source_summary: {
    llm: number
    pool: number
    fallback: number
  }
  fallback_used: boolean
}

type AttemptResult = {
  is_correct: boolean
  score: number
  feedback: string
  alerts_refreshed?: number
}

type ExerciseMode = 'pool' | 'personalized'

const difficultyLabel = (value?: number) => '⭐'.repeat(Math.min(Math.max(Number(value || 1), 1), 5))

const itemKey = (item: ExerciseItem) => `${item.source || 'pool'}-${item.generated_exercise_id || item.id}`

const normalizePoolExercise = (item: ExerciseItem): ExerciseItem => ({
  ...item,
  source: 'pool',
})

const visibleKnowledgePointLabels = (item?: ExerciseItem) => {
  const names = (item?.knowledge_point_names || []).filter(Boolean)
  if (names.length > 0) return names.slice(0, 3)
  return (item?.knowledge_point_ids || []).slice(0, 3).map((value) => `知识点 ${value}`)
}

const normalizeOptions = (options?: ExerciseItem['options']) => {
  if (!Array.isArray(options)) return []
  return options
    .map((option, index) => {
      if (typeof option === 'string') {
        const match = option.trim().match(/^([A-Za-z])[\.\s、:：-]+(.+)$/)
        return {
          key: (match?.[1] || String.fromCharCode(65 + index)).toUpperCase(),
          label: (match?.[2] || option).trim(),
        }
      }
      if (option && typeof option === 'object') {
        return {
          key: String(option.key || String.fromCharCode(65 + index)).trim().toUpperCase(),
          label: String(option.label || '').trim(),
        }
      }
      return null
    })
    .filter((option): option is ExerciseOption => !!option?.label)
}

export default function Exercises() {
  const { courseId: routeCourseId } = useParams()
  const user = useAuthStore((state) => state.user)
  const isStudent = user?.role === 'student'

  const [courses, setCourses] = useState<CourseItem[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>()
  const [poolExercises, setPoolExercises] = useState<ExerciseItem[]>([])
  const [generatedExercises, setGeneratedExercises] = useState<ExerciseItem[]>([])
  const [mode, setMode] = useState<ExerciseMode>('pool')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answerDraft, setAnswerDraft] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loadingPool, setLoadingPool] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [pageError, setPageError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [results, setResults] = useState<Record<string, AttemptResult>>({})
  const [agentCapability, setAgentCapability] = useState<CourseAgentCapability | null>(null)

  const activeItems = mode === 'personalized' ? generatedExercises : poolExercises
  const currentItem = activeItems[currentIndex]
  const currentKey = currentItem ? itemKey(currentItem) : ''
  const currentResult = currentKey ? results[currentKey] : undefined
  const normalizedOptions = useMemo(() => normalizeOptions(currentItem?.options), [currentItem])

  const completion = useMemo(() => {
    if (activeItems.length === 0) return 0
    const finished = activeItems.filter((item) => results[itemKey(item)]).length
    return Math.round((finished / activeItems.length) * 100)
  }, [activeItems, results])

  const scoreSummary = useMemo(() => {
    if (activeItems.length === 0) return { correct: 0, total: 0, score: 0 }
    const attempts = activeItems
      .map((item) => results[itemKey(item)])
      .filter(Boolean) as AttemptResult[]
    const correct = attempts.filter((item) => item.is_correct).length
    return {
      correct,
      total: activeItems.length,
      score: attempts.length ? Math.round(attempts.reduce((sum, item) => sum + item.score, 0) / attempts.length) : 0,
    }
  }, [activeItems, results])

  const resetSession = (nextMode: ExerciseMode) => {
    setMode(nextMode)
    setCurrentIndex(0)
    setAnswerDraft('')
    setAnswers({})
    setResults({})
  }

  const loadPoolExercises = async (courseId: number) => {
    setLoadingPool(true)
    setPageError(null)
    try {
      const { data } = await exerciseAPI.listPool(courseId)
      setPoolExercises(((data || []) as ExerciseItem[]).map(normalizePoolExercise))
      if (mode === 'pool') {
        setCurrentIndex(0)
        setAnswerDraft('')
        setAnswers({})
        setResults({})
      }
      if ((data || []).length === 0) {
        setNotice('当前课程题库为空。学生端可尝试“生成个性化练习”；教师端需先补充题库或知识点。')
      } else if (mode === 'pool') {
        setNotice('当前显示课程题库练习。该视图优先用于验证现有题库覆盖，不代表个性化生成结果。')
      }
    } catch (error) {
      setPoolExercises([])
      setPageError(getErrorMessage(error, '题库练习加载失败'))
    } finally {
      setLoadingPool(false)
    }
  }

  const loadAgentCapability = async (courseId: number) => {
    try {
      const capability = await getCourseAgentCapability(courseId)
      setAgentCapability(capability)
    } catch (error) {
      setAgentCapability(null)
      setPageError(getErrorMessage(error, '课程 Agent 能力加载失败'))
    }
  }

  const loadCourses = async () => {
    try {
      const { data } = await courseAPI.list()
      const nextCourses = data || []
      setCourses(nextCourses)
      const routeValue = Number(routeCourseId)
      const preferredId = Number.isFinite(routeValue) && nextCourses.some((item: CourseItem) => item.id === routeValue)
        ? routeValue
        : nextCourses[0]?.id
      setSelectedCourseId(preferredId)
      if (preferredId) {
        await loadAgentCapability(preferredId)
        await loadPoolExercises(preferredId)
      }
    } catch (error) {
      setPageError(getErrorMessage(error, '课程列表加载失败'))
    }
  }

  useEffect(() => {
    void loadCourses()
  }, [routeCourseId])

  const handleCourseChange = async (value: number) => {
    setSelectedCourseId(value)
    setGeneratedExercises([])
    resetSession('pool')
    await loadAgentCapability(value)
    await loadPoolExercises(value)
  }

  const handleGenerate = async () => {
    if (!selectedCourseId) {
      message.warning('请先选择课程')
      return
    }
    if (agentCapability && !agentCapability.hasExercise) {
      message.warning('当前课程未发布个性化练习生成能力')
      return
    }
    setGenerating(true)
    setPageError(null)
    try {
      const { data } = await exerciseAPI.generate({
        course_id: selectedCourseId,
        exercise_type: 'choice',
        difficulty: 2,
        count: 5,
        use_llm: true,
      })

      const response = data as GenerationResponse
      setGeneratedExercises(response.exercises || [])
      resetSession('personalized')

      const weakNames = response.target_knowledge_points.map((item) => item.name).filter(Boolean).slice(0, 3).join('、')
      const baseNotice = weakNames
        ? `本轮练习面向薄弱知识点：${weakNames}。`
        : '本轮练习按当前课程与学情状态生成。'

      if (response.fallback_used) {
        setNotice(
          `${baseNotice} 当前题目来源包含兜底题（pool=${response.source_summary.pool}，fallback=${response.source_summary.fallback}）。这表示题库或 LLM 结果不足，当前链路仍可用，但不应表述为完全稳定的自适应出题。`
        )
      } else if (response.generation_method === 'llm') {
        setNotice(`${baseNotice} 当前题目主要来自 LLM 个性化生成。`)
      } else {
        setNotice(`${baseNotice} 当前题目主要来自课程题库推荐。`)
      }
    } catch (error) {
      setGeneratedExercises([])
      setPageError(getErrorMessage(error, '个性化练习生成失败'))
    } finally {
      setGenerating(false)
    }
  }

  const handleSubmit = async () => {
    if (!currentItem) return
    if (!answerDraft.trim()) {
      message.warning('请先作答')
      return
    }
    if (currentResult) return

    setSubmitting(true)
    try {
      const isPoolItem = mode === 'pool' || currentItem.source === 'pool'
      const { data } = await exerciseAPI.attempt({
        exercise_id: isPoolItem ? currentItem.id : undefined,
        generated_exercise_id: isPoolItem
          ? undefined
          : currentItem.generated_exercise_id || (currentItem.source === 'generated' ? currentItem.id : undefined),
        student_answer: answerDraft.trim(),
      })
      setAnswers((prev) => ({ ...prev, [currentKey]: answerDraft.trim() }))
      setResults((prev) => ({ ...prev, [currentKey]: data }))
      if ((data.alerts_refreshed || 0) > 0) {
        setNotice(`本次作答已刷新 ${data.alerts_refreshed} 条学习预警，可前往学情页查看。`)
      }
    } catch (error) {
      message.error(getErrorMessage(error, '提交答案失败'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleNext = () => {
    if (!currentItem) return
    const nextIndex = currentIndex + 1
    if (nextIndex >= activeItems.length) {
      setAnswerDraft('')
      return
    }
    setCurrentIndex(nextIndex)
    const nextItem = activeItems[nextIndex]
    const nextKey = itemKey(nextItem)
    setAnswerDraft(answers[nextKey] || '')
  }

  useEffect(() => {
    if (!currentItem) {
      setAnswerDraft('')
      return
    }
    setAnswerDraft(answers[currentKey] || '')
  }, [currentItem, currentKey, answers])

  const renderSummary = () => {
    if (activeItems.length === 0 || completion < 100) return null
    return (
      <Card bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
        <Space direction="vertical" size={12} style={{ width: '100%', alignItems: 'center' }}>
          <TrophyOutlined style={{ fontSize: 40, color: scoreSummary.score >= 80 ? '#faad14' : '#1677ff' }} />
          <Typography.Title level={4} style={{ margin: 0 }}>
            已完成本轮练习
          </Typography.Title>
          <Typography.Text>
            正确 {scoreSummary.correct}/{scoreSummary.total} · 平均分 {scoreSummary.score}
          </Typography.Text>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => resetSession(mode)}>
              重新开始本轮
            </Button>
            {isStudent && (
              <Button
                type="primary"
                icon={<FireOutlined />}
                onClick={() => void handleGenerate()}
                disabled={agentCapability ? !agentCapability.hasExercise : false}
              >
                再生成一组
              </Button>
            )}
          </Space>
        </Space>
      </Card>
    )
  }

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 20 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>练习中心</Typography.Title>
        <Space wrap>
          <Select
            value={selectedCourseId}
            onChange={(value) => void handleCourseChange(value)}
            style={{ width: 260 }}
            placeholder="选择课程"
            options={courses.map((item) => ({ value: item.id, label: `${item.name}（${item.code}）` }))}
          />
          <Button
            onClick={() => {
              if (!selectedCourseId) return
              resetSession('pool')
              setNotice('当前显示课程题库练习。该视图优先用于验证现有题库覆盖，不代表个性化生成结果。')
              void loadPoolExercises(selectedCourseId)
            }}
            loading={loadingPool}
          >
            查看课程题库
          </Button>
          {isStudent && (
            <Button
              type="primary"
              icon={<FireOutlined />}
              onClick={() => void handleGenerate()}
              loading={generating}
              disabled={agentCapability ? !agentCapability.hasExercise : false}
            >
              生成个性化练习
            </Button>
          )}
        </Space>
      </Space>

      {!isStudent && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="当前页面主要用于学生侧练习链路演示"
          description="教师/管理员可以查看课程题库，但个性化生成与作答反馈主链路按当前产品口径面向学生端。"
        />
      )}

      {pageError && <Alert type="error" showIcon message={pageError} style={{ marginBottom: 16 }} />}
      {agentCapability && !agentCapability.hasExercise && (
        <Alert
          type="info"
          showIcon
          message="当前课程未发布个性化练习生成能力"
          description="课程题库浏览和现有题目作答仍可使用，但已发布 Agent workflow 不包含“练习生成”节点，因此后端不会开放个性化练习生成。若需要使用，请先在 Agent 构建器中加入该节点并重新发布。"
          style={{ marginBottom: 16 }}
        />
      )}
      {notice && (
        <Alert
          type={notice.includes('兜底题') ? 'warning' : 'info'}
          showIcon
          message="练习生成说明"
          description={notice}
          style={{ marginBottom: 16 }}
        />
      )}

      <Card bordered={false} style={{ borderRadius: 12, marginBottom: 16 }}>
        <Space size={8} wrap>
          <Tag color={mode === 'pool' ? 'blue' : 'default'}>课程题库</Tag>
          <Tag color={mode === 'personalized' ? 'purple' : 'default'}>个性化练习</Tag>
          {currentItem?.source && <Tag>{currentItem.source === 'pool' ? '题库来源' : '生成来源'}</Tag>}
          {currentItem?.generation_method && <Tag color={currentItem.generation_method === 'fallback' ? 'warning' : 'processing'}>{currentItem.generation_method}</Tag>}
          {currentItem?.difficulty && <Tag>{difficultyLabel(currentItem.difficulty)}</Tag>}
        </Space>
        <Progress percent={completion} showInfo={false} style={{ marginTop: 12 }} />
      </Card>

      {renderSummary()}

      {loadingPool || generating ? (
        <Card bordered={false} style={{ borderRadius: 12, textAlign: 'center', padding: 40 }}>
          <Spin />
        </Card>
      ) : activeItems.length === 0 ? (
        <Card bordered={false} style={{ borderRadius: 12 }}>
          <Empty description={mode === 'personalized' ? '暂无生成结果' : '当前课程暂无可用练习'} />
        </Card>
      ) : currentItem ? (
        <Card bordered={false} style={{ borderRadius: 12 }}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
              <Typography.Text strong>第 {currentIndex + 1} 题 / 共 {activeItems.length} 题</Typography.Text>
              <Space size={8} wrap>
                {visibleKnowledgePointLabels(currentItem).map((item) => (
                  <Tag key={item}>{item}</Tag>
                ))}
              </Space>
            </div>

            <Typography.Title level={5} style={{ margin: 0 }}>
              {currentItem.question}
            </Typography.Title>

            {currentItem.generation_method === 'fallback' && (
              <Alert
                type="warning"
                showIcon
                message="当前题目包含兜底逻辑"
                description="这表示题库或 LLM 生成结果不足，系统为保持练习链路可用生成了兜底题。当前能力可用，但不应表述为完全稳定的高质量自适应出题。"
              />
            )}

            {normalizedOptions.length > 0 ? (
              <Radio.Group
                value={answerDraft || null}
                onChange={(event) => !currentResult && setAnswerDraft(event.target.value)}
                style={{ width: '100%' }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {normalizedOptions.map((option, index) => (
                    <div
                      key={`${currentKey}-option-${option.key || index}`}
                      style={{
                        border: '1px solid #e5e7eb',
                        borderRadius: 10,
                        padding: '12px 14px',
                        background: answerDraft === option.key ? '#f0f7ff' : '#fff',
                      }}
                    >
                      <Radio value={option.key}>
                        <strong>{option.key}.</strong> {option.label}
                      </Radio>
                    </div>
                  ))}
                </Space>
              </Radio.Group>
            ) : (
              <Input.TextArea
                rows={5}
                value={answerDraft}
                disabled={!!currentResult}
                onChange={(event) => setAnswerDraft(event.target.value)}
                placeholder="请输入你的答案"
              />
            )}

            {currentResult && (
              <Alert
                type={currentResult.is_correct ? 'success' : 'warning'}
                showIcon
                message={currentResult.is_correct ? `回答正确` : `回答错误`}
                description={currentResult.feedback}
              />
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              {!isStudent && currentIndex < activeItems.length - 1 && (
                <Button onClick={handleNext}>
                  下一题
                </Button>
              )}
              {!currentResult && isStudent && (
                <Button type="primary" onClick={() => void handleSubmit()} loading={submitting}>
                  提交答案
                </Button>
              )}
              {currentResult && currentIndex < activeItems.length - 1 && (
                <Button type="primary" onClick={handleNext}>
                  下一题
                </Button>
              )}
            </div>
          </Space>
        </Card>
      ) : null}
    </div>
  )
}

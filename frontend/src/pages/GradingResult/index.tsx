import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Divider, Empty, List, Skeleton, Space, Tag, Typography } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { assignmentAPI } from '../../services/api'

type GradingResultData = {
  id: number
  submission_id: number
  score: number
  max_score: number
  overall_comment?: string | null
  strengths?: string[] | null
  weaknesses?: string[] | null
}

type AnnotationPosition = {
  type?: string
  line?: number
  paragraph?: number
  offset?: number
  length?: number
  quote?: string
}

type Annotation = {
  id: number
  annotation_type: string
  position: AnnotationPosition
  content: string
  severity: string
  knowledge_point_id?: number | null
}

const annotationLabel: Record<string, string> = {
  error: '错误',
  warning: '提醒',
  suggestion: '建议',
  praise: '表扬',
}

const annotationColor: Record<string, string> = {
  error: 'error',
  warning: 'warning',
  suggestion: 'processing',
  praise: 'success',
}

const severityLabel: Record<string, string> = {
  low: '轻微',
  medium: '中等',
  high: '较重',
  critical: '严重',
}

const severityColor: Record<string, string> = {
  low: 'default',
  medium: 'processing',
  high: 'warning',
  critical: 'error',
}

function formatPosition(position?: AnnotationPosition) {
  if (!position) return ''
  const parts: string[] = []
  if (typeof position.line === 'number') parts.push(`第 ${position.line} 行`)
  if (typeof position.paragraph === 'number') parts.push(`第 ${position.paragraph} 段`)
  if (typeof position.offset === 'number') parts.push(`偏移 ${position.offset}`)
  if (typeof position.length === 'number') parts.push(`长度 ${position.length}`)
  return parts.join(' · ')
}

function getQuote(position?: AnnotationPosition) {
  if (!position?.quote || typeof position.quote !== 'string') return ''
  return position.quote.trim()
}

export default function GradingResult() {
  const { submissionId } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [waiting, setWaiting] = useState(false)
  const [errorText, setErrorText] = useState('')
  const [result, setResult] = useState<GradingResultData | null>(null)
  const [annotations, setAnnotations] = useState<Annotation[]>([])

  const numericSubmissionId = useMemo(() => Number(submissionId), [submissionId])

  const loadData = useCallback(async (silent = false) => {
    if (!submissionId || Number.isNaN(numericSubmissionId)) return
    if (!silent) setLoading(true)
    setErrorText('')

    try {
      const resultRes = await assignmentAPI.getResult(numericSubmissionId)
      const annotationRes = await assignmentAPI.getAnnotations(numericSubmissionId).catch((error: any) => {
        if (error?.response?.status === 404) return { data: [] }
        throw error
      })

      setResult(resultRes.data)
      setAnnotations(annotationRes.data || [])
      setWaiting(false)
    } catch (error: any) {
      const status = error?.response?.status
      if (status === 404) {
        setWaiting(true)
        setResult(null)
        setAnnotations([])
      } else {
        setWaiting(false)
        setErrorText(error?.response?.data?.detail || '批改结果加载失败')
      }
    } finally {
      if (!silent) setLoading(false)
    }
  }, [numericSubmissionId, submissionId])

  useEffect(() => {
    void loadData()
  }, [loadData])

  useEffect(() => {
    if (!waiting) return
    const timer = window.setInterval(() => {
      void loadData(true)
    }, 4000)
    return () => window.clearInterval(timer)
  }, [loadData, waiting])

  const scorePercent = result?.max_score ? Math.round((result.score / result.max_score) * 100) : 0

  return (
    <div>
      <Space style={{ marginBottom: 24 }} wrap>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/assignments')}>返回</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>批改结果</Typography.Title>
        {submissionId && <Tag color="blue">Submission #{submissionId}</Tag>}
        <Button onClick={() => void loadData()}>刷新</Button>
      </Space>

      {loading && <Skeleton active paragraph={{ rows: 8 }} />}

      {!loading && waiting && (
        <Alert
          type="info"
          showIcon
          message="AI 正在批改中"
          description="结果页会自动刷新，批改完成后将显示分数、总评和批注列表。"
          style={{ marginBottom: 16 }}
        />
      )}

      {!loading && !!errorText && (
        <Alert type="error" showIcon message="加载失败" description={errorText} style={{ marginBottom: 16 }} />
      )}

      {!loading && !errorText && waiting && (
        <Card style={{ marginBottom: 16, borderRadius: 8 }}>
          <Empty description="正在等待 AI 批改结果" />
        </Card>
      )}

      {!loading && !errorText && result && (
        <>
          <Card style={{ marginBottom: 16, borderRadius: 8 }}>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <Typography.Title level={2} style={{ margin: 0, color: scorePercent >= 60 ? '#1677ff' : '#ff4d4f' }}>
                  {result.score} / {result.max_score}
                </Typography.Title>
                <Tag color={scorePercent >= 80 ? 'success' : scorePercent >= 60 ? 'processing' : 'error'}>
                  {scorePercent}%
                </Tag>
              </div>
              <Typography.Paragraph style={{ marginBottom: 0 }}>
                {result.overall_comment || '暂无总评'}
              </Typography.Paragraph>
            </Space>
          </Card>

          <Card title="优点与不足" style={{ marginBottom: 16, borderRadius: 8 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
              <div>
                <Typography.Text strong>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 6 }} />
                  优点
                </Typography.Text>
                {result.strengths && result.strengths.length > 0 ? (
                  <List dataSource={result.strengths} renderItem={(item) => <List.Item>{item}</List.Item>} />
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无优点项" />
                )}
              </div>
              <div>
                <Typography.Text strong>
                  <WarningOutlined style={{ color: '#faad14', marginRight: 6 }} />
                  不足
                </Typography.Text>
                {result.weaknesses && result.weaknesses.length > 0 ? (
                  <List dataSource={result.weaknesses} renderItem={(item) => <List.Item>{item}</List.Item>} />
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无不足项" />
                )}
              </div>
            </div>
          </Card>

          <Card title="批注列表" style={{ borderRadius: 8 }}>
            {annotations.length === 0 ? (
              <Empty description="暂无批注" />
            ) : (
              <List
                itemLayout="vertical"
                dataSource={annotations}
                renderItem={(item) => {
                  const quote = getQuote(item.position)
                  const positionText = formatPosition(item.position)
                  return (
                    <List.Item>
                      <Space direction="vertical" size={10} style={{ width: '100%' }}>
                        <Space wrap>
                          <Tag color={annotationColor[item.annotation_type] || 'default'}>
                            {annotationLabel[item.annotation_type] || item.annotation_type}
                          </Tag>
                          <Tag color={severityColor[item.severity] || 'default'}>
                            {severityLabel[item.severity] || item.severity}
                          </Tag>
                          {positionText && (
                            <Typography.Text type="secondary">{positionText}</Typography.Text>
                          )}
                          {item.knowledge_point_id && (
                            <Tag color="blue">知识点 {item.knowledge_point_id}</Tag>
                          )}
                        </Space>

                        {quote && (
                          <div
                            style={{
                              borderLeft: '3px solid #d9d9d9',
                              padding: '8px 12px',
                              background: '#fafafa',
                              color: '#595959',
                              lineHeight: 1.7,
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                            }}
                          >
                            {quote}
                          </div>
                        )}

                        <Typography.Paragraph style={{ marginBottom: 0, fontSize: 15, lineHeight: 1.8 }}>
                          {item.content}
                        </Typography.Paragraph>
                      </Space>
                    </List.Item>
                  )
                }}
              />
            )}
            <Divider />
            <Typography.Text type="secondary">
              如果页面仍显示“AI 正在批改中”，系统会自动刷新，也可以稍后手动刷新查看。
            </Typography.Text>
          </Card>
        </>
      )}
    </div>
  )
}

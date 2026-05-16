import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Divider, Empty, List, Skeleton, Space, Tag, Typography } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons'
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

type Annotation = {
  id: number
  annotation_type: string
  position: Record<string, unknown>
  content: string
  severity: string
  knowledge_point_id?: number | null
}

export default function GradingResult() {
  const { submissionId } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [waiting, setWaiting] = useState(false)
  const [errorText, setErrorText] = useState('')
  const [result, setResult] = useState<GradingResultData | null>(null)
  const [annotations, setAnnotations] = useState<Annotation[]>([])

  const loadData = async () => {
    if (!submissionId) return
    setLoading(true)
    setErrorText('')
    setWaiting(false)

    try {
      const [resultRes, annotationRes] = await Promise.all([
        assignmentAPI.getResult(Number(submissionId)),
        assignmentAPI.getAnnotations(Number(submissionId)).catch((error: any) => {
          if (error?.response?.status === 404) {
            return { data: [] }
          }
          throw error
        }),
      ])
      setResult(resultRes.data)
      setAnnotations(annotationRes.data || [])
    } catch (error: any) {
      const status = error?.response?.status
      if (status === 404) {
        setWaiting(true)
        setResult(null)
        setAnnotations([])
      } else {
        setErrorText(error?.response?.data?.detail || '批改结果加载失败')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void loadData() }, [submissionId])

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
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
          message="AI 批改中，请稍后刷新"
          description="当前还没有生成正式批改结果，系统可能仍在排队或处理中。"
          style={{ marginBottom: 16 }}
        />
      )}

      {!loading && !!errorText && (
        <Alert type="error" showIcon message="加载失败" description={errorText} style={{ marginBottom: 16 }} />
      )}

      {!loading && !errorText && waiting && (
        <Card style={{ marginBottom: 16, borderRadius: 12 }}>
          <Empty
            description="AI 正在批改中，结果生成后可在此查看"
          />
        </Card>
      )}

      {!loading && !errorText && result && (
        <>
          <Card style={{ marginBottom: 16, borderRadius: 12 }}>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <Typography.Title level={2} style={{ margin: 0, color: result.score / result.max_score >= 0.6 ? '#1677ff' : '#ff4d4f' }}>
                  {result.score} / {result.max_score}
                </Typography.Title>
                <Tag color={result.score / result.max_score >= 0.8 ? 'success' : result.score / result.max_score >= 0.6 ? 'processing' : 'error'}>{Math.round(result.score / result.max_score * 100)}%</Tag>
              </div>
              <Typography.Paragraph style={{ marginBottom: 0 }}>
                {result.overall_comment || '暂无总评'}
              </Typography.Paragraph>
            </Space>
          </Card>

          <Card title="优点与不足" style={{ marginBottom: 16, borderRadius: 12 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <Typography.Text strong><CheckCircleOutlined style={{ color: '#52c41a', marginRight: 6 }} />优点</Typography.Text>
                {result.strengths && result.strengths.length > 0 ? (
                  <List dataSource={result.strengths} renderItem={(item) => <List.Item>{item}</List.Item>} />
                ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无优点项" />}
              </div>
              <div>
                <Typography.Text strong><WarningOutlined style={{ color: '#faad14', marginRight: 6 }} />不足</Typography.Text>
                {result.weaknesses && result.weaknesses.length > 0 ? (
                  <List dataSource={result.weaknesses} renderItem={(item) => <List.Item>{item}</List.Item>} />
                ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无不足项" />}
              </div>
            </div>
          </Card>

          <Card title="批注列表" style={{ borderRadius: 12 }}>
            {annotations.length === 0 ? (
              <Empty description={waiting ? '批改尚未完成，暂时没有批注' : '暂无批注'} />
            ) : (
              <List
                dataSource={annotations}
                renderItem={(item) => (
                  <List.Item>
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <Space wrap>
                        <Tag color={item.annotation_type === 'error' ? 'error' : item.annotation_type === 'warning' ? 'warning' : 'blue'}>
                          {item.annotation_type}
                        </Tag>
                        <Tag>{item.severity}</Tag>
                        <Typography.Text type="secondary">位置：{JSON.stringify(item.position)}</Typography.Text>
                      </Space>
                      <Typography.Text>{item.content}</Typography.Text>
                    </Space>
                  </List.Item>
                )}
              />
            )}
            <Divider />
            <Typography.Text type="secondary">
              若仍显示“AI 批改中”，可稍后刷新页面再次查看。
            </Typography.Text>
          </Card>
        </>
      )}
    </div>
  )
}

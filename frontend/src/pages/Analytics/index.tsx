import { useEffect, useMemo, useState } from 'react'
import { Alert, Card, Col, Empty, List, Row, Select, Space, Tag, Typography } from 'antd'
import { AlertOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { analyticsAPI, courseAPI } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type Course = { id: number; name: string; code: string }
type MasteryItem = { knowledge_point?: string; knowledge_point_id?: number; mastery?: number; score?: number; label?: string; name?: string }
type AlertItem = { id?: number; level?: 'error' | 'warning' | 'info'; message?: string; title?: string; content?: string; student_name?: string }

const mockMastery = [
  { label: '循环结构', value: 63 },
  { label: '递归', value: 42 },
  { label: '列表操作', value: 78 },
]

const buildRadarOption = (items: { label: string; value: number }[]) => ({
  tooltip: {},
  radar: {
    indicator: items.map((item) => ({ name: item.label, max: 100 })),
    radius: 100,
    axisName: { color: '#555', fontSize: 12 },
  },
  series: [{
    type: 'radar',
    data: [{ value: items.map((item) => item.value), name: '我的掌握度', itemStyle: { color: '#6366f1' }, areaStyle: { color: 'rgba(99,102,241,0.15)' } }],
  }],
})

export default function Analytics() {
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>()
  const [mastery, setMastery] = useState<{ label: string; value: number }[]>([])
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [loading, setLoading] = useState(false)

  const radarOption = useMemo(() => buildRadarOption(mastery.length ? mastery : mockMastery), [mastery])

  const loadData = async (courseId?: number, courseList?: Course[]) => {
    if (!user) return
    const activeCourseId = courseId || selectedCourseId || courseList?.[0]?.id
    if (!activeCourseId) return

    setLoading(true)
    try {
      const [masteryRes, alertsRes] = await Promise.all([
        analyticsAPI.getStudentMastery(user.id, activeCourseId).catch(() => ({ data: [] })),
        analyticsAPI.getAlerts(activeCourseId).catch(() => ({ data: [] })),
      ])

      const mappedMastery = (masteryRes.data || []).map((item: MasteryItem) => ({
        label: item.knowledge_point || item.label || item.name || `知识点${item.knowledge_point_id ?? ''}`,
        value: Number(item.mastery ?? item.score ?? 0),
      }))

      setMastery(mappedMastery)
      setAlerts(alertsRes.data || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const bootstrap = async () => {
      const { data } = await courseAPI.list().catch(() => ({ data: [] }))
      setCourses(data)
      const firstId = data?.[0]?.id
      if (firstId) {
        setSelectedCourseId(firstId)
        await loadData(firstId, data)
      }
    }
    void bootstrap()
  }, [])

  if (isTeacher) {
    return (
      <div>
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>学情分析</Typography.Title>
          <Select style={{ width: 240 }} options={courses.map((course) => ({ value: course.id, label: `${course.name}（${course.code}）` }))} value={selectedCourseId} onChange={(value) => { setSelectedCourseId(value); void loadData(value) }} />
        </Space>
        <Alert type="info" showIcon message="教师端学情联调中" description="当前优先完成学生端最小真实学情展示。教师端完整看板后续继续对接。" />
      </div>
    )
  }

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>我的学情</Typography.Title>
        <Select style={{ width: 240 }} options={courses.map((course) => ({ value: course.id, label: `${course.name}（${course.code}）` }))} value={selectedCourseId} onChange={(value) => { setSelectedCourseId(value); void loadData(value) }} />
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="个人知识掌握情况" loading={loading} style={{ borderRadius: 12 }}>
            {mastery.length === 0 ? <Empty description="暂无掌握度数据" /> : <ReactECharts option={radarOption} style={{ height: 280 }} />}
            {mastery.length > 0 && (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                {mastery.map((item) => <Tag key={item.label} color={item.value >= 80 ? 'success' : item.value >= 60 ? 'warning' : 'error'}>{item.label} {item.value}%</Tag>)}
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title={<span><AlertOutlined style={{ color: '#ff4d4f', marginRight: 6 }} />学习预警</span>} loading={loading} style={{ borderRadius: 12 }}>
            {alerts.length === 0 ? (
              <Empty description="暂无预警信息" />
            ) : (
              <List
                dataSource={alerts}
                renderItem={(item) => (
                  <List.Item>
                    <Alert
                      type={item.level || 'warning'}
                      showIcon
                      message={item.title || item.student_name || '学习提醒'}
                      description={item.message || item.content || '暂无详细说明'}
                      style={{ width: '100%' }}
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

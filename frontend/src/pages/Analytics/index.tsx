import { useEffect, useMemo, useState } from 'react'
import { Alert, Card, Col, Empty, List, Row, Select, Skeleton, Space, Statistic, Tag, Typography } from 'antd'
import { AlertOutlined, BarChartOutlined, TeamOutlined, WarningOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { analyticsAPI, courseAPI } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type Course = { id: number; name: string; code: string }
type Student = { id: number; username: string; full_name: string; email: string }
type StudentMasteryItem = {
  knowledge_unit?: { id: number; name: string; difficulty?: number }
  knowledge_point?: string
  knowledge_point_id?: number
  mastery?: number
  mastery_score?: number
  score?: number
  label?: string
  name?: string
}
type ClassReport = {
  course_id: number
  overall_avg_mastery: number
  knowledge_unit_count: number
  by_knowledge_unit: {
    knowledge_unit_id: number
    name: string
    avg_mastery: number
    student_count: number
    risk_count: number
  }[]
}
type AlertItem = {
  id?: number
  level?: 'error' | 'warning' | 'info'
  severity?: 'high' | 'medium' | 'low'
  message?: string
  title?: string
  content?: string
  student_id?: number
  student_name?: string
  details?: { knowledge_unit_name?: string; mastery_score?: number; threshold?: number }
}

const toPercent = (value?: number) => {
  const numeric = Number(value ?? 0)
  return Math.round((numeric <= 1 ? numeric * 100 : numeric))
}

const alertType = (item: AlertItem): 'error' | 'warning' | 'info' => {
  if (item.level) return item.level
  if (item.severity === 'high') return 'error'
  if (item.severity === 'medium') return 'warning'
  return 'info'
}

const buildRadarOption = (items: { label: string; value: number }[]) => ({
  tooltip: {},
  radar: {
    indicator: items.map((item) => ({ name: item.label, max: 100 })),
    radius: 100,
    axisName: { color: '#555', fontSize: 12 },
  },
  series: [{
    type: 'radar',
    data: [{ value: items.map((item) => item.value), name: '掌握度', itemStyle: { color: '#1677ff' }, areaStyle: { color: 'rgba(22,119,255,0.15)' } }],
  }],
})

const buildClassBarOption = (items: ClassReport['by_knowledge_unit']) => ({
  tooltip: { trigger: 'axis' },
  grid: { top: 20, right: 20, bottom: 70, left: 50 },
  xAxis: {
    type: 'category',
    data: items.map((item) => item.name),
    axisLabel: { rotate: 25, fontSize: 11 },
  },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [{
    name: '平均掌握度',
    type: 'bar',
    data: items.map((item) => toPercent(item.avg_mastery)),
    itemStyle: {
      borderRadius: [6, 6, 0, 0],
      color: (params: any) => {
        if (params.value >= 80) return '#52c41a'
        if (params.value >= 60) return '#faad14'
        return '#ff4d4f'
      },
    },
  }],
})

function mapMastery(data: StudentMasteryItem[]) {
  return (data || []).map((item) => ({
    label: item.knowledge_unit?.name || item.knowledge_point || item.label || item.name || `知识点 ${item.knowledge_point_id ?? item.knowledge_unit?.id ?? ''}`,
    value: toPercent(item.mastery_score ?? item.mastery ?? item.score),
  }))
}

export default function Analytics() {
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>()
  const [students, setStudents] = useState<Student[]>([])
  const [selectedStudentId, setSelectedStudentId] = useState<number | undefined>()
  const [mastery, setMastery] = useState<{ label: string; value: number }[]>([])
  const [classReport, setClassReport] = useState<ClassReport | null>(null)
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [loading, setLoading] = useState(false)

  const radarOption = useMemo(() => buildRadarOption(mastery), [mastery])
  const classBarOption = useMemo(() => buildClassBarOption(classReport?.by_knowledge_unit || []), [classReport])

  const loadStudentAnalytics = async (courseId: number, studentId = user?.id) => {
    if (!studentId) return
    setLoading(true)
    try {
      const [masteryRes, alertsRes] = await Promise.all([
        analyticsAPI.getStudentMastery(studentId, courseId).catch(() => ({ data: [] })),
        analyticsAPI.getAlerts(courseId).catch(() => ({ data: [] })),
      ])
      setMastery(mapMastery(masteryRes.data || []))
      setAlerts(alertsRes.data || [])
    } finally {
      setLoading(false)
    }
  }

  const loadTeacherAnalytics = async (courseId: number, studentId?: number) => {
    setLoading(true)
    try {
      const [reportRes, alertsRes, studentsRes] = await Promise.all([
        analyticsAPI.getClassReport(courseId).catch(() => ({ data: null })),
        analyticsAPI.getAlerts(courseId).catch(() => ({ data: [] })),
        courseAPI.listStudents(courseId).catch(() => ({ data: [] })),
      ])

      const nextStudents = studentsRes.data || []
      const activeStudentId = studentId || selectedStudentId || nextStudents[0]?.id
      setStudents(nextStudents)
      setSelectedStudentId(activeStudentId)
      setClassReport(reportRes.data)
      setAlerts(alertsRes.data || [])

      if (activeStudentId) {
        const masteryRes = await analyticsAPI.getStudentMastery(activeStudentId, courseId).catch(() => ({ data: [] }))
        setMastery(mapMastery(masteryRes.data || []))
      } else {
        setMastery([])
      }
    } finally {
      setLoading(false)
    }
  }

  const loadData = async (courseId?: number, studentId?: number) => {
    if (!user) return
    const activeCourseId = courseId || selectedCourseId || courses[0]?.id
    if (!activeCourseId) return
    if (isTeacher) await loadTeacherAnalytics(activeCourseId, studentId)
    else await loadStudentAnalytics(activeCourseId, user.id)
  }

  useEffect(() => {
    const bootstrap = async () => {
      const { data } = await courseAPI.list().catch(() => ({ data: [] }))
      setCourses(data)
      const firstId = data?.[0]?.id
      if (firstId) {
        setSelectedCourseId(firstId)
        if (isTeacher) await loadTeacherAnalytics(firstId)
        else await loadStudentAnalytics(firstId, user?.id)
      }
    }
    void bootstrap()
  }, [isTeacher, user?.id])

  const courseSelect = (
    <Select
      style={{ width: 240 }}
      options={courses.map((course) => ({ value: course.id, label: `${course.name}（${course.code}）` }))}
      value={selectedCourseId}
      onChange={(value) => {
        setSelectedCourseId(value)
        void loadData(value)
      }}
    />
  )

  if (isTeacher) {
    const reportItems = classReport?.by_knowledge_unit || []
    const average = toPercent(classReport?.overall_avg_mastery)
    const riskTotal = reportItems.reduce((sum, item) => sum + item.risk_count, 0)

    return (
      <div>
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }} wrap>
          <Typography.Title level={4} style={{ margin: 0 }}>学情分析</Typography.Title>
          <Space wrap>
            {courseSelect}
            <Select
              allowClear
              placeholder="选择学生"
              style={{ width: 220 }}
              options={students.map((student) => ({ value: student.id, label: student.full_name || student.username }))}
              value={selectedStudentId}
              onChange={(value) => {
                setSelectedStudentId(value)
                if (selectedCourseId && value) void loadTeacherAnalytics(selectedCourseId, value)
              }}
            />
          </Space>
        </Space>

        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card bordered={false} style={{ borderRadius: 8 }}>
              <Statistic title="班级平均掌握度" value={average} suffix="%" prefix={<BarChartOutlined />} />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card bordered={false} style={{ borderRadius: 8 }}>
              <Statistic title="知识点数量" value={classReport?.knowledge_unit_count || 0} prefix={<TeamOutlined />} />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card bordered={false} style={{ borderRadius: 8 }}>
              <Statistic title="风险项" value={riskTotal} prefix={<WarningOutlined />} valueStyle={{ color: riskTotal ? '#ff4d4f' : undefined }} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={14}>
            <Card title="班级知识点平均掌握度" loading={loading} style={{ borderRadius: 8 }}>
              {reportItems.length === 0 ? <Empty description="暂无班级学情数据" /> : <ReactECharts option={classBarOption} style={{ height: 320 }} />}
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title="学生个人掌握度" loading={loading} style={{ borderRadius: 8 }}>
              {mastery.length === 0 ? <Empty description="暂无学生掌握度数据" /> : <ReactECharts option={radarOption} style={{ height: 320 }} />}
              {mastery.length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                  {mastery.map((item) => <Tag key={item.label} color={item.value >= 80 ? 'success' : item.value >= 60 ? 'warning' : 'error'}>{item.label} {item.value}%</Tag>)}
                </div>
              )}
            </Card>
          </Col>
        </Row>

        <Card title={<span><AlertOutlined style={{ color: '#ff4d4f', marginRight: 6 }} />学习预警</span>} loading={loading} style={{ marginTop: 16, borderRadius: 8 }}>
          {alerts.length === 0 ? <Empty description="暂无预警信息" /> : (
            <List
              dataSource={alerts}
              renderItem={(item) => (
                <List.Item>
                  <Alert
                    type={alertType(item)}
                    showIcon
                    message={`学生 ${item.student_id ?? ''}：${item.details?.knowledge_unit_name || item.title || '知识点预警'}`}
                    description={item.message || item.content || '暂无详细说明'}
                    style={{ width: '100%' }}
                  />
                </List.Item>
              )}
            />
          )}
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>我的学情</Typography.Title>
        {courseSelect}
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="个人知识掌握情况" loading={loading} style={{ borderRadius: 8 }}>
            {loading ? <Skeleton active paragraph={{ rows: 6 }} /> : mastery.length === 0 ? <Empty description="暂无掌握度数据" /> : <ReactECharts option={radarOption} style={{ height: 280 }} />}
            {mastery.length > 0 && (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                {mastery.map((item) => <Tag key={item.label} color={item.value >= 80 ? 'success' : item.value >= 60 ? 'warning' : 'error'}>{item.label} {item.value}%</Tag>)}
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title={<span><AlertOutlined style={{ color: '#ff4d4f', marginRight: 6 }} />学习预警</span>} loading={loading} style={{ borderRadius: 8 }}>
            {alerts.length === 0 ? (
              <Empty description="暂无预警信息" />
            ) : (
              <List
                dataSource={alerts}
                renderItem={(item) => (
                  <List.Item>
                    <Alert
                      type={alertType(item)}
                      showIcon
                      message={item.details?.knowledge_unit_name || item.title || '学习提醒'}
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

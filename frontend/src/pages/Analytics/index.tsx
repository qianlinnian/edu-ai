import { useEffect, useMemo, useState } from 'react'
import { Alert, Card, Col, Empty, List, Row, Select, Skeleton, Space, Statistic, Tag, Typography } from 'antd'
import { AlertOutlined, BarChartOutlined, TeamOutlined, WarningOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { analyticsAPI, courseAPI, getErrorMessage } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type Course = { id: number; name: string; code: string }
type Student = { id: number; username: string; full_name: string; email: string }
type StudentMasteryItem = {
  knowledge_unit?: { id: number; name: string; difficulty?: number }
  mastery?: number
  mastery_score?: number
  score?: number
  label?: string
  name?: string
}
type WeakPointItem = {
  knowledge_unit_id: number
  name: string
  mastery_score: number
  attempt_count: number
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
  severity?: 'high' | 'medium' | 'low'
  message?: string
  student_id?: number
  details?: { knowledge_unit_name?: string; mastery_score?: number; threshold?: number }
}

const toPercent = (value?: number) => {
  const numeric = Number(value ?? 0)
  return Math.round(numeric <= 1 ? numeric * 100 : numeric)
}

const alertType = (item: AlertItem): 'error' | 'warning' | 'info' => {
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
    label: item.knowledge_unit?.name || item.label || item.name || '未命名知识点',
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
  const [weakPoints, setWeakPoints] = useState<WeakPointItem[]>([])
  const [classReport, setClassReport] = useState<ClassReport | null>(null)
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [studentAlerts, setStudentAlerts] = useState<AlertItem[]>([])
  const [classAlerts, setClassAlerts] = useState<AlertItem[]>([])
  const [loading, setLoading] = useState(false)
  const [pageError, setPageError] = useState<string | null>(null)

  const radarOption = useMemo(() => buildRadarOption(mastery), [mastery])
  const classBarOption = useMemo(() => buildClassBarOption(classReport?.by_knowledge_unit || []), [classReport])

  const loadStudentSlice = async (courseId: number, studentId: number) => {
    const [masteryRes, weakRes, studentAlertsRes] = await Promise.all([
      analyticsAPI.getStudentMastery(studentId, courseId),
      analyticsAPI.getWeakPoints(studentId, courseId),
      analyticsAPI.getAlerts(courseId, studentId),
    ])
    setMastery(mapMastery(masteryRes.data || []))
    setWeakPoints(weakRes.data || [])
    setStudentAlerts(studentAlertsRes.data || [])
  }

  const loadTeacherAnalytics = async (courseId: number, studentId?: number) => {
    const [reportRes, classAlertsRes, studentsRes] = await Promise.all([
      analyticsAPI.getClassReport(courseId),
      analyticsAPI.getAlerts(courseId),
      courseAPI.listStudents(courseId),
    ])

    const nextStudents = studentsRes.data || []
    const activeStudentId = studentId || selectedStudentId || nextStudents[0]?.id
    setStudents(nextStudents)
    setSelectedStudentId(activeStudentId)
    setClassReport(reportRes.data)
    setClassAlerts(classAlertsRes.data || [])

    if (activeStudentId) {
      const studentAlertsRes = await analyticsAPI.getAlerts(courseId, activeStudentId)
      setStudentAlerts(studentAlertsRes.data || [])
    } else {
      setStudentAlerts([])
    }

    if (activeStudentId) {
      await loadStudentSlice(courseId, activeStudentId)
    } else {
      setMastery([])
      setWeakPoints([])
    }
  }

  const loadData = async (courseId?: number, studentId?: number) => {
    if (!user) return
    const activeCourseId = courseId || selectedCourseId || courses[0]?.id
    if (!activeCourseId) return

    setLoading(true)
    setPageError(null)
    try {
      if (isTeacher) {
        await loadTeacherAnalytics(activeCourseId, studentId)
      } else if (user.id) {
        await loadStudentSlice(activeCourseId, user.id)
      }
    } catch (error) {
      setPageError(getErrorMessage(error, '学情数据加载失败'))
      setMastery([])
      setWeakPoints([])
      setAlerts([])
      setClassReport(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const { data } = await courseAPI.list()
        setCourses(data || [])
        const firstId = data?.[0]?.id
        if (firstId) {
          setSelectedCourseId(firstId)
          await loadData(firstId)
        }
      } catch (error) {
        setPageError(getErrorMessage(error, '课程列表加载失败'))
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
                if (selectedCourseId) void loadData(selectedCourseId, value)
              }}
            />
          </Space>
        </Space>

        {pageError && <Alert type="error" showIcon style={{ marginBottom: 16 }} message={pageError} />}

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

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={10}>
            <Card title="当前薄弱点" loading={loading} style={{ borderRadius: 8 }}>
              {weakPoints.length === 0 ? (
                <Empty description="暂无薄弱点" />
              ) : (
                <List
                  dataSource={weakPoints}
                  renderItem={(item) => (
                    <List.Item>
                      <div style={{ width: '100%' }}>
                        <div style={{ fontWeight: 600 }}>{item.name}</div>
                        <div style={{ color: '#666' }}>掌握度 {Math.round(item.mastery_score * 100)}% · 作答次数 {item.attempt_count}</div>
                      </div>
                    </List.Item>
                  )}
                />
              )}
            </Card>
          </Col>
          <Col xs={24} lg={14}>
            <Card title="学习预警" loading={loading} style={{ borderRadius: 8 }}>
              {(selectedStudentId ? studentAlerts : classAlerts).length === 0 ? (
                <Empty description={selectedStudentId ? '暂无该学生预警信息' : '暂无预警信息'} />
              ) : (
                <List
                  dataSource={selectedStudentId ? studentAlerts : classAlerts}
                  renderItem={(item) => (
                    <List.Item>
                      <Alert
                        type={alertType(item)}
                        showIcon
                        message={`学生 ${item.student_id ?? ''} · ${item.details?.knowledge_unit_name || '知识点预警'}`}
                        description={item.message || '暂无详细说明'}
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

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>我的学情</Typography.Title>
        {courseSelect}
      </Space>

      {pageError && <Alert type="error" showIcon style={{ marginBottom: 16 }} message={pageError} />}

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
          <Card title="当前薄弱点与预警" loading={loading} style={{ borderRadius: 8 }}>
            {weakPoints.length === 0 && alerts.length === 0 ? (
              <Empty description="暂无薄弱点或预警" />
            ) : (
              <div style={{ display: 'grid', gap: 12 }}>
                {weakPoints.length > 0 && (
                  <Alert
                    type="warning"
                    showIcon
                    message="薄弱点"
                    description={weakPoints.map((item) => `${item.name}（掌握度 ${Math.round(item.mastery_score * 100)}%）`).join('；')}
                  />
                )}
                {alerts.map((item) => (
                  <Alert
                    key={item.id}
                    type={alertType(item)}
                    showIcon
                    message={item.details?.knowledge_unit_name || '学习提醒'}
                    description={item.message || '暂无详细说明'}
                  />
                ))}
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

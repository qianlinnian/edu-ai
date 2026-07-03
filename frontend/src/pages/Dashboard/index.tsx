import { useEffect, useMemo, useState } from 'react'
import { Alert, Card, Col, Empty, List, Row, Select, Skeleton, Statistic, Tag } from 'antd'
import {
  BookOutlined, TeamOutlined, FileTextOutlined, AlertOutlined,
  CheckCircleOutlined, ClockCircleOutlined, FireOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { analyticsAPI, assignmentAPI, courseAPI } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type StudentTodo = { id: number; name: string; course: string; ddl?: string }
type Course = { id: number; name: string; code?: string; description?: string | null; domain?: string }
type MasteryItem = {
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

const toPercent = (value?: number) => {
  const numeric = Number(value ?? 0)
  return Math.round(numeric <= 1 ? numeric * 100 : numeric)
}



const buildStudentRadarOption = (items: { label: string; value: number }[]) => ({
  tooltip: {},
  radar: {
    indicator: items.map((item) => ({ name: item.label, max: 100 })),
    radius: 90,
    axisName: { color: '#555', fontSize: 12 },
  },
  series: [{
    type: 'radar',
    data: [{
      value: items.map((item) => item.value),
      name: '我的掌握度',
      itemStyle: { color: '#00a8ff' },
      areaStyle: { color: 'rgba(0,168,255,0.15)' },
    }],
  }],
})

export default function Dashboard() {
  const user = useAuthStore(s => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  // 教师端数据
  const [teacherCourses, setTeacherCourses] = useState<Course[]>([])
  const [teacherSelectedCourseId, setTeacherSelectedCourseId] = useState<number | undefined>()
  const [classReport, setClassReport] = useState<ClassReport | null>(null)
  const [classAlerts, setClassAlerts] = useState<{ id?: number; severity?: 'high' | 'medium' | 'low'; message?: string; student_id?: number; details?: { knowledge_unit_name?: string } }[]>([])
  const [classStudentCount, setClassStudentCount] = useState(0)
  const [teacherLoading, setTeacherLoading] = useState(false)

  // 学生端数据
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>()
  const [mastery, setMastery] = useState<{ label: string; value: number }[]>([])
  const [alerts, setAlerts] = useState<{ id?: number; level?: 'error' | 'warning' | 'info'; message?: string; title?: string; content?: string; student_name?: string }[]>([])
  const [studentTodosReal, setStudentTodosReal] = useState<StudentTodo[]>([])
  const [studentLoading, setStudentLoading] = useState(false)

  const buildClassBarOption = (items: ClassReport['by_knowledge_unit']) => ({
    tooltip: { trigger: 'axis' },
    grid: { top: 20, right: 20, bottom: 55, left: 50 },
    xAxis: { type: 'category', data: items.map(i => i.name), axisLabel: { rotate: 15, fontSize: 11 } },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{
      name: '平均掌握度', type: 'bar',
      data: items.map(i => toPercent(i.avg_mastery)),
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

  const loadTeacherDashboard = async (courseId?: number) => {
    const activeCourseId = courseId || teacherSelectedCourseId
    if (!activeCourseId) return
    setTeacherLoading(true)
    try {
      const [reportRes, alertsRes, studentsRes] = await Promise.all([
        analyticsAPI.getClassReport(activeCourseId).catch(() => ({ data: null })),
        analyticsAPI.getAlerts(activeCourseId).catch(() => ({ data: [] })),
        courseAPI.listStudents(activeCourseId).catch(() => ({ data: [] })),
      ])
      setClassReport(reportRes.data)
      setClassAlerts(alertsRes.data || [])
      setClassStudentCount(Array.isArray(studentsRes.data) ? studentsRes.data.length : 0)
    } catch {
      // non-fatal
    } finally {
      setTeacherLoading(false)
    }
  }

  const loadStudentDashboard = async (courseId?: number, courseList?: Course[]) => {
    if (!user) return
    const activeCourseId = courseId || selectedCourseId || courseList?.[0]?.id
    if (!activeCourseId) return

    setStudentLoading(true)
    try {
      const [masteryRes, alertsRes, assignmentRes] = await Promise.all([
        analyticsAPI.getStudentMastery(user.id, activeCourseId).catch(() => ({ data: [] })),
        analyticsAPI.getAlerts(activeCourseId).catch(() => ({ data: [] })),
        assignmentAPI.list(activeCourseId).catch(() => ({ data: [] })),
      ])
      const mappedMastery = (masteryRes.data || []).map((item: MasteryItem) => ({
        label: item.knowledge_unit?.name || item.knowledge_point || item.label || item.name || `知识点 ${item.knowledge_point_id ?? item.knowledge_unit?.id ?? ''}`,
        value: toPercent(item.mastery_score ?? item.mastery ?? item.score),
      }))
      const sourceCourses = courseList || courses
      const mappedTodos = (assignmentRes.data || []).map((item: any) => ({
        id: item.id,
        name: item.title,
        course: sourceCourses.find((course) => course.id === activeCourseId)?.name || `课程 ${activeCourseId}`,
        ddl: item.due_date ? new Date(item.due_date).toLocaleDateString() : '未设置',
      }))
      setMastery(mappedMastery)
      setAlerts(alertsRes.data || [])
      setStudentTodosReal(mappedTodos)
    } finally {
      setStudentLoading(false)
    }
  }

  const studentRadarOption = useMemo(
    () => buildStudentRadarOption(mastery.length ? mastery : [{ label: '暂无数据', value: 0 }]),
    [mastery],
  )

  useEffect(() => {
    if (!isTeacher) return
    const bootstrap = async () => {
      try {
        const { data } = await courseAPI.list()
        setTeacherCourses(data || [])
        if (data?.[0]?.id) {
          setTeacherSelectedCourseId(data[0].id)
          await loadTeacherDashboard(data[0].id)
        }
      } catch { /* non-fatal */ }
    }
    void bootstrap()
  }, [isTeacher])

  useEffect(() => {
    if (isTeacher) return
    const bootstrap = async () => {
      const { data } = await courseAPI.list().catch(() => ({ data: [] }))
      setCourses(data)
      const firstId = data?.[0]?.id
      if (firstId) {
        setSelectedCourseId(firstId)
        await loadStudentDashboard(firstId, data)
      }
    }
    void bootstrap()
  }, [isTeacher])

  if (isTeacher) {
    const average = toPercent(classReport?.overall_avg_mastery)
    const barOption = classReport?.by_knowledge_unit?.length
      ? buildClassBarOption(classReport.by_knowledge_unit)
      : { tooltip: {}, xAxis: {}, yAxis: {}, series: [] }
    return (
      <div>
        <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: '#1a1a1a' }}>
            👋 你好，{user?.full_name}！
          </span>
          <Select
            style={{ width: 240 }}
            placeholder="选择课程查看学情"
            options={teacherCourses.map(c => ({ value: c.id, label: `${c.name}（${c.code || ''}）` }))}
            value={teacherSelectedCourseId}
            onChange={(id) => { setTeacherSelectedCourseId(id); void loadTeacherDashboard(id) }}
          />
          <span style={{ fontSize: 14, color: '#999' }}>
            {classReport ? `班级平均掌握度 ${average}%` : '已接入真实学情数据'}
          </span>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#e6f7ff,#bae7ff)' }}>
              <Statistic title="管理课程" value={teacherCourses.length || classReport ? 1 : 0}
                prefix={<BookOutlined style={{ color: '#00a8ff' }} />}
                valueStyle={{ color: '#00a8ff', fontWeight: 700 }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#f6ffed,#d9f7be)' }}>
              <Statistic title="在籍学生" value={classStudentCount}
                prefix={<TeamOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a', fontWeight: 700 }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fffbe6,#fff1b8)' }}>
              <Statistic title="班级平均掌握度" value={average}
                suffix="%"
                prefix={<FileTextOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: '#faad14', fontWeight: 700 }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fff1f0,#ffccc7)' }}>
              <Statistic title="学情预警" value={classAlerts.length}
                prefix={<AlertOutlined style={{ color: '#ff4d4f' }} />}
                valueStyle={{ color: '#ff4d4f', fontWeight: 700 }} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={10}>
            <Card title="班级知识点平均掌握度" bordered={false} style={{ borderRadius: 12 }} loading={teacherLoading}>
              {classReport?.by_knowledge_unit?.length ? (
                <ReactECharts option={barOption} style={{ height: 220 }} />
              ) : (
                <Empty description="暂无班级学情数据" />
              )}
            </Card>
          </Col>
          <Col xs={24} lg={14}>
            <Card title="⚠️ 学情预警" bordered={false} style={{ borderRadius: 12 }} loading={teacherLoading}>
              {classAlerts.length === 0 ? (
                <Empty description="暂无预警信息" />
              ) : (
                <List
                  dataSource={classAlerts}
                  renderItem={item => (
                    <List.Item style={{ padding: '6px 0' }}>
                      <Alert
                        type={item.severity === 'high' ? 'error' : item.severity === 'medium' ? 'warning' : 'info'}
                        message={`学生 ${item.student_id ?? ''} — ${item.details?.knowledge_unit_name || '知识点预警'}`}
                        description={item.message || '暂无详细说明'}
                        style={{ width: '100%', borderRadius: 8 }}
                        showIcon
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

  // 学生视角
return (
  <div>
    <div style={{ marginBottom: 24 }}>
      <span style={{ fontSize: 22, fontWeight: 700, color: '#1a1a1a' }}>
        👋 你好，{user?.full_name}！
      </span>
      <span style={{ fontSize: 14, color: '#999', marginLeft: 12 }}>
        已为你接入真实学情与预警信息
      </span>
    </div>

    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#e6f7ff,#bae7ff)' }}>
          <Statistic title="选修课程" value={courses.length}
            prefix={<BookOutlined style={{ color: '#00a8ff' }} />}
            valueStyle={{ color: '#00a8ff', fontWeight: 700 }} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fff1f0,#ffccc7)' }}>
          <Statistic title="学习预警" value={alerts.length}
            prefix={<ClockCircleOutlined style={{ color: '#ff4d4f' }} />}
            valueStyle={{ color: '#ff4d4f', fontWeight: 700 }} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#f6ffed,#d9f7be)' }}>
          <Statistic title="已评估知识点" value={mastery.length}
            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            valueStyle={{ color: '#52c41a', fontWeight: 700 }} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fffbe6,#fff1b8)' }}>
          <Statistic title="薄弱知识点" value={mastery.filter((item) => item.value < 60).length}
            prefix={<FireOutlined style={{ color: '#faad14' }} />}
            valueStyle={{ color: '#faad14', fontWeight: 700 }}
            suffix="个" />
        </Card>
      </Col>
    </Row>

    <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
      <Col xs={24} lg={10}>
        <Card title="📊 我的知识掌握雷达" bordered={false} style={{ borderRadius: 12 }} extra={<Select style={{ width: 220 }} options={courses.map((course) => ({ value: course.id, label: `${course.name}（${course.code}）` }))} value={selectedCourseId} onChange={(value) => { setSelectedCourseId(value); void loadStudentDashboard(value) }} />}>
          {studentLoading ? <Skeleton active paragraph={{ rows: 6 }} /> : mastery.length === 0 ? <Empty description="暂无掌握度数据" /> : <ReactECharts option={studentRadarOption} style={{ height: 260 }} />}
          {mastery.length > 0 && (
            <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {mastery.map((item) => <Tag key={item.label} color={item.value >= 80 ? 'success' : item.value >= 60 ? 'warning' : 'error'}>{item.label} {item.value}%</Tag>)}
            </div>
          )}
        </Card>
      </Col>
      <Col xs={24} lg={14}>
        <Card title="📝 待提交作业" bordered={false} style={{ borderRadius: 12 }}>
          {studentLoading ? <Skeleton active paragraph={{ rows: 4 }} /> : (
            <List
              dataSource={studentTodosReal}
              locale={{ emptyText: <Empty description="当前课程暂无作业" /> }}
              renderItem={item => (
                <List.Item actions={[<Tag color="red">截止 {item.ddl}</Tag>]}> 
                  <List.Item.Meta
                    avatar={<ClockCircleOutlined style={{ fontSize: 24, color: '#faad14', marginTop: 4 }} />}
                    title={item.name}
                    description={item.course}
                  />
                </List.Item>
              )}
            />
          )}
        </Card>

        <Card title="⚠️ 学习预警" bordered={false} style={{ borderRadius: 12, marginTop: 16 }}>
          {studentLoading ? <Skeleton active paragraph={{ rows: 4 }} /> : alerts.length === 0 ? <Empty description="暂无预警信息" /> : (
            <List
              dataSource={alerts}
              renderItem={(item) => (
                <List.Item style={{ padding: '6px 0' }}>
                  <Alert
                    type={item.level || 'warning'}
                    message={item.title || item.student_name || '学习提醒'}
                    description={item.message || item.content || '暂无详细说明'}
                    style={{ width: '100%', borderRadius: 8 }}
                    showIcon
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

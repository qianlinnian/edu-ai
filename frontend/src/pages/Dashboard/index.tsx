import { Card, Row, Col, Statistic, List, Tag, Progress, Alert } from 'antd'
import {
  BookOutlined, TeamOutlined, FileTextOutlined, AlertOutlined,
  CheckCircleOutlined, ClockCircleOutlined, FireOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { useAuthStore } from '../../hooks/useAuthStore'

const submitTrendOption = {
  tooltip: { trigger: 'axis' },
  grid: { top: 20, right: 20, bottom: 30, left: 40 },
  xAxis: {
    type: 'category',
    data: ['3/20', '3/21', '3/22', '3/23', '3/24', '3/25', '3/26'],
  },
  yAxis: { type: 'value' },
  series: [{
    name: '提交数', type: 'line', smooth: true,
    data: [12, 8, 25, 18, 30, 22, 28],
    itemStyle: { color: '#00a8ff' },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0,168,255,0.3)' },
          { offset: 1, color: 'rgba(0,168,255,0.02)' },
        ],
      },
    },
  }],
}

const masteryBarOption = {
  tooltip: { trigger: 'axis' },
  grid: { top: 20, right: 20, bottom: 55, left: 50 },
  xAxis: {
    type: 'category',
    data: ['Python基础', '循环结构', '函数', '递归', '列表操作', '面向对象'],
    axisLabel: { rotate: 15, fontSize: 11 },
  },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [{
    name: '掌握度', type: 'bar',
    data: [92, 61, 85, 45, 78, 66],
    itemStyle: {
      borderRadius: [6, 6, 0, 0],
      color: (params: any) => {
        if (params.value >= 80) return '#52c41a'
        if (params.value >= 60) return '#faad14'
        return '#ff4d4f'
      },
    },
  }],
}

const studentRadarOption = {
  tooltip: {},
  radar: {
    indicator: [
      { name: 'Python基础', max: 100 },
      { name: '循环结构', max: 100 },
      { name: '函数', max: 100 },
      { name: '递归', max: 100 },
      { name: '列表操作', max: 100 },
    ],
    radius: 90,
    axisName: { color: '#555', fontSize: 12 },
  },
  series: [{
    type: 'radar',
    data: [{
      value: [92, 63, 85, 42, 78],
      name: '我的掌握度',
      itemStyle: { color: '#00a8ff' },
      areaStyle: { color: 'rgba(0,168,255,0.15)' },
    }],
  }],
}

const recentAlerts = [
  { name: '张三', issue: '循环结构掌握度 30%，连续3次作业不及格', level: 'error' as const },
  { name: '王五', issue: '近2周未提交作业，递归知识薄弱', level: 'error' as const },
  { name: '李四', issue: '函数定义掌握度 45%，成绩下降趋势', level: 'warning' as const },
]

const recentAssignments = [
  { name: 'Python循环练习', course: 'Python程序设计', submitted: 12, total: 30, ddl: '04-10' },
  { name: '递归作业', course: 'Python程序设计', submitted: 5, total: 30, ddl: '04-15' },
  { name: '链表实现', course: '数据结构', submitted: 20, total: 25, ddl: '04-12' },
]

const studentTodos = [
  { name: 'Python循环练习', course: 'Python程序设计', ddl: '04-10' },
  { name: '数据结构链表', course: '数据结构', ddl: '04-12' },
]

const knowledgeProgress = [
  { label: 'Python基础', val: 92, color: '#52c41a' },
  { label: '循环结构', val: 63, color: '#faad14' },
  { label: '函数定义', val: 85, color: '#52c41a' },
  { label: '递归算法', val: 42, color: '#ff4d4f' },
]

export default function Dashboard() {
  const user = useAuthStore(s => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  if (isTeacher) {
    return (
      <div>
        <div style={{ marginBottom: 24 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: '#1a1a1a' }}>
            👋 你好，{user?.full_name}！
          </span>
          <span style={{ fontSize: 14, color: '#999', marginLeft: 12 }}>
            今天共有 15 份作业待批改
          </span>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#e6f7ff,#bae7ff)' }}>
              <Statistic title="管理课程" value={3}
                prefix={<BookOutlined style={{ color: '#00a8ff' }} />}
                valueStyle={{ color: '#00a8ff', fontWeight: 700 }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#f6ffed,#d9f7be)' }}>
              <Statistic title="在籍学生" value={128}
                prefix={<TeamOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a', fontWeight: 700 }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fffbe6,#fff1b8)' }}>
              <Statistic title="待批改作业" value={15}
                prefix={<FileTextOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: '#faad14', fontWeight: 700 }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fff1f0,#ffccc7)' }}>
              <Statistic title="学情预警" value={5}
                prefix={<AlertOutlined style={{ color: '#ff4d4f' }} />}
                valueStyle={{ color: '#ff4d4f', fontWeight: 700 }} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={14}>
            <Card title="近7天作业提交趋势" bordered={false} style={{ borderRadius: 12 }}>
              <ReactECharts option={submitTrendOption} style={{ height: 220 }} />
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title="班级知识掌握度" bordered={false} style={{ borderRadius: 12 }}>
              <ReactECharts option={masteryBarOption} style={{ height: 220 }} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={12}>
            <Card title="⚠️ 学情预警" bordered={false} style={{ borderRadius: 12 }}>
              <List
                dataSource={recentAlerts}
                renderItem={item => (
                  <List.Item style={{ padding: '6px 0' }}>
                    <Alert
                      type={item.level}
                      message={<span><strong>{item.name}</strong> — {item.issue}</span>}
                      style={{ width: '100%', borderRadius: 8 }}
                      showIcon
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="📋 近期作业进度" bordered={false} style={{ borderRadius: 12 }}>
              <List
                dataSource={recentAssignments}
                renderItem={item => (
                  <List.Item style={{ flexDirection: 'column', alignItems: 'stretch', padding: '8px 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontWeight: 500 }}>{item.name}</span>
                      <Tag color="blue">截止 {item.ddl}</Tag>
                    </div>
                    <Progress
                      percent={Math.round(item.submitted / item.total * 100)}
                      format={() => `${item.submitted}/${item.total}`}
                      strokeColor="#00a8ff"
                      size="small"
                    />
                  </List.Item>
                )}
              />
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
          今天有 2 份作业待提交
        </span>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#e6f7ff,#bae7ff)' }}>
            <Statistic title="选修课程" value={4}
              prefix={<BookOutlined style={{ color: '#00a8ff' }} />}
              valueStyle={{ color: '#00a8ff', fontWeight: 700 }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fff1f0,#ffccc7)' }}>
            <Statistic title="待交作业" value={2}
              prefix={<ClockCircleOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f', fontWeight: 700 }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#f6ffed,#d9f7be)' }}>
            <Statistic title="已完成作业" value={12}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a', fontWeight: 700 }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ borderRadius: 12, background: 'linear-gradient(135deg,#fffbe6,#fff1b8)' }}>
            <Statistic title="薄弱知识点" value={3}
              prefix={<FireOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14', fontWeight: 700 }}
              suffix="个" />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={10}>
          <Card title="📊 我的知识掌握雷达" bordered={false} style={{ borderRadius: 12 }}>
            <ReactECharts option={studentRadarOption} style={{ height: 260 }} />
            <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Tag color="orange">循环结构 63% 需加强</Tag>
              <Tag color="red">递归 42% 需加强</Tag>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="📝 待提交作业" bordered={false} style={{ borderRadius: 12 }}>
            <List
              dataSource={studentTodos}
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
          </Card>

          <Card title="📈 知识点掌握进度" bordered={false} style={{ borderRadius: 12, marginTop: 16 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {knowledgeProgress.map(k => (
                <div key={k.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 13 }}>
                    <span>{k.label}</span>
                    <span style={{ color: k.color, fontWeight: 600 }}>{k.val}%</span>
                  </div>
                  <Progress percent={k.val} strokeColor={k.color} showInfo={false} size="small" />
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

import { Card, Row, Col, Select, List, Alert, Tag, Avatar, Divider } from 'antd'
import { AlertOutlined, UserOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { useAuthStore } from '../../hooks/useAuthStore'

const COURSES = [
  { value: 1, label: 'Python程序设计' },
  { value: 2, label: '数据结构' },
]

const radarOption = {
  tooltip: {},
  radar: {
    indicator: [
      { name: '变量与类型', max: 100 },
      { name: '循环结构', max: 100 },
      { name: '函数', max: 100 },
      { name: '递归', max: 100 },
      { name: '列表操作', max: 100 },
      { name: '面向对象', max: 100 },
    ],
    radius: 110,
    axisName: { color: '#555', fontSize: 12 },
  },
  series: [{
    type: 'radar',
    data: [{
      value: [95, 61, 85, 45, 78, 66],
      name: '班级平均',
      itemStyle: { color: '#00a8ff' },
      areaStyle: { color: 'rgba(0,168,255,0.15)' },
      lineStyle: { color: '#00a8ff', width: 2 },
    }],
  }],
}

const heatmapData = [
  [0, 0, 95], [0, 1, 61], [0, 2, 85], [0, 3, 45], [0, 4, 78],
  [1, 0, 88], [1, 1, 55], [1, 2, 90], [1, 3, 38], [1, 4, 82],
  [2, 0, 72], [2, 1, 48], [2, 2, 76], [2, 3, 30], [2, 4, 65],
  [3, 0, 98], [3, 1, 75], [3, 2, 92], [3, 3, 60], [3, 4, 88],
]

const heatmapOption = {
  tooltip: { formatter: (p: any) => `${['张三','李四','王五','赵六'][p.data[0]]} · ${['变量','循环','函数','递归','列表'][p.data[1]]}: ${p.data[2]}%` },
  grid: { top: 30, right: 20, bottom: 60, left: 80 },
  xAxis: { type: 'category', data: ['变量与类型', '循环结构', '函数', '递归', '列表操作'], axisLabel: { rotate: 15, fontSize: 11 } },
  yAxis: { type: 'category', data: ['张三', '李四', '王五', '赵六'] },
  visualMap: { min: 0, max: 100, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
    inRange: { color: ['#ffccc7', '#fff1b8', '#d9f7be', '#52c41a'] } },
  series: [{ type: 'heatmap', data: heatmapData, label: { show: true, fontSize: 11 } }],
}

const trendOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: ['张三', '李四', '王五', '赵六'], top: 0 },
  grid: { top: 40, right: 20, bottom: 30, left: 40 },
  xAxis: { type: 'category', data: ['作业1', '作业2', '作业3', '作业4', '作业5'] },
  yAxis: { type: 'value', max: 100 },
  series: [
    { name: '张三', type: 'line', smooth: true, data: [75, 80, 82, 85, 88], itemStyle: { color: '#00a8ff' } },
    { name: '李四', type: 'line', smooth: true, data: [68, 65, 70, 72, 74], itemStyle: { color: '#faad14' } },
    { name: '王五', type: 'line', smooth: true, data: [55, 50, 48, 52, 58], itemStyle: { color: '#ff4d4f' } },
    { name: '赵六', type: 'line', smooth: true, data: [88, 90, 91, 92, 95], itemStyle: { color: '#52c41a' } },
  ],
}

const studentRadar = {
  tooltip: {},
  radar: {
    indicator: [
      { name: '变量与类型', max: 100 }, { name: '循环结构', max: 100 },
      { name: '函数', max: 100 }, { name: '递归', max: 100 }, { name: '列表操作', max: 100 },
    ],
    radius: 100, axisName: { color: '#555', fontSize: 12 },
  },
  series: [{
    type: 'radar',
    data: [{ value: [92, 63, 85, 42, 78], name: '我的掌握度', itemStyle: { color: '#6366f1' }, areaStyle: { color: 'rgba(99,102,241,0.15)' } }],
  }],
}

const ALERTS = [
  { name: '张三', avatar: '张', issue: '循环结构掌握度 30%，连续3次作业不及格', level: 'error' as const, color: '#ff4d4f' },
  { name: '王五', avatar: '王', issue: '近2周未提交作业，递归知识薄弱', level: 'error' as const, color: '#ff4d4f' },
  { name: '李四', avatar: '李', issue: '函数定义掌握度 45%，成绩下降趋势', level: 'warning' as const, color: '#faad14' },
  { name: '赵六', avatar: '赵', issue: '列表操作正确率低，练习频率不足', level: 'warning' as const, color: '#faad14' },
]

export default function Analytics() {
  const user = useAuthStore(s => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  if (!isTeacher) {
    return (
      <div>
        <div style={{ marginBottom: 24, fontSize: 20, fontWeight: 700 }}>我的学情</div>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={10}>
            <Card title="个人知识掌握雷达" bordered={false} style={{ borderRadius: 12 }}>
              <ReactECharts option={studentRadar} style={{ height: 280 }} />
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                <Tag color="orange">循环结构 63% 需加强</Tag>
                <Tag color="red">递归 42% 需加强</Tag>
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={14}>
            <Card title="学习建议" bordered={false} style={{ borderRadius: 12 }}>
              <Alert type="warning" showIcon message="你在循环结构方面较薄弱，建议完成相关练习" style={{ borderRadius: 8, marginBottom: 12 }} />
              <Alert type="error" showIcon message="递归算法掌握度偏低，推荐观看第5章教学视频" style={{ borderRadius: 8, marginBottom: 12 }} />
              <Alert type="success" showIcon message="变量与类型掌握优秀，继续保持！" style={{ borderRadius: 8 }} />
            </Card>
          </Col>
        </Row>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <span style={{ fontSize: 20, fontWeight: 700 }}>学情分析</span>
        <Select defaultValue={1} options={COURSES} style={{ width: 200 }} />
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={11}>
          <Card title="班级知识掌握雷达" bordered={false} style={{ borderRadius: 12 }}>
            <ReactECharts option={radarOption} style={{ height: 280 }} />
          </Card>
        </Col>
        <Col xs={24} lg={13}>
          <Card title="学生×知识点 掌握度热力图" bordered={false} style={{ borderRadius: 12 }}>
            <ReactECharts option={heatmapOption} style={{ height: 280 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="成绩趋势" bordered={false} style={{ borderRadius: 12 }}>
            <ReactECharts option={trendOption} style={{ height: 240 }} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            title={<span><AlertOutlined style={{ color: '#ff4d4f', marginRight: 6 }} />学情预警</span>}
            bordered={false} style={{ borderRadius: 12 }}
          >
            <List
              dataSource={ALERTS}
              renderItem={item => (
                <List.Item style={{ padding: '6px 0' }}>
                  <Alert
                    type={item.level}
                    showIcon
                    message={
                      <span>
                        <Avatar size="small" style={{ background: item.color, marginRight: 6 }}>{item.avatar}</Avatar>
                        <strong>{item.name}</strong> — {item.issue}
                      </span>
                    }
                    style={{ width: '100%', borderRadius: 8 }}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      <Card title="📊 班级共性错误分析报告" bordered={false} style={{ borderRadius: 12, marginTop: 16 }}>
        <div style={{ fontSize: 14, lineHeight: 2 }}>
          <div>1. <strong>62%</strong> 学生在「递归终止条件」题目出错</div>
          <div>2. <strong>45%</strong> 学生混淆「形参」与「实参」概念</div>
          <div>3. <strong>38%</strong> 学生在「列表切片」索引方向上出现偏差</div>
        </div>
        <Divider />
        <div style={{ fontWeight: 600, marginBottom: 8 }}>💡 AI 教学建议</div>
        <div style={{ fontSize: 14, lineHeight: 1.9, color: '#444' }}>
          - 建议增加递归专题练习，使用调用栈可视化工具辅助讲解<br />
          - 函数参数部分建议增加形参/实参对比练习<br />
          - 列表切片建议以图示方式进行专题讲解
        </div>
      </Card>
    </div>
  )
}

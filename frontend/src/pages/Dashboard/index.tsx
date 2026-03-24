import { Card, Row, Col, Statistic } from 'antd'
import { BookOutlined, TeamOutlined, FileTextOutlined, AlertOutlined } from '@ant-design/icons'

export default function Dashboard() {
  return (
    <div>
      <h2>仪表盘</h2>
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="课程数" value={3} prefix={<BookOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="学生数" value={128} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="待批改作业" value={15} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="学情预警" value={5} prefix={<AlertOutlined />} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>
      {/* TODO: 添加图表和更多统计 */}
    </div>
  )
}

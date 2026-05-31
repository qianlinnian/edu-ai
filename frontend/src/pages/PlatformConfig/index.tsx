import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Form, Input, Row, Select, Space, Tag, Typography, message } from 'antd'
import { ApiOutlined, CheckCircleOutlined, CopyOutlined } from '@ant-design/icons'
import { courseAPI, getErrorMessage, platformAPI } from '../../services/api'

type PlatformStatus = {
  connected: boolean
  lastTest?: string
  widgetUrl?: string
}

type CourseOption = {
  id: number
  name: string
}

export default function PlatformConfig() {
  const [chaoxingStatus, setChaoxingStatus] = useState<PlatformStatus>({ connected: false })
  const [dingtalkStatus, setDingtalkStatus] = useState<PlatformStatus>({ connected: false })
  const [chaoxingSaving, setChaoxingSaving] = useState(false)
  const [dingtalkSaving, setDingtalkSaving] = useState(false)
  const [testing, setTesting] = useState<'chaoxing' | 'dingtalk' | null>(null)
  const [courses, setCourses] = useState<CourseOption[]>([])
  const [selectedCourse, setSelectedCourse] = useState<number>()
  const [chaoxingForm] = Form.useForm()
  const [dingtalkForm] = Form.useForm()

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const { data } = await courseAPI.list()
        setCourses(data)
        if (data.length > 0) {
          setSelectedCourse(data[0].id)
        }
      } catch (error) {
        message.error(getErrorMessage(error, '加载课程列表失败'))
      }
    }

    void loadCourses()
  }, [])

  const widgetUrl = useMemo(() => {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'https://your-domain.com'
    return `${origin}/widget/chat?course=${selectedCourse ?? 1}&token=YOUR_TOKEN`
  }, [selectedCourse])

  const iframeCode = useMemo(
    () => `<iframe\n  src="${widgetUrl}"\n  width="400"\n  height="600"\n  frameborder="0">\n</iframe>`,
    [widgetUrl]
  )

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }

  const saveConnection = async (platform: 'chaoxing' | 'dingtalk') => {
    const form = platform === 'chaoxing' ? chaoxingForm : dingtalkForm
    const setSaving = platform === 'chaoxing' ? setChaoxingSaving : setDingtalkSaving
    const label = platform === 'chaoxing' ? '超星' : '钉钉'

    try {
      const values = await form.validateFields()
      setSaving(true)
      await platformAPI.createConnection({
        platform_type: platform,
        name: values.name || `${label} 演示连接`,
        config: platform === 'chaoxing'
          ? {
              lti_key: values.lti_key,
              lti_secret: values.lti_secret,
              callback_url: values.callback_url,
            }
          : {
              app_key: values.app_key,
              app_secret: values.app_secret,
              agent_id: values.agent_id,
            },
      })
      message.success(`${label} 连接已保存`)
    } catch (error) {
      message.error(getErrorMessage(error, `保存${label}连接失败`))
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async (platform: 'chaoxing' | 'dingtalk') => {
    if (!selectedCourse) {
      message.warning('请先选择课程')
      return
    }

    setTesting(platform)
    try {
      if (platform === 'chaoxing') {
        const { data } = await platformAPI.launchChaoxing({
          course: selectedCourse,
          token: 'EMBED_DEMO_TOKEN',
          role: 'student',
        })
        setChaoxingStatus({
          connected: true,
          lastTest: new Date().toLocaleString(),
          widgetUrl: data.widget_url,
        })
        message.success('超星连接测试成功')
      } else {
        const { data } = await platformAPI.dingtalkAuth({
          code: 'demo-code',
          course_id: selectedCourse,
        })
        setDingtalkStatus({
          connected: true,
          lastTest: new Date().toLocaleString(),
          widgetUrl: data.widget_url,
        })
        message.success('钉钉连接测试成功')
      }
    } catch (error) {
      message.error(getErrorMessage(error, '连接测试失败'))
    } finally {
      setTesting(null)
    }
  }

  return (
    <div>
      <Typography.Title level={4}>平台对接配置</Typography.Title>

      <Alert
        type="info"
        showIcon
        message="当前页已接入真实平台接口"
        description="保存会调用平台连接创建接口，测试连接会调用超星/钉钉模拟端点。嵌入 URL 仍使用演示令牌占位符，需要由上游平台在实际嵌入时下发真实 token。"
        style={{ borderRadius: 10, marginBottom: 20 }}
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <span>超星学习通</span>
                {chaoxingStatus.connected ? (
                  <Tag color="success" icon={<CheckCircleOutlined />}>已测试</Tag>
                ) : (
                  <Tag>未测试</Tag>
                )}
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 12 }}
          >
            <Form
              form={chaoxingForm}
              layout="vertical"
              initialValues={{
                name: '超星课程演示连接',
                callback_url: `${typeof window !== 'undefined' ? window.location.origin : 'https://your-domain.com'}/lti/chaoxing`,
              }}
            >
              <Form.Item label="连接名称" name="name" rules={[{ required: true, message: '请输入连接名称' }]}>
                <Input />
              </Form.Item>
              <Form.Item label="LTI Consumer Key" name="lti_key" rules={[{ required: true, message: '请输入 LTI Consumer Key' }]}>
                <Input />
              </Form.Item>
              <Form.Item label="LTI Shared Secret" name="lti_secret" rules={[{ required: true, message: '请输入 LTI Shared Secret' }]}>
                <Input.Password />
              </Form.Item>
              <Form.Item label="回调 URL" name="callback_url" rules={[{ required: true, message: '请输入回调 URL' }]}>
                <Input />
              </Form.Item>
              {chaoxingStatus.lastTest && (
                <Typography.Text type="secondary">上次测试：{chaoxingStatus.lastTest}</Typography.Text>
              )}
              {chaoxingStatus.widgetUrl && (
                <Typography.Paragraph copyable style={{ marginTop: 8, marginBottom: 12 }}>
                  {chaoxingStatus.widgetUrl}
                </Typography.Paragraph>
              )}
              <Space>
                <Button
                  loading={testing === 'chaoxing'}
                  icon={<ApiOutlined />}
                  onClick={() => void testConnection('chaoxing')}
                >
                  测试连接
                </Button>
                <Button
                  type="primary"
                  loading={chaoxingSaving}
                  onClick={() => void saveConnection('chaoxing')}
                >
                  保存
                </Button>
              </Space>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <span>钉钉</span>
                {dingtalkStatus.connected ? (
                  <Tag color="success" icon={<CheckCircleOutlined />}>已测试</Tag>
                ) : (
                  <Tag>未测试</Tag>
                )}
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 12 }}
          >
            <Form
              form={dingtalkForm}
              layout="vertical"
              initialValues={{ name: '钉钉课程演示连接' }}
            >
              <Form.Item label="连接名称" name="name" rules={[{ required: true, message: '请输入连接名称' }]}>
                <Input />
              </Form.Item>
              <Form.Item label="AppKey" name="app_key" rules={[{ required: true, message: '请输入 AppKey' }]}>
                <Input />
              </Form.Item>
              <Form.Item label="AppSecret" name="app_secret" rules={[{ required: true, message: '请输入 AppSecret' }]}>
                <Input.Password />
              </Form.Item>
              <Form.Item label="AgentId" name="agent_id" rules={[{ required: true, message: '请输入 AgentId' }]}>
                <Input />
              </Form.Item>
              {dingtalkStatus.lastTest && (
                <Typography.Text type="secondary">上次测试：{dingtalkStatus.lastTest}</Typography.Text>
              )}
              {dingtalkStatus.widgetUrl && (
                <Typography.Paragraph copyable style={{ marginTop: 8, marginBottom: 12 }}>
                  {dingtalkStatus.widgetUrl}
                </Typography.Paragraph>
              )}
              <Space>
                <Button
                  loading={testing === 'dingtalk'}
                  icon={<ApiOutlined />}
                  onClick={() => void testConnection('dingtalk')}
                >
                  测试连接
                </Button>
                <Button
                  type="primary"
                  loading={dingtalkSaving}
                  onClick={() => void saveConnection('dingtalk')}
                >
                  保存
                </Button>
              </Space>
            </Form>
          </Card>
        </Col>
      </Row>

      <Card title="嵌入式 Widget 代码生成" bordered={false} style={{ borderRadius: 12, marginTop: 16 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', marginBottom: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>选择课程</div>
            <Select
              value={selectedCourse}
              onChange={setSelectedCourse}
              style={{ width: 240 }}
              options={courses.map((item) => ({ value: item.id, label: item.name }))}
              placeholder="选择课程"
            />
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Widget URL</div>
          <div
            style={{
              background: '#f5f5f5',
              borderRadius: 8,
              padding: '10px 14px',
              fontFamily: 'monospace',
              fontSize: 13,
              color: '#333',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ wordBreak: 'break-all' }}>{widgetUrl}</span>
            <Button size="small" icon={<CopyOutlined />} onClick={() => void copyToClipboard(widgetUrl)}>
              复制
            </Button>
          </div>
        </div>

        <div>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>iframe 嵌入代码</div>
          <div style={{ position: 'relative' }}>
            <pre
              style={{
                background: '#1e1e1e',
                color: '#d4d4d4',
                padding: '14px 16px',
                borderRadius: 10,
                fontSize: 13,
                overflowX: 'auto',
                margin: 0,
              }}
            >
              {iframeCode}
            </pre>
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => void copyToClipboard(iframeCode)}
              style={{ position: 'absolute', top: 10, right: 10 }}
            >
              复制代码
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

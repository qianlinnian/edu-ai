import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Form, Input, Row, Select, Space, Tag, Typography, message } from 'antd'
import { ApiOutlined, CheckCircleOutlined, CopyOutlined } from '@ant-design/icons'
import { courseAPI, getErrorMessage, platformAPI } from '../../services/api'

type PlatformStatus = {
  connected: boolean
  lastTest?: string
  widgetUrl?: string
  tokenSource?: string
  courseIdSource?: string
  roleSource?: string
  role?: string
  upstreamReference?: string
}

type CourseOption = {
  id: number
  name: string
}

const ROLE_OPTIONS = [
  { value: 'student', label: 'student' },
  { value: 'teacher', label: 'teacher' },
  { value: 'assistant', label: 'assistant' },
]

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

  const widgetTemplate = useMemo(
    () => `/widget/chat?course=${selectedCourse ?? '{course_id}'}&token={backend_embed_token}`,
    [selectedCourse]
  )

  const iframeTemplate = useMemo(
    () => `<iframe\n  src="${widgetTemplate}"\n  width="400"\n  height="600"\n  frameborder="0">\n</iframe>`,
    [widgetTemplate]
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
        name: values.name || `${label} 模拟接入`,
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
        const values = await chaoxingForm.validateFields(['launch_ticket', 'test_role'])
        const { data } = await platformAPI.launchChaoxing({
          course_id: selectedCourse,
          launch_ticket: values.launch_ticket,
          role: values.test_role,
        })
        setChaoxingStatus({
          connected: true,
          lastTest: new Date().toLocaleString(),
          widgetUrl: data.widget_url,
          tokenSource: data.token_source,
          courseIdSource: data.course_id_source,
          roleSource: data.role_source,
          role: data.role,
          upstreamReference: `${data.upstream_reference_type}: ${data.upstream_reference}`,
        })
        message.success('超星模拟连接测试成功')
      } else {
        const values = await dingtalkForm.validateFields(['auth_code', 'test_role'])
        const { data } = await platformAPI.dingtalkAuth({
          code: values.auth_code,
          course_id: selectedCourse,
          role: values.test_role,
        })
        setDingtalkStatus({
          connected: true,
          lastTest: new Date().toLocaleString(),
          widgetUrl: data.widget_url,
          tokenSource: data.token_source,
          courseIdSource: data.course_id_source,
          roleSource: data.role_source,
          role: data.role,
          upstreamReference: `${data.upstream_reference_type}: ${data.upstream_reference}`,
        })
        message.success('钉钉模拟连接测试成功')
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
        message="当前页仅实现“模拟平台接入”，不是超星或钉钉真实联调"
        description="上游平台提供 course_id、role 和 launch_ticket/auth_code；本系统后端签发 embed token，并返回最终 widget_url。当前不接入真实 SDK，也不做真实签名校验。"
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
                <Tag color="blue">模拟接入</Tag>
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 12 }}
          >
            <Form
              form={chaoxingForm}
              layout="vertical"
              initialValues={{
                name: '超星课程模拟接入',
                callback_url: `${typeof window !== 'undefined' ? window.location.origin : 'https://example.com'}/lti/chaoxing`,
                test_role: 'student',
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

              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
                message="测试连接使用模拟上游参数"
                description="launch_ticket 与 role 视为上游平台提供；course_id 取当前页面所选课程；embed token 与 widget_url 由本系统后端生成。"
              />

              <Form.Item label="模拟 launch_ticket（上游提供）" name="launch_ticket" rules={[{ required: true, message: '请输入 launch_ticket' }]}>
                <Input placeholder="输入上游平台传入的 launch_ticket" />
              </Form.Item>
              <Form.Item label="模拟 role（上游提供）" name="test_role" rules={[{ required: true, message: '请选择 role' }]}>
                <Select options={ROLE_OPTIONS} />
              </Form.Item>

              {chaoxingStatus.lastTest && (
                <Typography.Text type="secondary">上次测试：{chaoxingStatus.lastTest}</Typography.Text>
              )}
              {chaoxingStatus.widgetUrl && (
                <div style={{ marginTop: 8, marginBottom: 12 }}>
                  <Typography.Paragraph copyable style={{ marginBottom: 8 }}>
                    {chaoxingStatus.widgetUrl}
                  </Typography.Paragraph>
                  <Typography.Text type="secondary">token 来源：{chaoxingStatus.tokenSource}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">course_id 来源：{chaoxingStatus.courseIdSource}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">role 来源：{chaoxingStatus.roleSource}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">本次 role：{chaoxingStatus.role}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">上游引用：{chaoxingStatus.upstreamReference}</Typography.Text>
                </div>
              )}
              <Space>
                <Button
                  loading={testing === 'chaoxing'}
                  icon={<ApiOutlined />}
                  onClick={() => void testConnection('chaoxing')}
                >
                  测试模拟接入
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
                <Tag color="blue">模拟接入</Tag>
              </Space>
            }
            bordered={false}
            style={{ borderRadius: 12 }}
          >
            <Form
              form={dingtalkForm}
              layout="vertical"
              initialValues={{ name: '钉钉课程模拟接入', test_role: 'student' }}
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

              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
                message="测试连接使用模拟上游参数"
                description="auth_code 与 role 视为上游平台提供；course_id 取当前页面所选课程；embed token 与 widget_url 由本系统后端生成。"
              />

              <Form.Item label="模拟 auth_code（上游提供）" name="auth_code" rules={[{ required: true, message: '请输入 auth_code' }]}>
                <Input placeholder="输入上游平台传入的 auth_code" />
              </Form.Item>
              <Form.Item label="模拟 role（上游提供）" name="test_role" rules={[{ required: true, message: '请选择 role' }]}>
                <Select options={ROLE_OPTIONS} />
              </Form.Item>

              {dingtalkStatus.lastTest && (
                <Typography.Text type="secondary">上次测试：{dingtalkStatus.lastTest}</Typography.Text>
              )}
              {dingtalkStatus.widgetUrl && (
                <div style={{ marginTop: 8, marginBottom: 12 }}>
                  <Typography.Paragraph copyable style={{ marginBottom: 8 }}>
                    {dingtalkStatus.widgetUrl}
                  </Typography.Paragraph>
                  <Typography.Text type="secondary">token 来源：{dingtalkStatus.tokenSource}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">course_id 来源：{dingtalkStatus.courseIdSource}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">role 来源：{dingtalkStatus.roleSource}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">本次 role：{dingtalkStatus.role}</Typography.Text>
                  <br />
                  <Typography.Text type="secondary">上游引用：{dingtalkStatus.upstreamReference}</Typography.Text>
                </div>
              )}
              <Space>
                <Button
                  loading={testing === 'dingtalk'}
                  icon={<ApiOutlined />}
                  onClick={() => void testConnection('dingtalk')}
                >
                  测试模拟接入
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

      <Card title="Widget URL 口径说明" bordered={false} style={{ borderRadius: 12, marginTop: 16 }}>
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

        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="字段来源统一口径"
          description="course_id 和 role 来自上游平台请求；token 由 EduAI 后端签发；widget_url 由 EduAI 后端根据 course_id + token 组装后返回。"
        />

        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>widget_url 结构模板</div>
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
            <span style={{ wordBreak: 'break-all' }}>{widgetTemplate}</span>
            <Button size="small" icon={<CopyOutlined />} onClick={() => void copyToClipboard(widgetTemplate)}>
              复制
            </Button>
          </div>
        </div>

        <div>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>iframe 嵌入模板</div>
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
              {iframeTemplate}
            </pre>
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => void copyToClipboard(iframeTemplate)}
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

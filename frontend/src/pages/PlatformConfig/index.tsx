import { useState } from 'react'
import { Card, Row, Col, Form, Input, Button, Tag, message, Alert, Select } from 'antd'
import { ApiOutlined, CheckCircleOutlined, CopyOutlined } from '@ant-design/icons'

interface PlatformStatus {
  connected: boolean
  lastTest?: string
}

export default function PlatformConfig() {
  const [chaoxingStatus, setChaoxingStatus] = useState<PlatformStatus>({ connected: false })
  const [dingtalkStatus, setDingtalkStatus] = useState<PlatformStatus>({ connected: false })
  const [chaoxingForm] = Form.useForm()
  const [dingtalkForm] = Form.useForm()
  const [testing, setTesting] = useState<'chaoxing' | 'dingtalk' | null>(null)
  const [selectedCourse, setSelectedCourse] = useState(1)

  const testConnection = async (platform: 'chaoxing' | 'dingtalk') => {
    setTesting(platform)
    await new Promise(r => setTimeout(r, 1500))
    if (platform === 'chaoxing') {
      setChaoxingStatus({ connected: true, lastTest: new Date().toLocaleString() })
      message.success('超星学习通连接测试成功')
    } else {
      setDingtalkStatus({ connected: true, lastTest: new Date().toLocaleString() })
      message.success('钉钉连接测试成功')
    }
    setTesting(null)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }

  const widgetUrl = `https://your-domain.com/widget/chat?course=${selectedCourse}&token=YOUR_TOKEN`
  const iframeCode = `<iframe\n  src="${widgetUrl}"\n  width="400"\n  height="600"\n  frameborder="0">\n</iframe>`

  return (
    <div>
      <div style={{ marginBottom: 24, fontSize: 20, fontWeight: 700 }}>平台对接配置</div>

      <Alert
        type="info" showIcon message="说明"
        description="根据赛题要求，平台对接无需真实集成调试，提供标准化接口和技术说明即可。以下为模拟配置界面展示对接能力。"
        style={{ borderRadius: 10, marginBottom: 20 }}
      />

      <Row gutter={[16, 16]}>
        {/* 超星学习通 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 22 }}>📚</span>超星学习通
                {chaoxingStatus.connected
                  ? <Tag color="success" icon={<CheckCircleOutlined />}>已连接</Tag>
                  : <Tag>未连接</Tag>}
              </span>
            }
            bordered={false} style={{ borderRadius: 12 }}
          >
            <Form form={chaoxingForm} layout="vertical">
              <Form.Item label="LTI Consumer Key" name="lti_key">
                <Input placeholder="输入超星 LTI Consumer Key" />
              </Form.Item>
              <Form.Item label="LTI Shared Secret" name="lti_secret">
                <Input.Password placeholder="输入 LTI Shared Secret" />
              </Form.Item>
              <Form.Item label="回调 URL" name="callback_url">
                <Input placeholder="https://your-domain.com/lti/chaoxing" />
              </Form.Item>
              {chaoxingStatus.lastTest && (
                <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>上次测试：{chaoxingStatus.lastTest}</div>
              )}
              <div style={{ display: 'flex', gap: 8 }}>
                <Button loading={testing === 'chaoxing'} icon={<ApiOutlined />}
                  onClick={() => testConnection('chaoxing')}>测试连接</Button>
                <Button type="primary" onClick={() => message.success('配置已保存')}>保存</Button>
              </div>
            </Form>
          </Card>
        </Col>

        {/* 钉钉 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 22 }}>🔔</span>钉钉
                {dingtalkStatus.connected
                  ? <Tag color="success" icon={<CheckCircleOutlined />}>已连接</Tag>
                  : <Tag>未连接</Tag>}
              </span>
            }
            bordered={false} style={{ borderRadius: 12 }}
          >
            <Form form={dingtalkForm} layout="vertical">
              <Form.Item label="AppKey" name="app_key">
                <Input placeholder="输入钉钉 AppKey" />
              </Form.Item>
              <Form.Item label="AppSecret" name="app_secret">
                <Input.Password placeholder="输入钉钉 AppSecret" />
              </Form.Item>
              <Form.Item label="AgentId" name="agent_id">
                <Input placeholder="钉钉机器人 AgentId" />
              </Form.Item>
              {dingtalkStatus.lastTest && (
                <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>上次测试：{dingtalkStatus.lastTest}</div>
              )}
              <div style={{ display: 'flex', gap: 8 }}>
                <Button loading={testing === 'dingtalk'} icon={<ApiOutlined />}
                  onClick={() => testConnection('dingtalk')}>测试连接</Button>
                <Button type="primary" onClick={() => message.success('配置已保存')}>保存</Button>
              </div>
            </Form>
          </Card>
        </Col>
      </Row>

      {/* 嵌入代码生成器 */}
      <Card
        title="🔗 嵌入式 Widget 代码生成"
        bordered={false}
        style={{ borderRadius: 12, marginTop: 16 }}
      >
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', marginBottom: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>选择课程</div>
            <Select
              value={selectedCourse}
              onChange={setSelectedCourse}
              style={{ width: 200 }}
              options={[
                { value: 1, label: 'Python程序设计' },
                { value: 2, label: '数据结构' },
                { value: 3, label: '高等数学' },
              ]}
            />
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Widget URL</div>
          <div style={{
            background: '#f5f5f5', borderRadius: 8, padding: '10px 14px',
            fontFamily: 'monospace', fontSize: 13, color: '#333',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ wordBreak: 'break-all' }}>{widgetUrl}</span>
            <Button
              size="small" icon={<CopyOutlined />}
              onClick={() => copyToClipboard(widgetUrl)}
              style={{ marginLeft: 8, flexShrink: 0 }}
            >复制</Button>
          </div>
        </div>

        <div>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>iframe 嵌入代码</div>
          <div style={{ position: 'relative' }}>
            <pre style={{
              background: '#1e1e1e', color: '#d4d4d4',
              padding: '14px 16px', borderRadius: 10,
              fontSize: 13, overflowX: 'auto', margin: 0,
            }}>{iframeCode}</pre>
            <Button
              size="small" icon={<CopyOutlined />}
              onClick={() => copyToClipboard(iframeCode)}
              style={{ position: 'absolute', top: 10, right: 10 }}
            >复制代码</Button>
          </div>
        </div>

        <div style={{ marginTop: 16, padding: '12px 16px', background: '#f6ffed', borderRadius: 8, border: '1px solid #b7eb8f', fontSize: 13 }}>
          <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
          将以上 iframe 代码粘贴到超星课程页面或钉钉工作台配置中，即可完成嵌入。Widget 支持 400×600px 尺寸，自动适配移动端。
        </div>
      </Card>
    </div>
  )
}

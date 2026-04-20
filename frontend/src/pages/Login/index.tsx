import { useState } from 'react'
import { Form, Input, Button, message, Tabs, Select } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const { data } = await authAPI.login(values.username, values.password)
      setAuth(data.access_token, data.user)
      message.success('登录成功')
      navigate('/')
    } catch {
      message.error('用户名或密码错误，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (values: any) => {
    setLoading(true)
    try {
      await authAPI.register(values)
      message.success('注册成功，请登录')
    } catch {
      message.error('注册失败，请检查信息后重试')
    } finally {
      setLoading(false)
    }
  }

  const inputStyle: React.CSSProperties = {
    background: 'rgba(255,255,255,0.08)',
    border: '1px solid rgba(255,255,255,0.18)',
    borderRadius: 10,
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      background: 'linear-gradient(135deg, #0f1b2d 0%, #1a3a5c 50%, #0d2137 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', width: 600, height: 600,
        borderRadius: '50%', top: -200, left: -150,
        background: 'radial-gradient(circle, rgba(0,168,255,0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', width: 400, height: 400,
        borderRadius: '50%', bottom: -100, right: -80,
        background: 'radial-gradient(circle, rgba(82,196,26,0.08) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* 左侧品牌区 */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'flex-start',
        padding: '0 80px',
        gap: 28,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: 'linear-gradient(135deg, #00a8ff, #0078d7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, fontWeight: 900, color: '#fff',
            boxShadow: '0 4px 24px rgba(0,168,255,0.45)',
          }}>E</div>
          <span style={{
            fontSize: 30, fontWeight: 800, color: '#fff',
            letterSpacing: 3, fontFamily: 'Georgia, serif',
          }}>EduAI</span>
        </div>

        <div style={{
          color: '#fff', fontSize: 38, fontWeight: 700,
          lineHeight: 1.35, fontFamily: 'Georgia, serif',
        }}>
          可嵌入式<br />
          <span style={{ color: '#00a8ff' }}>跨课程 AI Agent</span><br />
          通用架构平台
        </div>

        <p style={{
          color: 'rgba(255,255,255,0.55)', fontSize: 15,
          maxWidth: 400, lineHeight: 1.9, margin: 0,
        }}>
          智能答疑 · 作业批改 · 学情分析 · 个性化练习<br />
          让每一门课程都拥有专属 AI 教学助手
        </p>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {['智能答疑 ≥95%', '批注式批改', '学情预警', '可视化构建'].map(tag => (
            <div key={tag} style={{
              padding: '5px 16px', borderRadius: 20,
              border: '1px solid rgba(0,168,255,0.4)',
              color: 'rgba(255,255,255,0.75)', fontSize: 12,
              background: 'rgba(0,168,255,0.08)',
            }}>{tag}</div>
          ))}
        </div>
      </div>

      {/* 右侧登录卡片 */}
      <div style={{
        width: 480,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 40px',
      }}>
        <div style={{
          width: '100%',
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(24px)',
          borderRadius: 22,
          border: '1px solid rgba(255,255,255,0.12)',
          padding: '44px 40px',
          boxShadow: '0 24px 80px rgba(0,0,0,0.5)',
        }}>
          <style>{`
            .login-tab .ant-tabs-tab { color: rgba(255,255,255,0.5) !important; font-size: 15px; }
            .login-tab .ant-tabs-tab-active .ant-tabs-tab-btn { color: #00a8ff !important; }
            .login-tab .ant-tabs-ink-bar { background: #00a8ff !important; }
            .login-tab .ant-tabs-nav::before { border-bottom-color: rgba(255,255,255,0.1) !important; }
            .login-input input, .login-input { color: #fff !important; }
            .login-input .ant-input-prefix { color: rgba(255,255,255,0.4) !important; }
            .login-input:hover, .login-input:focus-within { border-color: #00a8ff !important; }
            .login-select .ant-select-selector { background: rgba(255,255,255,0.08) !important; border: 1px solid rgba(255,255,255,0.18) !important; border-radius: 10px !important; color: #fff !important; }
            .login-select .ant-select-arrow { color: rgba(255,255,255,0.4) !important; }
          `}</style>

        <Tabs
          centered
            className="login-tab"
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                  <Form onFinish={handleLogin} style={{ marginTop: 20 }}>
                  <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                      <Input
                        className="login-input"
                        prefix={<UserOutlined />}
                        placeholder="用户名"
                        size="large"
                        style={inputStyle}
                      />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                      <Input.Password
                        className="login-input"
                        prefix={<LockOutlined />}
                        placeholder="密码"
                        size="large"
                        style={inputStyle}
                      />
                  </Form.Item>
                    <Form.Item style={{ marginTop: 8 }}>
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        block
                        size="large"
                        style={{
                          borderRadius: 10,
                          height: 48,
                          fontSize: 16,
                          fontWeight: 600,
                          background: 'linear-gradient(90deg, #00a8ff, #0078d7)',
                          border: 'none',
                          boxShadow: '0 4px 16px rgba(0,168,255,0.4)',
                        }}
                      >
                      登录
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '注册',
              children: (
                  <Form onFinish={handleRegister} style={{ marginTop: 20 }}>
                    <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                      <Input
                        className="login-input"
                        prefix={<UserOutlined />}
                        placeholder="用户名"
                        size="large"
                        style={inputStyle}
                      />
                  </Form.Item>
                    <Form.Item name="email" rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}>
                      <Input
                        className="login-input"
                        prefix={<MailOutlined />}
                        placeholder="邮箱"
                        size="large"
                        style={inputStyle}
                      />
                  </Form.Item>
                    <Form.Item name="full_name" rules={[{ required: true, message: '请输入姓名' }]}>
                      <Input
                        className="login-input"
                        placeholder="姓名"
                        size="large"
                        style={inputStyle}
                      />
                  </Form.Item>
                    <Form.Item name="password" rules={[{ required: true, min: 6, message: '密码至少6位' }]}>
                      <Input.Password
                        className="login-input"
                        prefix={<LockOutlined />}
                        placeholder="密码（至少6位）"
                        size="large"
                        style={inputStyle}
                      />
                  </Form.Item>
                    <Form.Item name="role" initialValue="student" rules={[{ required: true }]}>
                      <Select
                        className="login-select"
                        size="large"
                        options={[
                          { value: 'student', label: '学生' },
                          { value: 'teacher', label: '教师' },
                        ]}
                      />
                  </Form.Item>
                    <Form.Item style={{ marginTop: 8 }}>
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        block
                        size="large"
                        style={{
                          borderRadius: 10,
                          height: 48,
                          fontSize: 16,
                          fontWeight: 600,
                          background: 'linear-gradient(90deg, #00a8ff, #0078d7)',
                          border: 'none',
                          boxShadow: '0 4px 16px rgba(0,168,255,0.4)',
                        }}
                      >
                      注册
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />
        </div>
      </div>
    </div>
  )
}

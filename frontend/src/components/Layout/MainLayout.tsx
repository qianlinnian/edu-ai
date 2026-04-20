import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, theme, Badge } from 'antd'
import {
  DashboardOutlined,
  BookOutlined,
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined,
  EditOutlined,
  RobotOutlined,
  ApiOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../../hooks/useAuthStore'

const { Header, Sider, Content } = Layout

const teacherMenuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/courses', icon: <BookOutlined />, label: '课程管理' },
  { key: '/chat', icon: <MessageOutlined />, label: '智能答疑' },
  { key: '/assignments', icon: <FileTextOutlined />, label: '作业管理' },
  { key: '/analytics', icon: <BarChartOutlined />, label: '学情分析' },
  { key: '/agent-builder', icon: <RobotOutlined />, label: 'Agent构建器' },
  { key: '/platform', icon: <ApiOutlined />, label: '平台对接' },
]

const studentMenuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/chat', icon: <MessageOutlined />, label: '智能答疑' },
  { key: '/assignments', icon: <FileTextOutlined />, label: '我的作业' },
  { key: '/exercises', icon: <EditOutlined />, label: '练习中心' },
]

const roleLabel: Record<string, string> = {
  teacher: '教师',
  student: '学生',
  admin: '管理员',
}

const roleColor: Record<string, string> = {
  teacher: '#00a8ff',
  student: '#52c41a',
  admin: '#faad14',
}

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { token: { colorBgContainer } } = theme.useToken()

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const menuItems = isTeacher ? teacherMenuItems : studentMenuItems

  // 选中当前路由对应菜单项（支持子路由高亮）
  const selectedKey = menuItems
    .map(item => item.key)
    .filter(k => k !== '/')
    .find(k => location.pathname.startsWith(k))
    ?? (location.pathname === '/' ? '/' : '')

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          background: 'linear-gradient(180deg, #0f1b2d 0%, #1a3a5c 100%)',
          boxShadow: '2px 0 12px rgba(0,0,0,0.3)',
        }}
        theme="dark"
      >
        {/* Logo */}
        <div style={{
          height: 56, margin: '12px 16px',
          display: 'flex', alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 10, overflow: 'hidden',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          paddingBottom: 12,
        }}>
          <div style={{
            minWidth: 32, width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #00a8ff, #0078d7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 900, fontSize: 16, color: '#fff',
            boxShadow: '0 2px 10px rgba(0,168,255,0.4)',
            flexShrink: 0,
          }}>E</div>
          {!collapsed && (
            <span style={{
              color: '#fff', fontWeight: 800, fontSize: 18,
              fontFamily: 'Georgia, serif', letterSpacing: 2,
              whiteSpace: 'nowrap',
            }}>EduAI</span>
          )}
        </div>

        {/* 角色标签 */}
        {!collapsed && user && (
          <div style={{
            margin: '8px 16px 12px',
            padding: '6px 12px',
            borderRadius: 8,
            background: 'rgba(255,255,255,0.06)',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <Badge color={roleColor[user.role]} />
            <span style={{ color: 'rgba(255,255,255,0.75)', fontSize: 12 }}>
              {user.full_name} · {roleLabel[user.role]}
            </span>
          </div>
        )}

        <Menu
          theme="dark"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ background: 'transparent', border: 'none', paddingTop: 4 }}
        />
      </Sider>

      <Layout>
        <Header style={{
          padding: '0 24px',
          background: colorBgContainer,
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        }}>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'info',
                  label: (
                    <div style={{ padding: '4px 0' }}>
                      <div style={{ fontWeight: 600 }}>{user?.full_name}</div>
                      <div style={{ fontSize: 12, color: '#999' }}>{user?.email}</div>
                    </div>
                  ),
                  disabled: true,
                },
                { type: 'divider' },
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true, onClick: logout },
              ],
            }}
          >
            <span style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10 }}>
              <Avatar
                style={{
                  background: roleColor[user?.role ?? 'student'],
                  fontWeight: 700,
                }}
              >
                {user?.full_name?.[0] ?? <UserOutlined />}
              </Avatar>
              <span style={{ fontWeight: 500 }}>{user?.full_name}</span>
              <span style={{
                fontSize: 11, padding: '1px 8px', borderRadius: 10,
                background: roleColor[user?.role ?? 'student'] + '20',
                color: roleColor[user?.role ?? 'student'],
                fontWeight: 600,
              }}>
                {roleLabel[user?.role ?? 'student']}
              </span>
            </span>
          </Dropdown>
        </Header>

        <Content style={{ margin: 24 }}>
          <div style={{
            padding: 24,
            background: colorBgContainer,
            borderRadius: 12,
            minHeight: 360,
            boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, theme } from 'antd'
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

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/courses', icon: <BookOutlined />, label: '课程管理' },
  { key: '/chat', icon: <MessageOutlined />, label: '智能答疑' },
  { key: '/assignments', icon: <FileTextOutlined />, label: '作业管理' },
  { key: '/analytics', icon: <BarChartOutlined />, label: '学情分析' },
  { key: '/exercises', icon: <EditOutlined />, label: '练习中心' },
  { key: '/agent-builder', icon: <RobotOutlined />, label: 'Agent构建器' },
  { key: '/platform', icon: <ApiOutlined />, label: '平台对接' },
]

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { token: { colorBgContainer } } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ height: 48, margin: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: '#fff', fontSize: collapsed ? 16 : 20, fontWeight: 'bold', whiteSpace: 'nowrap' }}>
            {collapsed ? 'EA' : 'EduAI'}
          </span>
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <Dropdown
            menu={{
              items: [
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: logout },
              ],
            }}
          >
            <span style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ marginRight: 8 }} />
              {user?.full_name}
            </span>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24 }}>
          <div style={{ padding: 24, background: colorBgContainer, borderRadius: 8, minHeight: 360 }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

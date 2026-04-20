import { useState } from 'react'
import {
  Card, Row, Col, Button, Modal, Form, Input, Tabs, Table, Tag,
  Upload, Tree, Avatar, message, Popconfirm, Typography, Space, Badge,
} from 'antd'
import {
  PlusOutlined, UploadOutlined, FilePdfOutlined, FileWordOutlined,
  FilePptOutlined, DeleteOutlined, BookOutlined, TeamOutlined,
  CheckCircleOutlined, LoadingOutlined, UserOutlined,
} from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import { useAuthStore } from '../../hooks/useAuthStore'

interface Course {
  id: number
  name: string
  description: string
  studentCount: number
  resourceCount: number
  color: string
}

interface Resource {
  id: number
  name: string
  type: string
  status: 'ready' | 'processing'
}

const MOCK_COURSES: Course[] = [
  { id: 1, name: 'Python程序设计', description: '面向初学者的Python编程入门课程', studentCount: 128, resourceCount: 12, color: '#3b82f6' },
  { id: 2, name: '数据结构', description: '数组、链表、树、图等经典数据结构', studentCount: 96, resourceCount: 8, color: '#8b5cf6' },
  { id: 3, name: '高等数学', description: '微积分、线性代数基础', studentCount: 150, resourceCount: 15, color: '#10b981' },
]

const MOCK_RESOURCES: Resource[] = [
  { id: 1, name: '第1章-基础语法.pdf', type: 'PDF', status: 'ready' },
  { id: 2, name: '第2章-函数.pptx', type: 'PPT', status: 'processing' },
  { id: 3, name: '第3章-循环结构.docx', type: 'Word', status: 'ready' },
  { id: 4, name: '第4章-面向对象.pdf', type: 'PDF', status: 'ready' },
]

const MOCK_KNOWLEDGE_TREE: DataNode[] = [
  {
    title: '基础语法', key: '1',
    children: [
      { title: '变量与类型', key: '1-1' },
      { title: '运算符', key: '1-2' },
      { title: '输入输出', key: '1-3' },
    ],
  },
  {
    title: '流程控制', key: '2',
    children: [
      { title: '条件判断', key: '2-1' },
      { title: '循环结构', key: '2-2' },
    ],
  },
  {
    title: '函数', key: '3',
    children: [
      { title: '函数定义', key: '3-1' },
      { title: '参数传递', key: '3-2' },
      { title: '递归', key: '3-3' },
    ],
  },
  {
    title: '数据结构', key: '4',
    children: [
      { title: '列表', key: '4-1' },
      { title: '字典', key: '4-2' },
      { title: '集合', key: '4-3' },
    ],
  },
]

const MOCK_STUDENTS = [
  { id: 1, name: '张三', email: 'zhangsan@example.com', score: 85 },
  { id: 2, name: '李四', email: 'lisi@example.com', score: 72 },
  { id: 3, name: '王五', email: 'wangwu@example.com', score: 58 },
  { id: 4, name: '赵六', email: 'zhaoliu@example.com', score: 91 },
]

const fileIcon = (type: string) => {
  if (type === 'PDF') return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />
  if (type === 'PPT') return <FilePptOutlined style={{ color: '#faad14', fontSize: 18 }} />
  return <FileWordOutlined style={{ color: '#00a8ff', fontSize: 18 }} />
}

export default function CourseManage() {
  const user = useAuthStore(s => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const [courses, setCourses] = useState<Course[]>(MOCK_COURSES)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [resources, setResources] = useState<Resource[]>(MOCK_RESOURCES)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const handleCreate = (values: any) => {
    const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b']
    const newCourse: Course = {
      id: Date.now(),
      name: values.name,
      description: values.description || '',
      studentCount: 0,
      resourceCount: 0,
      color: colors[courses.length % colors.length],
    }
    setCourses([...courses, newCourse])
    message.success('课程创建成功')
    setCreateOpen(false)
    form.resetFields()
  }

  const handleUpload = (file: File) => {
    const ext = file.name.split('.').pop()?.toUpperCase() ?? 'FILE'
    const type = ext === 'PDF' ? 'PDF' : (ext === 'PPTX' || ext === 'PPT') ? 'PPT' : 'Word'
    const newRes: Resource = { id: Date.now(), name: file.name, type, status: 'processing' }
    setResources(prev => [newRes, ...prev])
    setTimeout(() => {
      setResources(prev => prev.map(r => r.id === newRes.id ? { ...r, status: 'ready' as const } : r))
      message.success(`${file.name} 处理完成`)
    }, 2000)
    return false
  }

  const handleDeleteResource = (id: number) => {
    setResources(prev => prev.filter(r => r.id !== id))
    message.success('删除成功')
  }

  // 学生：只看课程列表
  if (!isTeacher) {
    return (
      <div>
        <div style={{ marginBottom: 24, fontSize: 20, fontWeight: 700 }}>我的课程</div>
        <Row gutter={[16, 16]}>
          {courses.map(c => (
            <Col key={c.id} xs={24} sm={12} lg={8}>
              <Card hoverable style={{ borderRadius: 14, overflow: 'hidden' }} styles={{ body: { padding: 0 } }}>
                <div style={{ height: 6, background: c.color }} />
                <div style={{ padding: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                    <Avatar size={44} style={{ background: c.color, fontWeight: 700 }}>{c.name[0]}</Avatar>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 16 }}>{c.name}</div>
                      <div style={{ color: '#999', fontSize: 12 }}>{c.description}</div>
                    </div>
                  </div>
                  <div style={{ color: '#888', fontSize: 13 }}>
                    <BookOutlined style={{ marginRight: 4 }} />{c.resourceCount} 份课件
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    )
  }

  // 教师：课程详情
  if (selectedCourse) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button onClick={() => setSelectedCourse(null)}>← 返回</Button>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: selectedCourse.color,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 700, fontSize: 16,
          }}>{selectedCourse.name[0]}</div>
          <span style={{ fontSize: 20, fontWeight: 700 }}>{selectedCourse.name}</span>
        </div>

        <Tabs items={[
          {
            key: 'resources',
            label: '📁 课件管理',
            children: (
              <div>
                <Upload.Dragger
                  accept=".pdf,.doc,.docx,.ppt,.pptx"
                  beforeUpload={handleUpload}
                  showUploadList={false}
                  style={{ marginBottom: 16, borderRadius: 10 }}
                >
                  <p style={{ fontSize: 28 }}><UploadOutlined /></p>
                  <p style={{ fontWeight: 500 }}>拖拽上传 PDF / Word / PPT</p>
                  <p style={{ color: '#999', fontSize: 12 }}>上传后自动进行分块向量化处理</p>
                </Upload.Dragger>
                <Table
                  dataSource={resources}
                  rowKey="id"
                  pagination={false}
                  columns={[
                    {
                      title: '文件名', dataIndex: 'name',
                      render: (name, row) => <Space>{fileIcon(row.type)}<span>{name}</span></Space>,
                    },
                    { title: '类型', dataIndex: 'type', render: t => <Tag>{t}</Tag> },
                    {
                      title: '状态', dataIndex: 'status',
                      render: s => s === 'ready'
                        ? <Tag icon={<CheckCircleOutlined />} color="success">已处理</Tag>
                        : <Tag icon={<LoadingOutlined />} color="processing">处理中</Tag>,
                    },
                    {
                      title: '操作',
                      render: (_, row) => (
                        <Popconfirm title="确认删除？" onConfirm={() => handleDeleteResource(row.id)}>
                          <Button danger size="small" icon={<DeleteOutlined />}>删除</Button>
                        </Popconfirm>
                      ),
                    },
                  ]}
                />
              </div>
            ),
          },
          {
            key: 'knowledge',
            label: '🌳 知识点',
            children: (
              <div style={{ display: 'flex', gap: 32 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ marginBottom: 12, fontWeight: 600 }}>知识点树</div>
                  <Tree treeData={MOCK_KNOWLEDGE_TREE} defaultExpandAll showLine={{ showLeafIcon: false }} />
                </div>
                <div style={{ width: 220 }}>
                  <div style={{ marginBottom: 12, fontWeight: 600 }}>添加知识点</div>
                  <Form layout="vertical">
                    <Form.Item label="知识点名称">
                      <Input placeholder="如：递归算法" />
                    </Form.Item>
                    <Form.Item label="父节点">
                      <Input placeholder="如：函数" />
                    </Form.Item>
                    <Button type="primary" icon={<PlusOutlined />} block>添加</Button>
                  </Form>
                </div>
              </div>
            ),
          },
          {
            key: 'students',
            label: '👥 学生名单',
            children: (
              <Table
                dataSource={MOCK_STUDENTS}
                rowKey="id"
                columns={[
                  {
                    title: '学生', dataIndex: 'name',
                    render: name => <Space><Avatar size="small" icon={<UserOutlined />} />{name}</Space>,
                  },
                  { title: '邮箱', dataIndex: 'email' },
                  {
                    title: '平均分', dataIndex: 'score',
                    render: score => {
                      const color = score >= 80 ? '#52c41a' : score >= 60 ? '#faad14' : '#ff4d4f'
                      return <span style={{ color, fontWeight: 600 }}>{score}</span>
                    },
                  },
                ]}
              />
            ),
          },
          {
            key: 'info',
            label: '📋 课程信息',
            children: (
              <Card style={{ maxWidth: 480 }}>
                <Form layout="vertical" initialValues={selectedCourse}>
                  <Form.Item label="课程名称" name="name">
                    <Input />
                  </Form.Item>
                  <Form.Item label="课程描述" name="description">
                    <Input.TextArea rows={3} />
                  </Form.Item>
                  <Button type="primary">保存修改</Button>
                </Form>
              </Card>
            ),
          },
        ]} />
      </div>
    )
  }

  // 教师：课程列表
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <span style={{ fontSize: 20, fontWeight: 700 }}>课程管理</span>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} style={{ borderRadius: 8 }}>
          创建课程
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {courses.map(c => (
          <Col key={c.id} xs={24} sm={12} lg={8}>
            <Card
              hoverable
              style={{ borderRadius: 14, overflow: 'hidden', border: '1px solid #f0f0f0', cursor: 'pointer' }}
              styles={{ body: { padding: 0 } }}
              onClick={() => setSelectedCourse(c)}
            >
              <div style={{ height: 6, background: c.color }} />
              <div style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <Avatar size={48} style={{ background: c.color, fontSize: 20, fontWeight: 700, flexShrink: 0 }}>
                    {c.name[0]}
                  </Avatar>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 2 }}>{c.name}</div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }} ellipsis>
                      {c.description}
                    </Typography.Text>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20, color: '#888', fontSize: 13, borderTop: '1px solid #f5f5f5', paddingTop: 12 }}>
                  <span><TeamOutlined style={{ marginRight: 4 }} />{c.studentCount} 学生</span>
                  <span><BookOutlined style={{ marginRight: 4 }} />{c.resourceCount} 份课件</span>
                  <span style={{ marginLeft: 'auto' }}>
                    <Badge status="processing" text={<span style={{ fontSize: 12 }}>Agent已激活</span>} />
                  </span>
                </div>
              </div>
            </Card>
          </Col>
        ))}

        <Col xs={24} sm={12} lg={8}>
          <Card
            hoverable
            onClick={() => setCreateOpen(true)}
            style={{
              borderRadius: 14, border: '2px dashed #d9d9d9',
              minHeight: 148, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            styles={{ body: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 } }}
          >
            <PlusOutlined style={{ fontSize: 28, color: '#bbb' }} />
            <span style={{ color: '#bbb', fontSize: 14 }}>创建新课程</span>
          </Card>
        </Col>
      </Row>

      <Modal
        title="创建课程"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="创建"
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Form.Item name="name" label="课程名称" rules={[{ required: true, message: '请输入课程名称' }]}>
            <Input placeholder="如：Python程序设计" />
          </Form.Item>
          <Form.Item name="description" label="课程描述">
            <Input.TextArea rows={3} placeholder="课程简介" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

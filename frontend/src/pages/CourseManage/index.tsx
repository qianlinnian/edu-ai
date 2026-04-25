import { useEffect, useMemo, useState } from 'react'
import {
  Card, Row, Col, Button, Modal, Form, Input, Tabs, Table, Tag,
  Upload, Tree, Avatar, message, Typography, Space, Badge, Empty, Alert,
} from 'antd'
import {
  PlusOutlined, UploadOutlined, FilePdfOutlined, FileWordOutlined,
  FilePptOutlined, BookOutlined, TeamOutlined,
  LoadingOutlined, UserOutlined,
} from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import { courseAPI } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

interface CourseItem {
  id: number
  name: string
  code: string
  description?: string | null
  domain: string
  teacher_id: number
}

interface ResourceItem {
  id: number
  name: string
  file_type?: string
  file_size?: number
  chunk_count?: number
  is_processed?: boolean
  processing_status?: 'pending' | 'processing' | 'processed' | 'failed'
  processing_error?: string | null
  created_at?: string
}

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
]

const MOCK_STUDENTS = [
  { id: 1, name: '张三', email: 'zhangsan@example.com', score: 85 },
  { id: 2, name: '李四', email: 'lisi@example.com', score: 72 },
  { id: 3, name: '王五', email: 'wangwu@example.com', score: 58 },
]

const colorPalette = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#14b8a6']

const fileIcon = (type?: string) => {
  const upper = (type ?? '').toUpperCase()
  if (upper === 'PDF') return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />
  if (upper === 'PPT' || upper === 'PPTX') return <FilePptOutlined style={{ color: '#faad14', fontSize: 18 }} />
  return <FileWordOutlined style={{ color: '#00a8ff', fontSize: 18 }} />
}

const statusTag = (status?: ResourceItem['processing_status']) => {
  if (status === 'processed') return <Tag color="success">已处理</Tag>
  if (status === 'failed') return <Tag color="error">处理失败</Tag>
  if (status === 'processing') return <Tag icon={<LoadingOutlined />} color="processing">处理中</Tag>
  return <Tag color="default">待处理</Tag>
}

export default function CourseManage() {
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const [courses, setCourses] = useState<CourseItem[]>([])
  const [selectedCourse, setSelectedCourse] = useState<CourseItem | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [resources, setResources] = useState<ResourceItem[]>([])
  const [resourceTip, setResourceTip] = useState<string>('当前后端尚未提供资源列表接口，上传成功后仅提示处理状态。')
  const [form] = Form.useForm()

  const courseColorMap = useMemo(() => {
    return new Map(courses.map((course, index) => [course.id, colorPalette[index % colorPalette.length]]))
  }, [courses])

  const loadCourses = async () => {
    setLoadingCourses(true)
    try {
      const { data } = await courseAPI.list()
      setCourses(data)
      if (selectedCourse) {
        const latest = data.find((item: CourseItem) => item.id === selectedCourse.id)
        setSelectedCourse(latest ?? null)
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '加载课程失败')
    } finally {
      setLoadingCourses(false)
    }
  }

  useEffect(() => {
    void loadCourses()
  }, [])

  const handleCreate = async (values: { name: string; code: string; description?: string; domain: string }) => {
    setCreating(true)
    try {
      const { data } = await courseAPI.create(values)
      message.success('课程创建成功')
      setCreateOpen(false)
      form.resetFields()
      await loadCourses()
      setSelectedCourse(data)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '课程创建失败')
    } finally {
      setCreating(false)
    }
  }

  const handleUpload = async (file: File) => {
    if (!selectedCourse) {
      message.warning('请先选择课程')
      return false
    }

    setUploading(true)
    try {
      const { data } = await courseAPI.uploadResource(selectedCourse.id, file)
      setResources((prev) => [
        {
          id: data.id,
          name: data.name,
          file_type: file.name.split('.').pop(),
          processing_status: 'pending',
          processing_error: null,
        },
        ...prev,
      ])
      setResourceTip('资料已上传，后端正在处理中。待后端补充资源列表接口后，可展示实时处理状态。')
      message.success(data.message || '上传成功，正在处理中')
    } catch (error: any) {
      const detail = error?.response?.data?.detail || '上传失败'
      const hint = String(detail).includes('task dispatch failed')
        ? '上传成功但任务派发失败，请确认 Celery Worker 与 Redis 已启动。'
        : detail
      message.error(hint)
    } finally {
      setUploading(false)
    }
    return false
  }

  if (!isTeacher) {
    return (
      <div>
        <div style={{ marginBottom: 24, fontSize: 20, fontWeight: 700 }}>我的课程</div>
        <Row gutter={[16, 16]}>
          {courses.map((course) => {
            const color = courseColorMap.get(course.id) ?? '#3b82f6'
            return (
              <Col key={course.id} xs={24} sm={12} lg={8}>
                <Card hoverable style={{ borderRadius: 14, overflow: 'hidden' }} styles={{ body: { padding: 0 } }}>
                  <div style={{ height: 6, background: color }} />
                  <div style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                      <Avatar size={44} style={{ background: color, fontWeight: 700 }}>{course.name[0]}</Avatar>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 16 }}>{course.name}</div>
                        <div style={{ color: '#999', fontSize: 12 }}>{course.description || course.domain}</div>
                      </div>
                    </div>
                    <div style={{ color: '#888', fontSize: 13 }}>
                      <BookOutlined style={{ marginRight: 4 }} />课程代码：{course.code}
                    </div>
                  </div>
                </Card>
              </Col>
            )
          })}
        </Row>
      </div>
    )
  }

  if (selectedCourse) {
    const courseColor = courseColorMap.get(selectedCourse.id) ?? '#3b82f6'

    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button onClick={() => setSelectedCourse(null)}>← 返回</Button>
          <div
            style={{
              width: 36, height: 36, borderRadius: 10,
              background: courseColor,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontWeight: 700, fontSize: 16,
            }}
          >
            {selectedCourse.name[0]}
          </div>
          <span style={{ fontSize: 20, fontWeight: 700 }}>{selectedCourse.name}</span>
          <Tag color="blue">{selectedCourse.code}</Tag>
          <Tag>{selectedCourse.domain}</Tag>
        </div>

        <Tabs
          items={[
            {
              key: 'resources',
              label: '📁 课件管理',
              children: (
                <div>
                  <Upload.Dragger
                    accept=".pdf,.doc,.docx,.ppt,.pptx"
                    beforeUpload={handleUpload}
                    showUploadList={false}
                    disabled={uploading}
                    style={{ marginBottom: 16, borderRadius: 10 }}
                  >
                    <p style={{ fontSize: 28 }}><UploadOutlined /></p>
                    <p style={{ fontWeight: 500 }}>{uploading ? '上传中...' : '拖拽上传 PDF / Word / PPT'}</p>
                    <p style={{ color: '#999', fontSize: 12 }}>上传后由后端异步处理并构建课程知识库</p>
                  </Upload.Dragger>

                  <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16, borderRadius: 10 }}
                    message="M2 当前说明"
                    description={resourceTip}
                  />

                  {resources.length === 0 ? (
                    <Empty description="暂无本次会话上传记录" />
                  ) : (
                    <Table
                      dataSource={resources}
                      rowKey="id"
                      pagination={false}
                      columns={[
                        {
                          title: '文件名', dataIndex: 'name',
                          render: (name: string, row: ResourceItem) => <Space>{fileIcon(row.file_type)}<span>{name}</span></Space>,
                        },
                        { title: '类型', dataIndex: 'file_type', render: (type: string) => <Tag>{(type || '未知').toUpperCase()}</Tag> },
                        { title: '状态', dataIndex: 'processing_status', render: (status: ResourceItem['processing_status']) => statusTag(status) },
                        {
                          title: '错误信息',
                          dataIndex: 'processing_error',
                          render: (error?: string | null) => error ? <Typography.Text type="danger">{error}</Typography.Text> : '-',
                        },
                      ]}
                    />
                  )}
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
                    <Alert type="warning" showIcon message="M2阶段知识点管理非主线" description="当前先聚焦课程资料上传与问答闭环，知识点CRUD可在后续阶段接入。" />
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
                      render: (name: string) => <Space><Avatar size="small" icon={<UserOutlined />} />{name}</Space>,
                    },
                    { title: '邮箱', dataIndex: 'email' },
                    {
                      title: '平均分', dataIndex: 'score',
                      render: (score: number) => {
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
                <Card style={{ maxWidth: 520 }}>
                  <Space direction="vertical" size={10} style={{ width: '100%' }}>
                    <div><strong>课程名称：</strong>{selectedCourse.name}</div>
                    <div><strong>课程代码：</strong>{selectedCourse.code}</div>
                    <div><strong>所属领域：</strong>{selectedCourse.domain}</div>
                    <div><strong>课程描述：</strong>{selectedCourse.description || '暂无描述'}</div>
                  </Space>
                </Card>
              ),
            },
          ]}
        />
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <span style={{ fontSize: 20, fontWeight: 700 }}>课程管理</span>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} style={{ borderRadius: 8 }}>
          创建课程
        </Button>
      </div>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16, borderRadius: 10 }}
        message="M2 使用说明"
        description="课程管理首页默认展示全部课程。点击课程卡片后才进入该课程的课件管理页面。"
      />

      {courses.length === 0 && !loadingCourses ? (
        <Empty description="暂无课程，请先创建一门课程用于上传资料和问答演示" />
      ) : (
        <Row gutter={[16, 16]}>
          {courses.map((course) => {
            const color = courseColorMap.get(course.id) ?? '#3b82f6'
            return (
              <Col key={course.id} xs={24} sm={12} lg={8}>
                <Card
                  hoverable
                  style={{ borderRadius: 14, overflow: 'hidden', border: '1px solid #f0f0f0', cursor: 'pointer' }}
                  styles={{ body: { padding: 0 } }}
                  onClick={() => setSelectedCourse(course)}
                >
                  <div style={{ height: 6, background: color }} />
                  <div style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                      <Avatar size={48} style={{ background: color, fontSize: 20, fontWeight: 700, flexShrink: 0 }}>
                        {course.name[0]}
                      </Avatar>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 2 }}>{course.name}</div>
                        <Typography.Text type="secondary" style={{ fontSize: 12 }} ellipsis>
                          {course.description || course.domain}
                        </Typography.Text>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 16, color: '#888', fontSize: 13, borderTop: '1px solid #f5f5f5', paddingTop: 12 }}>
                      <span><BookOutlined style={{ marginRight: 4 }} />{course.code}</span>
                      <span>{course.domain}</span>
                      <span style={{ marginLeft: 'auto' }}>
                        <Badge status="processing" text={<span style={{ fontSize: 12 }}>可上传资料</span>} />
                      </span>
                    </div>
                  </div>
                </Card>
              </Col>
            )
          })}

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
      )}

      <Modal
        title="创建课程"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="创建"
        confirmLoading={creating}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Form.Item name="name" label="课程名称" rules={[{ required: true, message: '请输入课程名称' }]}>
            <Input placeholder="如：面向对象程序设计（Java）" />
          </Form.Item>
          <Form.Item name="code" label="课程代码" rules={[{ required: true, message: '请输入课程代码' }]}>
            <Input placeholder="如：CS101" />
          </Form.Item>
          <Form.Item name="domain" label="课程领域" rules={[{ required: true, message: '请输入课程领域' }]}>
            <Input placeholder="如：计算机科学" />
          </Form.Item>
          <Form.Item name="description" label="课程描述">
            <Input.TextArea rows={3} placeholder="课程简介" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

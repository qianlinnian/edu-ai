import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Avatar,
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  Modal,
  Row,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd'
import {
  BookOutlined,
  DownloadOutlined,
  FilePdfOutlined,
  FilePptOutlined,
  FileWordOutlined,
  LoadingOutlined,
  PlusOutlined,
  UploadOutlined,
} from '@ant-design/icons'
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
  course_id: number
  name: string
  file_type?: string
  file_size?: number
  chunk_count?: number
  is_processed?: boolean
  processing_status?: 'pending' | 'processing' | 'processed' | 'failed'
  processing_error?: string | null
  created_at?: string
}

const colorPalette = ['#2563eb', '#0891b2', '#059669', '#d97706', '#7c3aed', '#dc2626']

const fileIcon = (type?: string) => {
  const upper = (type ?? '').toUpperCase()
  if (upper === 'PDF') return <FilePdfOutlined style={{ color: '#ef4444', fontSize: 18 }} />
  if (upper === 'PPT' || upper === 'PPTX') return <FilePptOutlined style={{ color: '#f59e0b', fontSize: 18 }} />
  return <FileWordOutlined style={{ color: '#2563eb', fontSize: 18 }} />
}

const statusTag = (status?: ResourceItem['processing_status']) => {
  if (status === 'processed') return <Tag color="success">已处理</Tag>
  if (status === 'failed') return <Tag color="error">处理失败</Tag>
  if (status === 'processing') return <Tag icon={<LoadingOutlined />} color="processing">处理中</Tag>
  return <Tag color="default">待处理</Tag>
}

const formatFileSize = (value?: number) => {
  if (!value) return '-'
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

const formatProcessingError = (error?: string | null) => {
  if (!error) return '-'
  if (error.includes('batch size is invalid') && error.includes('should not be larger than 10')) {
    return '向量化失败：embedding 单批文本数量超过 10，请检查 EMBEDDING_BATCH_SIZE 后重试。'
  }
  if (error.includes('task dispatch failed')) {
    return '任务派发失败：请确认 Celery worker 和 Redis 已启动。'
  }
  return error
}

export default function CourseManage() {
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const [courses, setCourses] = useState<CourseItem[]>([])
  const [selectedCourse, setSelectedCourse] = useState<CourseItem | null>(null)
  const [resources, setResources] = useState<ResourceItem[]>([])
  const [createOpen, setCreateOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [loadingResources, setLoadingResources] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
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

  const loadResources = async (courseId: number) => {
    setLoadingResources(true)
    try {
      const { data } = await courseAPI.listResources(courseId)
      setResources(data)
    } catch (error: any) {
      setResources([])
      message.error(error?.response?.data?.detail || '资源列表加载失败')
    } finally {
      setLoadingResources(false)
    }
  }

  useEffect(() => {
    void loadCourses()
  }, [])

  useEffect(() => {
    if (!selectedCourse) {
      setResources([])
      return
    }
    void loadResources(selectedCourse.id)
  }, [selectedCourse?.id])

  useEffect(() => {
    if (!selectedCourse) return
    const hasPending = resources.some((item) => item.processing_status === 'pending' || item.processing_status === 'processing')
    if (!hasPending) return

    const timer = window.setInterval(() => {
      void loadResources(selectedCourse.id)
    }, 3000)

    return () => window.clearInterval(timer)
  }, [selectedCourse?.id, resources])

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
      message.success(data.message || '上传成功，正在处理')
      await loadResources(selectedCourse.id)
    } catch (error: any) {
      const detail = error?.response?.data?.detail || '上传失败'
      const hint = String(detail).includes('task dispatch failed')
        ? '上传成功但任务派发失败，请确认 Celery worker 和 Redis 已启动。'
        : detail
      message.error(hint)
    } finally {
      setUploading(false)
    }
    return false
  }

  const handleDownload = async (resource: ResourceItem) => {
    if (!selectedCourse) return

    setDownloadingId(resource.id)
    try {
      const { data } = await courseAPI.downloadResource(selectedCourse.id, resource.id)
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      link.download = resource.name
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '下载失败')
    } finally {
      setDownloadingId(null)
    }
  }

  const resourceColumns = [
    {
      title: '文件名',
      dataIndex: 'name',
      render: (name: string, row: ResourceItem) => (
        <Space>
          {fileIcon(row.file_type)}
          <span>{name}</span>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      render: (type: string) => <Tag>{(type || 'unknown').toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'processing_status',
      render: (status: ResourceItem['processing_status']) => statusTag(status),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, row: ResourceItem) => (
        <Button
          icon={<DownloadOutlined />}
          size="small"
          loading={downloadingId === row.id}
          onClick={() => void handleDownload(row)}
        >
          下载
        </Button>
      ),
    },
  ]

  const teacherResourceColumns = [
    ...resourceColumns.slice(0, 4),
    {
      title: '错误信息',
      dataIndex: 'processing_error',
      render: (error?: string | null) => (
        error ? <Typography.Text type="danger">{formatProcessingError(error)}</Typography.Text> : '-'
      ),
    },
    resourceColumns[4],
  ]

  const renderCourseCards = () => (
    <Row gutter={[16, 16]}>
      {courses.map((course) => {
        const color = courseColorMap.get(course.id) ?? '#2563eb'
        return (
          <Col key={course.id} xs={24} sm={12} lg={8}>
            <Card
              hoverable
              onClick={() => setSelectedCourse(course)}
              style={{
                borderRadius: 16,
                border: '1px solid #e5edf7',
                boxShadow: '0 8px 24px rgba(15, 23, 42, 0.06)',
                overflow: 'hidden',
              }}
              styles={{ body: { padding: 20 } }}
            >
              <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <Avatar size={48} style={{ background: color, fontWeight: 700, flexShrink: 0 }}>
                  {course.name[0]}
                </Avatar>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <Typography.Text strong style={{ fontSize: 16 }} ellipsis>{course.name}</Typography.Text>
                    <Tag color="blue">{course.code}</Tag>
                  </div>
                  <Typography.Paragraph
                    type="secondary"
                    ellipsis={{ rows: 2 }}
                    style={{ marginBottom: 14, minHeight: 44 }}
                  >
                    {course.description || course.domain}
                  </Typography.Paragraph>
                  <Space size={10} wrap>
                    <Tag>{course.domain}</Tag>
                    <Badge status="processing" text={<span style={{ fontSize: 12 }}>可查看资料</span>} />
                  </Space>
                </div>
              </div>
            </Card>
          </Col>
        )
      })}

      {isTeacher && (
        <Col xs={24} sm={12} lg={8}>
          <Card
            hoverable
            onClick={() => setCreateOpen(true)}
            style={{
              borderRadius: 16,
              border: '2px dashed #cbd5e1',
              minHeight: 156,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            styles={{ body: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 } }}
          >
            <PlusOutlined style={{ fontSize: 28, color: '#94a3b8' }} />
            <span style={{ color: '#64748b' }}>创建新课程</span>
          </Card>
        </Col>
      )}
    </Row>
  )

  if (selectedCourse) {
    const courseColor = courseColorMap.get(selectedCourse.id) ?? '#2563eb'

    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button onClick={() => setSelectedCourse(null)}>返回</Button>
          <Avatar shape="square" size={40} style={{ background: courseColor, fontWeight: 700 }}>
            {selectedCourse.name[0]}
          </Avatar>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>{selectedCourse.name}</div>
            <Space size={6}>
              <Tag color="blue">{selectedCourse.code}</Tag>
              <Tag>{selectedCourse.domain}</Tag>
            </Space>
          </div>
        </div>

        {isTeacher ? (
          <Tabs
            items={[
              {
                key: 'resources',
                label: '课件管理',
                children: (
                  <div>
                    <Upload.Dragger
                      accept=".pdf,.docx,.ppt,.pptx,.xlsx"
                      beforeUpload={handleUpload}
                      showUploadList={false}
                      disabled={uploading}
                      style={{ marginBottom: 16, borderRadius: 12 }}
                    >
                      <p style={{ fontSize: 28 }}><UploadOutlined /></p>
                      <p style={{ fontWeight: 600 }}>{uploading ? '上传中...' : '拖拽上传 PDF / Word / PPT / Excel'}</p>
                      <p style={{ color: '#999', fontSize: 12 }}>上传后由后端异步处理并构建课程知识库</p>
                    </Upload.Dragger>

                    <Table
                      dataSource={resources}
                      rowKey="id"
                      loading={loadingResources}
                      pagination={false}
                      columns={teacherResourceColumns}
                      locale={{ emptyText: '暂无课程资料' }}
                    />
                  </div>
                ),
              },
              {
                key: 'knowledge',
                label: '知识点',
                children: (
                  <Alert
                    type="info"
                    showIcon
                    message="知识点自动生成/树状展示后续接入"
                    description="当前主链路优先完成资料上传、知识入库、RAG 问答和作业批改闭环。"
                  />
                ),
              },
              {
                key: 'students',
                label: '学生名单',
                children: (
                  <Alert
                    type="info"
                    showIcon
                    message="学生名单接口后续接入"
                    description="后端目前已有 enroll 数据表，仍需要补充课程学生列表接口和前端真实数据展示。"
                  />
                ),
              },
              {
                key: 'info',
                label: '课程信息',
                children: (
                  <Card style={{ maxWidth: 560 }}>
                    <Space direction="vertical" size={10}>
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
        ) : (
          <Card
            title="课程资料"
            extra={<Button size="small" onClick={() => void loadResources(selectedCourse.id)}>刷新</Button>}
            style={{ borderRadius: 16 }}
          >
            <Table
              dataSource={resources.filter((item) => item.processing_status === 'processed' || item.is_processed)}
              rowKey="id"
              loading={loadingResources}
              pagination={false}
              columns={resourceColumns}
              locale={{ emptyText: '当前课程暂无可下载资料' }}
            />
          </Card>
        )}
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800 }}>{isTeacher ? '课程管理' : '我的课程'}</div>
          <div style={{ color: '#64748b', marginTop: 4 }}>
            {isTeacher ? '管理课程资料、知识库和课程配置。' : '查看已开放课程资料。'}
          </div>
        </div>
        {isTeacher && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} style={{ borderRadius: 8 }}>
            创建课程
          </Button>
        )}
      </div>

      {courses.length === 0 && !loadingCourses ? (
        <Empty description={isTeacher ? '暂无课程，请先创建课程。' : '暂无课程。'} />
      ) : (
        renderCourseCards()
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
            <Input placeholder="例如：数据结构" />
          </Form.Item>
          <Form.Item name="code" label="课程代码" rules={[{ required: true, message: '请输入课程代码' }]}>
            <Input placeholder="例如：CS102" />
          </Form.Item>
          <Form.Item name="domain" label="课程领域" rules={[{ required: true, message: '请输入课程领域' }]}>
            <Input placeholder="例如：计算机科学" />
          </Form.Item>
          <Form.Item name="description" label="课程描述">
            <Input.TextArea rows={3} placeholder="课程简介" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

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
  Popconfirm,
  Row,
  Space,
  Table,
  Tabs,
  Tag,
  Tree,
  Typography,
  Upload,
  message,
} from 'antd'
import {
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  FilePdfOutlined,
  FilePptOutlined,
  FileWordOutlined,
  LoadingOutlined,
  PlusOutlined,
  ReloadOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import { courseAPI } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type Course = {
  id: number
  name: string
  code: string
  description?: string | null
  domain: string
  teacher_id: number
}

type Resource = {
  id: number
  course_id?: number
  name: string
  file_type?: string
  file_size?: number
  chunk_count?: number
  is_processed?: boolean
  processing_status?: 'pending' | 'processing' | 'processed' | 'failed'
  processing_error?: string | null
  created_at?: string
}

type KnowledgeUnit = {
  id: number
  name: string
  domain: string
  difficulty: number
  description?: string | null
}

type CourseStudent = {
  id: number
  username: string
  email: string
  full_name: string
  enrolled_at: string
}

const colors = ['#2563eb', '#0891b2', '#059669', '#d97706', '#7c3aed', '#dc2626']

const fileIcon = (type?: string) => {
  const upper = (type ?? '').toUpperCase()
  if (upper === 'PDF') return <FilePdfOutlined style={{ color: '#ef4444', fontSize: 18 }} />
  if (upper === 'PPT' || upper === 'PPTX') return <FilePptOutlined style={{ color: '#f59e0b', fontSize: 18 }} />
  return <FileWordOutlined style={{ color: '#2563eb', fontSize: 18 }} />
}

const statusTag = (status?: Resource['processing_status']) => {
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

  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [resources, setResources] = useState<Resource[]>([])
  const [knowledgeUnits, setKnowledgeUnits] = useState<KnowledgeUnit[]>([])
  const [students, setStudents] = useState<CourseStudent[]>([])
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [knowledgeOpen, setKnowledgeOpen] = useState(false)
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [loadingResources, setLoadingResources] = useState(false)
  const [loadingStudents, setLoadingStudents] = useState(false)
  const [savingCourse, setSavingCourse] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [creatingKnowledge, setCreatingKnowledge] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [knowledgeForm] = Form.useForm()

  const colorMap = useMemo(() => {
    return new Map(courses.map((course, index) => [course.id, colors[index % colors.length]]))
  }, [courses])
  const currentColor = selectedCourse ? colorMap.get(selectedCourse.id) ?? colors[0] : colors[0]
  const knowledgeTree: DataNode[] = knowledgeUnits.map((item) => ({
    key: item.id,
    title: (
      <Space>
        <span>{item.name}</span>
        <Tag color="blue">难度 {item.difficulty}</Tag>
        <Tag>{item.domain}</Tag>
      </Space>
    ),
  }))

  const loadCourses = async () => {
    setLoadingCourses(true)
    try {
      const { data } = await courseAPI.list()
      setCourses(data)
      if (selectedCourse) {
        const latest = data.find((item: Course) => item.id === selectedCourse.id)
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

  const loadKnowledgeUnits = async (courseId: number) => {
    try {
      const { data } = await courseAPI.listKnowledgeUnits(courseId)
      setKnowledgeUnits(data)
    } catch (error: any) {
      setKnowledgeUnits([])
      message.error(error?.response?.data?.detail || '知识点加载失败')
    }
  }

  const loadStudents = async (courseId: number) => {
    setLoadingStudents(true)
    try {
      const { data } = await courseAPI.listStudents(courseId)
      setStudents(data)
    } catch (error: any) {
      setStudents([])
      message.error(error?.response?.data?.detail || '学生名单加载失败')
    } finally {
      setLoadingStudents(false)
    }
  }

  useEffect(() => {
    void loadCourses()
  }, [])

  useEffect(() => {
    if (!selectedCourse) {
      setResources([])
      setKnowledgeUnits([])
      setStudents([])
      return
    }
    void loadResources(selectedCourse.id)
    void loadKnowledgeUnits(selectedCourse.id)
    if (isTeacher) void loadStudents(selectedCourse.id)
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

  const saveCourse = async (values: any, mode: 'create' | 'edit') => {
    setSavingCourse(true)
    try {
      if (mode === 'create') {
        const { data } = await courseAPI.create(values)
        message.success('课程创建成功')
        setCreateOpen(false)
        form.resetFields()
        await loadCourses()
        setSelectedCourse(data)
      } else if (selectedCourse) {
        const { data } = await courseAPI.update(selectedCourse.id, values)
        message.success('课程信息已更新')
        setSelectedCourse(data)
        setEditOpen(false)
        await loadCourses()
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || (mode === 'create' ? '课程创建失败' : '课程更新失败，请确认后端已实现 PUT /courses/{course_id}'))
    } finally {
      setSavingCourse(false)
    }
  }

  const deleteCourse = async (course: Course) => {
    try {
      await courseAPI.remove(course.id)
      message.success('课程已删除')
      if (selectedCourse?.id === course.id) setSelectedCourse(null)
      await loadCourses()
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '课程删除失败，请确认后端已实现 DELETE /courses/{course_id}')
    }
  }

  const uploadResource = async (file: File) => {
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

  const deleteResource = async (resource: Resource) => {
    if (!selectedCourse) return
    try {
      await courseAPI.deleteResource(selectedCourse.id, resource.id)
      message.success('课件已删除')
      await loadResources(selectedCourse.id)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '课件删除失败')
    }
  }

  const handleDownload = async (resource: Resource) => {
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

  const createKnowledge = async (values: any) => {
    if (!selectedCourse) return
    setCreatingKnowledge(true)
    try {
      const payload = {
        ...values,
        difficulty: Number(values.difficulty || 1),
        tags: values.tags ? String(values.tags).split(',').map((tag) => tag.trim()).filter(Boolean) : null,
      }
      await courseAPI.createKnowledgeUnit(selectedCourse.id, payload)
      message.success('知识点创建成功')
      setKnowledgeOpen(false)
      knowledgeForm.resetFields()
      await loadKnowledgeUnits(selectedCourse.id)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '创建知识点失败')
    } finally {
      setCreatingKnowledge(false)
    }
  }

  const openEdit = () => {
    if (!selectedCourse) return
    editForm.setFieldsValue(selectedCourse)
    setEditOpen(true)
  }

  const resourceColumns = [
    {
      title: '文件名',
      dataIndex: 'name',
      render: (name: string, row: Resource) => (
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
      title: '切片数',
      dataIndex: 'chunk_count',
      render: (count?: number) => count ?? 0,
    },
    {
      title: '状态',
      dataIndex: 'processing_status',
      render: (status: Resource['processing_status']) => statusTag(status),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, row: Resource) => (
        <Space>
          <Button
            icon={<DownloadOutlined />}
            size="small"
            loading={downloadingId === row.id}
            onClick={() => void handleDownload(row)}
          >
            下载
          </Button>
          {isTeacher && (
            <Popconfirm
              title="确认删除该课件？"
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              onConfirm={() => void deleteResource(row)}
            >
              <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const teacherResourceColumns = [
    ...resourceColumns.slice(0, 5),
    {
      title: '错误信息',
      dataIndex: 'processing_error',
      render: (error?: string | null) => (
        error ? <Typography.Text type="danger">{formatProcessingError(error)}</Typography.Text> : '-'
      ),
    },
    resourceColumns[5],
  ]

  const formItems = (
    <>
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
    </>
  )

  const renderCourseCards = () => (
    <Row gutter={[16, 16]}>
      {courses.map((course) => {
        const color = colorMap.get(course.id) ?? colors[0]
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
              actions={isTeacher ? [
                <span key="enter" onClick={() => setSelectedCourse(course)}>进入课程</span>,
                <Popconfirm
                  key="delete"
                  title="确认删除课程？"
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                  onConfirm={() => void deleteCourse(course)}
                >
                  <Typography.Text type="danger" onClick={(event) => event.stopPropagation()}>删除</Typography.Text>
                </Popconfirm>,
              ] : undefined}
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

  if (!isTeacher) {
    return (
      <div>
        <Typography.Title level={4}>我的课程</Typography.Title>
        {courses.length === 0 && !loadingCourses ? (
          <Empty description="暂无课程。" />
        ) : (
          renderCourseCards()
        )}
      </div>
    )
  }

  if (selectedCourse) {
    return (
      <div>
        <Space style={{ marginBottom: 24, width: '100%' }} wrap>
          <Button onClick={() => setSelectedCourse(null)}>返回</Button>
          <Avatar shape="square" size={40} style={{ background: currentColor, fontWeight: 700 }}>
            {selectedCourse.name[0]}
          </Avatar>
          <Typography.Text strong style={{ fontSize: 20 }}>{selectedCourse.name}</Typography.Text>
          <Tag color="blue">{selectedCourse.code}</Tag>
          <Tag>{selectedCourse.domain}</Tag>
          <Space style={{ marginLeft: 'auto' }}>
            <Button icon={<EditOutlined />} onClick={openEdit}>修改课程信息</Button>
            <Popconfirm
              title="确认删除课程？"
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              onConfirm={() => void deleteCourse(selectedCourse)}
            >
              <Button danger icon={<DeleteOutlined />}>删除课程</Button>
            </Popconfirm>
          </Space>
        </Space>

        <Tabs
          items={[
            {
              key: 'resources',
              label: '课件管理',
              children: (
                <div>
                  <Upload.Dragger
                    accept=".pdf,.docx,.ppt,.pptx,.xlsx"
                    beforeUpload={uploadResource}
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
                    locale={{ emptyText: <Empty description="暂无资源记录" /> }}
                  />
                </div>
              ),
            },
            {
              key: 'knowledge',
              label: '知识点',
              children: (
                <Row gutter={24}>
                  <Col flex="auto">
                    <Space style={{ marginBottom: 12 }}>
                      <Button icon={<ReloadOutlined />} onClick={() => void loadKnowledgeUnits(selectedCourse.id)}>刷新</Button>
                      <Button type="primary" icon={<PlusOutlined />} onClick={() => setKnowledgeOpen(true)}>新增知识点</Button>
                    </Space>
                    {knowledgeTree.length ? (
                      <Tree treeData={knowledgeTree} defaultExpandAll showLine={{ showLeafIcon: false }} />
                    ) : (
                      <Empty description="暂无知识点，可点击新增知识点" />
                    )}
                  </Col>
                  <Col style={{ width: 280 }}>
                    <Alert
                      type="info"
                      showIcon
                      message="知识点管理"
                      description="可手动新增知识点，创建完成后列表会自动刷新。"
                    />
                  </Col>
                </Row>
              ),
            },
            {
              key: 'students',
              label: '学生名单',
              children: (
                <Table
                  rowKey="id"
                  dataSource={students}
                  loading={loadingStudents}
                  columns={[
                    { title: '学生', dataIndex: 'full_name' },
                    { title: '用户名', dataIndex: 'username' },
                    { title: '邮箱', dataIndex: 'email' },
                    {
                      title: '选课时间',
                      dataIndex: 'enrolled_at',
                      render: (value: string) => value ? new Date(value).toLocaleString() : '-',
                    },
                  ]}
                  locale={{ emptyText: '暂无学生选课记录' }}
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
                    <Button icon={<EditOutlined />} onClick={openEdit}>修改课程信息</Button>
                  </Space>
                </Card>
              ),
            },
          ]}
        />

        <Modal
          title="修改课程信息"
          open={editOpen}
          onCancel={() => setEditOpen(false)}
          onOk={() => editForm.submit()}
          okText="保存"
          confirmLoading={savingCourse}
        >
          <Form form={editForm} layout="vertical" onFinish={(values) => void saveCourse(values, 'edit')}>
            {formItems}
          </Form>
        </Modal>

        <Modal
          title="新增知识点"
          open={knowledgeOpen}
          onCancel={() => { setKnowledgeOpen(false); knowledgeForm.resetFields() }}
          onOk={() => knowledgeForm.submit()}
          okText="创建"
          confirmLoading={creatingKnowledge}
        >
          <Form
            form={knowledgeForm}
            layout="vertical"
            onFinish={createKnowledge}
            initialValues={{ domain: selectedCourse.domain, difficulty: 1 }}
          >
            <Form.Item name="name" label="知识点名称" rules={[{ required: true, message: '请输入知识点名称' }]}>
              <Input placeholder="如：变量与数据类型" />
            </Form.Item>
            <Form.Item name="domain" label="所属领域" rules={[{ required: true, message: '请输入所属领域' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="difficulty" label="难度" rules={[{ required: true, message: '请输入难度' }]}>
              <Input type="number" min={1} max={5} />
            </Form.Item>
            <Form.Item name="tags" label="标签">
              <Input placeholder="多个标签用英文逗号分隔" />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={3} />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800 }}>课程管理</div>
          <div style={{ color: '#64748b', marginTop: 4 }}>管理课程资料、知识库和课程配置。</div>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} style={{ borderRadius: 8 }}>
          创建课程
        </Button>
      </div>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="课程管理"
        description="点击课程卡片进入课件、知识点与课程信息管理页面。"
      />

      {courses.length === 0 && !loadingCourses ? (
        <Empty description="暂无课程，请先创建课程。" />
      ) : (
        renderCourseCards()
      )}

      <Modal
        title="创建课程"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="创建"
        confirmLoading={savingCourse}
      >
        <Form form={form} layout="vertical" onFinish={(values) => void saveCourse(values, 'create')} style={{ marginTop: 16 }}>
          {formItems}
        </Form>
      </Modal>
    </div>
  )
}

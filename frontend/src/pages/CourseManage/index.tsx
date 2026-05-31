import { useEffect, useMemo, useState } from 'react'
import { Alert, Avatar, Button, Card, Col, Empty, Form, Input, message, Modal, Popconfirm, Row, Space, Table, Tabs, Tag, Tree, Typography, Upload } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, FilePdfOutlined, FilePptOutlined, FileWordOutlined, LoadingOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import { courseAPI } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type Course = { id: number; name: string; code: string; description?: string | null; domain: string; teacher_id: number }
type Resource = { id: number; name: string; file_type?: string; chunk_count?: number; processing_status?: 'pending' | 'processing' | 'processed' | 'failed'; processing_error?: string | null }
type KnowledgeUnit = { id: number; name: string; domain: string; difficulty: number; description?: string | null }

const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#14b8a6']
const students = [{ id: 1, name: '张三', email: 'zhangsan@example.com', score: 85 }, { id: 2, name: '李四', email: 'lisi@example.com', score: 72 }, { id: 3, name: '王五', email: 'wangwu@example.com', score: 58 }]

const fileIcon = (type?: string) => {
  const upper = (type || '').toUpperCase()
  if (upper === 'PDF') return <FilePdfOutlined style={{ color: '#ff4d4f' }} />
  if (upper === 'PPT' || upper === 'PPTX') return <FilePptOutlined style={{ color: '#faad14' }} />
  return <FileWordOutlined style={{ color: '#00a8ff' }} />
}

const statusTag = (status?: Resource['processing_status']) => {
  if (status === 'processed') return <Tag color="success">已处理</Tag>
  if (status === 'failed') return <Tag color="error">处理失败</Tag>
  if (status === 'processing') return <Tag icon={<LoadingOutlined />} color="processing">处理中</Tag>
  return <Tag>待处理</Tag>
}

const formatError = (error?: string | null) => {
  if (!error) return '-'
  if (error.includes('task dispatch failed')) return '任务派发失败：请确认 Celery Worker 与 Redis 已启动。'
  return error
}

export default function CourseManage() {
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [resources, setResources] = useState<Resource[]>([])
  const [knowledgeUnits, setKnowledgeUnits] = useState<KnowledgeUnit[]>([])
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [knowledgeOpen, setKnowledgeOpen] = useState(false)
  const [creatingKnowledge, setCreatingKnowledge] = useState(false)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [knowledgeForm] = Form.useForm()

  const colorMap = useMemo(() => new Map(courses.map((c, i) => [c.id, colors[i % colors.length]])), [courses])
  const currentColor = selectedCourse ? colorMap.get(selectedCourse.id) || colors[0] : colors[0]
  const knowledgeTree: DataNode[] = knowledgeUnits.map((item) => ({ key: item.id, title: <Space><span>{item.name}</span><Tag color="blue">难度 {item.difficulty}</Tag><Tag>{item.domain}</Tag></Space> }))

  const loadCourses = async () => {
    setLoading(true)
    try {
      const { data } = await courseAPI.list()
      setCourses(data)
      if (selectedCourse) setSelectedCourse(data.find((c: Course) => c.id === selectedCourse.id) || null)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '加载课程失败')
    } finally {
      setLoading(false)
    }
  }

  const loadResources = async (courseId: number) => {
    try {
      const { data } = await courseAPI.listResources(courseId)
      setResources(data)
    } catch (error: any) {
      setResources([])
      message.error(error?.response?.data?.detail || '资源列表加载失败')
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

  useEffect(() => { void loadCourses() }, [])
  useEffect(() => {
    if (!selectedCourse) { setResources([]); setKnowledgeUnits([]); return }
    void loadResources(selectedCourse.id)
    void loadKnowledgeUnits(selectedCourse.id)
  }, [selectedCourse?.id])

  const saveCourse = async (values: any, mode: 'create' | 'edit') => {
    setLoading(true)
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
      message.error(error?.response?.data?.detail || '课程更新失败')
    } finally {
      setLoading(false)
    }
  }

  const deleteCourse = async (course: Course) => {
    try {
      await courseAPI.remove(course.id)
      message.success('课程已删除')
      if (selectedCourse?.id === course.id) setSelectedCourse(null)
      await loadCourses()
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '课程删除失败')
    }
  }

  const uploadResource = async (file: File) => {
    if (!selectedCourse) return false
    setUploading(true)
    try {
      const { data } = await courseAPI.uploadResource(selectedCourse.id, file)
      message.success(data.message || '上传成功，正在处理中')
      await loadResources(selectedCourse.id)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '上传失败，请稍后重试或确认文件格式正确')
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

  const createKnowledge = async (values: any) => {
    if (!selectedCourse) return
    setCreatingKnowledge(true)
    try {
      const payload = {
        ...values,
        difficulty: Number(values.difficulty || 1),
        tags: values.tags ? { values: String(values.tags).split(',').map((tag) => tag.trim()).filter(Boolean) } : null,
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

  const formItems = <><Form.Item name="name" label="课程名称" rules={[{ required: true, message: '请输入课程名称' }]}><Input /></Form.Item><Form.Item name="code" label="课程代码" rules={[{ required: true, message: '请输入课程代码' }]}><Input /></Form.Item><Form.Item name="domain" label="课程领域" rules={[{ required: true, message: '请输入课程领域' }]}><Input /></Form.Item><Form.Item name="description" label="课程描述"><Input.TextArea rows={3} /></Form.Item></>

  if (!isTeacher) return <div><Typography.Title level={4}>我的课程</Typography.Title><Row gutter={[16, 16]}>{courses.map((course) => <Col key={course.id} xs={24} sm={12} lg={8}><Card title={course.name}><Tag color="blue">{course.code}</Tag><p>{course.description || course.domain}</p></Card></Col>)}</Row></div>

  if (selectedCourse) return <div>
    <Space style={{ marginBottom: 24, width: '100%' }} wrap>
      <Button onClick={() => setSelectedCourse(null)}>← 返回</Button><Avatar style={{ background: currentColor }}>{selectedCourse.name[0]}</Avatar><Typography.Text strong style={{ fontSize: 20 }}>{selectedCourse.name}</Typography.Text><Tag color="blue">{selectedCourse.code}</Tag><Tag>{selectedCourse.domain}</Tag>
      <Space style={{ marginLeft: 'auto' }}><Button icon={<EditOutlined />} onClick={openEdit}>修改课程信息</Button><Popconfirm title="确认删除课程？" okText="删除" cancelText="取消" okButtonProps={{ danger: true }} onConfirm={() => deleteCourse(selectedCourse)}><Button danger icon={<DeleteOutlined />}>删除课程</Button></Popconfirm></Space>
    </Space>
    <Tabs items={[{
      key: 'resources', label: '课件管理', children: <><Upload.Dragger accept=".pdf,.doc,.docx,.ppt,.pptx" beforeUpload={uploadResource} showUploadList={false} disabled={uploading} style={{ marginBottom: 16 }}><p style={{ fontSize: 28 }}><UploadOutlined /></p><p>{uploading ? '上传中...' : '拖拽上传 PDF / Word / PPT'}</p></Upload.Dragger><Table rowKey="id" dataSource={resources} pagination={false} locale={{ emptyText: <Empty description="暂无资源记录" /> }} columns={[{ title: '文件名', dataIndex: 'name', render: (name: string, row: Resource) => <Space>{fileIcon(row.file_type)}{name}</Space> }, { title: '类型', dataIndex: 'file_type', render: (v: string) => <Tag>{(v || '未知').toUpperCase()}</Tag> }, { title: '切片数', dataIndex: 'chunk_count', render: (v?: number) => v ?? 0 }, { title: '状态', dataIndex: 'processing_status', render: statusTag }, { title: '错误信息', dataIndex: 'processing_error', render: (v?: string | null) => <Typography.Text type={v ? 'danger' : undefined}>{formatError(v)}</Typography.Text> }, { title: '操作', render: (_, row: Resource) => <Popconfirm title="确认删除该课件？" okText="删除" cancelText="取消" okButtonProps={{ danger: true }} onConfirm={() => deleteResource(row)}><Button size="small" danger icon={<DeleteOutlined />}>删除课件</Button></Popconfirm> }]} /></>
    }, {
      key: 'knowledge', label: '知识点', children: <Row gutter={24}><Col flex="auto"><Space style={{ marginBottom: 12 }}><Button icon={<ReloadOutlined />} onClick={() => loadKnowledgeUnits(selectedCourse.id)}>刷新</Button><Button type="primary" icon={<PlusOutlined />} onClick={() => setKnowledgeOpen(true)}>新增知识点</Button></Space>{knowledgeTree.length ? <Tree treeData={knowledgeTree} defaultExpandAll showLine={{ showLeafIcon: false }} /> : <Empty description="暂无知识点，可点击新增知识点" />}</Col><Col style={{ width: 280 }}><Alert type="info" showIcon message="知识点管理" description="可手动新增知识点，创建完成后列表会自动刷新。" /></Col></Row>
    }, {
      key: 'students', label: '学生名单', children: <Table rowKey="id" dataSource={students} columns={[{ title: '学生', dataIndex: 'name' }, { title: '邮箱', dataIndex: 'email' }, { title: '平均分', dataIndex: 'score' }]} />
    }, {
      key: 'info', label: '课程信息', children: <Card style={{ maxWidth: 560 }}><Space direction="vertical"><div><b>课程名称：</b>{selectedCourse.name}</div><div><b>课程代码：</b>{selectedCourse.code}</div><div><b>所属领域：</b>{selectedCourse.domain}</div><div><b>课程描述：</b>{selectedCourse.description || '暂无描述'}</div><Button icon={<EditOutlined />} onClick={openEdit}>修改课程信息</Button></Space></Card>
    }]} />
    <Modal title="修改课程信息" open={editOpen} onCancel={() => setEditOpen(false)} onOk={() => editForm.submit()} okText="保存" confirmLoading={loading}><Form form={editForm} layout="vertical" onFinish={(v) => saveCourse(v, 'edit')}>{formItems}</Form></Modal>
    <Modal title="新增知识点" open={knowledgeOpen} onCancel={() => { setKnowledgeOpen(false); knowledgeForm.resetFields() }} onOk={() => knowledgeForm.submit()} okText="创建" confirmLoading={creatingKnowledge}>
      <Form form={knowledgeForm} layout="vertical" onFinish={createKnowledge} initialValues={{ domain: selectedCourse.domain, difficulty: 1 }}>
        <Form.Item name="name" label="知识点名称" rules={[{ required: true, message: '请输入知识点名称' }]}><Input placeholder="如：变量与数据类型" /></Form.Item>
        <Form.Item name="domain" label="所属领域" rules={[{ required: true, message: '请输入所属领域' }]}><Input /></Form.Item>
        <Form.Item name="difficulty" label="难度" rules={[{ required: true, message: '请输入难度' }]}><Input type="number" min={1} max={5} /></Form.Item>
        <Form.Item name="tags" label="标签"><Input placeholder="多个标签用英文逗号分隔" /></Form.Item>
        <Form.Item name="description" label="描述"><Input.TextArea rows={3} /></Form.Item>
      </Form>
    </Modal>
  </div>

  return <div><Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }}><Typography.Title level={4} style={{ margin: 0 }}>课程管理</Typography.Title><Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建课程</Button></Space><Alert type="info" showIcon style={{ marginBottom: 16 }} message="课程管理" description="点击课程卡片进入课件、知识点与课程信息管理页面。" />{courses.length === 0 && !loading ? <Empty description="暂无课程，请先创建课程" /> : <Row gutter={[16, 16]}>{courses.map((course) => { const color = colorMap.get(course.id) || colors[0]; return <Col key={course.id} xs={24} sm={12} lg={8}><Card hoverable title={<Space><Avatar style={{ background: color }}>{course.name[0]}</Avatar>{course.name}</Space>} actions={[<span onClick={() => setSelectedCourse(course)}>进入课程</span>, <Popconfirm title="确认删除课程？" okText="删除" cancelText="取消" okButtonProps={{ danger: true }} onConfirm={() => deleteCourse(course)}><Typography.Text type="danger">删除</Typography.Text></Popconfirm>]}><Tag color="blue">{course.code}</Tag><Tag>{course.domain}</Tag><p style={{ marginTop: 12 }}>{course.description || '暂无描述'}</p></Card></Col> })}</Row>}<Modal title="创建课程" open={createOpen} onCancel={() => { setCreateOpen(false); form.resetFields() }} onOk={() => form.submit()} okText="创建" confirmLoading={loading}><Form form={form} layout="vertical" onFinish={(v) => saveCourse(v, 'create')}>{formItems}</Form></Modal></div>
}

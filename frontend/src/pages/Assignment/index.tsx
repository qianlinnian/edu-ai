import { useEffect, useMemo, useState } from 'react'
import {
  Alert, Avatar, Button, Card, Col, Empty, Form, Input, message, Modal, Row,
  Select, Space, Table, Tabs, Tag, Typography, Upload,
} from 'antd'
import {
  ArrowLeftOutlined, CodeOutlined, EyeOutlined, PlusOutlined, RobotOutlined, SendOutlined, UploadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { assignmentAPI, courseAPI, getErrorMessage } from '../../services/api'
import { useAuthStore } from '../../hooks/useAuthStore'

type Course = { id: number; name: string; code: string; domain: string; description?: string | null }
type AssignmentItem = {
  id: number
  course_id: number
  title: string
  description?: string | null
  assignment_type: string
  max_score: number
  courseName?: string
  courseCode?: string
}
type Submission = {
  id: number
  assignment_id: number
  student_id: number
  content?: string | null
  file_path?: string | null
  status?: 'pending' | 'grading' | 'graded' | 'failed'
  submitted_at?: string
}

const statusTag = (status?: Submission['status']) => {
  if (status === 'graded') return <Tag color="success">已批改</Tag>
  if (status === 'grading') return <Tag color="processing">批改中</Tag>
  if (status === 'failed') return <Tag color="error">批改失败</Tag>
  return <Tag>待批改</Tag>
}

export default function Assignment() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const [courses, setCourses] = useState<Course[]>([])
  const [assignments, setAssignments] = useState<AssignmentItem[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<number | undefined>()
  const [selectedAssignment, setSelectedAssignment] = useState<AssignmentItem | null>(null)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null)
  const [loading, setLoading] = useState(false)
  const [submissionsLoading, setSubmissionsLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [submitOpen, setSubmitOpen] = useState<AssignmentItem | null>(null)
  const [submitMode, setSubmitMode] = useState<'code' | 'file'>('code')
  const [codeContent, setCodeContent] = useState('')
  const [submitFile, setSubmitFile] = useState<File | undefined>()
  const [submitting, setSubmitting] = useState(false)
  const [createForm] = Form.useForm()

  const courseOptions = useMemo(
    () => courses.map((course) => ({ value: course.id, label: `${course.name}（${course.code}）` })),
    [courses],
  )
  const visibleAssignments = selectedCourseId
    ? assignments.filter((item) => item.course_id === selectedCourseId)
    : assignments

  const loadAssignments = async (courseList: Course[]) => {
    const result = await Promise.allSettled(courseList.map(async (course) => {
      const { data } = await assignmentAPI.list(course.id)
      return data.map((item: AssignmentItem) => ({
        ...item,
        courseName: course.name,
        courseCode: course.code,
      }))
    }))
    const fulfilled = result
      .filter((r): r is PromiseFulfilledResult<AssignmentItem[]> => r.status === 'fulfilled')
      .map(r => r.value)
    const rejected = result.filter((r): r is PromiseRejectedResult => r.status === 'rejected')
    if (rejected.length > 0) {
      message.warning(`部分课程作业加载失败（${rejected.length}/${courseList.length} 个课程）`)
    }
    setAssignments(fulfilled.flat())
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const { data: courseData } = await courseAPI.list()
      setCourses(courseData)
      if (courseData.length && !selectedCourseId) setSelectedCourseId(courseData[0].id)
      await loadAssignments(courseData)
    } catch (error) {
      message.error(getErrorMessage(error, '作业数据加载失败'))
    } finally {
      setLoading(false)
    }
  }

  const loadSubmissions = async (assignmentId: number) => {
    setSubmissionsLoading(true)
    try {
      const { data } = await assignmentAPI.listSubmissions(assignmentId)
      setSubmissions(data)
    } catch (error) {
      setSubmissions([])
      message.error(getErrorMessage(error, '提交列表加载失败'))
    } finally {
      setSubmissionsLoading(false)
    }
  }

  useEffect(() => { void loadData() }, [])

  const openAssignmentDetail = async (assignment: AssignmentItem) => {
    setSelectedAssignment(assignment)
    setSelectedSubmission(null)
    await loadSubmissions(assignment.id)
  }

  const closeAssignmentDetail = () => {
    setSelectedAssignment(null)
    setSubmissions([])
    setSelectedSubmission(null)
  }

  const handleTeacherAIClick = async (assignment: AssignmentItem) => {
    message.info('学生提交后会自动进入 AI 批改流程，可在提交列表中查看批改进度。')
    await openAssignmentDetail(assignment)
  }

  const createAssignment = async (values: any) => {
    setLoading(true)
    try {
      await assignmentAPI.create({
        course_id: values.course_id,
        title: values.title,
        description: values.description,
        assignment_type: values.assignment_type || 'text',
        max_score: Number(values.max_score || 100),
        rubric: values.rubric ? { text: values.rubric } : null,
        reference_answer: values.reference_answer || null,
        knowledge_points: null,
      })
      message.success('作业创建成功')
      setCreateOpen(false)
      createForm.resetFields()
      await loadData()
    } catch (error) {
      message.error(getErrorMessage(error, '作业创建失败'))
    } finally {
      setLoading(false)
    }
  }

  const submitAssignment = async () => {
    if (!submitOpen) return
    if (submitMode === 'code' && !codeContent.trim()) {
      message.warning('请输入提交内容')
      return
    }
    if (submitMode === 'file' && !submitFile) {
      message.warning('请先选择上传文件')
      return
    }
    setSubmitting(true)
    try {
      const { data } = await assignmentAPI.submit(
        submitOpen.id,
        submitMode === 'code' ? codeContent : undefined,
        submitMode === 'file' ? submitFile : undefined,
      )
      message.success(data?.message || '提交成功，正在批改中')
      const submissionId = data?.id
      setSubmitOpen(null)
      setCodeContent('')
      setSubmitFile(undefined)
      if (selectedAssignment) await loadSubmissions(selectedAssignment.id)
      if (submissionId) navigate(`/grading/${submissionId}`)
    } catch (error) {
      message.error(getErrorMessage(error, '提交失败'))
    } finally {
      setSubmitting(false)
    }
  }

  const detailContent = (assignment: AssignmentItem) => (
    <Space direction="vertical" size={14} style={{ width: '100%' }}>
      <Row gutter={[16, 12]}>
        <Col xs={24} md={12}>
          <Typography.Text type="secondary">作业名称</Typography.Text>
          <div style={{ fontWeight: 600 }}>{assignment.title}</div>
        </Col>
        <Col xs={24} md={12}>
          <Typography.Text type="secondary">所属课程</Typography.Text>
          <div><Tag color="blue">{assignment.courseName || assignment.course_id}</Tag></div>
        </Col>
        <Col xs={24} md={12}>
          <Typography.Text type="secondary">作业类型</Typography.Text>
          <div>{assignment.assignment_type}</div>
        </Col>
        <Col xs={24} md={12}>
          <Typography.Text type="secondary">满分</Typography.Text>
          <div>{assignment.max_score} 分</div>
        </Col>
      </Row>
      <div>
        <Typography.Text type="secondary">作业说明</Typography.Text>
        <Typography.Paragraph style={{ marginTop: 6, whiteSpace: 'pre-wrap' }}>
          {assignment.description || '暂无说明'}
        </Typography.Paragraph>
      </div>
    </Space>
  )

  const submissionColumns = [
    { title: '提交ID', dataIndex: 'id' },
    ...(isTeacher ? [{
      title: '学生ID',
      dataIndex: 'student_id',
      render: (id: number) => <Space><Avatar size="small">{id}</Avatar>学生 {id}</Space>,
    }] : []),
    { title: '提交时间', dataIndex: 'submitted_at', render: (v?: string) => v ? new Date(v).toLocaleString() : '-' },
    { title: '提交方式', render: (_: unknown, row: Submission) => row.file_path ? <Tag>文件</Tag> : <Tag>文本</Tag> },
    { title: '批改状态', dataIndex: 'status', render: statusTag },
    {
      title: '操作',
      render: (_: unknown, row: Submission) => (
        <Space>
          <Button size="small" onClick={() => setSelectedSubmission(row)}>查看内容</Button>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/grading/${row.id}`)}>查看批改</Button>
        </Space>
      ),
    },
  ]

  if (selectedAssignment) {
    return <div>
      <Space style={{ marginBottom: 24 }} wrap>
        <Button icon={<ArrowLeftOutlined />} onClick={closeAssignmentDetail}>返回</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>{selectedAssignment.title}</Typography.Title>
        <Tag color="blue">{selectedAssignment.courseName}</Tag>
      </Space>

      <Card title="作业信息" style={{ marginBottom: 16, borderRadius: 8 }}>
        {detailContent(selectedAssignment)}
      </Card>

      {isTeacher ? (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="学生提交后会自动触发 AI 批改，可在下方列表查看批改进度与结果入口。"
        />
      ) : (
        <Card style={{ marginBottom: 16, borderRadius: 8 }}>
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Typography.Text strong>提交作业</Typography.Text>
            <Typography.Text type="secondary">
              可以先查看作业信息和历史提交；需要再次提交时，点击下方按钮。已有提交可以直接查看批改内容。
            </Typography.Text>
            <Button type="primary" icon={<SendOutlined />} onClick={() => setSubmitOpen(selectedAssignment)}>
              提交作业
            </Button>
          </Space>
        </Card>
      )}

      <Card title={isTeacher ? '学生提交列表' : '我的提交记录'} style={{ borderRadius: 8 }}>
        <Table
          loading={submissionsLoading}
          dataSource={submissions}
          rowKey="id"
          columns={submissionColumns}
          locale={{ emptyText: <Empty description={isTeacher ? '暂无学生提交' : '暂无提交记录'} /> }}
        />
      </Card>

      <Modal
        title="提交内容"
        open={selectedSubmission !== null}
        onCancel={() => setSelectedSubmission(null)}
        footer={<Button type="primary" onClick={() => setSelectedSubmission(null)}>关闭</Button>}
        width={760}
      >
        {selectedSubmission && (
          <Space direction="vertical" size={14} style={{ width: '100%' }}>
            <Row gutter={[16, 12]}>
              <Col xs={24} md={12}><Typography.Text type="secondary">提交ID</Typography.Text><div>{selectedSubmission.id}</div></Col>
              <Col xs={24} md={12}><Typography.Text type="secondary">学生ID</Typography.Text><div>{selectedSubmission.student_id}</div></Col>
              <Col xs={24} md={12}><Typography.Text type="secondary">提交时间</Typography.Text><div>{selectedSubmission.submitted_at ? new Date(selectedSubmission.submitted_at).toLocaleString() : '-'}</div></Col>
              <Col xs={24} md={12}><Typography.Text type="secondary">批改状态</Typography.Text><div>{statusTag(selectedSubmission.status)}</div></Col>
            </Row>
            <div>
              <Typography.Text type="secondary">文本内容</Typography.Text>
              <Card size="small" style={{ marginTop: 6, background: '#fafafa' }}>
                <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                  {selectedSubmission.content?.trim() || '该提交未填写文本内容'}
                </Typography.Paragraph>
              </Card>
            </div>
            <div>
              <Typography.Text type="secondary">附件路径</Typography.Text>
              <Card size="small" style={{ marginTop: 6, background: '#fafafa' }}>
                <Typography.Paragraph style={{ marginBottom: 0, wordBreak: 'break-all' }}>
                  {selectedSubmission.file_path || '该提交未上传附件'}
                </Typography.Paragraph>
              </Card>
            </div>
          </Space>
        )}
      </Modal>

      <SubmitModal
        openAssignment={submitOpen}
        submitMode={submitMode}
        codeContent={codeContent}
        submitting={submitting}
        onCancel={() => setSubmitOpen(null)}
        onSubmit={submitAssignment}
        onModeChange={setSubmitMode}
        onCodeChange={setCodeContent}
        onFileChange={setSubmitFile}
      />
    </div>
  }

  const assignmentColumns = [
    {
      title: '作业名称',
      dataIndex: 'title',
      render: (title: string, row: AssignmentItem) => <Button type="link" onClick={() => void openAssignmentDetail(row)}>{title}</Button>,
    },
    { title: '课程', render: (_: unknown, row: AssignmentItem) => <Tag color="blue">{row.courseName || row.course_id}</Tag> },
    { title: '作业类型', dataIndex: 'assignment_type' },
    { title: '满分', dataIndex: 'max_score', render: (score: number) => `${score} 分` },
    {
      title: '操作',
      render: (_: unknown, row: AssignmentItem) => isTeacher ? (
        <Space>
          <Button size="small" onClick={() => void openAssignmentDetail(row)}>查看提交</Button>
          <Button size="small" icon={<RobotOutlined />} type="primary" ghost onClick={() => void handleTeacherAIClick(row)}>查看批改进度</Button>
        </Space>
      ) : (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => void openAssignmentDetail(row)}>查看详情</Button>
          <Button size="small" type="primary" icon={<SendOutlined />} onClick={() => setSubmitOpen(row)}>提交作业</Button>
        </Space>
      ),
    },
  ]

  return <div>
    <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }} wrap>
      <Typography.Title level={4} style={{ margin: 0 }}>{isTeacher ? '作业管理' : '我的作业'}</Typography.Title>
      <Space>
        <Select
          allowClear
          placeholder="筛选课程"
          style={{ width: 260 }}
          options={courseOptions}
          value={selectedCourseId}
          onChange={setSelectedCourseId}
        />
        {isTeacher && <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建作业</Button>}
      </Space>
    </Space>

    <Table
      loading={loading}
      dataSource={visibleAssignments}
      rowKey="id"
      columns={assignmentColumns}
      locale={{ emptyText: <Empty description="暂无作业" /> }}
    />

    <Modal title="创建作业" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => createForm.submit()} okText="创建" confirmLoading={loading}>
      <Form form={createForm} layout="vertical" onFinish={createAssignment} initialValues={{ course_id: selectedCourseId, assignment_type: 'text', max_score: 100 }}>
        <Form.Item name="title" label="作业标题" rules={[{ required: true, message: '请输入作业标题' }]}><Input /></Form.Item>
        <Form.Item name="course_id" label="所属课程" rules={[{ required: true, message: '请选择课程' }]}><Select options={courseOptions} /></Form.Item>
        <Form.Item name="assignment_type" label="作业类型"><Select options={[{ value: 'text', label: '文本' }, { value: 'code', label: '代码' }, { value: 'mixed', label: '混合' }]} /></Form.Item>
        <Form.Item name="max_score" label="满分"><Input type="number" min={1} /></Form.Item>
        <Form.Item name="description" label="作业说明"><Input.TextArea rows={3} /></Form.Item>
        <Form.Item name="rubric" label="评分标准"><Input.TextArea rows={2} /></Form.Item>
        <Form.Item name="reference_answer" label="参考答案"><Input.TextArea rows={2} /></Form.Item>
      </Form>
    </Modal>

    <SubmitModal
      openAssignment={submitOpen}
      submitMode={submitMode}
      codeContent={codeContent}
      submitting={submitting}
      onCancel={() => setSubmitOpen(null)}
      onSubmit={submitAssignment}
      onModeChange={setSubmitMode}
      onCodeChange={setCodeContent}
      onFileChange={setSubmitFile}
    />
  </div>
}

type SubmitModalProps = {
  openAssignment: AssignmentItem | null
  submitMode: 'code' | 'file'
  codeContent: string
  submitting: boolean
  onCancel: () => void
  onSubmit: () => void
  onModeChange: (mode: 'code' | 'file') => void
  onCodeChange: (value: string) => void
  onFileChange: (file: File | undefined) => void
}

function SubmitModal({
  openAssignment,
  submitMode,
  codeContent,
  submitting,
  onCancel,
  onSubmit,
  onModeChange,
  onCodeChange,
  onFileChange,
}: SubmitModalProps) {
  return (
    <Modal
      title="提交作业"
      open={openAssignment !== null}
      onCancel={onCancel}
      onOk={onSubmit}
      okText="提交"
      confirmLoading={submitting}
      width={640}
    >
      <Tabs activeKey={submitMode} onChange={(key) => onModeChange(key as 'code' | 'file')} items={[
        {
          key: 'code',
          label: <span><CodeOutlined /> 在线编辑</span>,
          children: (
            <Input.TextArea
              value={codeContent}
              onChange={(e) => onCodeChange(e.target.value)}
              rows={12}
              placeholder="在此输入代码或文字内容..."
              style={{ fontFamily: 'monospace' }}
            />
          ),
        },
        {
          key: 'file',
          label: <span><UploadOutlined /> 上传文件</span>,
          children: (
            <Upload.Dragger
              accept=".py,.txt,.md,.pdf,.docx,.pptx,.xlsx,.csv,.json"
              maxCount={1}
              beforeUpload={(file) => {
                onFileChange(file)
                return false
              }}
              onRemove={() => onFileChange(undefined)}
            >
              <p style={{ fontSize: 24 }}><UploadOutlined /></p>
              <p>点击或拖拽上传 .py / .txt / .md / .pdf / .docx / .pptx / .xlsx / .csv / .json</p>
            </Upload.Dragger>
          ),
        },
      ]} />
    </Modal>
  )
}

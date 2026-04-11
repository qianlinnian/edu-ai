import { useState } from 'react'
import {
  Card, Table, Tag, Button, Modal, Form, Input, DatePicker,
  Upload, message, Space, Avatar, Progress, Tabs, Select,
  Popconfirm, Typography,
} from 'antd'
import {
  PlusOutlined, UploadOutlined, RobotOutlined,
  EyeOutlined, SendOutlined, CodeOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../hooks/useAuthStore'

interface Assignment {
  id: number
  title: string
  course: string
  courseId: number
  deadline: string
  submitted: number
  total: number
  status: 'open' | 'closed'
}

interface Submission {
  id: number
  student: string
  submitTime: string
  grade: number | null
  gradingStatus: 'pending' | 'graded' | 'grading'
}

const ASSIGNMENTS: Assignment[] = [
  { id: 1, title: 'Python循环练习', course: 'Python程序设计', courseId: 1, deadline: '2026-04-10', submitted: 12, total: 30, status: 'open' },
  { id: 2, title: '递归算法作业', course: 'Python程序设计', courseId: 1, deadline: '2026-04-15', submitted: 5, total: 30, status: 'open' },
  { id: 3, title: '链表实现', course: '数据结构', courseId: 2, deadline: '2026-04-12', submitted: 20, total: 25, status: 'open' },
  { id: 4, title: '二叉树遍历', course: '数据结构', courseId: 2, deadline: '2026-03-30', submitted: 24, total: 25, status: 'closed' },
]

const SUBMISSIONS: Submission[] = [
  { id: 1, student: '张三', submitTime: '04-08 14:30', grade: 85, gradingStatus: 'graded' },
  { id: 2, student: '李四', submitTime: '04-09 09:15', grade: 72, gradingStatus: 'graded' },
  { id: 3, student: '王五', submitTime: '04-09 23:50', grade: null, gradingStatus: 'pending' },
  { id: 4, student: '赵六', submitTime: '04-10 08:00', grade: null, gradingStatus: 'grading' },
]

const STUDENT_ASSIGNMENTS = [
  { id: 1, title: 'Python循环练习', course: 'Python程序设计', deadline: '2026-04-10', status: 'pending' as const, grade: null },
  { id: 2, title: '递归算法作业', course: 'Python程序设计', deadline: '2026-04-15', status: 'pending' as const, grade: null },
  { id: 3, title: '链表实现', course: '数据结构', deadline: '2026-04-12', status: 'submitted' as const, grade: null },
  { id: 4, title: '二叉树遍历', course: '数据结构', deadline: '2026-03-30', status: 'graded' as const, grade: 88 },
]

export default function Assignment() {
  const navigate = useNavigate()
  const user = useAuthStore(s => s.user)
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [submitOpen, setSubmitOpen] = useState<number | null>(null)
  const [submitMode, setSubmitMode] = useState<'code' | 'file'>('code')
  const [codeContent, setCodeContent] = useState('')
  const [form] = Form.useForm()
  const [batchGrading, setBatchGrading] = useState(false)

  const handleBatchGrade = () => {
    setBatchGrading(true)
    message.loading({ content: 'AI 正在批改中...', key: 'grading' })
    setTimeout(() => {
      message.success({ content: '批改完成！', key: 'grading', duration: 2 })
      setBatchGrading(false)
    }, 3000)
  }

  const gradingStatusTag = (status: Submission['gradingStatus'], grade: number | null) => {
    if (status === 'graded') return <Tag color="success">✅ 已批改 {grade}分</Tag>
    if (status === 'grading') return <Tag color="processing">⏳ 批改中</Tag>
    return <Tag color="default">待批改</Tag>
  }

  // 教师：作业详情
  if (isTeacher && selectedAssignment) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Button onClick={() => setSelectedAssignment(null)}>← 返回</Button>
          <span style={{ fontSize: 18, fontWeight: 700 }}>{selectedAssignment.title}</span>
          <Tag color={selectedAssignment.status === 'open' ? 'blue' : 'default'}>
            {selectedAssignment.status === 'open' ? '进行中' : '已截止'}
          </Tag>
        </div>

        <Card style={{ marginBottom: 16, borderRadius: 12 }}>
          <div style={{ display: 'flex', gap: 32 }}>
            <div><div style={{ color: '#999', fontSize: 12 }}>截止时间</div><div style={{ fontWeight: 600 }}>{selectedAssignment.deadline}</div></div>
            <div><div style={{ color: '#999', fontSize: 12 }}>提交进度</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600 }}>{selectedAssignment.submitted}/{selectedAssignment.total}</span>
                <Progress percent={Math.round(selectedAssignment.submitted / selectedAssignment.total * 100)} style={{ width: 120 }} size="small" strokeColor="#00a8ff" />
              </div>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <Button
                type="primary" icon={<RobotOutlined />}
                loading={batchGrading} onClick={handleBatchGrade}
                style={{ background: 'linear-gradient(90deg,#00a8ff,#0078d7)', border: 'none', borderRadius: 8 }}
              >
                一键 AI 批改全部
              </Button>
            </div>
          </div>
        </Card>

        <Table
          dataSource={SUBMISSIONS}
          rowKey="id"
          columns={[
            {
              title: '学生',
              dataIndex: 'student',
              render: name => <Space><Avatar size="small" style={{ background: '#6366f1' }}>{name[0]}</Avatar>{name}</Space>,
            },
            { title: '提交时间', dataIndex: 'submitTime' },
            {
              title: '批改状态',
              render: (_, row) => gradingStatusTag(row.gradingStatus, row.grade),
            },
            {
              title: '操作',
              render: (_, row) => (
                <Button
                  size="small" icon={<EyeOutlined />}
                  onClick={() => navigate(`/grading/${row.id}`)}
                >
                  查看批改
                </Button>
              ),
            },
          ]}
        />
      </div>
    )
  }

  // 教师：作业列表
  if (isTeacher) {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <span style={{ fontSize: 20, fontWeight: 700 }}>作业管理</span>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} style={{ borderRadius: 8 }}>
            创建作业
          </Button>
        </div>

        <Table
          dataSource={ASSIGNMENTS}
          rowKey="id"
          columns={[
            {
              title: '作业名称', dataIndex: 'title',
              render: (title, row) => (
                <span style={{ cursor: 'pointer', color: '#00a8ff', fontWeight: 500 }}
                  onClick={() => setSelectedAssignment(row)}>{title}</span>
              ),
            },
            { title: '课程', dataIndex: 'course', render: c => <Tag color="blue">{c}</Tag> },
            { title: '截止时间', dataIndex: 'deadline' },
            {
              title: '提交情况',
              render: (_, row) => (
                <Space>
                  <span>{row.submitted}/{row.total}</span>
                  <Progress percent={Math.round(row.submitted / row.total * 100)} style={{ width: 80 }} size="small" strokeColor="#00a8ff" showInfo={false} />
                </Space>
              ),
            },
            {
              title: '状态',
              dataIndex: 'status',
              render: s => <Tag color={s === 'open' ? 'blue' : 'default'}>{s === 'open' ? '进行中' : '已截止'}</Tag>,
            },
            {
              title: '操作',
              render: (_, row) => (
                <Space>
                  <Button size="small" onClick={() => setSelectedAssignment(row)}>查看提交</Button>
                  <Button size="small" icon={<RobotOutlined />} type="primary" ghost onClick={handleBatchGrade}>AI批改</Button>
                </Space>
              ),
            },
          ]}
        />

        <Modal title="创建作业" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()} okText="创建">
          <Form form={form} layout="vertical" style={{ marginTop: 16 }}
            onFinish={v => { message.success('作业创建成功'); setCreateOpen(false); form.resetFields() }}>
            <Form.Item name="title" label="作业标题" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="courseId" label="所属课程" rules={[{ required: true }]}>
              <Select options={[{ value: 1, label: 'Python程序设计' }, { value: 2, label: '数据结构' }]} />
            </Form.Item>
            <Form.Item name="deadline" label="截止时间" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="description" label="作业说明"><Input.TextArea rows={3} /></Form.Item>
          </Form>
        </Modal>
      </div>
    )
  }

  // 学生视角
  return (
    <div>
      <div style={{ marginBottom: 24, fontSize: 20, fontWeight: 700 }}>我的作业</div>
      <Table
        dataSource={STUDENT_ASSIGNMENTS}
        rowKey="id"
        columns={[
          { title: '作业名称', dataIndex: 'title', render: t => <span style={{ fontWeight: 500 }}>{t}</span> },
          { title: '课程', dataIndex: 'course', render: c => <Tag color="blue">{c}</Tag> },
          { title: '截止时间', dataIndex: 'deadline' },
          {
            title: '状态',
            render: (_, row) => {
              if (row.status === 'graded') return <Tag color="success">✅ 已批改 {row.grade}分</Tag>
              if (row.status === 'submitted') return <Tag color="processing">已提交</Tag>
              return <Tag color="warning">待提交</Tag>
            },
          },
          {
            title: '操作',
            render: (_, row) => {
              if (row.status === 'graded') return <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/grading/${row.id}`)}>查看批改</Button>
              if (row.status === 'submitted') return <Tag color="processing">等待批改</Tag>
              return (
                <Button size="small" type="primary" icon={<SendOutlined />} onClick={() => setSubmitOpen(row.id)}>提交作业</Button>
              )
            },
          },
        ]}
      />

      <Modal
        title="提交作业"
        open={submitOpen !== null}
        onCancel={() => setSubmitOpen(null)}
        onOk={() => { message.success('提交成功，等待 AI 批改'); setSubmitOpen(null) }}
        okText="提交"
        width={640}
      >
        <Tabs
          activeKey={submitMode}
          onChange={k => setSubmitMode(k as 'code' | 'file')}
          items={[
            {
              key: 'code',
              label: <span><CodeOutlined /> 在线编辑器</span>,
              children: (
                <Input.TextArea
                  value={codeContent}
                  onChange={e => setCodeContent(e.target.value)}
                  rows={12}
                  placeholder="在此输入代码或文字内容..."
                  style={{ fontFamily: 'monospace', fontSize: 13, background: '#1e1e1e', color: '#d4d4d4', borderRadius: 8 }}
                />
              ),
            },
            {
              key: 'file',
              label: <span><UploadOutlined /> 上传文件</span>,
              children: (
                <Upload.Dragger accept=".py,.pdf,.doc,.docx" beforeUpload={() => false} style={{ borderRadius: 10 }}>
                  <p style={{ fontSize: 24 }}><UploadOutlined /></p>
                  <p>点击或拖拽上传 .py / .pdf / .docx</p>
                </Upload.Dragger>
              ),
            },
          ]}
        />
      </Modal>
    </div>
  )
}

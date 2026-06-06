import { useCallback, useEffect, useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Alert, Button, Drawer, Form, Input, Select, Tag, message } from 'antd'
import { EyeOutlined, PlayCircleOutlined, SaveOutlined } from '@ant-design/icons'
import { agentAPI, courseAPI, getErrorMessage } from '../../services/api'

const NODE_TYPES_CONFIG = [
  { type: 'input_node', label: '用户输入', color: '#6366f1', icon: 'I', runtimeSupported: true },
  { type: 'rag_node', label: '知识检索', color: '#00a8ff', icon: 'R', runtimeSupported: true },
  { type: 'llm_node', label: 'LLM 对话', color: '#8b5cf6', icon: 'L', runtimeSupported: true },
  { type: 'grading_node', label: '作业批改', color: '#f59e0b', icon: 'G', runtimeSupported: false },
  { type: 'analytics_node', label: '学情分析', color: '#10b981', icon: 'A', runtimeSupported: false },
  { type: 'exercise_node', label: '练习生成', color: '#ec4899', icon: 'E', runtimeSupported: false },
  { type: 'condition_node', label: '条件判断', color: '#64748b', icon: 'C', runtimeSupported: false },
  { type: 'output_node', label: '输出', color: '#52c41a', icon: 'O', runtimeSupported: true },
]

const NODE_TYPE_META = Object.fromEntries(NODE_TYPES_CONFIG.map((item) => [item.type, item]))
const RUNTIME_NODE_TYPES = NODE_TYPES_CONFIG.filter((item) => item.runtimeSupported).map((item) => item.type)

type CourseItem = {
  id: number
  name: string
  code: string
}

type TemplateItem = {
  id: number
  name: string
}

type AgentItem = {
  id: number
  name: string
  description?: string | null
  course_id: number
  llm_provider: string
  llm_model: string
  is_active: boolean
}

type WorkflowItem = {
  id: number
  agent_id: number
  name: string
  description?: string | null
  workflow_dag: {
    nodes?: Node[]
    edges?: Edge[]
  }
  is_active: boolean
}

type WorkflowValidation = {
  saveErrors: string[]
  publishErrors: string[]
  warnings: string[]
  summary: string[]
  mapping: {
    llmModel: string
    topK: number
    similarity: number
    toolNames: string[]
  }
}

const INIT_NODES: Node[] = [
  { id: 'n1', type: 'custom', position: { x: 250, y: 40 }, data: { label: '用户输入', color: '#6366f1', icon: 'I', nodeType: 'input_node' } },
  { id: 'n2', type: 'custom', position: { x: 250, y: 160 }, data: { label: '知识检索', color: '#00a8ff', icon: 'R', nodeType: 'rag_node', topK: 5, similarity: 0.7 } },
  { id: 'n3', type: 'custom', position: { x: 250, y: 280 }, data: { label: 'LLM 对话', color: '#8b5cf6', icon: 'L', nodeType: 'llm_node', model: 'qwen-max' } },
  { id: 'n4', type: 'custom', position: { x: 250, y: 400 }, data: { label: '输出', color: '#52c41a', icon: 'O', nodeType: 'output_node' } },
]

const INIT_EDGES: Edge[] = [
  { id: 'e1-2', source: 'n1', target: 'n2', animated: true, style: { stroke: '#00a8ff' } },
  { id: 'e2-3', source: 'n2', target: 'n3', animated: true, style: { stroke: '#8b5cf6' } },
  { id: 'e3-4', source: 'n3', target: 'n4', animated: true, style: { stroke: '#52c41a' } },
]

function buildDefaultNodes() {
  return INIT_NODES.map((node) => ({
    ...node,
    position: { ...node.position },
    data: { ...node.data },
  }))
}

function buildDefaultEdges() {
  return INIT_EDGES.map((edge) => ({
    ...edge,
    style: edge.style ? { ...edge.style } : edge.style,
  }))
}

function buildWorkflowPayload(nodes: Node[], edges: Edge[]) {
  return {
    nodes: nodes.map((node) => ({
      id: node.id,
      type: 'custom',
      position: node.position,
      data: { ...node.data },
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      animated: edge.animated,
      style: edge.style,
    })),
  }
}

function validateWorkflow(nodes: Node[], edges: Edge[], selectedCourse?: number): WorkflowValidation {
  const saveErrors: string[] = []
  const publishErrors: string[] = []
  const warnings: string[] = []
  const summary: string[] = []

  const nodeMap = new Map<string, Node>()
  const incoming = new Map<string, number>()
  const outgoing = new Map<string, number>()
  const typeCounts = new Map<string, number>()

  for (const node of nodes) {
    nodeMap.set(node.id, node)
    incoming.set(node.id, 0)
    outgoing.set(node.id, 0)
    const nodeType = String(node.data?.nodeType || '')
    typeCounts.set(nodeType, (typeCounts.get(nodeType) ?? 0) + 1)

    if (!NODE_TYPE_META[nodeType]) {
      saveErrors.push(`节点 ${node.id} 的类型未受支持`)
      continue
    }
    if (nodeType === 'rag_node') {
      const topK = Number(node.data?.topK)
      const similarity = Number(node.data?.similarity)
      const course = Number(node.data?.course ?? selectedCourse)
      if (!Number.isInteger(topK) || topK <= 0) {
        saveErrors.push(`RAG 节点 ${node.data?.label || node.id} 缺少有效的 Top-K`)
      }
      if (!Number.isFinite(similarity) || similarity < 0 || similarity > 1) {
        saveErrors.push(`RAG 节点 ${node.data?.label || node.id} 的相似度阈值必须在 0 到 1 之间`)
      }
      if (!selectedCourse || course !== selectedCourse) {
        saveErrors.push(`RAG 节点 ${node.data?.label || node.id} 必须绑定当前课程`)
      }
    }
    if (nodeType === 'llm_node' && !String(node.data?.model || '').trim()) {
      saveErrors.push(`LLM 节点 ${node.data?.label || node.id} 缺少模型配置`)
    }
    if (NODE_TYPE_META[nodeType] && !NODE_TYPE_META[nodeType].runtimeSupported) {
      publishErrors.push(`当前运行时不能发布 ${NODE_TYPE_META[nodeType].label} 节点`)
    }
  }

  for (const edge of edges) {
    if (!nodeMap.has(edge.source) || !nodeMap.has(edge.target)) {
      saveErrors.push(`连线 ${edge.id} 引用了不存在的节点`)
      continue
    }
    if (edge.source === edge.target) {
      saveErrors.push(`连线 ${edge.id} 不能连接到自身`)
      continue
    }
    outgoing.set(edge.source, (outgoing.get(edge.source) ?? 0) + 1)
    incoming.set(edge.target, (incoming.get(edge.target) ?? 0) + 1)
  }

  const inputNodes = nodes.filter((node) => node.data?.nodeType === 'input_node')
  const ragNodes = nodes.filter((node) => node.data?.nodeType === 'rag_node')
  const llmNodes = nodes.filter((node) => node.data?.nodeType === 'llm_node')
  const outputNodes = nodes.filter((node) => node.data?.nodeType === 'output_node')

  if (inputNodes.length !== 1) saveErrors.push('工作流必须且只能包含 1 个输入节点')
  if (llmNodes.length !== 1) saveErrors.push('工作流必须且只能包含 1 个 LLM 节点')
  if (outputNodes.length !== 1) saveErrors.push('工作流必须且只能包含 1 个输出节点')
  if (ragNodes.length > 1) publishErrors.push('当前运行时最多支持 1 个 RAG 节点')

  const startNodes = nodes.filter((node) => (incoming.get(node.id) ?? 0) === 0)
  const endNodes = nodes.filter((node) => (outgoing.get(node.id) ?? 0) === 0)
  if (startNodes.length === 0) saveErrors.push('工作流必须有起点')
  if (endNodes.length === 0) saveErrors.push('工作流必须有终点')
  if (inputNodes[0] && (incoming.get(inputNodes[0].id) ?? 0) !== 0) saveErrors.push('输入节点必须是起点')
  if (outputNodes[0] && (outgoing.get(outputNodes[0].id) ?? 0) !== 0) saveErrors.push('输出节点必须是终点')

  const adjacency = new Map<string, string[]>()
  for (const node of nodes) {
    adjacency.set(node.id, [])
  }
  for (const edge of edges) {
    if (adjacency.has(edge.source) && nodeMap.has(edge.target) && edge.source !== edge.target) {
      adjacency.get(edge.source)?.push(edge.target)
    }
  }

  const hasPath = (sourceId?: string, targetId?: string) => {
    if (!sourceId || !targetId) return false
    const queue = [sourceId]
    const visited = new Set<string>()
    while (queue.length > 0) {
      const current = queue.pop()!
      if (current === targetId) return true
      if (visited.has(current)) continue
      visited.add(current)
      adjacency.get(current)?.forEach((next) => queue.push(next))
    }
    return false
  }

  const inputId = inputNodes[0]?.id
  const llmId = llmNodes[0]?.id
  const outputId = outputNodes[0]?.id
  if (inputId && llmId && !hasPath(inputId, llmId)) saveErrors.push('输入节点必须能到达 LLM 节点')
  if (llmId && outputId && !hasPath(llmId, outputId)) saveErrors.push('LLM 节点必须能到达输出节点')
  if (inputId && outputId && !hasPath(inputId, outputId)) saveErrors.push('工作流必须存在从输入到输出的完整路径')

  const ragNode = ragNodes[0]
  const llmNode = llmNodes[0]
  const mapping = {
    llmModel: String(llmNode?.data?.model || 'qwen-max'),
    topK: Number(ragNode?.data?.topK ?? 5),
    similarity: Number(ragNode?.data?.similarity ?? 0.7),
    toolNames: ragNode ? ['rag'] : [],
  }

  summary.push(`节点数 ${nodes.length} / 连线数 ${edges.length}`)
  summary.push(`节点类型 ${Array.from(typeCounts.entries()).map(([type, count]) => `${type}:${count}`).join(', ') || '无'}`)
  summary.push(`运行时映射 QA 管线: input -> ${ragNode ? 'rag -> ' : ''}llm -> output`)
  summary.push(`发布后生效方式：将工作流映射到 Agent 配置，不执行通用工作流引擎`)

  const uiOnlyNodes = nodes.filter((node) => {
    const nodeType = String(node.data?.nodeType || '')
    return NODE_TYPE_META[nodeType] && !NODE_TYPE_META[nodeType].runtimeSupported
  })
  if (uiOnlyNodes.length > 0) {
    warnings.push('存在仅 UI 原型节点，可保存但不能发布生效。')
  }
  if (nodes.some((node) => !RUNTIME_NODE_TYPES.includes(String(node.data?.nodeType || '')))) {
    warnings.push('当前运行时只支持 input/rag/llm/output 四类节点的发布映射。')
  }

  return { saveErrors, publishErrors, warnings, summary, mapping }
}

function CustomNode({ data }: { data: any }) {
  return (
    <div
      style={{
        padding: '10px 16px',
        borderRadius: 10,
        minWidth: 130,
        background: '#fff',
        border: `2px solid ${data.color}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
        fontSize: 13,
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: data.color, width: 10, height: 10 }} />
      <span style={{ fontSize: 18 }}>{data.icon}</span>
      <span style={{ color: data.color }}>{data.label}</span>
      <Handle type="source" position={Position.Bottom} style={{ background: data.color, width: 10, height: 10 }} />
    </div>
  )
}

const nodeTypes = { custom: CustomNode }

function makeNode(type: string, label: string, color: string, icon: string, x: number, y: number): Node {
  return {
    id: `${type}-${Date.now()}`,
    type: 'custom',
    position: { x, y },
    data: { label, color, icon, nodeType: type },
  }
}

export default function AgentBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState(buildDefaultNodes())
  const [edges, setEdges, onEdgesChange] = useEdgesState(buildDefaultEdges())
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [agentName, setAgentName] = useState('课程答疑 Agent')
  const [agentDescription, setAgentDescription] = useState('')
  const [selectedCourse, setSelectedCourse] = useState<number>()
  const [selectedTemplate, setSelectedTemplate] = useState<number>()
  const [courses, setCourses] = useState<CourseItem[]>([])
  const [templates, setTemplates] = useState<TemplateItem[]>([])
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [saving, setSaving] = useState(false)
  const [currentAgentId, setCurrentAgentId] = useState<number | null>(null)
  const [currentWorkflowId, setCurrentWorkflowId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const validation = useMemo(() => validateWorkflow(nodes, edges, selectedCourse), [edges, nodes, selectedCourse])

  useEffect(() => {
    const loadBaseData = async () => {
      setLoadingCourses(true)
      setLoadingTemplates(true)
      try {
        const [{ data: courseData }, { data: templateData }] = await Promise.all([
          courseAPI.list(),
          agentAPI.listTemplates(),
        ])
        setCourses(courseData)
        setTemplates(templateData)
        if (courseData.length > 0) {
          setSelectedCourse((prev) => prev ?? courseData[0].id)
        }
        if (templateData.length > 0) {
          setSelectedTemplate((prev) => prev ?? templateData[0].id)
        }
      } catch (error) {
        message.error(getErrorMessage(error, '加载 Agent Builder 基础数据失败'))
      } finally {
        setLoadingCourses(false)
        setLoadingTemplates(false)
      }
    }

    void loadBaseData()
  }, [])

  useEffect(() => {
    if (!selectedCourse) return

    const loadExistingAgent = async () => {
      try {
        const { data } = await agentAPI.listInstances(selectedCourse)
        const nextAgent = data.find((item: AgentItem) => item.is_active) ?? data[0] ?? null

        if (!nextAgent) {
          setCurrentAgentId(null)
          setCurrentWorkflowId(null)
          setAgentName('课程答疑 Agent')
          setAgentDescription('')
          setNodes(buildDefaultNodes())
          setEdges(buildDefaultEdges())
          return
        }

        setCurrentAgentId(nextAgent.id)
        setAgentName(nextAgent.name)
        setAgentDescription(nextAgent.description || '')

        const workflowResponse = await agentAPI.listWorkflows(nextAgent.id)
        const nextWorkflow =
          workflowResponse.data.find((item: WorkflowItem) => item.is_active) ?? workflowResponse.data[0] ?? null

        if (!nextWorkflow) {
          setCurrentWorkflowId(null)
          setNodes(buildDefaultNodes())
          setEdges(buildDefaultEdges())
          return
        }

        setCurrentWorkflowId(nextWorkflow.id)
        setNodes(nextWorkflow.workflow_dag.nodes?.length ? nextWorkflow.workflow_dag.nodes : buildDefaultNodes())
        setEdges(nextWorkflow.workflow_dag.edges?.length ? nextWorkflow.workflow_dag.edges : buildDefaultEdges())
      } catch (error) {
        message.error(getErrorMessage(error, '加载现有 Agent 配置失败'))
      }
    }

    void loadExistingAgent()
  }, [selectedCourse, setEdges, setNodes])

  const onConnect = useCallback(
    (params: Connection) => setEdges((currentEdges) => addEdge({ ...params, animated: true }, currentEdges)),
    [setEdges]
  )

  const onNodeClick = useCallback(
    (_: unknown, node: Node) => {
      setSelectedNode(node)
      setDrawerOpen(true)
      form.setFieldsValue({
        label: node.data.label,
        course: node.data.course ?? selectedCourse ?? 1,
        topK: node.data.topK ?? 5,
        similarity: node.data.similarity ?? 0.7,
        model: node.data.model ?? 'qwen-max',
      })
    },
    [form, selectedCourse]
  )

  const addNode = (cfg: typeof NODE_TYPES_CONFIG[number]) => {
    const node = makeNode(cfg.type, cfg.label, cfg.color, cfg.icon, 100 + Math.random() * 300, 100 + Math.random() * 300)
    setNodes((currentNodes) => [...currentNodes, node])
  }

  const handleNodeConfigSave = () => {
    if (!selectedNode) return
    const values = form.getFieldsValue()
    setNodes((currentNodes) =>
      currentNodes.map((node) =>
        node.id === selectedNode.id
          ? {
              ...node,
              data: {
                ...node.data,
                label: values.label,
                course: values.course,
                topK: values.topK,
                similarity: values.similarity,
                model: values.model,
              },
            }
          : node
      )
    )
    setDrawerOpen(false)
    message.success('节点配置已保存')
  }

  const upsertAgent = async () => {
    if (!selectedCourse) {
      message.warning('请先选择关联课程')
      return null
    }
    if (!agentName.trim()) {
      message.warning('请输入 Agent 名称')
      return null
    }

    const payload = {
      template_id: selectedTemplate,
      course_id: selectedCourse,
      name: agentName,
      description: agentDescription,
      system_prompt: '你是该课程的 AI 助手，请优先依据当前课程资料回答。',
      config: {
        agent_type: 'qa',
        workflow_mode: 'draft',
        runtime_note: '保存阶段仅校验并持久化 DAG；发布后才会映射为可生效的 QA Agent 配置。',
        top_k: validation.mapping.topK,
        similarity_threshold: validation.mapping.similarity,
      },
      tools: validation.mapping.toolNames,
      llm_provider: 'dashscope',
      llm_model: validation.mapping.llmModel,
    }

    const response = currentAgentId
      ? await agentAPI.updateInstance(currentAgentId, payload)
      : await agentAPI.createInstance(payload)

    const nextAgentId = response.data.id as number
    setCurrentAgentId(nextAgentId)
    return nextAgentId
  }

  const saveWorkflow = async (agentId: number) => {
    const workflowPayload = {
      name: `${agentName} 工作流`,
      description: agentDescription || '课程问答工作流',
      workflow_dag: buildWorkflowPayload(nodes, edges),
    }

    const response = currentWorkflowId
      ? await agentAPI.updateWorkflow(currentWorkflowId, workflowPayload)
      : await agentAPI.createWorkflow({ agent_id: agentId, ...workflowPayload })

    const nextWorkflowId = response.data.id as number
    setCurrentWorkflowId(nextWorkflowId)
    return nextWorkflowId
  }

  const handleSave = async () => {
    if (validation.saveErrors.length > 0) {
      setPreviewOpen(true)
      message.error(validation.saveErrors[0])
      return
    }

    setSaving(true)
    try {
      const agentId = await upsertAgent()
      if (!agentId) return
      await saveWorkflow(agentId)
      message.success(currentAgentId ? 'Agent 配置已更新' : 'Agent 配置已保存')
    } catch (error) {
      message.error(getErrorMessage(error, '保存 Agent 失败'))
    } finally {
      setSaving(false)
    }
  }

  const handlePublish = async () => {
    if (validation.saveErrors.length > 0 || validation.publishErrors.length > 0) {
      setPreviewOpen(true)
      message.error(validation.saveErrors[0] || validation.publishErrors[0] || '当前工作流无法发布')
      return
    }

    setSaving(true)
    try {
      const agentId = await upsertAgent()
      if (!agentId) return
      const workflowId = await saveWorkflow(agentId)
      await agentAPI.publishWorkflow(workflowId)
      setCurrentAgentId(agentId)
      setCurrentWorkflowId(workflowId)
      message.success('Agent 已发布，可在课程问答中使用')
    } catch (error) {
      message.error(getErrorMessage(error, '发布 Agent 失败'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 160px)', borderRadius: 12, overflow: 'hidden', border: '1px solid #f0f0f0' }}>
      <div style={{ width: 180, background: '#fafafa', borderRight: '1px solid #f0f0f0', padding: '16px 12px', overflowY: 'auto' }}>
        <div style={{ fontWeight: 700, fontSize: 13, color: '#888', marginBottom: 12, letterSpacing: 1 }}>节点面板</div>
        {NODE_TYPES_CONFIG.map((cfg) => (
          <div
            key={cfg.type}
            onClick={() => addNode(cfg)}
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              marginBottom: 8,
              cursor: 'pointer',
              background: '#fff',
              border: `1.5px solid ${cfg.color}20`,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 13,
              fontWeight: 500,
              boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
            }}
          >
            <span style={{ fontSize: 16 }}>{cfg.icon}</span>
            <span style={{ color: cfg.color }}>{cfg.label}</span>
          </div>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '10px 16px', borderBottom: '1px solid #f0f0f0', background: '#fff', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <Input
            value={agentName}
            onChange={(event) => setAgentName(event.target.value)}
            style={{ width: 220, fontWeight: 600, border: 'none', background: '#f5f5f5', borderRadius: 8 }}
            placeholder="Agent 名称"
          />
          <Select
            size="small"
            value={selectedCourse}
            onChange={setSelectedCourse}
            style={{ width: 180 }}
            loading={loadingCourses}
            placeholder="选择课程"
            options={courses.map((course) => ({ value: course.id, label: course.name }))}
          />
          <Select
            size="small"
            value={selectedTemplate}
            onChange={setSelectedTemplate}
            style={{ width: 180 }}
            loading={loadingTemplates}
            placeholder="选择模板"
            options={templates.map((template) => ({ value: template.id, label: template.name }))}
          />
          <Tag color={currentWorkflowId ? 'green' : 'blue'}>{currentWorkflowId ? '已关联工作流' : '新建配置'}</Tag>
          <Tag color={validation.saveErrors.length === 0 ? 'success' : 'error'}>
            {validation.saveErrors.length === 0 ? '结构可保存' : `保存前问题 ${validation.saveErrors.length}`}
          </Tag>
          <Tag color={validation.saveErrors.length === 0 && validation.publishErrors.length === 0 ? 'success' : 'warning'}>
            {validation.saveErrors.length === 0 && validation.publishErrors.length === 0 ? '可发布' : '需发布前检查'}
          </Tag>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <Button icon={<SaveOutlined />} onClick={() => void handleSave()} loading={saving}>保存</Button>
            <Button icon={<PlayCircleOutlined />} type="primary" ghost onClick={() => setPreviewOpen(true)}>预览</Button>
            <Button
              icon={<EyeOutlined />}
              type="primary"
              onClick={() => void handlePublish()}
              loading={saving}
              style={{ background: 'linear-gradient(90deg,#00a8ff,#0078d7)', border: 'none' }}
            >
              发布
            </Button>
          </div>
        </div>

        <div style={{ padding: '10px 16px', background: '#fcfcfc', borderBottom: '1px solid #f3f3f3' }}>
          <Alert
            type={validation.saveErrors.length === 0 && validation.publishErrors.length === 0 ? 'success' : 'warning'}
            showIcon
            message="当前是可视化 Agent 配置器：仅支持将 input/rag/llm/output 线性工作流映射为 QA Agent 配置"
            description="保存会校验 DAG 结构；发布还会检查是否包含仅 UI 原型节点。当前平台不会执行通用工作流引擎，也不承诺通用 DAG 运行能力。"
          />
        </div>

        <div style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#e0e0e0" gap={20} />
            <Controls />
            <MiniMap nodeColor={(node) => node.data?.color ?? '#888'} style={{ borderRadius: 8 }} />
          </ReactFlow>
        </div>
      </div>

      <Drawer
        title={selectedNode ? `配置：${selectedNode.data.label}` : '节点配置'}
        placement="right"
        width={300}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        getContainer={false}
        style={{ position: 'absolute' }}
      >
        {selectedNode && (
          <Form form={form} layout="vertical">
            <Form.Item label="节点名称" name="label">
              <Input />
            </Form.Item>
            {selectedNode.data.nodeType === 'rag_node' && (
              <>
                <Form.Item label="关联课程" name="course">
                  <Select options={courses.map((course) => ({ value: course.id, label: course.name }))} />
                </Form.Item>
                <Form.Item label="Top-K 检索数" name="topK">
                  <Select options={[3, 5, 8, 10].map((value) => ({ value, label: `${value} 条` }))} />
                </Form.Item>
                <Form.Item label="相似度阈值" name="similarity">
                  <Select options={[0.5, 0.6, 0.7, 0.8, 0.9].map((value) => ({ value, label: `${value}` }))} />
                </Form.Item>
              </>
            )}
            {selectedNode.data.nodeType === 'llm_node' && (
              <Form.Item label="模型" name="model">
                <Select
                  options={[
                    { value: 'qwen-max', label: '通义千问 qwen-max' },
                    { value: 'deepseek-chat', label: 'DeepSeek Chat' },
                    { value: 'glm-4', label: '智谱 GLM-4' },
                  ]}
                />
              </Form.Item>
            )}
            <Form.Item>
              <Button type="primary" block onClick={handleNodeConfigSave}>保存配置</Button>
            </Form.Item>
          </Form>
        )}
      </Drawer>

      <Drawer
        title="工作流预览与校验"
        placement="right"
        width={420}
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
      >
        <div style={{ display: 'grid', gap: 12 }}>
          <Alert
            type={validation.saveErrors.length === 0 && validation.publishErrors.length === 0 ? 'success' : 'warning'}
            showIcon
            message={validation.saveErrors.length === 0 && validation.publishErrors.length === 0 ? '当前工作流可发布' : '当前工作流需要处理以下问题'}
            description="发布后会映射到 Agent 的 `config/tools/llm_model`，不是执行一个通用 DAG 引擎。"
          />

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>结构摘要</div>
            {validation.summary.map((item) => (
              <div key={item} style={{ color: '#444', marginBottom: 6 }}>{item}</div>
            ))}
          </div>

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>发布映射</div>
            <div style={{ color: '#444', marginBottom: 6 }}>LLM 模型：{validation.mapping.llmModel}</div>
            <div style={{ color: '#444', marginBottom: 6 }}>检索 Top-K：{validation.mapping.topK}</div>
            <div style={{ color: '#444', marginBottom: 6 }}>相似度阈值：{validation.mapping.similarity}</div>
            <div style={{ color: '#444', marginBottom: 6 }}>工具：{validation.mapping.toolNames.join(', ') || '无'}</div>
          </div>

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>保存前必须修复</div>
            {validation.saveErrors.length === 0 ? (
              <Tag color="success">无</Tag>
            ) : (
              validation.saveErrors.map((item) => (
                <Alert key={item} type="error" showIcon message={item} style={{ marginBottom: 8 }} />
              ))
            )}
          </div>

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>发布前必须修复</div>
            {validation.publishErrors.length === 0 ? (
              <Tag color="success">无</Tag>
            ) : (
              validation.publishErrors.map((item) => (
                <Alert key={item} type="warning" showIcon message={item} style={{ marginBottom: 8 }} />
              ))
            )}
          </div>

          {validation.warnings.length > 0 && (
            <div>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>提示</div>
              {validation.warnings.map((item) => (
                <Alert key={item} type="info" showIcon message={item} style={{ marginBottom: 8 }} />
              ))}
            </div>
          )}
        </div>
      </Drawer>
    </div>
  )
}

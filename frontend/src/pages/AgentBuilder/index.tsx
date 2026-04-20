import { useState, useCallback } from 'react'
import ReactFlow, {
  addEdge, Background, Controls, MiniMap,
  useNodesState, useEdgesState,
  type Connection, type Edge, type Node,
  Handle, Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Card, Button, Input, Select, Form, Drawer, Tag, message, Space } from 'antd'
import { SaveOutlined, PlayCircleOutlined, EyeOutlined, PlusOutlined } from '@ant-design/icons'

const NODE_TYPES_CONFIG = [
  { type: 'input_node', label: '用户输入', color: '#6366f1', icon: '💬' },
  { type: 'rag_node', label: '知识检索', color: '#00a8ff', icon: '🔍' },
  { type: 'llm_node', label: 'LLM对话', color: '#8b5cf6', icon: '🤖' },
  { type: 'grading_node', label: '作业批改', color: '#f59e0b', icon: '📝' },
  { type: 'analytics_node', label: '学情分析', color: '#10b981', icon: '📊' },
  { type: 'exercise_node', label: '练习生成', color: '#ec4899', icon: '✏️' },
  { type: 'condition_node', label: '条件判断', color: '#64748b', icon: '🔀' },
  { type: 'output_node', label: '输出', color: '#52c41a', icon: '📤' },
]

function CustomNode({ data }: { data: any }) {
  return (
    <div style={{
      padding: '10px 16px', borderRadius: 10, minWidth: 130,
      background: '#fff', border: `2px solid ${data.color}`,
      boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
      fontSize: 13, fontWeight: 600,
      display: 'flex', alignItems: 'center', gap: 8,
    }}>
      <Handle type="target" position={Position.Top} style={{ background: data.color, width: 10, height: 10 }} />
      <span style={{ fontSize: 18 }}>{data.icon}</span>
      <span style={{ color: data.color }}>{data.label}</span>
      <Handle type="source" position={Position.Bottom} style={{ background: data.color, width: 10, height: 10 }} />
    </div>
  )
}

const nodeTypes = { custom: CustomNode }

const makeNode = (type: string, label: string, color: string, icon: string, x: number, y: number): Node => ({
  id: `${type}-${Date.now()}`,
  type: 'custom',
  position: { x, y },
  data: { label, color, icon, nodeType: type },
})

const INIT_NODES: Node[] = [
  { id: 'n1', type: 'custom', position: { x: 250, y: 40 }, data: { label: '用户输入', color: '#6366f1', icon: '💬', nodeType: 'input_node' } },
  { id: 'n2', type: 'custom', position: { x: 250, y: 160 }, data: { label: '知识检索', color: '#00a8ff', icon: '🔍', nodeType: 'rag_node' } },
  { id: 'n3', type: 'custom', position: { x: 250, y: 280 }, data: { label: 'LLM对话', color: '#8b5cf6', icon: '🤖', nodeType: 'llm_node' } },
  { id: 'n4', type: 'custom', position: { x: 250, y: 400 }, data: { label: '输出', color: '#52c41a', icon: '📤', nodeType: 'output_node' } },
]

const INIT_EDGES: Edge[] = [
  { id: 'e1-2', source: 'n1', target: 'n2', animated: true, style: { stroke: '#00a8ff' } },
  { id: 'e2-3', source: 'n2', target: 'n3', animated: true, style: { stroke: '#8b5cf6' } },
  { id: 'e3-4', source: 'n3', target: 'n4', animated: true, style: { stroke: '#52c41a' } },
]

export default function AgentBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState(INIT_NODES)
  const [edges, setEdges, onEdgesChange] = useEdgesState(INIT_EDGES)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [agentName, setAgentName] = useState('Python课程答疑Agent')
  const [form] = Form.useForm()

  const onConnect = useCallback(
    (params: Connection) => setEdges(eds => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node)
    setDrawerOpen(true)
    form.setFieldsValue({
      label: node.data.label,
      course: 1,
      topK: 5,
      similarity: 0.7,
      model: 'qwen-max',
    })
  }, [form])

  const addNode = (cfg: typeof NODE_TYPES_CONFIG[0]) => {
    const n = makeNode(cfg.type, cfg.label, cfg.color, cfg.icon, 100 + Math.random() * 300, 100 + Math.random() * 300)
    setNodes(nds => [...nds, n])
  }

  const handleSave = () => message.success('Agent工作流已保存')
  const handlePublish = () => message.success('Agent已发布，可在课程中使用')

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 160px)', gap: 0, borderRadius: 12, overflow: 'hidden', border: '1px solid #f0f0f0' }}>

      {/* 左侧节点面板 */}
      <div style={{ width: 180, background: '#fafafa', borderRight: '1px solid #f0f0f0', padding: '16px 12px', overflowY: 'auto' }}>
        <div style={{ fontWeight: 700, fontSize: 13, color: '#888', marginBottom: 12, letterSpacing: 1 }}>节点面板</div>
        {NODE_TYPES_CONFIG.map(cfg => (
          <div
            key={cfg.type}
            draggable
            onClick={() => addNode(cfg)}
            style={{
              padding: '8px 12px', borderRadius: 8, marginBottom: 8, cursor: 'grab',
              background: '#fff', border: `1.5px solid ${cfg.color}20`,
              display: 'flex', alignItems: 'center', gap: 8,
              fontSize: 13, fontWeight: 500,
              transition: 'box-shadow 0.15s',
              boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
            }}
          >
            <span style={{ fontSize: 16 }}>{cfg.icon}</span>
            <span style={{ color: cfg.color }}>{cfg.label}</span>
          </div>
        ))}
        <div style={{ marginTop: 16, fontSize: 11, color: '#bbb', lineHeight: 1.6 }}>
          点击节点添加到画布，拖动节点连线搭建工作流
        </div>
      </div>

      {/* 中间画布 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '10px 16px', borderBottom: '1px solid #f0f0f0', background: '#fff', display: 'flex', alignItems: 'center', gap: 12 }}>
          <Input
            value={agentName}
            onChange={e => setAgentName(e.target.value)}
            style={{ width: 260, fontWeight: 600, border: 'none', background: '#f5f5f5', borderRadius: 8 }}
          />
          <Tag color="blue">草稿</Tag>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <Button icon={<SaveOutlined />} onClick={handleSave}>保存</Button>
            <Button icon={<PlayCircleOutlined />} type="primary" ghost>预览</Button>
            <Button icon={<EyeOutlined />} type="primary" onClick={handlePublish}
              style={{ background: 'linear-gradient(90deg,#00a8ff,#0078d7)', border: 'none' }}
            >发布</Button>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes} edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#e0e0e0" gap={20} />
            <Controls />
            <MiniMap nodeColor={n => n.data?.color ?? '#888'} style={{ borderRadius: 8 }} />
          </ReactFlow>
        </div>
      </div>

      {/* 右侧配置面板 */}
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
                  <Select options={[{ value: 1, label: 'Python程序设计' }, { value: 2, label: '数据结构' }]} />
                </Form.Item>
                <Form.Item label="Top-K 检索数" name="topK">
                  <Select options={[3,5,8,10].map(v => ({ value: v, label: `${v} 条` }))} />
                </Form.Item>
                <Form.Item label="相似度阈值" name="similarity">
                  <Select options={[0.5,0.6,0.7,0.8,0.9].map(v => ({ value: v, label: `${v}` }))} />
                </Form.Item>
              </>
            )}
            {selectedNode.data.nodeType === 'llm_node' && (
              <Form.Item label="模型" name="model">
                <Select options={[
                  { value: 'qwen-max', label: '通义千问 qwen-max' },
                  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
                  { value: 'glm-4', label: '智谱 GLM-4' },
                ]} />
              </Form.Item>
            )}
            <Form.Item>
              <Button type="primary" block onClick={() => { message.success('配置已保存'); setDrawerOpen(false) }}>保存配置</Button>
            </Form.Item>
          </Form>
        )}
      </Drawer>
    </div>
  )
}

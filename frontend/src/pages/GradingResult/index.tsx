import { useParams, useNavigate } from 'react-router-dom'
import { Card, Tag, Button, Tooltip, Divider, Progress, Space, Badge } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons'

interface LineAnnotation {
  type: 'error' | 'warning' | 'ok'
  message: string
  suggestion?: string
}

const CODE_LINES = [
  'for i in range(10)',
  '    print(i)',
  '',
  'def sum(a, b):',
  '    return a + b',
  '',
  'x = [1, 2, 3]',
  'print(x[3])',
]

const LINE_ANNOTATIONS: Record<number, LineAnnotation> = {
  0: { type: 'error', message: '缺少冒号', suggestion: '应为 for i in range(10):' },
  7: { type: 'error', message: '索引越界：列表长度为3，最大索引为2', suggestion: '使用 x[-1] 或 x[len(x)-1] 访问最后一个元素' },
}

const TEXT_PARAGRAPHS = [
  { id: 1, text: '一、实验目的', annotation: null },
  { id: 2, text: '本实验旨在了解 Python 的基本数据类型及其操作方法，通过实践加深对变量、类型转换和基本输入输出的理解。', annotation: null },
  { id: 3, text: '二、实验过程', annotation: null },
  {
    id: 4,
    text: '首先创建了变量 x = "hello"，然后使用 type() 函数查看其类型为 int。',
    annotation: { type: 'error' as const, message: '类型描述错误："hello" 的类型应为 str，而非 int。建议重新运行代码确认输出结果。' },
  },
  {
    id: 5,
    text: '三、实验总结',
    annotation: null,
  },
  {
    id: 6,
    text: '（此部分为空）',
    annotation: { type: 'warning' as const, message: '缺少实验总结：建议结合实验过程，总结收获、遇到的问题及解决方案。' },
  },
]

const KNOWLEDGE_TAGS = [
  { label: '循环结构', status: 'error' as const },
  { label: '函数定义', status: 'success' as const },
  { label: '列表索引', status: 'error' as const },
  { label: '基本语法', status: 'success' as const },
]

export default function GradingResult() {
  const { submissionId } = useParams()
  const navigate = useNavigate()
  // submissionId=1 => code grading; others => text grading
  const isCode = submissionId === '1' || submissionId === '4'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/assignments')}>返回</Button>
        <span style={{ fontSize: 18, fontWeight: 700 }}>批改结果</span>
        <Tag color="blue">{isCode ? 'Python循环练习' : '实验报告'}</Tag>
        <Tag color="purple">张三</Tag>
      </div>

      {/* 分数概览 */}
      <Card style={{ borderRadius: 12, marginBottom: 16, background: 'linear-gradient(135deg,#f0f9ff,#e6f4ff)' }} bordered={false}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, fontWeight: 900, color: '#00a8ff', lineHeight: 1 }}>
              {isCode ? 85 : 78}
            </div>
            <div style={{ color: '#888', fontSize: 13, marginTop: 4 }}>/ 100 分</div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ marginBottom: 12, fontWeight: 600 }}>知识点掌握情况</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {KNOWLEDGE_TAGS.map(k => (
                <Tag
                  key={k.label}
                  icon={k.status === 'success' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                  color={k.status === 'success' ? 'success' : 'error'}
                  style={{ fontSize: 13, padding: '3px 10px' }}
                >
                  {k.label}
                </Tag>
              ))}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Progress
              type="circle"
              percent={isCode ? 85 : 78}
              strokeColor={{ '0%': '#00a8ff', '100%': '#52c41a' }}
              size={80}
            />
          </div>
        </div>
      </Card>

      {isCode ? (
        // 代码批改视图
        <Card title="📝 代码批改" style={{ borderRadius: 12, marginBottom: 16 }} bordered={false}>
          <div style={{
            fontFamily: 'monospace', fontSize: 14, lineHeight: 1.8,
            background: '#1e1e1e', borderRadius: 10, overflow: 'hidden',
          }}>
            {CODE_LINES.map((line, idx) => {
              const ann = LINE_ANNOTATIONS[idx]
              return (
                <div key={idx}>
                  <div style={{
                    display: 'flex', alignItems: 'stretch',
                    background: ann?.type === 'error' ? 'rgba(255,77,79,0.12)' : 'transparent',
                    borderLeft: ann?.type === 'error' ? '3px solid #ff4d4f' : ann?.type === 'warning' ? '3px solid #faad14' : '3px solid transparent',
                  }}>
                    <span style={{
                      minWidth: 40, padding: '2px 12px', color: '#555',
                      userSelect: 'none', fontSize: 12, lineHeight: '24px',
                      borderRight: '1px solid #333',
                    }}>
                      {idx + 1}
                    </span>
                    <span style={{ padding: '2px 16px', color: '#d4d4d4', flex: 1 }}>
                      {line || ' '}
                    </span>
                    {ann && (
                      <span style={{ padding: '2px 12px', display: 'flex', alignItems: 'center' }}>
                        {ann.type === 'error'
                          ? <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                          : <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        }
                      </span>
                    )}
                  </div>
                  {ann && ann.type !== 'ok' && (
                    <div style={{
                      background: 'rgba(255,77,79,0.08)',
                      borderLeft: '3px solid #ff4d4f',
                      padding: '8px 16px 8px 56px',
                      fontSize: 13,
                    }}>
                      <div style={{ color: '#ff4d4f', fontFamily: 'sans-serif', marginBottom: ann.suggestion ? 4 : 0 }}>
                        ❌ {ann.message}
                      </div>
                      {ann.suggestion && (
                        <div style={{ color: '#52c41a', fontFamily: 'sans-serif' }}>
                          💡 建议：{ann.suggestion}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </Card>
      ) : (
        // 文本批改视图
        <Card title="📄 文档批改" style={{ borderRadius: 12, marginBottom: 16 }} bordered={false}>
          <div style={{ fontSize: 14, lineHeight: 2 }}>
            {TEXT_PARAGRAPHS.map(para => (
              <div key={para.id} style={{ marginBottom: 12 }}>
                <span
                  style={{
                    background: para.annotation?.type === 'error' ? 'rgba(255,77,79,0.12)'
                      : para.annotation?.type === 'warning' ? 'rgba(250,173,20,0.12)' : 'transparent',
                    borderRadius: 4,
                    padding: para.annotation ? '2px 4px' : 0,
                    borderBottom: para.annotation?.type === 'error' ? '2px solid #ff4d4f'
                      : para.annotation?.type === 'warning' ? '2px solid #faad14' : 'none',
                  }}
                >
                  {para.text}
                </span>
                {para.annotation && (
                  <div style={{
                    margin: '6px 0 6px 16px',
                    padding: '8px 14px',
                    background: para.annotation.type === 'error' ? '#fff1f0' : '#fffbe6',
                    border: `1px solid ${para.annotation.type === 'error' ? '#ffccc7' : '#ffe58f'}`,
                    borderRadius: 8,
                    fontSize: 13,
                    color: para.annotation.type === 'error' ? '#cf1322' : '#874d00',
                  }}>
                    {para.annotation.type === 'error' ? '❌' : '⚠️'} {para.annotation.message}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 总评 */}
      <Card title="📋 AI 总评" style={{ borderRadius: 12 }} bordered={false}>
        <div style={{ fontSize: 14, lineHeight: 1.9, color: '#444', marginBottom: 16 }}>
          {isCode
            ? '同学的基础语法掌握较好，函数定义和列表创建均正确。主要问题：① for 语句末尾必须加冒号；② 列表索引从0开始，访问 x[3] 会越界（列表长度为3）。建议多练习循环语法细节。'
            : '实验报告结构较完整，实验目的清晰。主要问题：① 对 type() 函数返回值描述有误，"hello" 应为 str 类型；② 实验总结部分缺失，建议补充实验收获和问题分析。'
          }
        </div>
        <Divider />
        <div style={{ display: 'flex', gap: 24 }}>
          {[
            { label: '错误数', value: 2, color: '#ff4d4f' },
            { label: '警告数', value: isCode ? 0 : 1, color: '#faad14' },
            { label: '正确点', value: isCode ? 5 : 3, color: '#52c41a' },
          ].map(s => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 12, color: '#999' }}>{s.label}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

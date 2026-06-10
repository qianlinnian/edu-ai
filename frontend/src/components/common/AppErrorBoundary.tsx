import React from 'react'
import { Alert, Button, Result, Space } from 'antd'

type Props = {
  children: React.ReactNode
}

type State = {
  hasError: boolean
  message: string
}

export default class AppErrorBoundary extends React.Component<Props, State> {
  state: State = {
    hasError: false,
    message: '',
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error?.message || '页面发生异常',
    }
  }

  componentDidCatch(error: Error) {
    console.error('AppErrorBoundary caught error:', error)
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    return (
      <Result
        status="error"
        title="页面加载失败"
        subTitle="当前页面出现运行错误，已阻止整页白屏。"
        extra={(
          <Space direction="vertical" size={12}>
            <Alert type="error" showIcon message={this.state.message} />
            <Button type="primary" onClick={() => window.location.reload()}>
              刷新页面
            </Button>
          </Space>
        )}
      />
    )
  }
}

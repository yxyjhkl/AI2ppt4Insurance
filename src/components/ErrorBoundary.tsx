import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] Uncaught error:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-8">
          <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 shadow-lg">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
                <span className="text-xl">⚠</span>
              </div>
              <h2 className="text-lg font-semibold text-gray-800">
                页面出现异常
              </h2>
            </div>
            <p className="mb-2 text-sm text-gray-500">
              应用遇到了意外错误，请尝试刷新页面。
            </p>
            {this.state.error && (
              <details className="mb-4">
                <summary className="cursor-pointer text-xs text-gray-400">
                  查看错误详情
                </summary>
                <pre className="mt-2 max-h-48 overflow-auto rounded bg-gray-100 p-3 text-xs text-red-700">
                  {this.state.error.message}
                  {'\n'}
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            <button
              onClick={this.handleReset}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              重试
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

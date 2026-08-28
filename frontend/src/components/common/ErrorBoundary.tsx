import { Component, type ErrorInfo, type ReactNode } from 'react'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'

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
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex min-h-[40vh] items-center justify-center p-6">
          <Card className="max-w-md text-center">
            <h2 className="text-lg font-semibold text-[var(--color-text)]">
              Something went wrong
            </h2>
            <p className="mt-2 text-sm text-[var(--color-text-muted)]">
              {this.state.error?.message ?? 'An unexpected error occurred.'}
            </p>
            <Button
              className="mt-4"
              variant="primary"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try again
            </Button>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

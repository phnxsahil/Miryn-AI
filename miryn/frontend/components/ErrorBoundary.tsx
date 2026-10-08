"use client";

import { Component, ReactNode } from "react";

type Props = {
  children: ReactNode;
  fallback?: ReactNode;
};

type State = {
  hasError: boolean;
  error?: Error;
};

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: { componentStack?: string }) {
    try {
      const ph = (window as Window & { posthog?: { capture?: (event: string, properties?: Record<string, unknown>) => void } }).posthog;
      if (ph?.capture) {
        ph.capture("error_boundary_caught", {
          error: error.message,
          component_stack: errorInfo?.componentStack,
        });
      }
    } catch {
      // silently fail
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center min-h-[40vh] text-center p-8">
          <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-primary mb-2">Something went wrong</h2>
          <p className="text-muted text-sm mb-6 max-w-sm">An unexpected error occurred. Try refreshing the page.</p>
          <button
            onClick={() => window.location.reload()}
            className="h-12 px-8 bg-accent text-[color:var(--theme-accent-contrast)] rounded-full font-bold hover:scale-105 transition-all"
          >
            Refresh
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

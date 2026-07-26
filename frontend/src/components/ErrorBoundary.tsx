import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary — catches render-time exceptions anywhere in its subtree
 * and shows a visible fallback instead of a blank white page.
 *
 * Intentionally kept local to the UI layer. It does NOT call any
 * backend service, does NOT touch CostEngine/Quotes/Orders/Execution,
 * and does NOT persist anything.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Surface in console so we still have the stack for debugging.
    console.error("[ErrorBoundary] caught render error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    const err = this.state.error;
    const title = this.props.fallbackTitle ?? "A apărut o eroare în această pagină";

    return (
      <div className="p-4">
        <div className="bg-red-900/15 border border-red-800/40 rounded-lg p-5 max-w-3xl">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <h2 className="text-[14px] font-bold text-red-300 mb-1">{title}</h2>
              <p className="text-[12px] text-red-200/80 mb-3">
                Pagina a întâmpinat o eroare în timpul randării. Detaliile sunt mai jos — vă rugăm
                raportați-le pentru investigație.
              </p>

              {err && (
                <div className="bg-wo-surface-inset border border-red-900/40 rounded p-3 mb-3 overflow-auto max-h-64">
                  <p className="text-[11px] text-red-300 font-mono mb-1">
                    {err.name}: {err.message}
                  </p>
                  {err.stack && (
                    <pre className="text-[10px] text-slate-400 whitespace-pre-wrap font-mono">
                      {err.stack.split("\n").slice(0, 10).join("\n")}
                    </pre>
                  )}
                </div>
              )}

              <div className="flex items-center gap-2">
                <button
                  onClick={this.handleReset}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded text-[11px] font-semibold transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  Încearcă din nou
                </button>
                <button
                  onClick={this.handleReload}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-red-700 hover:bg-red-600 text-white rounded text-[11px] font-semibold transition-colors"
                >
                  Reîncarcă pagina
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;
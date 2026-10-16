import React, { Component, type ErrorInfo, type ReactNode } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("AtmoGraph Runtime Error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "40px", color: "#dc2626", fontFamily: "system-ui, sans-serif", background: "#f8fafc", minHeight: "100vh", boxSizing: "border-box" }}>
          <div style={{ maxWidth: "800px", margin: "0 auto", background: "#ffffff", border: "1px solid #fecaca", borderRadius: "12px", padding: "24px", boxShadow: "0 10px 25px -5px rgba(0,0,0,0.05)" }}>
            <h2 style={{ color: "#dc2626", margin: "0 0 12px" }}>Something went wrong</h2>
            <p style={{ color: "#334155", fontSize: "14px", lineHeight: 1.6 }}>
              {this.state.error?.message || String(this.state.error)}
            </p>
            {this.state.error?.stack && (
              <pre style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: "16px", borderRadius: "8px", overflow: "auto", fontSize: "12px", color: "#64748b" }}>
                {this.state.error.stack}
              </pre>
            )}
            <div style={{ marginTop: "20px", display: "flex", gap: "10px" }}>
              <button
                onClick={() => {
                  try {
                    localStorage.clear();
                    sessionStorage.clear();
                  } catch (e) {}
                  window.location.reload();
                }}
                style={{
                  padding: "10px 18px",
                  background: "#2563eb",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Clear Cache & Restart
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
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
        <div style={{ padding: "40px", color: "#f87171", fontFamily: "system-ui, sans-serif", background: "#0a0b0e", minHeight: "100vh", boxSizing: "border-box" }}>
          <div style={{ maxWidth: "800px", margin: "0 auto", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "12px", padding: "24px" }}>
            <h2 style={{ color: "#ef4444", margin: "0 0 12px" }}>⚠️ AtmoGraph UI Startup Issue</h2>
            <p style={{ color: "#e2e8f0", fontSize: "14px", lineHeight: 1.6 }}>
              {this.state.error?.message || String(this.state.error)}
            </p>
            {this.state.error?.stack && (
              <pre style={{ background: "#060709", padding: "16px", borderRadius: "8px", overflow: "auto", fontSize: "12px", color: "#fca5a5" }}>
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
                  background: "#e8a838",
                  color: "#0a0b0e",
                  border: "none",
                  borderRadius: "6px",
                  fontWeight: 700,
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
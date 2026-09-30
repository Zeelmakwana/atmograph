import { useState } from "react";
import { Network, Loader2, Mail, Lock, Building2 } from "lucide-react";

interface AuthPageProps {
  onAuthSuccess: (user: { id: number; email: string; company_name: string }, token: string) => void;
}

export default function AuthPage({ onAuthSuccess }: AuthPageProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
      const body = isLogin
        ? { email, password }
        : { email, password, company_name: companyName };

      const apiBase =
        import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiBase}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (data.success && data.user && data.token) {
        onAuthSuccess(data.user, data.token);
      } else {
        setError(data.error || "Authentication failed. Please try again.");
      }
    } catch (err) {
      setError("Unable to connect to server. Please check your connection.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Brand */}
        <div className="auth-brand">
          <div className="auth-logo">
            <Network size={32} />
          </div>
          <div className="auth-title">AtmoGraph</div>
          <div className="auth-subtitle">Supply Chain Disruption Intelligence</div>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs">
          <button
            className={`auth-tab ${isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(true); setError(""); }}
          >
            Login
          </button>
          <button
            className={`auth-tab ${!isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(false); setError(""); }}
          >
            Register
          </button>
        </div>

        {/* Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          {/* Email */}
          <div className="auth-field">
            <label className="auth-label">Email Address</label>
            <div className="auth-input-wrap">
              <Mail size={16} className="auth-input-icon" />
              <input
                type="email"
                className="auth-input"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>
          </div>

          {/* Password */}
          <div className="auth-field">
            <label className="auth-label">Password</label>
            <div className="auth-input-wrap">
              <Lock size={16} className="auth-input-icon" />
              <input
                type="password"
                className="auth-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                minLength={6}
              />
            </div>
          </div>

          {/* Company Name (Register Only) */}
          {!isLogin && (
            <div className="auth-field">
              <label className="auth-label">Company Name</label>
              <div className="auth-input-wrap">
                <Building2 size={16} className="auth-input-icon" />
                <input
                  type="text"
                  className="auth-input"
                  placeholder="Your Company Pvt Ltd"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="auth-spin" />
                {isLogin ? "Signing In..." : "Creating Account..."}
              </>
            ) : (
              isLogin ? "Sign In" : "Create Account"
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer">
          {isLogin ? (
            <span>
              New to AtmoGraph?{" "}
              <button className="auth-link" onClick={() => { setIsLogin(false); setError(""); }}>
                Register your company
              </button>
            </span>
          ) : (
            <span>
              Already have an account?{" "}
              <button className="auth-link" onClick={() => { setIsLogin(true); setError(""); }}>
                Sign in
              </button>
            </span>
          )}
        </div>
      </div>

      <style>{`
        .auth-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #0a0a0b 0%, #141416 50%, #0a0a0b 100%);
          padding: 24px;
        }

        .auth-container {
          width: 100%;
          max-width: 420px;
          background: rgba(20, 20, 22, 0.95);
          border-radius: 16px;
          border: 1px solid rgba(232, 168, 56, 0.15);
          padding: 40px 32px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .auth-brand {
          text-align: center;
          margin-bottom: 32px;
        }

        .auth-logo {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 64px;
          height: 64px;
          background: linear-gradient(135deg, rgba(232, 168, 56, 0.15), rgba(212, 148, 44, 0.1));
          border-radius: 16px;
          color: #e8a838;
          margin-bottom: 16px;
        }

        .auth-title {
          font-size: 28px;
          font-weight: 700;
          color: #f8fafc;
          letter-spacing: -0.5px;
        }

        .auth-subtitle {
          font-size: 13px;
          color: #94a3b8;
          margin-top: 4px;
        }

        .auth-tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 24px;
          padding: 4px;
          background: rgba(10, 10, 11, 0.5);
          border-radius: 8px;
        }

        .auth-tab {
          flex: 1;
          padding: 10px 16px;
          border: none;
          background: transparent;
          color: #94a3b8;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.2s ease;
        }

        .auth-tab:hover {
          color: #e8a838;
        }

        .auth-tab.active {
          background: rgba(232, 168, 56, 0.15);
          color: #e8a838;
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .auth-field {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .auth-label {
          font-size: 13px;
          font-weight: 500;
          color: #e2e8f0;
        }

        .auth-input-wrap {
          position: relative;
          display: flex;
          align-items: center;
        }

        .auth-input-icon {
          position: absolute;
          left: 14px;
          color: #64748b;
          pointer-events: none;
        }

        .auth-input {
          width: 100%;
          padding: 12px 14px 12px 42px;
          background: rgba(10, 10, 11, 0.6);
          border: 1px solid rgba(232, 168, 56, 0.2);
          border-radius: 8px;
          color: #f8fafc;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .auth-input:focus {
          outline: none;
          border-color: #e8a838;
          background: rgba(10, 10, 11, 0.8);
        }

        .auth-input::placeholder {
          color: #64748b;
        }

        .auth-error {
          padding: 12px 14px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 8px;
          color: #f87171;
          font-size: 13px;
        }

        .auth-submit {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 14px;
          background: linear-gradient(135deg, #d4942c 0%, #e8a838 50%, #f0b848 100%);
          border: none;
          border-radius: 8px;
          color: #0a0a0b;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .auth-submit:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 8px 20px rgba(232, 168, 56, 0.3);
        }

        .auth-submit:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .auth-spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .auth-footer {
          margin-top: 24px;
          text-align: center;
          font-size: 13px;
          color: #94a3b8;
        }

        .auth-link {
          background: none;
          border: none;
          color: #e8a838;
          font-weight: 500;
          cursor: pointer;
          text-decoration: none;
        }

        .auth-link:hover {
          text-decoration: underline;
        }

        @media (max-width: 480px) {
          .auth-container {
            padding: 32px 20px;
          }

          .auth-title {
            font-size: 24px;
          }
        }
      `}</style>
    </div>
  );
}

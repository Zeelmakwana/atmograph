import React, { useState, useEffect } from "react";
import {
  Building2,
  Check,
  CheckCircle2,
  ChevronRight,
  Factory,
  Layers,
  Loader2,
  Lock,
  Plus,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Truck,
  User,
  X,
  Package,
} from "lucide-react";
import {
  getWorkspaces,
  switchWorkspace,
  registerWorkspace,
  type BusinessWorkspace,
  type WorkspacesResponse,
} from "../services/supplyChainApi";

interface WorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onWorkspaceSwitched: (workspace: BusinessWorkspace) => void;
}

export default function WorkspaceModal({
  isOpen,
  onClose,
  onWorkspaceSwitched,
}: WorkspaceModalProps) {
  const [data, setData] = useState<WorkspacesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [switchingId, setSwitchingId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"overview" | "register">("overview");

  // Registration Form State
  const [regName, setRegName] = useState("");
  const [regIndustry, setRegIndustry] = useState("");
  const [regOwner, setRegOwner] = useState("");
  const [regLocation, setRegLocation] = useState("");
  const [regSubmitting, setRegSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchWorkspaces = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await getWorkspaces();
      setData(res);
    } catch (err: any) {
      console.warn("Failed to load workspaces:", err);
      setErrorMsg(err.message || "Failed to load workspaces.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      void fetchWorkspaces();
      setErrorMsg(null);
      setSuccessMsg(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSwitch = async (ws: BusinessWorkspace) => {
    if (ws.is_active) {
      onClose();
      return;
    }

    try {
      setSwitchingId(ws.workspace_id);
      setErrorMsg(null);
      setSuccessMsg(null);
      const updated = await switchWorkspace(ws.workspace_id);
      setData(updated);
      setSuccessMsg(`Switched to ${ws.company_name}! Studio scoped to your entity.`);
      onWorkspaceSwitched(ws);
      window.dispatchEvent(new CustomEvent("atmograph:workspace-changed", { detail: ws }));
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to switch workspace.");
    } finally {
      setSwitchingId(null);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName.trim() || !regIndustry.trim()) {
      setErrorMsg("Please enter both Company/Branch Name and Industry Sector.");
      return;
    }

    try {
      setRegSubmitting(true);
      setErrorMsg(null);
      const res = await registerWorkspace(
        regName.trim(),
        regIndustry.trim(),
        regOwner.trim() || undefined,
        regLocation.trim() || undefined
      );

      setSuccessMsg(res.message || "Branch workspace registered!");
      await fetchWorkspaces();
      const newWs: BusinessWorkspace = {
        workspace_id: res.company.company_id,
        company_id: res.company.company_id,
        company_name: res.company.company_name,
        industry: res.company.industry,
        owner_name: regOwner.trim() || "Owner",
        location: regLocation.trim() || "Verified Facility",
        suppliers_count: 0,
        plants_count: 0,
        is_active: true,
        badge: res.company.company_name.slice(0, 2).toUpperCase(),
        description: "Freshly registered enterprise branch.",
      };
      onWorkspaceSwitched(newWs);
      window.dispatchEvent(new CustomEvent("atmograph:workspace-changed", { detail: newWs }));
      setTimeout(() => {
        onClose();
      }, 900);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register workspace.");
    } finally {
      setRegSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.78)",
        backdropFilter: "blur(8px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "680px",
          backgroundColor: "#12141a",
          borderRadius: "16px",
          border: "1px solid rgba(232, 168, 56, 0.25)",
          boxShadow: "0 28px 60px rgba(0, 0, 0, 0.8), 0 0 20px rgba(232, 168, 56, 0.08)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          maxHeight: "90vh",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "linear-gradient(180deg, rgba(232, 168, 56, 0.06) 0%, transparent 100%)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "10px",
                backgroundColor: "rgba(232, 168, 56, 0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#e8a838",
                border: "1px solid rgba(232, 168, 56, 0.3)",
              }}
            >
              <Building2 size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "#f8fafc" }}>
                  My Business Workspace
                </h3>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "2px 8px",
                    borderRadius: "6px",
                    backgroundColor: "rgba(74, 222, 128, 0.15)",
                    border: "1px solid rgba(74, 222, 128, 0.3)",
                    color: "#4ade80",
                    fontSize: "10px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  <Lock size={10} /> Private & Tenant Isolated
                </span>
              </div>
              <p style={{ margin: "3px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                Complete data privacy active. Strictly isolated to your company account.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "#94a3b8",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Security & Privacy Banner */}
        <div
          style={{
            padding: "10px 24px",
            backgroundColor: "rgba(74, 222, 128, 0.06)",
            borderBottom: "1px solid rgba(74, 222, 128, 0.15)",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontSize: "11.5px",
            color: "#86efac",
          }}
        >
          <ShieldCheck size={16} color="#4ade80" style={{ flexShrink: 0 }} />
          <div>
            <strong>Strict Privacy Active:</strong> You can only view and manage your own enterprise assets. Other businesses cannot see or access your supply chain topology.
          </div>
        </div>

        {/* Tab switch / register */}
        <div
          style={{
            display: "flex",
            padding: "10px 24px",
            gap: "10px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
            backgroundColor: "#0d0f14",
          }}
        >
          <button
            onClick={() => {
              setViewMode("overview");
              setErrorMsg(null);
            }}
            style={{
              padding: "7px 16px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              fontSize: "12.5px",
              fontWeight: 600,
              backgroundColor: viewMode === "overview" ? "rgba(232, 168, 56, 0.18)" : "transparent",
              color: viewMode === "overview" ? "#e8a838" : "#94a3b8",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
          >
            <Layers size={14} />
            <span>Active Enterprise Workspace</span>
          </button>

          <button
            onClick={() => {
              setViewMode("register");
              setErrorMsg(null);
            }}
            style={{
              padding: "7px 16px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              fontSize: "12.5px",
              fontWeight: 600,
              backgroundColor: viewMode === "register" ? "rgba(74, 222, 128, 0.15)" : "transparent",
              color: viewMode === "register" ? "#4ade80" : "#94a3b8",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
          >
            <Plus size={14} />
            <span>+ Add Subsidiary / Branch</span>
          </button>
        </div>

        {/* Content body */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          {errorMsg && (
            <div
              style={{
                marginBottom: "16px",
                padding: "12px 14px",
                borderRadius: "8px",
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#f87171",
                fontSize: "12.5px",
              }}
            >
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div
              style={{
                marginBottom: "16px",
                padding: "12px 14px",
                borderRadius: "8px",
                backgroundColor: "rgba(74, 222, 128, 0.15)",
                border: "1px solid rgba(74, 222, 128, 0.3)",
                color: "#4ade80",
                fontSize: "12.5px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <CheckCircle2 size={16} />
              <span>{successMsg}</span>
            </div>
          )}

          {viewMode === "overview" && (
            <div>
              <div style={{ marginBottom: "16px", fontSize: "12px", color: "#94a3b8", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span>Your private workspaces ({data?.workspaces?.length ?? 1}):</span>
                <span style={{ color: "#4ade80", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                  <ShieldCheck size={13} /> Zero Cross-Tenant Leakage
                </span>
              </div>

              {loading ? (
                <div style={{ textAlign: "center", padding: "40px", color: "#94a3b8" }}>
                  <Loader2 size={24} className="spin" style={{ marginBottom: "10px", color: "#e8a838" }} />
                  <div>Loading your business workspace...</div>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {data?.workspaces.map((ws) => {
                    const isBusy = switchingId === ws.workspace_id;
                    return (
                      <div
                        key={ws.workspace_id}
                        style={{
                          padding: "18px",
                          borderRadius: "12px",
                          border: ws.is_active
                            ? "1.5px solid rgba(232, 168, 56, 0.5)"
                            : "1px solid rgba(255, 255, 255, 0.08)",
                          backgroundColor: ws.is_active
                            ? "rgba(232, 168, 56, 0.06)"
                            : "rgba(255, 255, 255, 0.02)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: "16px",
                          boxShadow: ws.is_active ? "0 4px 20px rgba(232, 168, 56, 0.1)" : "none",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "14px", flex: 1 }}>
                          <div
                            style={{
                              width: "48px",
                              height: "48px",
                              borderRadius: "12px",
                              backgroundColor: ws.is_active
                                ? "rgba(232, 168, 56, 0.2)"
                                : "rgba(255, 255, 255, 0.06)",
                              color: ws.is_active ? "#e8a838" : "#f8fafc",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontWeight: 800,
                              fontSize: "16px",
                              flexShrink: 0,
                              border: ws.is_active ? "1px solid rgba(232, 168, 56, 0.4)" : "none",
                            }}
                          >
                            {ws.badge}
                          </div>

                          <div style={{ flex: 1 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                              <strong style={{ color: "#f8fafc", fontSize: "15px" }}>
                                {ws.company_name}
                              </strong>
                              {ws.is_active && (
                                <span
                                  style={{
                                    fontSize: "10px",
                                    padding: "2px 8px",
                                    borderRadius: "999px",
                                    backgroundColor: "rgba(74, 222, 128, 0.2)",
                                    border: "1px solid rgba(74, 222, 128, 0.4)",
                                    color: "#4ade80",
                                    fontWeight: 700,
                                    textTransform: "uppercase",
                                    letterSpacing: "0.5px",
                                  }}
                                >
                                  Active Business
                                </span>
                              )}
                            </div>

                            <div style={{ fontSize: "12px", color: "#e8a838", marginTop: "3px", fontWeight: 500 }}>
                              {ws.industry} · {ws.location || "Verified Facility"}
                            </div>

                            <p style={{ margin: "5px 0 0 0", fontSize: "11.5px", color: "#94a3b8", lineHeight: 1.4 }}>
                              {ws.description}
                            </p>

                            <div
                              style={{
                                display: "flex",
                                gap: "14px",
                                marginTop: "10px",
                                fontSize: "11.5px",
                                color: "#f8fafc",
                                flexWrap: "wrap",
                              }}
                            >
                              <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                                <Truck size={13} color="#e8a838" />
                                <strong>{ws.suppliers_count}</strong> Suppliers
                              </span>
                              <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                                <Factory size={13} color="#e8a838" />
                                <strong>{ws.plants_count}</strong> Processing Units
                              </span>
                              {ws.owner_name && (
                                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", color: "#94a3b8" }}>
                                  <User size={13} />
                                  {ws.owner_name}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div>
                          {ws.is_active ? (
                            <div
                              style={{
                                padding: "8px 14px",
                                borderRadius: "8px",
                                border: "1px solid rgba(74, 222, 128, 0.4)",
                                backgroundColor: "rgba(74, 222, 128, 0.12)",
                                color: "#4ade80",
                                fontSize: "12px",
                                fontWeight: 700,
                                display: "flex",
                                alignItems: "center",
                                gap: "6px",
                              }}
                            >
                              <Check size={14} />
                              Active
                            </div>
                          ) : (
                            <button
                              onClick={() => void handleSwitch(ws)}
                              disabled={isBusy}
                              style={{
                                padding: "8px 16px",
                                borderRadius: "8px",
                                border: "1px solid rgba(255, 255, 255, 0.15)",
                                backgroundColor: "rgba(255, 255, 255, 0.08)",
                                color: "#ececef",
                                fontSize: "12px",
                                fontWeight: 600,
                                display: "flex",
                                alignItems: "center",
                                gap: "6px",
                                cursor: isBusy ? "not-allowed" : "pointer",
                                transition: "all 0.2s",
                              }}
                            >
                              {isBusy ? (
                                <>
                                  <Loader2 size={14} className="spin" />
                                  <span>Loading...</span>
                                </>
                              ) : (
                                <>
                                  <span>Switch to Entity</span>
                                  <ChevronRight size={14} />
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {viewMode === "register" && (
            <form onSubmit={handleRegister}>
              <div style={{ marginBottom: "16px", fontSize: "12px", color: "#94a3b8" }}>
                Add another operating division, subsidiary, or regional workspace under your account. All branches remain strictly private to your company login.
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#f8fafc", marginBottom: "6px" }}>
                    Company / Branch / Division Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Mohilya Textiles Export Division or Western Hub"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      borderRadius: "8px",
                      backgroundColor: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#ececef",
                      fontSize: "13px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#f8fafc", marginBottom: "6px" }}>
                    Industry Sector *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Textiles, Attar & Fragrance, FMCG, Electronics, Apparel"
                    value={regIndustry}
                    onChange={(e) => setRegIndustry(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      borderRadius: "8px",
                      backgroundColor: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#ececef",
                      fontSize: "13px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#f8fafc", marginBottom: "6px" }}>
                      Division Lead / Manager
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Lead Officer"
                      value={regOwner}
                      onChange={(e) => setRegOwner(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#ececef",
                        fontSize: "13px",
                        outline: "none",
                        boxSizing: "border-box",
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#f8fafc", marginBottom: "6px" }}>
                      Headquarters / Hub Location
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Surat, Gujarat / Mumbai"
                      value={regLocation}
                      onChange={(e) => setRegLocation(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#ececef",
                        fontSize: "13px",
                        outline: "none",
                        boxSizing: "border-box",
                      }}
                    />
                  </div>
                </div>

                <div style={{ marginTop: "10px" }}>
                  <button
                    type="submit"
                    disabled={regSubmitting}
                    style={{
                      width: "100%",
                      padding: "12px",
                      borderRadius: "8px",
                      backgroundColor: "#4ade80",
                      color: "#0c0d0e",
                      fontWeight: 700,
                      fontSize: "13px",
                      border: "none",
                      cursor: regSubmitting ? "not-allowed" : "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "8px",
                      transition: "all 0.2s ease",
                    }}
                  >
                    {regSubmitting ? (
                      <>
                        <Loader2 size={16} className="spin" />
                        <span>Registering & Initializing Subsidiary...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} />
                        <span>Create Isolated Branch Workspace</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

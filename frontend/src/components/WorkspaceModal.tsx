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
          backgroundColor: "#ffffff",
          borderRadius: "16px",
          border: "1px solid #cbd5e1",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.12)",
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
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#f8fafc",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "10px",
                backgroundColor: "rgba(37, 99, 235, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#2563eb",
                border: "1px solid rgba(37, 99, 235, 0.2)",
              }}
            >
              <Building2 size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "#0f172a" }}>
                  My Company Workspaces
                </h3>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "2px 8px",
                    borderRadius: "6px",
                    backgroundColor: "#dcfce7",
                    border: "1px solid #bbf7d0",
                    color: "#16a34a",
                    fontSize: "11px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  <Lock size={10} /> Private & Secure
                </span>
              </div>
              <p style={{ margin: "3px 0 0 0", fontSize: "12px", color: "#64748b" }}>
                Only your account has access to this data.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "#f1f5f9",
              border: "1px solid #cbd5e1",
              color: "#64748b",
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
            backgroundColor: "rgba(22, 163, 74, 0.08)",
            borderBottom: "1px solid #bbf7d0",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontSize: "12px",
            color: "#166534",
          }}
        >
          <ShieldCheck size={16} color="#16a34a" style={{ flexShrink: 0 }} />
          <div>
            <strong>Strict Privacy Active:</strong> You can only see and manage your own company's suppliers and factories.
          </div>
        </div>

        {/* Tab switch / register */}
        <div
          style={{
            display: "flex",
            padding: "10px 24px",
            gap: "10px",
            borderBottom: "1px solid #e2e8f0",
            backgroundColor: "#f8fafc",
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
              backgroundColor: viewMode === "overview" ? "#2563eb" : "transparent",
              color: viewMode === "overview" ? "#ffffff" : "#64748b",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
          >
            <Layers size={14} />
            <span>Active Companies</span>
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
              backgroundColor: viewMode === "register" ? "#2563eb" : "transparent",
              color: viewMode === "register" ? "#ffffff" : "#64748b",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
          >
            <Plus size={14} />
            <span>+ Add New Branch</span>
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
                backgroundColor: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#b91c1c",
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
                backgroundColor: "#f0fdf4",
                border: "1px solid #bbf7d0",
                color: "#166534",
                fontSize: "12.5px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <CheckCircle2 size={16} color="#16a34a" />
              <span>{successMsg}</span>
            </div>
          )}

          {viewMode === "overview" && (
            <div>
              <div style={{ marginBottom: "16px", fontSize: "12px", color: "#64748b", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span>Your private workspaces ({data?.workspaces?.length ?? 1}):</span>
                <span style={{ color: "#16a34a", display: "inline-flex", alignItems: "center", gap: "4px", fontWeight: 600 }}>
                  <ShieldCheck size={13} /> Complete Data Protection
                </span>
              </div>

              {loading ? (
                <div style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>
                  <Loader2 size={24} className="sc-spin" style={{ marginBottom: "10px", color: "#2563eb" }} />
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
                            ? "2px solid #2563eb"
                            : "1px solid #e2e8f0",
                          backgroundColor: ws.is_active
                            ? "#ffffff"
                            : "#f8fafc",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: "16px",
                          boxShadow: ws.is_active ? "0 4px 12px rgba(37, 99, 235, 0.08)" : "none",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "14px", flex: 1 }}>
                          <div
                            style={{
                              width: "48px",
                              height: "48px",
                              borderRadius: "12px",
                              backgroundColor: ws.is_active
                                ? "rgba(37, 99, 235, 0.1)"
                                : "#e2e8f0",
                              color: ws.is_active ? "#2563eb" : "#475569",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontWeight: 800,
                              fontSize: "16px",
                              flexShrink: 0,
                            }}
                          >
                            {ws.badge}
                          </div>

                          <div style={{ flex: 1 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                              <strong style={{ color: "#0f172a", fontSize: "15px" }}>
                                {ws.company_name}
                              </strong>
                              {ws.is_active && (
                                <span
                                  style={{
                                    fontSize: "10px",
                                    padding: "2px 8px",
                                    borderRadius: "999px",
                                    backgroundColor: "#dcfce7",
                                    border: "1px solid #bbf7d0",
                                    color: "#16a34a",
                                    fontWeight: 700,
                                    textTransform: "uppercase",
                                    letterSpacing: "0.5px",
                                  }}
                                >
                                  Current Company
                                </span>
                              )}
                            </div>

                            <div style={{ fontSize: "12px", color: "#2563eb", marginTop: "3px", fontWeight: 600 }}>
                              {ws.industry} · {ws.location || "Verified Facility"}
                            </div>

                            <p style={{ margin: "5px 0 0 0", fontSize: "12px", color: "#64748b", lineHeight: 1.4 }}>
                              {ws.description}
                            </p>

                            <div
                              style={{
                                display: "flex",
                                gap: "14px",
                                marginTop: "10px",
                                fontSize: "12px",
                                color: "#0f172a",
                                flexWrap: "wrap",
                              }}
                            >
                              <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                                <Truck size={13} color="#2563eb" />
                                <strong>{ws.suppliers_count}</strong> Suppliers
                              </span>
                              <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                                <Factory size={13} color="#2563eb" />
                                <strong>{ws.plants_count}</strong> Factories
                              </span>
                              {ws.owner_name && (
                                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", color: "#64748b" }}>
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
                                border: "1px solid #bbf7d0",
                                backgroundColor: "#dcfce7",
                                color: "#16a34a",
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
                                border: "none",
                                backgroundColor: "#2563eb",
                                color: "#ffffff",
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
                                  <Loader2 size={14} className="sc-spin" />
                                  <span>Loading...</span>
                                </>
                              ) : (
                                <>
                                  <span>Switch to This Company</span>
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
              <div style={{ marginBottom: "16px", fontSize: "12px", color: "#64748b" }}>
                Add another business, subsidiary, or regional branch. Each company stays private to your account.
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                    Company / Branch Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. My Business Second Branch"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      borderRadius: "8px",
                      backgroundColor: "#ffffff",
                      border: "1px solid #cbd5e1",
                      color: "#0f172a",
                      fontSize: "13px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                    Industry *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Manufacturing, Retail, Food, Fashion"
                    value={regIndustry}
                    onChange={(e) => setRegIndustry(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      borderRadius: "8px",
                      backgroundColor: "#ffffff",
                      border: "1px solid #cbd5e1",
                      color: "#0f172a",
                      fontSize: "13px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                      Manager Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Operations Manager"
                      value={regOwner}
                      onChange={(e) => setRegOwner(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        backgroundColor: "#ffffff",
                        border: "1px solid #cbd5e1",
                        color: "#0f172a",
                        fontSize: "13px",
                        outline: "none",
                        boxSizing: "border-box",
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
                      City / Location
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Mumbai, Surat, Delhi"
                      value={regLocation}
                      onChange={(e) => setRegLocation(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "10px 14px",
                        borderRadius: "8px",
                        backgroundColor: "#ffffff",
                        border: "1px solid #cbd5e1",
                        color: "#0f172a",
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
                      backgroundColor: "#2563eb",
                      color: "#ffffff",
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
                        <Loader2 size={16} className="sc-spin" />
                        <span>Creating Workspace...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} />
                        <span>Create Workspace</span>
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

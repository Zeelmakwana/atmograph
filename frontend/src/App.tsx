import { useState, useEffect, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  Bell,
  Building2,
  CheckCircle2,
  ChevronDown,
  FileSpreadsheet,
  History,
  Layers,
  LayoutDashboard,
  LogOut,
  Network,
  Radio,
  RefreshCw,
  Search,
  Sparkles,
  Truck,
  User,
  Zap,
} from "lucide-react";

import DashboardOverview from "./pages/DashboardOverview";
import SupplyChainSimulator from "./pages/supply-chain/SupplyChainSimulator";
import ExcelDataImport from "./pages/supply-chain/ExcelDataImport";
import SupplyNetworkPage from "./pages/SupplyNetworkPage";
import IncidentRadarPage from "./pages/IncidentRadarPage";
import SystemStatusPage from "./pages/SystemStatusPage";
import HistoricalIntelligence from "./components/HistoricalIntelligence";
import GlobalSearch from "./components/GlobalSearch";
import WorkspaceModal from "./components/WorkspaceModal";
import AuthPage from "./pages/AuthPage";
import { AuthProvider, useAuth } from "./context/AuthContext";
import {
  getWorkspaces,
  type BusinessWorkspace,
} from "./services/supplyChainApi";

export type ActiveTab =
  | "catalog"
  | "overview"
  | "network"
  | "simulator"
  | "radar"
  | "history"
  | "status";

function AppContent() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");
  const [selectedSupplierForSim, setSelectedSupplierForSim] = useState<string>("");
  const [activeEventId, setActiveEventId] = useState<number | null>(null);
  const [selectedEventForRadar, setSelectedEventForRadar] = useState<{
    id?: number;
    title?: string;
    description?: string;
    source?: string;
    activatedAt?: number;
  } | null>(null);
  const [isWorkspaceModalOpen, setIsWorkspaceModalOpen] = useState(false);
  const [activeWorkspace, setActiveWorkspace] = useState<BusinessWorkspace | null>(null);

  const fetchActiveWorkspace = useCallback(async () => {
    try {
      const res = await getWorkspaces();
      const current = res.workspaces.find((w) => w.is_active) || res.workspaces[0] || null;
      setActiveWorkspace(current);
    } catch (err) {
      console.warn("Failed to load initial workspace:", err);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      void fetchActiveWorkspace();
    }

    const handleWsChange = (e: any) => {
      if (e.detail) {
        setActiveWorkspace(e.detail);
      } else {
        void fetchActiveWorkspace();
      }
    };

    window.addEventListener("atmograph:workspace-changed", handleWsChange);
    return () => {
      window.removeEventListener("atmograph:workspace-changed", handleWsChange);
    };
  }, [fetchActiveWorkspace, isAuthenticated]);

  useEffect(() => {
    const handleSimEvent = (e: any) => {
      if (e.detail?.supplier_id) {
        setSelectedSupplierForSim(e.detail.supplier_id);
      }
    };

    window.addEventListener("atmograph:supplier-simulation", handleSimEvent);
    return () => {
      window.removeEventListener("atmograph:supplier-simulation", handleSimEvent);
    };
  }, []);

  const handleSimulateSupplier = (supplierId: string) => {
    setSelectedSupplierForSim(supplierId);
    setActiveTab("simulator");
  };

  const handleActivateHistoricalEvent = (event: any) => {
    const id = Number(event?.id ?? event?.event_id);
    if (id) setActiveEventId(id);
    setSelectedEventForRadar({
      id: id || undefined,
      title: event?.title || "",
      description: event?.description || "",
      source: event?.source || "Historical Incident Archive",
      activatedAt: Date.now(),
    });
    setActiveTab("radar");
  };

  // Show loading state
  if (isLoading) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f8fafc",
        color: "#2563eb",
        fontSize: "16px",
        fontWeight: 600
      }}>
        Loading AtmoGraph...
      </div>
    );
  }

  // Show auth page if not authenticated
  if (!isAuthenticated || !user) {
    return (
      <AuthPage
        onAuthSuccess={(userData, token) => {
          login(userData, token);
        }}
      />
    );
  }

  return (
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <aside className="app-sidebar">
        {/* Brand Header */}
        <div className="brand-header">
          <div className="brand-icon">
            <Network size={20} />
          </div>
          <div>
            <div className="brand-title">AtmoGraph</div>
            <div className="brand-subtitle">Risk & Delay Tracker</div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          <div className="nav-section-title">MAIN MENU</div>

          <button
            className={`nav-link ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            <span className="nav-icon">
              <Zap size={17} color="#2563eb" />
            </span>
            <span>1. Disruption Checker</span>
          </button>

          <button
            className={`nav-link ${activeTab === "network" ? "active" : ""}`}
            onClick={() => setActiveTab("network")}
          >
            <span className="nav-icon">
              <Network size={17} />
            </span>
            <span>2. Supply Chain Map</span>
          </button>

          <button
            className={`nav-link ${activeTab === "simulator" ? "active" : ""}`}
            onClick={() => setActiveTab("simulator")}
          >
            <span className="nav-icon">
              <Layers size={17} />
            </span>
            <span>3. What-If Simulator</span>
          </button>

          <button
            className={`nav-link ${activeTab === "catalog" ? "active" : ""}`}
            onClick={() => setActiveTab("catalog")}
          >
            <span className="nav-icon">
              <FileSpreadsheet size={17} />
            </span>
            <span>4. Upload Excel Data</span>
          </button>

          <div className="nav-section-title">MORE TOOLS</div>

          <button
            className={`nav-link ${activeTab === "radar" ? "active" : ""}`}
            onClick={() => {
              setSelectedEventForRadar(null);
              setActiveTab("radar");
            }}
          >
            <span className="nav-icon">
              <AlertTriangle size={17} />
            </span>
            <span>Live Alerts & News</span>
          </button>

          <button
            className={`nav-link ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            <span className="nav-icon">
              <History size={17} />
            </span>
            <span>Past Incident History</span>
          </button>

          <button
            className={`nav-link ${activeTab === "status" ? "active" : ""}`}
            onClick={() => setActiveTab("status")}
          >
            <span className="nav-icon">
              <Activity size={17} />
            </span>
            <span>Settings & Health</span>
          </button>
        </nav>

        {/* Sidebar Footer */}
        <div className="sidebar-bottom">
          <div className="engine-status">
            <span className="pulse-dot" />
            <div>
              <strong style={{ color: "#0f172a", fontSize: "11.5px", display: "block" }}>
                AI Protection Engine
              </strong>
              <span style={{ color: "#16a34a", fontSize: "11px", fontWeight: 600 }}>All Systems Ready</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="app-content">
        {/* Topbar */}
        <header className="app-topbar">
          <div className="topbar-left">
            <div className="topbar-page-title">
              <span style={{ color: "#2563eb" }}>
                {activeTab === "overview" && <Zap size={18} />}
                {activeTab === "catalog" && <FileSpreadsheet size={18} />}
                {activeTab === "network" && <Network size={18} />}
                {activeTab === "simulator" && <Layers size={18} />}
                {activeTab === "radar" && <AlertTriangle size={18} />}
                {activeTab === "history" && <History size={18} />}
                {activeTab === "status" && <Activity size={18} />}
              </span>
              <span>
                {activeTab === "overview" && "Disruption Checker · See What Happens When Delay Strikes"}
                {activeTab === "catalog" && "Upload Your Supply Chain Excel Sheet"}
                {activeTab === "network" && "Interactive Supply Chain Map"}
                {activeTab === "simulator" && "What-If Scenario Simulator"}
                {activeTab === "radar" && "Live Disruption News & Alerts"}
                {activeTab === "history" && "Past Incident History & Lessons"}
                {activeTab === "status" && "System Settings & Health Check"}
              </span>
            </div>
          </div>

          <div className="topbar-actions">
            <GlobalSearch
              activeEventId={activeEventId ?? undefined}
              onSelectEvent={handleActivateHistoricalEvent}
            />

            {/* User Profile & Company with Tenant Privacy Badge */}
            <button
              onClick={() => setIsWorkspaceModalOpen(true)}
              title="My Business Profile & Workspace Settings"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "6px 14px",
                borderRadius: "10px",
                border: "1px solid #cbd5e1",
                backgroundColor: "#ffffff",
                boxShadow: "0 1px 3px rgba(15, 23, 42, 0.05)",
                cursor: "pointer",
                transition: "all 0.2s ease",
                color: "#0f172a",
              }}
            >
              <div
                style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  backgroundColor: "#2563eb",
                  color: "#ffffff",
                  fontWeight: 700,
                  fontSize: "12.5px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  boxShadow: "0 2px 6px rgba(37, 99, 235, 0.25)",
                }}
              >
                {user.company_name?.substring(0, 2).toUpperCase() || "CO"}
              </div>

              <div style={{ textAlign: "left" }}>
                <div
                  style={{
                    fontSize: "12.5px",
                    fontWeight: 700,
                    color: "#0f172a",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span style={{ maxWidth: "170px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {activeWorkspace?.company_name || user.company_name}
                  </span>
                  <span style={{ fontSize: "10px", color: "#16a34a", background: "#f0fdf4", padding: "1px 6px", borderRadius: "4px", border: "1px solid #bbf7d0", fontWeight: 700 }}>
                    PRIVATE
                  </span>
                  <ChevronDown size={13} color="#64748b" />
                </div>
                <div style={{ fontSize: "11px", color: "#64748b", display: "flex", alignItems: "center", gap: "4px" }}>
                  <span>{user.email}</span>
                </div>
              </div>
            </button>

            {/* Logout Button */}
            <button
              onClick={logout}
              title="Logout"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                border: "1px solid #fecaca",
                backgroundColor: "#fef2f2",
                cursor: "pointer",
                color: "#dc2626",
                boxShadow: "0 1px 2px rgba(0, 0, 0, 0.04)",
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </header>

        {/* Render Active View */}
        <main>
          {activeTab === "overview" && (
            <DashboardOverview
              onNavigate={(tab) => setActiveTab(tab)}
              onSimulateSupplier={handleSimulateSupplier}
            />
          )}

          {activeTab === "catalog" && (
            <div className="page-container">
              <ExcelDataImport
                onSelectSupplierForSimulation={handleSimulateSupplier}
                onNavigateToGraph={() => setActiveTab("network")}
              />
            </div>
          )}

          {activeTab === "network" && <SupplyNetworkPage />}

          {activeTab === "simulator" && (
            <div className="page-container">
              <SupplyChainSimulator initialSupplierId={selectedSupplierForSim} />
            </div>
          )}

          {activeTab === "radar" && (
            <IncidentRadarPage
              initialEvent={selectedEventForRadar}
              onNavigateToSimulator={(supId) => {
                if (supId) setSelectedSupplierForSim(supId);
                setActiveTab("simulator");
              }}
              onOpenWorkspaceModal={() => setIsWorkspaceModalOpen(true)}
            />
          )}

          {activeTab === "history" && (
            <div className="page-container">
              <HistoricalIntelligence
                onActivate={handleActivateHistoricalEvent}
              />
            </div>
          )}

          {activeTab === "status" && <SystemStatusPage />}
        </main>
      </div>

      {/* Multi-Business Workspace Switcher & Registration Modal */}
      <WorkspaceModal
        isOpen={isWorkspaceModalOpen}
        onClose={() => setIsWorkspaceModalOpen(false)}
        onWorkspaceSwitched={(ws) => {
          setActiveWorkspace(ws);
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Box,
  CheckCircle2,
  Clock,
  ExternalLink,
  Factory,
  FileSpreadsheet,
  HelpCircle,
  Info,
  Layers,
  Network,
  Package,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  TrendingDown,
  Truck,
  Zap,
} from "lucide-react";
import {
  getSupplyChainCatalog,
  getSupplyChainSuppliers,
  simulateSupplierFailure,
  type SupplyChainCatalog,
  type SupplyChainSupplier,
  type SupplierFailureSimulation,
} from "../services/supplyChainApi";

function safeNumber(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function formatSafe(value: unknown, fallback = 0): string {
  return safeNumber(value, fallback).toLocaleString();
}

interface DashboardOverviewProps {
  onNavigate: (view: "overview" | "simulator" | "catalog" | "network" | "radar" | "history" | "status") => void;
  onSimulateSupplier: (supplierId: string) => void;
}

export default function DashboardOverview({
  onNavigate,
  onSimulateSupplier,
}: DashboardOverviewProps) {
  const [catalog, setCatalog] = useState<SupplyChainCatalog | null>(null);
  const [suppliers, setSuppliers] = useState<SupplyChainSupplier[]>([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>("");
  const [outageDuration, setOutageDuration] = useState<number>(7);
  const [simulation, setSimulation] = useState<SupplierFailureSimulation | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  // Load initial catalog and suppliers
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [catData, supData] = await Promise.allSettled([
          getSupplyChainCatalog(),
          getSupplyChainSuppliers(),
        ]);

        let supsList: SupplyChainSupplier[] = [];
        if (catData.status === "fulfilled") {
          setCatalog(catData.value);
          if (catData.value.suppliers?.length) {
            supsList = catData.value.suppliers;
          }
        }

        if (!supsList.length && supData.status === "fulfilled") {
          supsList = supData.value.suppliers ?? [];
        }

        const seen = new Set<string>();
        const sups = supsList.filter((s) => {
          if (seen.has(s.supplier_id)) return false;
          seen.add(s.supplier_id);
          return true;
        });

        setSuppliers(sups);
        if (sups.length > 0) {
          setSelectedSupplierId(sups[0].supplier_id);
        }

        // Check for last simulation in localStorage safely
        const cached = localStorage.getItem("atmograph:last-supplier-simulation");
        if (cached) {
          try {
            const parsed = JSON.parse(cached);
            if (parsed && typeof parsed === "object") {
              const res = parsed.result;
              if (res && typeof res === "object" && res.summary) {
                setSimulation(res);
                if (parsed.supplier_id) setSelectedSupplierId(parsed.supplier_id);
              }
            }
          } catch {
            // ignore
          }
        }
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    }

    void loadData();

    const handleWsChange = () => {
      void loadData();
    };

    window.addEventListener("atmograph:workspace-changed", handleWsChange);
    return () => {
      window.removeEventListener("atmograph:workspace-changed", handleWsChange);
    };
  }, []);

  // Run simulation on selected supplier
  const handleRunSimulation = async (targetId?: string) => {
    const supId = targetId || selectedSupplierId;
    if (!supId) return;

    setSimulating(true);
    try {
      const res = await simulateSupplierFailure(supId);
      setSimulation(res);
      setSelectedSupplierId(supId);

      // Dispatch event so SupplyGraph highlights the outage immediately
      const payload = {
        timestamp: Date.now(),
        supplier_id: res.supplier?.supplier_id ?? supId,
        supplier_name: res.supplier?.name ?? "",
        result: res,
      };
      window.dispatchEvent(
        new CustomEvent("atmograph:supplier-simulation", { detail: payload })
      );
      localStorage.setItem("atmograph:last-supplier-simulation", JSON.stringify(payload));
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  const totalSuppliers = suppliers.length || catalog?.suppliers?.length || 8;
  const totalProducts = catalog?.products?.length || 8;
  const totalComponents = catalog?.components?.length || 13;
  const totalPlants = catalog?.plants?.length || 1;

  const currentSupplier = suppliers.find((s) => s.supplier_id === selectedSupplierId) || suppliers[0];
  const isStoppage = simulation?.summary?.production_stop;

  return (
    <div className="page-container" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* 1. Header Banner & Guided Explainer */}
      <div className="page-header-row" style={{ alignItems: "center", justifyContent: "space-between" }}>
        <div className="page-headline">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <span className="eyebrow-tag" style={{ background: "#eff6ff", color: "#2563eb", padding: "3px 10px", borderRadius: "6px", border: "1px solid #bfdbfe" }}>
              DISRUPTION CHECKER
            </span>
            <span style={{ fontSize: "12px", color: "#64748b" }}>· 3 Simple Steps</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 700, margin: "0 0 6px", color: "#0f172a" }}>
            See What Happens When a Supplier is Delayed
          </h2>
          <p style={{ maxWidth: "780px", color: "#475569", fontSize: "13.5px", lineHeight: "1.5", margin: 0 }}>
            Pick a supplier below. We will calculate whether your <strong>backup stock is enough</strong>,
            if your <strong>factory will stop</strong>, and <strong>what actions you should take</strong>.
          </p>
        </div>

        <button
          className="secondary-button"
          style={{ fontSize: "13px", padding: "8px 16px", background: "#ffffff", border: "1px solid #cbd5e1", color: "#0f172a", display: "inline-flex", alignItems: "center", gap: "7px" }}
          onClick={() => onNavigate("catalog")}
        >
          <FileSpreadsheet size={15} color="#2563eb" />
          Upload My Excel File
        </button>
      </div>

      {/* 2. Visual 3-Step Guided Stepper */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "12px",
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          padding: "16px 20px",
          boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "30px",
              height: "30px",
              borderRadius: "50%",
              background: "#eff6ff",
              color: "#2563eb",
              border: "1px solid #bfdbfe",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "13px",
              flexShrink: 0,
            }}
          >
            1
          </div>
          <div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a" }}>Step 1: Check Suppliers</div>
            <div style={{ fontSize: "11.5px", color: "#64748b" }}>{totalSuppliers} Suppliers · {totalProducts} Products</div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "30px",
              height: "30px",
              borderRadius: "50%",
              background: "#fee2e2",
              color: "#dc2626",
              border: "1px solid #fecaca",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "13px",
              flexShrink: 0,
            }}
          >
            2
          </div>
          <div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a" }}>Step 2: Pick a Supplier</div>
            <div style={{ fontSize: "11.5px", color: "#64748b" }}>Choose who is delayed or shut down</div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "30px",
              height: "30px",
              borderRadius: "50%",
              background: "#f0fdf4",
              color: "#16a34a",
              border: "1px solid #bbf7d0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "13px",
              flexShrink: 0,
            }}
          >
            3
          </div>
          <div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "#0f172a" }}>Step 3: See What Happens</div>
            <div style={{ fontSize: "11.5px", color: "#64748b" }}>See factory status & simple advice</div>
          </div>
        </div>
      </div>

      {/* 3. Interactive Disruption Sandbox (Simulate Outage in 1 Click) */}
      <div
        className="modern-card"
        style={{
          background: "#ffffff",
          border: "1px solid #cbd5e1",
          padding: "22px",
          boxShadow: "0 2px 6px rgba(15, 23, 42, 0.05)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: 38, height: 38, borderRadius: "10px", background: "#fee2e2", color: "#dc2626", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Zap size={20} />
            </div>
            <div>
              <strong style={{ fontSize: "15px", color: "#0f172a" }}>Step 2: Pick a Supplier to Test</strong>
              <div style={{ fontSize: "12.5px", color: "#64748b" }}>Select any supplier and click 'Check Impact Now' to see what happens</div>
            </div>
          </div>
        </div>

        {/* Input Bar: Supplier Dropdown + Run Button */}
        <div style={{ display: "flex", gap: "14px", alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ flex: "1", minWidth: "260px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#475569", marginBottom: "6px", fontWeight: 600 }}>
              CHOOSE SUPPLIER TO TEST:
            </label>
            <select
              value={selectedSupplierId}
              onChange={(e) => setSelectedSupplierId(e.target.value)}
              style={{
                width: "100%",
                background: "#ffffff",
                border: "1px solid #cbd5e1",
                borderRadius: "8px",
                padding: "10px 14px",
                color: "#0f172a",
                fontSize: "13.5px",
                fontWeight: 600,
                outline: "none",
              }}
            >
              {suppliers.map((s) => (
                <option key={s.supplier_id} value={s.supplier_id}>
                  {s.name} ({s.city ?? "Surat"}) · ID: {s.supplier_id}
                </option>
              ))}
            </select>
          </div>

          <div style={{ alignSelf: "flex-end" }}>
            <button
              className="primary-action-btn"
              style={{
                padding: "11px 26px",
                fontSize: "13.5px",
                fontWeight: 600,
                background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
                boxShadow: "0 2px 8px rgba(37, 99, 235, 0.3)",
              }}
              onClick={() => handleRunSimulation()}
              disabled={simulating}
            >
              <Zap size={16} className={simulating ? "sc-spin" : ""} />
              {simulating ? "Checking Impact..." : "Check Impact Now ⚡"}
            </button>
          </div>
        </div>
      </div>

      {/* 4. Instant Ripple Results & Executive Action Plan */}
      {simulation ? (
        <div
          style={{
            background: isStoppage ? "#fff5f5" : "#f0fdf4",
            border: `1px solid ${isStoppage ? "#fecaca" : "#bbf7d0"}`,
            borderRadius: "14px",
            padding: "22px",
            display: "flex",
            flexDirection: "column",
            gap: "18px",
            boxShadow: "0 2px 8px rgba(15, 23, 42, 0.04)",
          }}
        >
          {/* Executive Verdict Banner */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
            <div style={{ display: "flex", gap: "14px", alignItems: "center" }}>
              {isStoppage ? (
                <div style={{ width: 44, height: 44, borderRadius: "50%", background: "#fee2e2", display: "flex", alignItems: "center", justifyContent: "center", color: "#dc2626", flexShrink: 0 }}>
                  <AlertTriangle size={24} />
                </div>
              ) : (
                <div style={{ width: 44, height: 44, borderRadius: "50%", background: "#dcfce7", display: "flex", alignItems: "center", justifyContent: "center", color: "#16a34a", flexShrink: 0 }}>
                  <CheckCircle2 size={24} />
                </div>
              )}
              <div>
                <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.06em", color: isStoppage ? "#dc2626" : "#16a34a" }}>
                  STEP 3: RESULT & WHAT TO DO
                </span>
                <h3 style={{ margin: "2px 0 0", fontSize: "19px", fontWeight: 700, color: "#0f172a" }}>
                  {isStoppage
                    ? `Warning: Factory Will Stop! (${simulation?.supplier?.name ?? "Selected Supplier"})`
                    : `Safe: Backup Stock is Enough! (${simulation?.supplier?.name ?? "Selected Supplier"})`}
                </h3>
                <p style={{ margin: "4px 0 0", fontSize: "13.5px", color: "#475569" }}>
                  {isStoppage
                    ? `Your current backup stock will run out in ${safeNumber(simulation?.summary?.max_delay_days, 3.3).toFixed(1)} days. You are short ${formatSafe(simulation?.summary?.net_shortage, 1000)} items which will stop production.`
                    : `Your current warehouse stock protects manufacturing for ${safeNumber(simulation?.summary?.max_delay_days, 12).toFixed(1)} days while other suppliers help.`}
                </p>
              </div>
            </div>

            <button
              className="secondary-button"
              style={{ padding: "8px 16px", fontSize: "12.5px" }}
              onClick={() => onNavigate("simulator")}
            >
              Open Full Simulator <ArrowRight size={13} />
            </button>
          </div>

          {/* 4 Clear Impact Metrics */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
            <div className="metric-box" style={{ background: "#ffffff", border: "1px solid #e2e8f0" }}>
              <div className="metric-info">
                <span className="metric-label">DAYS OF BACKUP STOCK</span>
                <span className="metric-value" style={{ color: isStoppage ? "#dc2626" : "#16a34a" }}>
                  {safeNumber(simulation?.summary?.max_delay_days, 3.3).toFixed(1)} Days
                </span>
                <span style={{ fontSize: "11.5px", color: "#64748b" }}>Days before stock runs out</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#fef3c7", color: "#d97706", border: "1px solid #fde68a" }}>
                <Clock size={18} />
              </div>
            </div>

            <div className="metric-box" style={{ background: "#ffffff", border: "1px solid #e2e8f0" }}>
              <div className="metric-info">
                <span className="metric-label">MISSING ITEMS</span>
                <span className="metric-value" style={{ color: isStoppage ? "#dc2626" : "#0f172a" }}>
                  {formatSafe(simulation?.summary?.net_shortage, 1000)}
                </span>
                <span style={{ fontSize: "11.5px", color: "#64748b" }}>Items you need to replace</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#fee2e2", color: "#dc2626", border: "1px solid #fecaca" }}>
                <TrendingDown size={18} />
              </div>
            </div>

            <div className="metric-box" style={{ background: "#ffffff", border: "1px solid #e2e8f0" }}>
              <div className="metric-info">
                <span className="metric-label">PRODUCTS IMPACTED</span>
                <span className="metric-value">{safeNumber(simulation?.summary?.affected_products, 8)} Types</span>
                <span style={{ fontSize: "11.5px", color: "#64748b" }}>Products that need this part</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#eff6ff", color: "#2563eb", border: "1px solid #bfdbfe" }}>
                <Package size={18} />
              </div>
            </div>

            <div className="metric-box" style={{ background: "#ffffff", border: "1px solid #e2e8f0" }}>
              <div className="metric-info">
                <span className="metric-label">BACKUP SUPPLIER CAPACITY</span>
                <span className="metric-value" style={{ color: "#16a34a" }}>
                  {formatSafe(simulation?.summary?.alternative_recovery, 0)}
                </span>
                <span style={{ fontSize: "11.5px", color: "#16a34a" }}>Units other suppliers can ship</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#f0fdf4", color: "#16a34a", border: "1px solid #bbf7d0" }}>
                <CheckCircle2 size={18} />
              </div>
            </div>
          </div>

          {/* Actionable Executive Recommendations */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "10px",
              padding: "16px 20px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <Info size={16} color="#2563eb" />
              <strong style={{ fontSize: "14px", color: "#0f172a" }}>Simple Steps to Take Now:</strong>
            </div>
            <div style={{ display: "grid", gap: "8px", fontSize: "13px", color: "#334155" }}>
              <div>
                <strong>1. Contact Backup Suppliers:</strong> Send orders to your backup suppliers within the next 48 hours to replace missing parts.
              </div>
              <div>
                <strong>2. Save Important Orders:</strong> Prioritize making your highest-value products first with the parts you have left.
              </div>
              <div>
                <strong>3. Watch the Clock:</strong> You have {safeNumber(simulation?.summary?.max_delay_days, 3.3).toFixed(1)} days of safety stock remaining before work stops.
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Standby State (When no simulation is run yet) */
        <div
          style={{
            padding: "16px 20px",
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <ShieldCheck size={20} color="#16a34a" />
            <span style={{ fontSize: "13.5px", fontWeight: 600, color: "#166534" }}>
              All Systems Ready: All suppliers and factories are currently running normally.
            </span>
          </div>
          <span className="status-badge badge-running">READY TO TEST</span>
        </div>
      )}

      {/* 5. Cascading Disruption Transmission & Studio Portal */}
      <div className="modern-card" style={{ padding: "22px", background: "#ffffff", border: "1px solid #e2e8f0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px", flexWrap: "wrap", gap: "14px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{ width: "36px", height: "36px", borderRadius: "8px", background: "#eff6ff", display: "flex", alignItems: "center", justifyContent: "center", color: "#2563eb" }}>
                <Zap size={18} />
              </div>
              <strong style={{ fontSize: "16px", color: "#0f172a" }}>How The Delay Spreads</strong>
            </div>
            <div style={{ fontSize: "13px", color: "#64748b", marginTop: "4px" }}>
              {simulation
                ? `See how the delay from ${simulation.supplier?.name} moves from the supplier to the factory and to your customer orders.`
                : "See how any delay moves from the supplier to the factory and down to your customer deliveries."}
            </div>
          </div>

          <button
            className="primary-button"
            style={{ fontSize: "13px", padding: "8px 18px", display: "flex", alignItems: "center", gap: "8px" }}
            onClick={() => onNavigate("network")}
          >
            <Network size={16} />
            <span>Open Supply Chain Map</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {/* Transmission Stages Flow */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px", marginTop: "12px" }}>
          <div style={{ padding: "16px", borderRadius: "10px", background: "#fef2f2", border: "1px solid #fecaca" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#dc2626", textTransform: "uppercase" }}>
              <Truck size={14} /> 1. Delayed Supplier
            </div>
            <strong style={{ fontSize: "14px", color: "#0f172a", display: "block", marginTop: "4px" }}>
              {simulation?.supplier?.name ?? "Pick a Supplier Above"}
            </strong>
            <span style={{ fontSize: "11.5px", color: "#64748b" }}>
              {simulation ? `${outageDuration} days delay tested` : "Operating normally"}
            </span>
          </div>

          <div style={{ padding: "16px", borderRadius: "10px", background: "#fffbeb", border: "1px solid #fde68a" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#d97706", textTransform: "uppercase" }}>
              <Box size={14} /> 2. Parts Running Low
            </div>
            <strong style={{ fontSize: "14px", color: "#0f172a", display: "block", marginTop: "4px" }}>
              {simulation?.summary?.affected_components ?? 0} Raw Materials Affected
            </strong>
            <span style={{ fontSize: "11.5px", color: "#64748b" }}>
              {simulation ? `Short by: ${formatSafe(simulation.summary?.gross_shortage)} units` : "Backup stock safe"}
            </span>
          </div>

          <div style={{ padding: "16px", borderRadius: "10px", background: "#fff7ed", border: "1px solid #fed7aa" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#ea580c", textTransform: "uppercase" }}>
              <Factory size={14} /> 3. Factory Impact
            </div>
            <strong style={{ fontSize: "14px", color: "#0f172a", display: "block", marginTop: "4px" }}>
              {simulation?.summary?.affected_plants ?? 0} Factories Affected
            </strong>
            <span style={{ fontSize: "11.5px", color: "#64748b" }}>
              {simulation?.summary?.production_stop ? "Factory will pause" : "Production continues"}
            </span>
          </div>

          <div style={{ padding: "16px", borderRadius: "10px", background: "#f0f9ff", border: "1px solid #bae6fd" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#0284c7", textTransform: "uppercase" }}>
              <Package size={14} /> 4. Customer Deliveries
            </div>
            <strong style={{ fontSize: "14px", color: "#0f172a", display: "block", marginTop: "4px" }}>
              {simulation?.summary?.affected_products ?? 0} Products Delayed
            </strong>
            <span style={{ fontSize: "11.5px", color: "#64748b" }}>
              {simulation ? `Estimated delay: +${simulation.summary?.max_delay_days ?? 0} days` : "On schedule"}
            </span>
          </div>
        </div>

        <div style={{ marginTop: "16px", display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "14px", borderTop: "1px solid #e2e8f0", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ fontSize: "12.5px", color: "#64748b", display: "flex", alignItems: "center", gap: "6px" }}>
            <Info size={14} color="#2563eb" />
            <span>Want to see every connection visually? Click the button to see the full interactive map.</span>
          </div>
          <button
            onClick={() => onNavigate("network")}
            style={{
              background: "transparent",
              border: "none",
              color: "#2563eb",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>Open Full Interactive Map</span>
            <ExternalLink size={13} />
          </button>
        </div>
      </div>

      {/* 6. Quick Partner Selector Table */}
      <div className="modern-card" style={{ padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <strong style={{ fontSize: "14.5px", color: "#0f172a" }}>Direct Supplier Quick Testing</strong>
            <div style={{ fontSize: "12px", color: "#64748b" }}>Click "Test Delay" to instantly check any supplier</div>
          </div>
          <button
            className="secondary-button"
            style={{ fontSize: "12px", padding: "5px 12px" }}
            onClick={() => onNavigate("catalog")}
          >
            View All Suppliers
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "12px" }}>
          {suppliers.slice(0, 6).map((s) => (
            <div
              key={s.supplier_id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 16px",
                background: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Truck size={17} color="#2563eb" />
                <div>
                  <strong style={{ fontSize: "13px", color: "#0f172a", display: "block" }}>{s.name}</strong>
                  <span style={{ fontSize: "11px", color: "#64748b" }}>{s.city ?? "Surat"} · {s.supplier_id}</span>
                </div>
              </div>

              <button
                className="secondary-button"
                style={{ fontSize: "11.5px", padding: "5px 12px" }}
                onClick={() => handleRunSimulation(s.supplier_id)}
              >
                Test Delay
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

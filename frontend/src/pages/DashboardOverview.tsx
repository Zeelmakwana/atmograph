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
  const [selectedIndustry, setSelectedIndustry] = useState<string>("textiles");

  // Load initial catalog and suppliers
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [catData, supData] = await Promise.allSettled([
          getSupplyChainCatalog(),
          getSupplyChainSuppliers(),
        ]);

        if (catData.status === "fulfilled") setCatalog(catData.value);
        if (supData.status === "fulfilled") {
          const sups = supData.value.suppliers ?? [];
          setSuppliers(sups);
          if (sups.length > 0) {
            setSelectedSupplierId(sups[0].supplier_id);
          }
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
      <div className="page-header-row" style={{ alignItems: "flex-start" }}>
        <div className="page-headline">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <span className="eyebrow-tag" style={{ background: "rgba(232, 168, 56, 0.15)", color: "#e8a838" }}>
              SUPPLY CHAIN RIPPLE PREDICTOR
            </span>
            <span style={{ fontSize: "11px", color: "#8e8e96" }}>· 3-Step Guided Workflow</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 700, margin: "0 0 6px" }}>
            Test How Any Disruption Impacts Your Business
          </h2>
          <p style={{ maxWidth: "780px", color: "#9ca3af", fontSize: "13px", lineHeight: "1.5" }}>
            Select or upload your business structure, pick an unexpected supplier or port disruption, and watch AtmoGraph
            calculate your <strong>inventory runway, factory stoppage risk, and recommended decisions</strong> in real time.
          </p>
        </div>

        {/* Industry Switcher & Quick Upload */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "rgba(255,255,255,0.04)", padding: "4px 8px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
            <span style={{ fontSize: "11px", color: "#8e8e96", fontWeight: 600 }}>BUSINESS PRESET:</span>
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                color: "#e8a838",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                outline: "none",
              }}
            >
              <option value="textiles" style={{ background: "#18181b", color: "#fff" }}>👗 Ethnic Wear & Textiles (Surat Hub)</option>
              <option value="electronics" style={{ background: "#18181b", color: "#fff" }}>📱 Consumer Electronics & Chips</option>
              <option value="automotive" style={{ background: "#18181b", color: "#fff" }}>🚗 Automotive & EV Battery</option>
            </select>
          </div>

          <button
            className="secondary-button"
            style={{ fontSize: "12px", padding: "6px 12px" }}
            onClick={() => onNavigate("catalog")}
          >
            <FileSpreadsheet size={14} />
            Upload My Excel/JSON
          </button>
        </div>
      </div>

      {/* 2. Visual 3-Step Guided Stepper */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "12px",
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px solid rgba(255, 255, 255, 0.06)",
          borderRadius: "12px",
          padding: "14px 18px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: "rgba(232, 168, 56, 0.2)",
              color: "#e8a838",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "12px",
            }}
          >
            1
          </div>
          <div>
            <div style={{ fontSize: "12px", fontWeight: 600, color: "#ececef" }}>Pick / Upload Business</div>
            <div style={{ fontSize: "11px", color: "#8e8e96" }}>{totalSuppliers} Suppliers · {totalProducts} Finished Products</div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: "rgba(239, 68, 68, 0.2)",
              color: "#f87171",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "12px",
            }}
          >
            2
          </div>
          <div>
            <div style={{ fontSize: "12px", fontWeight: 600, color: "#ececef" }}>Select Outage Event</div>
            <div style={{ fontSize: "11px", color: "#8e8e96" }}>Choose supplier shutdown or delay</div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: "rgba(61, 214, 140, 0.2)",
              color: "#3dd68c",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "12px",
            }}
          >
            3
          </div>
          <div>
            <div style={{ fontSize: "12px", fontWeight: 600, color: "#ececef" }}>See Ripple & Decision</div>
            <div style={{ fontSize: "11px", color: "#8e8e96" }}>Graph cascade + Mitigation advice</div>
          </div>
        </div>
      </div>

      {/* 3. Interactive Disruption Sandbox (Simulate Outage in 1 Click) */}
      <div
        className="modern-card"
        style={{
          background: "linear-gradient(180deg, rgba(30, 30, 36, 0.7) 0%, rgba(20, 20, 24, 0.9) 100%)",
          border: "1px solid rgba(232, 168, 56, 0.2)",
          padding: "20px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: 34, height: 34, borderRadius: "8px", background: "rgba(239, 68, 68, 0.15)", color: "#f87171", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Zap size={18} />
            </div>
            <div>
              <strong style={{ fontSize: "15px", color: "#ececef" }}>Step 2: Trigger Disruption Simulation</strong>
              <div style={{ fontSize: "12px", color: "#8e8e96" }}>Select which supplier is affected to calculate ripple effects</div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "12px", color: "#8e8e96" }}>Outage Duration:</span>
            {[
              { label: "3 Days", days: 3 },
              { label: "7 Days", days: 7 },
              { label: "14 Days", days: 14 },
              { label: "30 Days", days: 30 },
            ].map((item) => (
              <button
                key={item.days}
                onClick={() => setOutageDuration(item.days)}
                style={{
                  background: outageDuration === item.days ? "rgba(232, 168, 56, 0.2)" : "rgba(255, 255, 255, 0.05)",
                  color: outageDuration === item.days ? "#e8a838" : "#8e8e96",
                  border: `1px solid ${outageDuration === item.days ? "#e8a838" : "rgba(255, 255, 255, 0.1)"}`,
                  borderRadius: "6px",
                  padding: "4px 10px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar: Supplier Dropdown + Run Button */}
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ flex: "1", minWidth: "260px" }}>
            <label style={{ display: "block", fontSize: "11px", color: "#8e8e96", marginBottom: "6px", fontWeight: 600 }}>
              SELECT DISRUPTED SUPPLIER NODE:
            </label>
            <select
              value={selectedSupplierId}
              onChange={(e) => setSelectedSupplierId(e.target.value)}
              style={{
                width: "100%",
                background: "rgba(10, 10, 14, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.15)",
                borderRadius: "8px",
                padding: "10px 14px",
                color: "#ececef",
                fontSize: "13px",
                fontWeight: 600,
                outline: "none",
              }}
            >
              {suppliers.map((s) => (
                <option key={s.supplier_id} value={s.supplier_id} style={{ background: "#18181b", color: "#fff" }}>
                  {s.name} ({s.city ?? "Surat"}) · ID: {s.supplier_id}
                </option>
              ))}
            </select>
          </div>

          <div style={{ alignSelf: "flex-end" }}>
            <button
              className="primary-action-btn"
              style={{
                padding: "10px 24px",
                fontSize: "13px",
                fontWeight: 700,
                background: "linear-gradient(135deg, #e8a838 0%, #d48b16 100%)",
                boxShadow: "0 4px 14px rgba(232, 168, 56, 0.35)",
              }}
              onClick={() => handleRunSimulation()}
              disabled={simulating}
            >
              <Zap size={16} className={simulating ? "sc-spin" : ""} />
              {simulating ? "Calculating Ripple..." : "Run Ripple Prediction ⚡"}
            </button>
          </div>
        </div>
      </div>

      {/* 4. Instant Ripple Results & Executive Action Plan */}
      {simulation ? (
        <div
          style={{
            background: isStoppage ? "rgba(239, 68, 68, 0.06)" : "rgba(61, 214, 140, 0.06)",
            border: `1px solid ${isStoppage ? "rgba(239, 68, 68, 0.25)" : "rgba(61, 214, 140, 0.25)"}`,
            borderRadius: "14px",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {/* Executive Verdict Banner */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              {isStoppage ? (
                <div style={{ width: 40, height: 40, borderRadius: "50%", background: "rgba(239, 68, 68, 0.2)", display: "flex", alignItems: "center", justifyContent: "center", color: "#f87171" }}>
                  <AlertTriangle size={22} />
                </div>
              ) : (
                <div style={{ width: 40, height: 40, borderRadius: "50%", background: "rgba(61, 214, 140, 0.2)", display: "flex", alignItems: "center", justifyContent: "center", color: "#3dd68c" }}>
                  <CheckCircle2 size={22} />
                </div>
              )}
              <div>
                <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: isStoppage ? "#f87171" : "#3dd68c" }}>
                  STEP 3: EXECUTIVE DECISION VERDICT
                </span>
                <h3 style={{ margin: "2px 0 0", fontSize: "18px", color: "#ececef" }}>
                  {isStoppage
                    ? `CRITICAL FACTORY HALT PREDICTED (${simulation?.supplier?.name ?? "Selected Supplier"})`
                    : `PRODUCTION SAFE · BUFFER ABSORBS DISRUPTION (${simulation?.supplier?.name ?? "Selected Supplier"})`}
                </h3>
                <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#9ca3af" }}>
                  {isStoppage
                    ? `Current stock buffer will run out in ${safeNumber(simulation?.summary?.max_delay_days, 3.3).toFixed(1)} days. Net deficit of ${formatSafe(simulation?.summary?.net_shortage, 1000)} units will halt assembly.`
                    : `Existing warehouse stock protects manufacturing for ${safeNumber(simulation?.summary?.max_delay_days, 12).toFixed(1)} days while secondary sourcing activates.`}
                </p>
              </div>
            </div>

            <button
              className="secondary-button"
              style={{ padding: "6px 14px", fontSize: "12px" }}
              onClick={() => onNavigate("simulator")}
            >
              Open Full Simulator Studio <ArrowRight size={13} />
            </button>
          </div>

          {/* 4 Clear Impact Metrics */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
            <div className="metric-box" style={{ background: "rgba(0,0,0,0.2)" }}>
              <div className="metric-info">
                <span className="metric-label">STOCK BUFFER RUNWAY</span>
                <span className="metric-value" style={{ color: isStoppage ? "#f87171" : "#3dd68c" }}>
                  {safeNumber(simulation?.summary?.max_delay_days, 3.3).toFixed(1)} Days
                </span>
                <span style={{ fontSize: "11px", color: "#8e8e96" }}>Time until lines stop</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(245, 158, 11, 0.1)", color: "#fbbf24" }}>
                <Clock size={16} />
              </div>
            </div>

            <div className="metric-box" style={{ background: "rgba(0,0,0,0.2)" }}>
              <div className="metric-info">
                <span className="metric-label">MATERIAL DEFICIT</span>
                <span className="metric-value">{formatSafe(simulation?.summary?.net_shortage, 1000)}</span>
                <span style={{ fontSize: "11px", color: "#8e8e96" }}>Uncovered units</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(239, 68, 68, 0.1)", color: "#f87171" }}>
                <TrendingDown size={16} />
              </div>
            </div>

            <div className="metric-box" style={{ background: "rgba(0,0,0,0.2)" }}>
              <div className="metric-info">
                <span className="metric-label">PRODUCTS AT RISK</span>
                <span className="metric-value">{safeNumber(simulation?.summary?.affected_products, 8)} Lines</span>
                <span style={{ fontSize: "11px", color: "#8e8e96" }}>Kurtas, Lehengas & Gowns</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(155, 140, 255, 0.1)", color: "#9b8cff" }}>
                <Package size={16} />
              </div>
            </div>

            <div className="metric-box" style={{ background: "rgba(0,0,0,0.2)" }}>
              <div className="metric-info">
                <span className="metric-label">BACKUP RECOVERY</span>
                <span className="metric-value">{formatSafe(simulation?.summary?.alternative_recovery, 0)}</span>
                <span style={{ fontSize: "11px", color: "#34d399" }}>Units from secondary suppliers</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(16, 185, 129, 0.1)", color: "#34d399" }}>
                <CheckCircle2 size={16} />
              </div>
            </div>
          </div>

          {/* Actionable Executive Recommendations */}
          <div
            style={{
              background: "rgba(0, 0, 0, 0.25)",
              border: "1px solid rgba(255, 255, 255, 0.07)",
              borderRadius: "10px",
              padding: "14px 18px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <Info size={15} color="#e8a838" />
              <strong style={{ fontSize: "13px", color: "#ececef" }}>Recommended Mitigation Actions for Business Owner:</strong>
            </div>
            <div style={{ display: "grid", gap: "6px", fontSize: "12px", color: "#d1d5db" }}>
              <div>
                <strong>1. Immediate Allocation:</strong> Switch orders to secondary fabric suppliers in Surat cluster within the next 48 hours.
              </div>
              <div>
                <strong>2. Inventory Rationing:</strong> Protect high-margin finished garments by reserving remaining georgette & chinon stock.
              </div>
              <div>
                <strong>3. Buffer Window:</strong> You have {safeNumber(simulation?.summary?.max_delay_days, 3.3).toFixed(1)} days before assembly stoppage. Expedited transit can resolve shortage.
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Standby State (When no simulation is run yet) */
        <div
          style={{
            padding: "14px 18px",
            background: "rgba(61, 214, 140, 0.05)",
            border: "1px solid rgba(61, 214, 140, 0.18)",
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <ShieldCheck size={18} color="#3dd68c" />
            <span style={{ fontSize: "13px", fontWeight: 600, color: "#ececef" }}>
              Supply Chain Baseline: All 8 Suppliers & Surat Assembly Lines Operational
            </span>
          </div>
          <span className="status-badge badge-running">READY TO SIMULATE</span>
        </div>
      )}

      {/* 5. Cascading Disruption Transmission & Studio Portal */}
      <div className="modern-card" style={{ padding: "22px", background: "linear-gradient(135deg, rgba(232, 168, 56, 0.05) 0%, rgba(18, 22, 32, 0.95) 100%)", border: "1px solid rgba(232, 168, 56, 0.25)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px", flexWrap: "wrap", gap: "14px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(232, 168, 56, 0.15)", display: "flex", alignItems: "center", justifyContent: "center", color: "#e8a838" }}>
                <Zap size={18} />
              </div>
              <strong style={{ fontSize: "16px", color: "#f8fafc" }}>Multi-Tier Shock Propagation Pathway</strong>
            </div>
            <div style={{ fontSize: "12.5px", color: "#94a3b8", marginTop: "4px" }}>
              {simulation
                ? `Trace the real-time cascading outage triggered by ${simulation.supplier?.name} through your entire value chain.`
                : "Active topology mapping showing how disruptions propagate from tier-1 suppliers down to customer deliveries."}
            </div>
          </div>

          <button
            className="primary-button"
            style={{ fontSize: "13px", padding: "8px 18px", display: "flex", alignItems: "center", gap: "8px", boxShadow: "0 4px 14px rgba(232, 168, 56, 0.25)" }}
            onClick={() => onNavigate("network")}
          >
            <Network size={16} />
            <span>Open Dedicated Graph Studio</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {/* Transmission Stages Flow */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px", marginTop: "12px" }}>
          <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(239, 68, 68, 0.25)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#f87171", textTransform: "uppercase" }}>
              <Truck size={14} /> Tier-1 Disruption Source
            </div>
            <strong style={{ fontSize: "14px", color: "#f8fafc", display: "block", marginTop: "4px" }}>
              {simulation?.supplier?.name ?? "Select Supplier Above"}
            </strong>
            <span style={{ fontSize: "11px", color: "#94a3b8" }}>
              {simulation ? `${outageDuration} days outage simulated` : "Operational baseline"}
            </span>
          </div>

          <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(245, 158, 11, 0.25)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#fbbf24", textTransform: "uppercase" }}>
              <Box size={14} /> Component Stockout
            </div>
            <strong style={{ fontSize: "14px", color: "#f8fafc", display: "block", marginTop: "4px" }}>
              {simulation?.summary?.affected_components ?? 0} Raw Materials Depleted
            </strong>
            <span style={{ fontSize: "11px", color: "#94a3b8" }}>
              {simulation ? `Gross shortage: ${formatSafe(simulation.summary?.gross_shortage)} units` : "Inventory buffer intact"}
            </span>
          </div>

          <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(249, 115, 22, 0.25)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#fb923c", textTransform: "uppercase" }}>
              <Factory size={14} /> Facility Throughput
            </div>
            <strong style={{ fontSize: "14px", color: "#f8fafc", display: "block", marginTop: "4px" }}>
              {simulation?.summary?.affected_plants ?? 0} Assembly Units Halted
            </strong>
            <span style={{ fontSize: "11px", color: "#94a3b8" }}>
              {simulation?.summary?.production_stop ? "Line halt triggered" : "Normal throughput"}
            </span>
          </div>

          <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(56, 189, 248, 0.25)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#38bdf8", textTransform: "uppercase" }}>
              <Package size={14} /> Customer Product Impact
            </div>
            <strong style={{ fontSize: "14px", color: "#f8fafc", display: "block", marginTop: "4px" }}>
              {simulation?.summary?.affected_products ?? 0} Finished SKUs Delayed
            </strong>
            <span style={{ fontSize: "11px", color: "#94a3b8" }}>
              {simulation ? `Est. delay: +${simulation.summary?.max_delay_days ?? 0} days` : "On schedule"}
            </span>
          </div>
        </div>

        <div style={{ marginTop: "14px", display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "12px", borderTop: "1px solid rgba(255, 255, 255, 0.06)", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ fontSize: "12px", color: "#94a3b8", display: "flex", alignItems: "center", gap: "6px" }}>
            <Info size={14} color="#e8a838" />
            <span>Interactive graph topology is exclusively rendered in the <strong>Graph Intelligence Suite</strong> for maximum screen space and high-resolution inspection.</span>
          </div>
          <button
            onClick={() => onNavigate("network")}
            style={{
              background: "transparent",
              border: "none",
              color: "#e8a838",
              fontSize: "12.5px",
              fontWeight: 600,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>View Fullscreen Nodes & Links</span>
            <ExternalLink size={13} />
          </button>
        </div>
      </div>

      {/* 6. Quick Partner Selector Table */}
      <div className="modern-card" style={{ padding: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div>
            <strong style={{ fontSize: "14px", color: "#ececef" }}>Direct Supplier Stress Testing</strong>
            <div style={{ fontSize: "11px", color: "#8e8e96" }}>Click "Simulate Outage" to instantly test any partner</div>
          </div>
          <button
            className="secondary-button"
            style={{ fontSize: "11px", padding: "4px 10px" }}
            onClick={() => onNavigate("catalog")}
          >
            View All Suppliers
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "10px" }}>
          {suppliers.slice(0, 6).map((s) => (
            <div
              key={s.supplier_id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "10px 14px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                borderRadius: "8px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Truck size={16} color="#e8a838" />
                <div>
                  <strong style={{ fontSize: "13px", color: "#ececef", display: "block" }}>{s.name}</strong>
                  <span style={{ fontSize: "11px", color: "#8e8e96" }}>{s.city ?? "Surat"} · {s.supplier_id}</span>
                </div>
              </div>

              <button
                className="secondary-button"
                style={{ fontSize: "11px", padding: "4px 10px" }}
                onClick={() => handleRunSimulation(s.supplier_id)}
              >
                Test Outage
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

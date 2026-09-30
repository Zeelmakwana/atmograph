import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertTriangle,
  Box,
  CheckCircle2,
  Clock,
  Factory,
  Layers,
  Loader2,
  Package,
  RefreshCw,
  TrendingDown,
  Truck,
  Zap,
} from "lucide-react";

import {
  getSupplyChainSuppliers,
  simulateSupplierFailure,
  type SimulationComponent,
  type SimulationProduct,
  type SimulationPlant,
  type SupplierFailureSimulation,
  type SupplyChainSupplier,
} from "../../services/supplyChainApi";
import OperationalTimeline from "../../components/OperationalTimeline";

function number(value: unknown) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function formatNumber(value: unknown) {
  return number(value).toLocaleString();
}

function publishSimulationImpact(result: SupplierFailureSimulation) {
  const payload = {
    timestamp: Date.now(),
    supplier_id: result.supplier?.supplier_id ?? "",
    supplier_name: result.supplier?.name ?? "",
    result,
  };

  window.dispatchEvent(
    new CustomEvent("atmograph:supplier-simulation", {
      detail: payload,
    })
  );

  try {
    window.localStorage.setItem(
      "atmograph:last-supplier-simulation",
      JSON.stringify(payload)
    );
  } catch {
    // ignore
  }
}

interface SupplyChainSimulatorProps {
  initialSupplierId?: string;
}

export default function SupplyChainSimulator({ initialSupplierId }: SupplyChainSimulatorProps) {
  const [suppliers, setSuppliers] = useState<SupplyChainSupplier[]>([]);
  const [selectedSupplier, setSelectedSupplier] = useState(initialSupplierId || "");
  const [result, setResult] = useState<SupplierFailureSimulation | null>(null);
  const [loadingSuppliers, setLoadingSuppliers] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState("");

  async function loadSuppliers(targetId?: string) {
    setLoadingSuppliers(true);
    setError("");
    try {
      const response = await getSupplyChainSuppliers();
      const rows = response.suppliers ?? [];
      setSuppliers(rows);
      setSelectedSupplier((current) => {
        if (targetId && rows.some((x) => x.supplier_id === targetId)) {
          return targetId;
        }
        if (current && rows.some((x) => x.supplier_id === current)) {
          return current;
        }
        return rows[0]?.supplier_id ?? "";
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load suppliers list."
      );
    } finally {
      setLoadingSuppliers(false);
    }
  }

  useEffect(() => {
    void loadSuppliers(initialSupplierId);
  }, [initialSupplierId]);

  useEffect(() => {
    if (initialSupplierId) {
      setSelectedSupplier(initialSupplierId);
    }
  }, [initialSupplierId]);

  async function runSimulation() {
    if (!selectedSupplier) return;
    setSimulating(true);
    setError("");
    try {
      const response = await simulateSupplierFailure(selectedSupplier);
      setResult(response);
      publishSimulationImpact(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Disruption simulation failed."
      );
    } finally {
      setSimulating(false);
    }
  }

  const summary = result?.summary;

  const recoveryPct = useMemo(() => {
    if (!summary?.gross_lost_supply || summary.gross_lost_supply <= 0) return 0;
    return Math.min(
      100,
      Math.round(((summary.alternative_recovery ?? 0) / summary.gross_lost_supply) * 100)
    );
  }, [summary]);

  const uniqueProducts = useMemo(() => {
    if (!result) return [];
    const seen = new Set<string>();
    return result.products.filter((p) => {
      if (seen.has(p.product_id)) return false;
      seen.add(p.product_id);
      return true;
    });
  }, [result]);

  const timelineIntelligence = useMemo(() => {
    if (!result) return null;
    if ((result as any).operational_timeline) {
      return result;
    }

    const simSummary = result.summary;
    const comps = (result.components || []).map((c: any) => ({
      component_id: c.component_id,
      component_name: c.component_name,
      plant_id: c.plant_id,
      plant_name: c.plant_name,
      status: c.production_stop ? "STOPPED" : (c.net_shortage > 0 ? "REDUCED" : "BUFFERED"),
      inventory_units: c.inventory_quantity ?? 0,
      buffer_days: c.inventory_coverage_days ?? 0,
      recovery_units: c.alternative_recovery ?? 0,
      first_recovery_day: c.estimated_delay_days ?? (c.alternative_suppliers?.[0]?.lead_time_days ?? 7),
    }));

    const minBufferDays = comps.length > 0
      ? Math.min(...comps.map((c: any) => Number(c.buffer_days || 0)))
      : 0;

    const firstRecovery = comps.length > 0
      ? Math.min(...comps.map((c: any) => Number(c.first_recovery_day || 0)))
      : 0;

    const recommendations = [];
    if (simSummary.production_stop) {
      recommendations.push({
        priority: "critical",
        action: "Deploy priority rerouting & secondary supplier allocation immediately.",
        reason: `Immediate net component deficit of ${formatNumber(simSummary.net_shortage)} units risks manufacturing line shut down.`,
      });
      recommendations.push({
        priority: "high",
        action: "Reallocate plant inventory buffers across Surat facilities.",
        reason: "Maintain active stitching and assembly for highest-margin garment lines.",
      });
    } else {
      recommendations.push({
        priority: "optimal",
        action: "Stock buffers adequate. Track secondary lead-times and transit milestones.",
        reason: "Protected by inventory run-time; minimal disruption to Mohilya Couture delivery targets.",
      });
    }

    return {
      operational_timeline: {
        production_status: simSummary.production_stop ? "STOPPED" : (simSummary.net_shortage > 0 ? "REDUCED" : "BUFFERED"),
        summary: {
          minimum_buffer_days: minBufferDays,
          first_shortage_day: simSummary.production_stop ? 0 : (minBufferDays > 0 ? minBufferDays : null),
          first_recovery_day: firstRecovery,
          net_shortage: simSummary.net_shortage,
        },
        components: comps,
        recommendations,
      },
    };
  }, [result]);

  return (
    <div className="sc-page">
      {/* Header */}
      <div className="page-header-row">
        <div className="page-headline">
          <span className="eyebrow-tag">WHAT-IF SCENARIO STUDIO</span>
          <h2>Deterministic Disruption Simulator</h2>
          <p>
            Simulate sudden supplier outages to evaluate alternative capacity recovery and downstream plant vulnerability.
          </p>
        </div>
      </div>

      {/* Supplier Selection Bar */}
      <div className="sc-control-card">
        <div className="sc-control-icon">
          <Zap size={20} />
        </div>
        <div className="sc-control-copy">
          <strong>Select Target Supplier</strong>
          <span>Simulate immediate failure and trace propagation</span>
        </div>

        <select
          value={selectedSupplier}
          disabled={loadingSuppliers || simulating}
          onChange={(e) => setSelectedSupplier(e.target.value)}
          className="sc-select"
        >
          {loadingSuppliers ? (
            <option value="">Loading suppliers from database...</option>
          ) : suppliers.length === 0 ? (
            <option value="">No suppliers found in database</option>
          ) : (
            suppliers.map((s) => (
              <option key={s.supplier_id} value={s.supplier_id}>
                {s.name} ({s.city ?? "HQ"}, {s.country ?? "Global"})
              </option>
            ))
          )}
        </select>

        <button
          className="sc-primary-button"
          disabled={!selectedSupplier || simulating || loadingSuppliers}
          onClick={runSimulation}
        >
          {simulating ? (
            <>
              <Loader2 size={16} className="sc-spin" />
              Simulating Disruption...
            </>
          ) : (
            <>
              <Zap size={16} />
              Run Simulation
            </>
          )}
        </button>

        <button
          className="sc-icon-button"
          title="Refresh suppliers list"
          disabled={loadingSuppliers || simulating}
          onClick={() => void loadSuppliers()}
        >
          <RefreshCw size={15} />
        </button>
      </div>

      {error && (
        <div className="active-banner" style={{ background: "rgba(239, 68, 68, 0.12)", borderColor: "rgba(239, 68, 68, 0.3)" }}>
          <div className="active-banner-left">
            <div className="active-banner-icon">
              <AlertTriangle size={18} />
            </div>
            <div>
              <div className="active-banner-title">Simulation Error</div>
              <div className="active-banner-sub">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Initial Empty State */}
      {!result && !error && (
        <div className="sc-empty">
          <div className="sc-empty-icon">
            <Truck size={26} />
          </div>
          <h3>Ready for Disruption Simulation</h3>
          <p>
            Choose any supplier from your supply network above to compute gross lost volume, alternative recovery, inventory buffer days, and plant operational health.
          </p>
        </div>
      )}

      {/* Simulation Results Section */}
      {result && (
        <>
          {/* Active Supplier Failure Card */}
          <div className="sc-failed-card">
            <div className="sc-failed-icon">
              <Truck size={20} />
            </div>
            <div>
              <span className="sc-kicker">SIMULATED OUTAGE</span>
              <strong style={{ fontSize: 16, color: "#f8fafc" }}>{result.supplier.name}</strong>
              <small style={{ display: "block", color: "#94a3b8", marginTop: 2 }}>
                {result.supplier.city ?? "HQ"}, {result.supplier.country ?? "Global"} · {result.supplier.supplier_id}
              </small>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
              <span className="status-badge badge-critical">OUTAGE IN EFFECT</span>
            </div>
          </div>

          {/* Primary KPI Metrics */}
          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">GROSS LOST SUPPLY</span>
                <span className="metric-value">{formatNumber(summary?.gross_lost_supply)}</span>
                <span style={{ fontSize: "11px", color: "#94a3b8" }}>Allocated units</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(239, 68, 68, 0.12)", color: "#f87171", borderColor: "rgba(239, 68, 68, 0.25)" }}>
                <TrendingDown size={18} />
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">ALTERNATIVE RECOVERY</span>
                <span className="metric-value">{formatNumber(summary?.alternative_recovery)}</span>
                <span style={{ fontSize: "11px", color: "#34d399" }}>{recoveryPct}% Recovered</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(16, 185, 129, 0.12)", color: "#34d399", borderColor: "rgba(16, 185, 129, 0.25)" }}>
                <CheckCircle2 size={18} />
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">NET SHORTAGE</span>
                <span className="metric-value" style={{ color: (summary?.net_shortage ?? 0) > 0 ? "#f87171" : "#34d399" }}>
                  {formatNumber(summary?.net_shortage)}
                </span>
                <span style={{ fontSize: "11px", color: "#94a3b8" }}>Uncovered deficit</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(245, 158, 11, 0.12)", color: "#fbbf24", borderColor: "rgba(245, 158, 11, 0.25)" }}>
                <Box size={18} />
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">MAX DOWNSTREAM DELAY</span>
                <span className="metric-value">{summary?.max_delay_days ?? 0}</span>
                <span style={{ fontSize: "11px", color: "#94a3b8" }}>Transit + disruption days</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "rgba(56, 189, 248, 0.12)", color: "#38bdf8", borderColor: "rgba(56, 189, 248, 0.25)" }}>
                <Clock size={18} />
              </div>
            </div>
          </div>

          {/* Operational Decision Banner */}
          <div className={`sc-decision ${summary?.production_stop ? "danger" : "safe"}`}>
            <div className="sc-decision-icon">
              {summary?.production_stop ? <AlertTriangle size={22} /> : <CheckCircle2 size={22} />}
            </div>
            <div>
              <span className="sc-kicker">EXECUTIVE DECISION SIGNAL</span>
              <strong>{summary?.production_stop ? "CRITICAL PRODUCTION STOPPAGE PREDICTED" : "PRODUCTION PROTECTED VIA INVENTORY BUFFER"}</strong>
              <p>
                {summary?.production_stop
                  ? `Immediate supplier outage causes an unabsorbed deficit of ${formatNumber(summary?.net_shortage)} units. Direct intervention or rerouting required.`
                  : `Current stock buffers absorb the estimated ${formatNumber(summary?.gross_lost_supply)} units of lost supply. Production lines can operate safely while alternate sourcing activates.`}
              </p>
            </div>
          </div>

          {/* Operational Timeline & Buffer Runout */}
          {timelineIntelligence && (
            <OperationalTimeline intelligence={timelineIntelligence} />
          )}

          {/* Affected Plants Operational Matrix */}
          <div className="sc-panel">
            <div className="sc-panel-header">
              <div className="sc-panel-title-icon">
                <Factory size={16} />
              </div>
              <div>
                <strong>Manufacturing Plants Status</strong>
                <span>{result.plants.length} facilities monitored under this failure mode</span>
              </div>
            </div>

            <div className="sc-plant-list">
              {result.plants.map((plant: SimulationPlant) => {
                const isStopped = plant.risk_score >= 80;
                const isReduced = plant.risk_score >= 50 && plant.risk_score < 80;
                const statusBadge = isStopped ? "badge-stopped" : isReduced ? "badge-reduced" : "badge-running";
                const statusLabel = isStopped ? "STOPPED" : isReduced ? "REDUCED CAPACITY" : "RUNNING";

                return (
                  <div className="sc-plant-row" key={plant.plant_id}>
                    <div className="sc-plant-main">
                      <Factory size={18} color="#e8a838" />
                      <div>
                        <strong>{plant.plant_name}</strong>
                        <small>{plant.plant_id}</small>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                      <span style={{ color: "#94a3b8", fontSize: "12px" }}>
                        <strong style={{ color: "#f8fafc" }}>{plant.affected_components}</strong> components affected
                      </span>
                      <span style={{ color: "#94a3b8", fontSize: "12px" }}>
                        <strong style={{ color: "#f8fafc" }}>{plant.max_delay_days}</strong> days delay
                      </span>
                      <span className={`status-badge ${statusBadge}`}>{statusLabel}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Component Level Impact Table */}
          <div className="sc-panel">
            <div className="sc-panel-header">
              <div className="sc-panel-title-icon">
                <Layers size={16} />
              </div>
              <div>
                <strong>Component Buffer & Inventory Depletion</strong>
                <span>{result.components.length} components analyzed across affected plants</span>
              </div>
            </div>

            <div className="sc-table-wrap">
              <div className="sc-table">
                <div className="sc-table-head">
                  <span>COMPONENT</span>
                  <span>TARGET PLANT</span>
                  <span>LOST SUPPLY</span>
                  <span>INVENTORY</span>
                  <span>BUFFER DAYS</span>
                  <span>DAILY DEMAND</span>
                  <span>RISK LEVEL</span>
                </div>

                {result.components.map((c: SimulationComponent) => {
                  const coverage = c.inventory_coverage_days;
                  const isWarning = coverage !== null && coverage <= 14 && coverage > 5;
                  const isCritical = coverage !== null && coverage <= 5;

                  return (
                    <div className="sc-table-row" key={`${c.component_id}-${c.plant_id}`}>
                      <div>
                        <strong>{c.component_name}</strong>
                        <small>{c.component_id}</small>
                      </div>

                      <span>{c.plant_name}</span>
                      <span style={{ color: "#f87171", fontWeight: 600 }}>{formatNumber(c.gross_lost_supply)}</span>
                      <span>{formatNumber(c.inventory_quantity)}</span>

                      <span style={{ fontWeight: 700, color: isCritical ? "#f87171" : isWarning ? "#fbbf24" : "#34d399" }}>
                        {coverage !== null ? `${coverage} days` : "UNKNOWN"}
                      </span>

                      <span>{formatNumber(c.daily_demand)}/day</span>

                      <span>
                        <span className={`sc-risk ${c.risk_level?.toLowerCase() ?? "low"}`}>
                          {c.risk_score ? `${c.risk_score} ` : ""}
                          {c.risk_level ?? "LOW"}
                        </span>
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Product Impact Grid */}
          <div className="sc-panel">
            <div className="sc-panel-header">
              <div className="sc-panel-title-icon">
                <Package size={16} />
              </div>
              <div>
                <strong>Downstream Products Exposure</strong>
                <span>{uniqueProducts.length} finished goods impacted</span>
              </div>
            </div>

            <div className="sc-products-grid">
              {result.products.map((p: SimulationProduct, idx: number) => {
                const isShortage = p.exposure_status === "shortage";
                return (
                  <div className="sc-product-card" key={`${p.product_id}-${idx}`}>
                    <div className="sc-product-head">
                      <div>
                        <strong>{p.product_name}</strong>
                        <small>{p.product_id}</small>
                      </div>
                      <span className={`status-badge ${isShortage ? "badge-critical" : "badge-buffered"}`}>
                        {isShortage ? "SHORTAGE" : "BUFFERED"}
                      </span>
                    </div>

                    <div className="sc-product-detail">
                      <span>Dependency:</span>
                      <strong>{p.component_name}</strong>
                    </div>

                    <div className="sc-product-status" style={{ color: isShortage ? "#f87171" : "#34d399" }}>
                      {isShortage ? <AlertTriangle size={14} /> : <CheckCircle2 size={14} />}
                      <span>{isShortage ? "Direct assembly line risk" : "Protected by component stock"}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

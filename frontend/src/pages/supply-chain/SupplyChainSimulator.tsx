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
          <span className="eyebrow-tag">WHAT-IF TESTER</span>
          <h2>Test What Happens If a Supplier Fails</h2>
          <p>
            Pick any supplier to see if your factory will run out of parts and which backup suppliers can help.
          </p>
        </div>
      </div>

      {/* Supplier Selection Bar */}
      <div className="sc-control-card">
        <div className="sc-control-icon">
          <Zap size={20} />
        </div>
        <div className="sc-control-copy">
          <strong>Pick a Supplier</strong>
          <span>Choose who is delayed or shut down</span>
        </div>

        <select
          value={selectedSupplier}
          disabled={loadingSuppliers || simulating}
          onChange={(e) => setSelectedSupplier(e.target.value)}
          className="sc-select"
        >
          {loadingSuppliers ? (
            <option value="">Loading suppliers...</option>
          ) : suppliers.length === 0 ? (
            <option value="">No suppliers found</option>
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
              Running Test...
            </>
          ) : (
            <>
              <Zap size={16} />
              Run Test
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
        <div className="active-banner" style={{ background: "#fef2f2", borderColor: "#fecaca" }}>
          <div className="active-banner-left">
            <div className="active-banner-icon">
              <AlertTriangle size={18} />
            </div>
            <div>
              <div className="active-banner-title">Test Error</div>
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
          <h3>Ready to Test Your Suppliers</h3>
          <p>
            Choose any supplier from the dropdown above and click <strong>"Run Test"</strong> to see if you have enough backup stock to avoid factory shutdowns.
          </p>
        </div>
      )}

      {/* Simulation Results Section */}
      {result && (
        <>
          {/* Active Supplier Failure Card */}
          <div className="sc-failed-card" style={{ background: "#fef2f2", border: "1px solid #fecaca" }}>
            <div className="sc-failed-icon" style={{ background: "#fee2e2", color: "#dc2626" }}>
              <Truck size={20} />
            </div>
            <div>
              <span className="sc-kicker" style={{ color: "#dc2626" }}>TESTED SUPPLIER</span>
              <strong style={{ fontSize: 16, color: "#0f172a" }}>{result.supplier.name}</strong>
              <small style={{ display: "block", color: "#64748b", marginTop: 2 }}>
                {result.supplier.city ?? "HQ"}, {result.supplier.country ?? "Global"} · {result.supplier.supplier_id}
              </small>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
              <span className="status-badge badge-critical">DELAY TESTED</span>
            </div>
          </div>

          {/* Primary KPI Metrics */}
          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">LOST UNITS</span>
                <span className="metric-value">{formatNumber(summary?.gross_lost_supply)}</span>
                <span style={{ fontSize: "11.5px", color: "#64748b" }}>Units not delivered</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#fee2e2", color: "#dc2626", borderColor: "#fecaca" }}>
                <TrendingDown size={18} />
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">BACKUP UNITS AVAILABLE</span>
                <span className="metric-value" style={{ color: "#16a34a" }}>{formatNumber(summary?.alternative_recovery)}</span>
                <span style={{ fontSize: "11.5px", color: "#16a34a" }}>{recoveryPct}% from other suppliers</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#f0fdf4", color: "#16a34a", borderColor: "#bbf7d0" }}>
                <CheckCircle2 size={18} />
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">FINAL SHORTAGE</span>
                <span className="metric-value" style={{ color: (summary?.net_shortage ?? 0) > 0 ? "#dc2626" : "#16a34a" }}>
                  {formatNumber(summary?.net_shortage)}
                </span>
                <span style={{ fontSize: "11.5px", color: "#64748b" }}>Units still missing</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#fffbeb", color: "#d97706", borderColor: "#fde68a" }}>
                <Box size={18} />
              </div>
            </div>

            <div className="metric-box">
              <div className="metric-info">
                <span className="metric-label">MAX ESTIMATED DELAY</span>
                <span className="metric-value">{summary?.max_delay_days ?? 0} Days</span>
                <span style={{ fontSize: "11.5px", color: "#64748b" }}>Expected delay time</span>
              </div>
              <div className="metric-icon-wrap" style={{ background: "#eff6ff", color: "#2563eb", borderColor: "#bfdbfe" }}>
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
              <span className="sc-kicker">{summary?.production_stop ? "ATTENTION NEEDED" : "ALL SAFE"}</span>
              <strong>{summary?.production_stop ? "Warning: Factory Will Stop!" : "Safe: Backup Stock is Enough!"}</strong>
              <p>
                {summary?.production_stop
                  ? `This supplier delay causes an uncovered deficit of ${formatNumber(summary?.net_shortage)} parts. Your factory lines will pause unless backup suppliers are contacted.`
                  : `Your current warehouse stock covers the estimated ${formatNumber(summary?.gross_lost_supply)} delayed parts. Your factory can continue working while backup suppliers deliver.`}
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
                <strong>Factory Status</strong>
                <span>{result.plants.length} factories checked under this scenario</span>
              </div>
            </div>

            <div className="sc-plant-list">
              {result.plants.map((plant: SimulationPlant) => {
                const isStopped = plant.risk_score >= 80;
                const isReduced = plant.risk_score >= 50 && plant.risk_score < 80;
                const statusBadge = isStopped ? "badge-stopped" : isReduced ? "badge-reduced" : "badge-running";
                const statusLabel = isStopped ? "STOPPED" : isReduced ? "PARTIAL DELAY" : "RUNNING NORMALLY";

                return (
                  <div className="sc-plant-row" key={plant.plant_id}>
                    <div className="sc-plant-main">
                      <Factory size={18} color="#2563eb" />
                      <div>
                        <strong>{plant.plant_name}</strong>
                        <small>{plant.plant_id}</small>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                      <span style={{ color: "#64748b", fontSize: "12.5px" }}>
                        <strong style={{ color: "#0f172a" }}>{plant.affected_components}</strong> parts affected
                      </span>
                      <span style={{ color: "#64748b", fontSize: "12.5px" }}>
                        <strong style={{ color: "#0f172a" }}>{plant.max_delay_days}</strong> days delay
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
                <strong>Part Stock & Days of Supply Left</strong>
                <span>{result.components.length} parts checked across factories</span>
              </div>
            </div>

            <div className="sc-table-wrap">
              <div className="sc-table">
                <div className="sc-table-head">
                  <span>PART NAME</span>
                  <span>FACTORY</span>
                  <span>LOST UNITS</span>
                  <span>IN STOCK</span>
                  <span>STOCK RUNWAY</span>
                  <span>DAILY USE</span>
                  <span>STATUS</span>
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
                      <span style={{ color: "#dc2626", fontWeight: 600 }}>{formatNumber(c.gross_lost_supply)}</span>
                      <span>{formatNumber(c.inventory_quantity)}</span>

                      <span style={{ fontWeight: 700, color: isCritical ? "#dc2626" : isWarning ? "#d97706" : "#16a34a" }}>
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
                <strong>Finished Products Impacted</strong>
                <span>{uniqueProducts.length} products affected by this supplier</span>
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
                        {isShortage ? "SHORTAGE" : "PROTECTED"}
                      </span>
                    </div>

                    <div className="sc-product-detail">
                      <span>Needs part:</span>
                      <strong>{p.component_name}</strong>
                    </div>

                    <div className="sc-product-status" style={{ color: isShortage ? "#dc2626" : "#16a34a" }}>
                      {isShortage ? <AlertTriangle size={14} /> : <CheckCircle2 size={14} />}
                      <span>{isShortage ? "Assembly line at risk" : "Protected by backup stock"}</span>
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

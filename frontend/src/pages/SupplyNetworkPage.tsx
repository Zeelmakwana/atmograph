import { useState, useEffect } from "react";
import {
  Network,
  RefreshCw,
  Layers,
  Filter,
  Search,
  Info,
  GitBranch,
  TrendingUp,
  Boxes,
  Database,
  ShieldAlert,
} from "lucide-react";
import SupplyGraph from "../components/dashboard/SupplyGraph";
import RippleAnalysis from "../components/RippleAnalysis";
import PredictionIntelligence from "../components/PredictionIntelligence";
import { getEvents } from "../services/api";

type GraphViewMode = "topology" | "ripple" | "gnn";

export default function SupplyNetworkPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [viewMode, setViewMode] = useState<GraphViewMode>("topology");
  const [events, setEvents] = useState<any[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number>(1);
  const [loadingEvents, setLoadingEvents] = useState(false);

  useEffect(() => {
    async function loadEventList() {
      try {
        setLoadingEvents(true);
        const data = await getEvents("", "", "", 50);
        const raw = data?.events || data?.data || (Array.isArray(data) ? data : []);
        setEvents(raw);
        if (raw.length > 0 && raw[0]?.id) {
          setSelectedEventId(Number(raw[0].id));
        }
      } catch (err) {
        console.warn("Failed to load events for graph selector:", err);
      } finally {
        setLoadingEvents(false);
      }
    }

    void loadEventList();
  }, []);

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header-row">
        <div className="page-headline">
          <span className="eyebrow-tag">GRAPH INTELLIGENCE SUITE</span>
          <h2>Supply Network & Impact Graph Explorer</h2>
          <p>
            Explore multi-tier supply chain topology, simulate cascading ripple shock propagation, and inspect GNN predictive risk metrics.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div style={{ display: "flex", gap: "6px", background: "rgba(255,255,255,0.03)", padding: "4px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
          <button
            className={viewMode === "topology" ? "primary-button" : "secondary-button"}
            style={{ padding: "6px 14px", fontSize: "12px" }}
            onClick={() => setViewMode("topology")}
          >
            <Network size={14} />
            Topology Graph
          </button>

          <button
            className={viewMode === "ripple" ? "primary-button" : "secondary-button"}
            style={{ padding: "6px 14px", fontSize: "12px" }}
            onClick={() => setViewMode("ripple")}
          >
            <GitBranch size={14} />
            Cascading Ripple Paths
          </button>

          <button
            className={viewMode === "gnn" ? "primary-button" : "secondary-button"}
            style={{ padding: "6px 14px", fontSize: "12px" }}
            onClick={() => setViewMode("gnn")}
          >
            <TrendingUp size={14} />
            GNN Risk Model
          </button>
        </div>
      </div>

      {/* Mode 1: Interactive ReactFlow Topology Graph */}
      {viewMode === "topology" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
          {/* Main Interactive Graph Container - Full Viewport Studio */}
          <div
            className="modern-card"
            style={{
              padding: 0,
              overflow: "hidden",
              height: "calc(100vh - 210px)",
              minHeight: "660px",
              display: "flex",
              flexDirection: "column",
              border: "1px solid rgba(232, 168, 56, 0.25)",
              boxShadow: "0 12px 36px rgba(0, 0, 0, 0.5)",
            }}
          >
            <SupplyGraph key={refreshKey} />
          </div>
        </div>
      )}

      {/* Mode 2: Cascading Ripple Analysis */}
      {viewMode === "ripple" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "14px 18px",
              background: "#141416",
              border: "1px solid rgba(255, 255, 255, 0.06)",
              borderRadius: "12px",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <GitBranch size={18} color="#e8a838" />
              <div>
                <strong style={{ fontSize: "13.5px", color: "#ececef" }}>Target Disruption Event for Propagation Trace</strong>
                <span style={{ fontSize: "11px", color: "#8e8e96", display: "block" }}>
                  Select an event to compute 1-hop, 2-hop, and 3-hop downstream shock ripple paths
                </span>
              </div>
            </div>

            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(Number(e.target.value))}
              className="sc-select"
              style={{ minWidth: "300px" }}
            >
              {events.map((ev) => (
                <option key={ev.id || ev.event_id} value={ev.id || ev.event_id}>
                  #{ev.id || ev.event_id} - {ev.title || "Disruption Event"} ({ev.severity || "HIGH"})
                </option>
              ))}
            </select>
          </div>

          <RippleAnalysis eventId={selectedEventId} />
        </div>
      )}

      {/* Mode 3: GNN Predictive Risk Model */}
      {viewMode === "gnn" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "14px 18px",
              background: "#141416",
              border: "1px solid rgba(255, 255, 255, 0.06)",
              borderRadius: "12px",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <TrendingUp size={18} color="#e8a838" />
              <div>
                <strong style={{ fontSize: "13.5px", color: "#ececef" }}>Graph Neural Network (GNN) Risk Inference</strong>
                <span style={{ fontSize: "11px", color: "#8e8e96", display: "block" }}>
                  Predictive link risk scores and node vulnerability forecasting on knowledge graph
                </span>
              </div>
            </div>

            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(Number(e.target.value))}
              className="sc-select"
              style={{ minWidth: "300px" }}
            >
              {events.map((ev) => (
                <option key={ev.id || ev.event_id} value={ev.id || ev.event_id}>
                  #{ev.id || ev.event_id} - {ev.title || "Disruption Event"}
                </option>
              ))}
            </select>
          </div>

          <PredictionIntelligence eventId={selectedEventId} graphId={`event_${selectedEventId}`} />
        </div>
      )}
    </div>
  );
}

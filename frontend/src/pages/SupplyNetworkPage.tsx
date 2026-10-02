import { useState, useEffect } from "react";
import {
  Network,
  GitBranch,
  TrendingUp,
} from "lucide-react";
import SupplyGraph from "../components/dashboard/SupplyGraph";
import RippleAnalysis from "../components/RippleAnalysis";
import PredictionIntelligence from "../components/PredictionIntelligence";
import { getEvents } from "../services/api";

type GraphViewMode = "topology" | "ripple" | "gnn";

export default function SupplyNetworkPage() {
  const [refreshKey] = useState(0);
  const [viewMode, setViewMode] = useState<GraphViewMode>("topology");
  const [events, setEvents] = useState<any[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number>(1);
  const [, setLoadingEvents] = useState(false);

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
          <span className="eyebrow-tag">MAP & NETWORK</span>
          <h2>Interactive Supply Chain Map</h2>
          <p>
            Explore your suppliers, shipping routes, and factories on an interactive visual map.
            Click any supplier or port to see details or test delays.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div style={{ display: "flex", gap: "6px", background: "#ffffff", padding: "4px", borderRadius: "10px", border: "1px solid #cbd5e1", boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}>
          <button
            className={viewMode === "topology" ? "primary-button" : "secondary-button"}
            style={{ padding: "6px 14px", fontSize: "12.5px" }}
            onClick={() => setViewMode("topology")}
          >
            <Network size={14} />
            1. Network Map
          </button>

          <button
            className={viewMode === "ripple" ? "primary-button" : "secondary-button"}
            style={{ padding: "6px 14px", fontSize: "12.5px" }}
            onClick={() => setViewMode("ripple")}
          >
            <GitBranch size={14} />
            2. Ripple Impact Path
          </button>

          <button
            className={viewMode === "gnn" ? "primary-button" : "secondary-button"}
            style={{ padding: "6px 14px", fontSize: "12.5px" }}
            onClick={() => setViewMode("gnn")}
          >
            <TrendingUp size={14} />
            3. AI Risk Scores
          </button>
        </div>
      </div>

      {/* Mode 1: Interactive ReactFlow Topology Graph */}
      {viewMode === "topology" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
          <div
            className="modern-card"
            style={{
              padding: 0,
              overflow: "hidden",
              height: "calc(100vh - 210px)",
              minHeight: "660px",
              display: "flex",
              flexDirection: "column",
              border: "1px solid #cbd5e1",
              boxShadow: "0 4px 12px rgba(15, 23, 42, 0.05)",
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
              padding: "16px 20px",
              background: "#ffffff",
              border: "1px solid #cbd5e1",
              borderRadius: "12px",
              flexWrap: "wrap",
              gap: "12px",
              boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <GitBranch size={20} color="#2563eb" />
              <div>
                <strong style={{ fontSize: "14px", color: "#0f172a" }}>Choose an Alert to Trace</strong>
                <span style={{ fontSize: "12px", color: "#64748b", display: "block" }}>
                  Select an event to see step-by-step how the delay spreads through your suppliers and factories
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
              padding: "16px 20px",
              background: "#ffffff",
              border: "1px solid #cbd5e1",
              borderRadius: "12px",
              flexWrap: "wrap",
              gap: "12px",
              boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <TrendingUp size={20} color="#2563eb" />
              <div>
                <strong style={{ fontSize: "14px", color: "#0f172a" }}>AI Risk Predictions</strong>
                <span style={{ fontSize: "12px", color: "#64748b", display: "block" }}>
                  See automated risk scores calculated for each connection in your supply network
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

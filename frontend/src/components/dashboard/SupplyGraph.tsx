import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useRef,
} from "react";

import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  Download,
  Factory,
  FileSpreadsheet,
  Maximize2,
  Minimize2,
  Package,
  RefreshCw,
  Search,
  Server,
  ShieldAlert,
  ShieldCheck,
  Truck,
  Warehouse,
  X,
  Zap,
  Info,
  Layers,
  ArrowRight,
} from "lucide-react";

import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  MarkerType,
  useReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";
import { getAuthHeaders } from "../../services/api";

type SupplyGraphProps = {
  graphId?: string;
};

type BusinessGraphNode = {
  id: string;
  name: string;
  type: string;
  labels?: string[];
  properties?: Record<string, any>;
};

type BusinessGraphRelationship = {
  source: string;
  target: string;
  relationship: string;
  properties?: Record<string, any>;
};

type BusinessGraphResponse = {
  success: boolean;
  stage?: string;
  nodes: BusinessGraphNode[];
  relationships: BusinessGraphRelationship[];
  graph?: {
    nodes?: number;
    relationships?: number;
  };
};

type SimulationImpact = {
  supplier_id?: string;
  supplier_name?: string;
  result?: any;
  matched_suppliers?: any[];
  supplier_match_count?: number;
  simulation?: {
    success?: boolean;
    status?: string;
    suppliers?: any[];
    simulations?: any[];
  };
  suppliers?: any[];
  components?: any[];
  products?: any[];
  plants?: any[];
  summary?: any;
  event_id?: number;
  title?: string;
  source?: string;
  created_at?: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function normalizeId(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function normalizeText(value: unknown): string {
  return String(value ?? "").trim().toLowerCase();
}

function firstDefined(...values: unknown[]) {
  for (const value of values) {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      return value;
    }
  }
  return undefined;
}

function getNodeIcon(type: string) {
  switch (normalizeText(type)) {
    case "company":
      return <Building2 size={16} />;
    case "supplier":
      return <Truck size={16} />;
    case "plant":
      return <Factory size={16} />;
    case "product":
      return <Package size={16} />;
    case "component":
      return <Server size={16} />;
    case "warehouse":
      return <Warehouse size={16} />;
    default:
      return <Package size={16} />;
  }
}

function getNodeColor(type: string) {
  switch (normalizeText(type)) {
    case "supplier":
      return "#38bdf8";
    case "component":
      return "#e8a838";
    case "plant":
      return "#f97316";
    case "product":
      return "#10b981";
    case "company":
      return "#a78bfa";
    case "warehouse":
      return "#c084fc";
    default:
      return "#94a3b8";
  }
}

/* Custom Node Component */
function BusinessNode({ data }: { data: any }) {
  const impacted = Boolean(data?.impacted);
  const failed = Boolean(data?.failed);
  const selected = Boolean(data?.selected);
  const type = String(data?.type ?? "Entity");
  const typeColor = getNodeColor(type);

  let borderStyle = selected ? "1.5px solid #e8a838" : "1px solid rgba(255, 255, 255, 0.12)";
  let bgStyle = "rgba(18, 22, 32, 0.95)";
  let shadowStyle = selected ? "0 0 16px rgba(232, 168, 56, 0.4)" : "0 4px 14px rgba(0, 0, 0, 0.4)";

  if (failed) {
    borderStyle = "2px solid #ef4444";
    bgStyle = "linear-gradient(135deg, rgba(239, 68, 68, 0.28) 0%, rgba(18, 22, 32, 0.98) 100%)";
    shadowStyle = "0 0 24px rgba(239, 68, 68, 0.5)";
  } else if (impacted) {
    borderStyle = "2px solid #f59e0b";
    bgStyle = "linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(18, 22, 32, 0.98) 100%)";
    shadowStyle = "0 0 20px rgba(245, 158, 11, 0.4)";
  }

  const subtitle =
    data?.properties?.city ||
    data?.properties?.category ||
    data?.properties?.industry ||
    data?.properties?.country ||
    (type === "Company" ? "Enterprise Hub" : type);

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: typeColor,
          width: 9,
          height: 9,
          border: "2px solid #080c14",
        }}
      />
      <div
        style={{
          width: 250,
          borderRadius: 12,
          padding: "10px 14px",
          border: borderStyle,
          background: bgStyle,
          boxShadow: shadowStyle,
          backdropFilter: "blur(12px)",
          transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
          cursor: "pointer",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: failed
                ? "rgba(239, 68, 68, 0.25)"
                : impacted
                ? "rgba(245, 158, 11, 0.25)"
                : `${typeColor}1f`,
              color: failed ? "#f87171" : impacted ? "#fbbf24" : typeColor,
              border: `1.5px solid ${
                failed
                  ? "rgba(239, 68, 68, 0.6)"
                  : impacted
                  ? "rgba(245, 158, 11, 0.6)"
                  : `${typeColor}4d`
              }`,
              flexShrink: 0,
            }}
          >
            {failed || impacted ? <ShieldAlert size={19} /> : getNodeIcon(type)}
          </div>

          <div style={{ minWidth: 0, flex: 1 }}>
            <strong
              style={{
                display: "block",
                color: "#f8fafc",
                fontSize: 13,
                fontWeight: 700,
                lineHeight: 1.3,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
              title={data?.label}
            >
              {data?.label ?? "Unknown"}
            </strong>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 3 }}>
              <span
                style={{
                  fontSize: 10.5,
                  color: "#94a3b8",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  maxWidth: 110,
                }}
              >
                {subtitle}
              </span>

              <span
                style={{
                  fontSize: 9.5,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  padding: "1px 6px",
                  borderRadius: "4px",
                  backgroundColor: failed
                    ? "rgba(239, 68, 68, 0.2)"
                    : impacted
                    ? "rgba(245, 158, 11, 0.2)"
                    : `${typeColor}1a`,
                  color: failed ? "#fca5a5" : impacted ? "#fcd34d" : typeColor,
                  border: `1px solid ${
                    failed ? "rgba(239,68,68,0.3)" : impacted ? "rgba(245,158,11,0.3)" : `${typeColor}33`
                  }`,
                }}
              >
                {failed ? "DISRUPTED" : impacted ? "IMPACTED" : type}
              </span>
            </div>
          </div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: typeColor,
          width: 9,
          height: 9,
          border: "2px solid #080c14",
        }}
      />
    </>
  );
}

const nodeTypes = {
  business: BusinessNode,
};

function normalizeGraph(payload: any): BusinessGraphResponse {
  const data = payload?.data ?? payload ?? {};
  const rawNodes = Array.isArray(data?.nodes) ? data.nodes : [];
  const rawRelationships = Array.isArray(data?.relationships) ? data.relationships : [];

  const nodes = rawNodes.map((node: any, index: number) => ({
    id: normalizeId(node?.id ?? node?.graph_id ?? index),
    name: node?.name ?? node?.properties?.name ?? `Entity ${index + 1}`,
    type: node?.type ?? node?.node_type ?? "Entity",
    labels: Array.isArray(node?.labels) ? node.labels : [],
    properties: node?.properties ?? {},
  }));

  const relationships = rawRelationships
    .map((relationship: any) => ({
      source: normalizeId(relationship?.source ?? relationship?.from ?? relationship?.source_id),
      target: normalizeId(relationship?.target ?? relationship?.to ?? relationship?.target_id),
      relationship: String(relationship?.relationship ?? relationship?.type ?? "RELATED_TO"),
      properties: relationship?.properties ?? {},
    }))
    .filter((rel: BusinessGraphRelationship) => Boolean(rel.source) && Boolean(rel.target));

  return {
    success: data?.success !== false,
    stage: data?.stage,
    nodes,
    relationships,
    graph: data?.graph ?? {
      nodes: nodes.length,
      relationships: relationships.length,
    },
  };
}

function extractSupplierRecords(impact: SimulationImpact | null): any[] {
  if (!impact) return [];
  if (Array.isArray(impact.matched_suppliers)) return impact.matched_suppliers;
  if (Array.isArray(impact.simulation?.suppliers)) return impact.simulation.suppliers;
  if (impact.supplier_id) {
    return [{ supplier_id: impact.supplier_id, name: impact.supplier_name }];
  }
  return [];
}

function extractComponentRecords(impact: SimulationImpact | null): any[] {
  if (!impact) return [];
  if (Array.isArray(impact.components)) return impact.components;
  if (impact.result && Array.isArray(impact.result.components)) return impact.result.components;
  return [];
}

function extractProductRecords(impact: SimulationImpact | null): any[] {
  if (!impact) return [];
  if (Array.isArray(impact.products)) return impact.products;
  if (impact.result && Array.isArray(impact.result.products)) return impact.result.products;
  return [];
}

function extractPlantRecords(impact: SimulationImpact | null): any[] {
  if (!impact) return [];
  if (Array.isArray(impact.plants)) return impact.plants;
  if (impact.result && Array.isArray(impact.result.plants)) return impact.result.plants;
  return [];
}

function buildImpactSets(graph: BusinessGraphResponse, impact: SimulationImpact | null) {
  const impactedIds = new Set<string>();
  const failedIds = new Set<string>();

  if (!impact) return { impactedIds, failedIds };

  const supplierRecords = extractSupplierRecords(impact);
  const componentRecords = extractComponentRecords(impact);
  const plantRecords = extractPlantRecords(impact);
  const productRecords = extractProductRecords(impact);

  for (const node of graph.nodes) {
    const nodeName = normalizeText(node.name);
    const nodeType = normalizeText(node.type);

    if (nodeType === "supplier") {
      const matched = supplierRecords.some(
        (supplier: any) =>
          normalizeText(firstDefined(supplier?.name, supplier?.supplier_name)) === nodeName ||
          normalizeText(supplier?.supplier_id) === normalizeText(node.properties?.supplier_id)
      );
      if (matched) {
        failedIds.add(node.id);
        impactedIds.add(node.id);
      }
    }
    if (nodeType === "component") {
      const matched = componentRecords.some(
        (comp: any) =>
          normalizeText(firstDefined(comp?.component_name, comp?.name)) === nodeName ||
          normalizeText(comp?.component_id) === normalizeText(node.properties?.component_id)
      );
      if (matched) impactedIds.add(node.id);
    }
    if (nodeType === "plant") {
      const matched = plantRecords.some(
        (plant: any) =>
          normalizeText(firstDefined(plant?.plant_name, plant?.name)) === nodeName ||
          normalizeText(plant?.plant_id) === normalizeText(node.properties?.plant_id)
      );
      if (matched) impactedIds.add(node.id);
    }
    if (nodeType === "product") {
      const matched = productRecords.some(
        (prod: any) =>
          normalizeText(firstDefined(prod?.product_name, prod?.name)) === nodeName ||
          normalizeText(prod?.product_id) === normalizeText(node.properties?.product_id)
      );
      if (matched) impactedIds.add(node.id);
    }
  }

  return { impactedIds, failedIds };
}

function SupplyGraphInternal({ graphId: _graphId }: SupplyGraphProps) {
  const { fitView } = useReactFlow();
  const [graph, setGraph] = useState<BusinessGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<BusinessGraphNode | null>(null);
  const [simulationImpact, setSimulationImpact] = useState<SimulationImpact | null>(null);
  const [filterType, setFilterType] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/supply-chain/business-graph`, {
        headers: {
          Accept: "application/json",
          ...getAuthHeaders(),
        },
      });
      if (!response.ok) {
        throw new Error(`Business graph request failed (${response.status})`);
      }
      const data = await response.json();
      const normalized = normalizeGraph(data);
      setGraph(normalized);
    } catch (err: any) {
      setGraph(null);
      setError(err?.message ?? "Unable to load the business supply-chain graph.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Listen to Escape key for exiting fullscreen
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFullscreen]);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("atmograph:last-supplier-simulation");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && (parsed.result || parsed.components || parsed.simulation || parsed.matched_suppliers)) {
          setSimulationImpact(parsed);
        }
      }
    } catch {
      // Ignore storage errors.
    }
  }, []);

  useEffect(() => {
    function handleSimulation(event: Event) {
      const customEvent = event as CustomEvent<SimulationImpact>;
      if (customEvent.detail) {
        setSimulationImpact(customEvent.detail);
      }
    }
    window.addEventListener("atmograph:supplier-simulation", handleSimulation);
    return () => {
      window.removeEventListener("atmograph:supplier-simulation", handleSimulation);
    };
  }, []);

  const impactSets = useMemo(
    () => (graph ? buildImpactSets(graph, simulationImpact) : { impactedIds: new Set<string>(), failedIds: new Set<string>() }),
    [graph, simulationImpact]
  );

  const filteredNodes = useMemo(() => {
    if (!graph) return [];
    let list = graph.nodes;
    if (filterType !== "all") {
      list = list.filter((n) => normalizeText(n.type) === filterType.toLowerCase());
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter((n) => n.name.toLowerCase().includes(q) || n.type.toLowerCase().includes(q));
    }
    return list;
  }, [graph, filterType, searchQuery]);

  // Auto fit view whenever nodes load or layout updates
  useEffect(() => {
    if (graph && filteredNodes.length > 0) {
      const timer = setTimeout(() => {
        fitView({ padding: 0.15, duration: 400 });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [graph, filteredNodes.length, fitView, isFullscreen]);

  // SMART COMPACT HIERARCHICAL LAYOUT
  // Groups tiers horizontally, splits dense tiers into 2 sub-columns, and centers vertically!
  const flowNodes = useMemo<Node[]>(() => {
    if (!graph || filteredNodes.length === 0) return [];

    // Define tier columns: Left to Right
    // Tier 0: Company
    // Tier 1: Suppliers
    // Tier 2: Components (Raw Materials & Fabrics/Parts)
    // Tier 3: Plants & Warehouses (Processing & Storage Hubs)
    // Tier 4: Products (Finished SKUs)
    const tierMapping: Record<string, number> = {
      company: 0,
      supplier: 1,
      component: 2,
      warehouse: 3,
      plant: 3,
      product: 4,
    };

    const tiers = new Map<number, BusinessGraphNode[]>();
    for (let i = 0; i <= 4; i++) tiers.set(i, []);

    for (const node of filteredNodes) {
      const typeKey = normalizeText(node.type);
      const tierIdx = tierMapping[typeKey] ?? 2;
      tiers.get(tierIdx)!.push(node);
    }

    const positions = new Map<string, { x: number; y: number }>();
    const nodeCardWidth = 260;
    const nodeCardHeight = 68;
    const rowGap = 16;
    const effectiveRowHeight = nodeCardHeight + rowGap;

    // Calculate maximum tier height so we can vertically center all tiers
    let maxOverallHeight = 0;
    tiers.forEach((nodes) => {
      // If nodes > 4, we use 2 sub-columns, so row count is ceil(n/2)
      const numRows = nodes.length > 5 ? Math.ceil(nodes.length / 2) : nodes.length;
      const height = numRows * effectiveRowHeight;
      if (height > maxOverallHeight) maxOverallHeight = height;
    });

    maxOverallHeight = Math.max(maxOverallHeight, 400);

    let currentTierX = 60;
    const tierSpacing = 310;

    for (let tierIdx = 0; tierIdx <= 4; tierIdx++) {
      const nodes = tiers.get(tierIdx) ?? [];
      if (nodes.length === 0) continue;

      const useTwoColumns = nodes.length > 5;
      const numRows = useTwoColumns ? Math.ceil(nodes.length / 2) : nodes.length;
      const tierTotalHeight = numRows * effectiveRowHeight;
      const verticalOffset = Math.max(40, (maxOverallHeight - tierTotalHeight) / 2 + 40);

      nodes.forEach((node, idx) => {
        let x = currentTierX;
        let y = verticalOffset;

        if (useTwoColumns) {
          const colOffset = idx % 2; // 0 or 1
          const rowOffset = Math.floor(idx / 2);
          x = currentTierX + colOffset * (nodeCardWidth + 24);
          y = verticalOffset + rowOffset * effectiveRowHeight;
        } else {
          y = verticalOffset + idx * effectiveRowHeight;
        }

        positions.set(node.id, { x, y });
      });

      currentTierX += (useTwoColumns ? (nodeCardWidth * 2 + 60) : nodeCardWidth) + 90;
    }

    return filteredNodes.map((node) => {
      const failed = impactSets.failedIds.has(node.id);
      const impacted = failed || impactSets.impactedIds.has(node.id);
      const isNodeSelected = selected?.id === node.id;

      return {
        id: node.id,
        type: "business",
        position: positions.get(node.id) ?? { x: 80, y: 80 },
        data: {
          label: node.name,
          type: node.type,
          properties: node.properties,
          impacted,
          failed,
          selected: isNodeSelected,
        },
      };
    });
  }, [graph, filteredNodes, impactSets, selected]);

  const flowEdges = useMemo<Edge[]>(() => {
    if (!graph) return [];
    const visibleIds = new Set(filteredNodes.map((n) => n.id));

    return graph.relationships
      .filter((rel) => visibleIds.has(rel.source) && visibleIds.has(rel.target))
      .map((rel, index) => {
        const sourceFailed = impactSets.failedIds.has(rel.source);
        const sourceImpacted = impactSets.impactedIds.has(rel.source);
        const targetImpacted = impactSets.impactedIds.has(rel.target);
        const isShockEdge = (sourceFailed || sourceImpacted) && targetImpacted;

        return {
          id: `edge-${index}-${rel.source}-${rel.target}`,
          source: rel.source,
          target: rel.target,
          type: "smoothstep",
          animated: isShockEdge,
          style: {
            stroke: isShockEdge ? "#f59e0b" : "rgba(255, 255, 255, 0.16)",
            strokeWidth: isShockEdge ? 2.5 : 1.4,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: isShockEdge ? "#f59e0b" : "rgba(255, 255, 255, 0.4)",
            width: 14,
            height: 14,
          },
        };
      });
  }, [graph, filteredNodes, impactSets]);

  const counts = useMemo(() => {
    const res: Record<string, number> = {};
    for (const node of graph?.nodes ?? []) {
      const t = normalizeText(node.type);
      res[t] = (res[t] ?? 0) + 1;
    }
    return res;
  }, [graph]);

  function clearImpact() {
    setSimulationImpact(null);
    try {
      localStorage.removeItem("atmograph:last-supplier-simulation");
    } catch {
      // Ignore
    }
  }

  const handleSimulateOutageOnNode = (node: BusinessGraphNode) => {
    const supId = node.properties?.supplier_id || node.id;
    window.dispatchEvent(
      new CustomEvent("atmograph:supplier-simulation", {
        detail: {
          supplier_id: supId,
          supplier_name: node.name,
          matched_suppliers: [{ supplier_id: supId, name: node.name }],
        },
      })
    );
  };

  const containerStyle: React.CSSProperties = isFullscreen
    ? {
        position: "fixed",
        inset: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 99999,
        background: "#080a0f",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }
    : {
        width: "100%",
        height: "100%",
        minHeight: "620px",
        position: "relative",
        borderRadius: "14px",
        overflow: "hidden",
        border: "1px solid rgba(255,255,255,0.08)",
        background: "#080c14",
        display: "flex",
        flexDirection: "column",
        flex: 1,
      };

  return (
    <div ref={containerRef} style={containerStyle}>
      {/* Top Filter & Control Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "10px 18px",
          background: "rgba(14, 18, 28, 0.9)",
          backdropFilter: "blur(14px)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          zIndex: 20,
          position: "relative",
          flexWrap: "wrap",
        }}
      >
        {/* Left Search and Filter Tabs */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "#0a0d14",
              border: "1px solid rgba(255, 255, 255, 0.14)",
              padding: "5px 12px",
              borderRadius: "20px",
            }}
          >
            <Search size={14} color="#64748b" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search nodes or city..."
              style={{
                background: "none",
                border: "none",
                outline: "none",
                color: "#f8fafc",
                fontSize: "12px",
                width: "170px",
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                style={{ color: "#64748b", background: "none", border: "none", cursor: "pointer" }}
              >
                <X size={12} />
              </button>
            )}
          </div>

          <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
            {[
              { id: "all", label: "All Nodes" },
              { id: "supplier", label: "Suppliers" },
              { id: "component", label: "Components" },
              { id: "plant", label: "Facilities" },
              { id: "product", label: "Products" },
            ].map((tab) => {
              const active = filterType === tab.id;
              const count = tab.id === "all" ? graph?.nodes.length ?? 0 : counts[tab.id] ?? 0;
              return (
                <button
                  key={tab.id}
                  onClick={() => setFilterType(tab.id)}
                  style={{
                    padding: "5px 11px",
                    borderRadius: "8px",
                    fontSize: "11.5px",
                    fontWeight: active ? 700 : 500,
                    background: active ? "rgba(232, 168, 56, 0.18)" : "rgba(255, 255, 255, 0.04)",
                    color: active ? "#e8a838" : "#94a3b8",
                    border: active ? "1px solid rgba(232, 168, 56, 0.4)" : "1px solid transparent",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  {tab.label} <span style={{ opacity: 0.65, fontSize: "10.5px" }}>({count})</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Status, View Fit & Fullscreen Toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {simulationImpact && (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  padding: "4px 8px",
                  borderRadius: "6px",
                  background: "rgba(239, 68, 68, 0.18)",
                  color: "#f87171",
                  border: "1px solid rgba(239, 68, 68, 0.35)",
                }}
              >
                {impactSets.failedIds.size} Disrupted · {impactSets.impactedIds.size} Affected
              </span>
              <button
                onClick={clearImpact}
                style={{
                  fontSize: "11px",
                  padding: "4px 8px",
                  borderRadius: "6px",
                  background: "rgba(255, 255, 255, 0.06)",
                  color: "#cbd5e1",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  cursor: "pointer",
                }}
              >
                Clear Impact
              </button>
            </div>
          )}

          <button
            onClick={() => fitView({ padding: 0.15, duration: 400 })}
            title="Fit Entire Graph to Screen"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              padding: "6px 12px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.06)",
              color: "#cbd5e1",
              fontSize: "12px",
              fontWeight: 500,
              border: "1px solid rgba(255, 255, 255, 0.1)",
              cursor: "pointer",
            }}
          >
            <span>Center & Fit</span>
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? "Exit Fullscreen (Esc)" : "Maximize Fullscreen Canvas"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "6px 12px",
              borderRadius: "8px",
              background: isFullscreen ? "rgba(232, 168, 56, 0.2)" : "rgba(255, 255, 255, 0.08)",
              color: isFullscreen ? "#e8a838" : "#f8fafc",
              fontSize: "12px",
              fontWeight: 600,
              border: isFullscreen ? "1px solid rgba(232, 168, 56, 0.4)" : "1px solid rgba(255, 255, 255, 0.15)",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            {isFullscreen ? (
              <>
                <Minimize2 size={14} />
                <span>Exit Fullscreen</span>
              </>
            ) : (
              <>
                <Maximize2 size={14} />
                <span>Fullscreen Studio</span>
              </>
            )}
          </button>

          <button
            onClick={load}
            disabled={loading}
            title="Reload Topology"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              padding: "6px 10px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.06)",
              color: "#cbd5e1",
              fontSize: "12px",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              cursor: "pointer",
            }}
          >
            <RefreshCw size={13} className={loading ? "spin" : ""} />
          </button>
        </div>
      </div>

      {/* Error View */}
      {error && (
        <div
          style={{
            margin: 20,
            padding: 16,
            borderRadius: 10,
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.35)",
            color: "#fca5a5",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Empty State / Onboarding View */}
      {!loading && !error && flowNodes.length === 0 && (
        <div
          style={{
            width: "100%",
            height: "calc(100% - 56px)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "40px 20px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              width: 68,
              height: 68,
              borderRadius: "50%",
              background: "rgba(232, 168, 56, 0.14)",
              border: "1px solid rgba(232, 168, 56, 0.35)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 16,
              color: "#e8a838",
            }}
          >
            <FileSpreadsheet size={32} />
          </div>
          <h3 style={{ fontSize: 19, fontWeight: 700, color: "#f8fafc", marginBottom: 6 }}>
            No Supply Chain Topology Found
          </h3>
          <p style={{ maxWidth: 480, fontSize: 13, color: "#94a3b8", lineHeight: 1.5, marginBottom: 20 }}>
            Upload your multi-sheet Excel workbook to visualize your interactive network nodes, multi-tier BOM flows, and disruption ripple paths.
          </p>
          <a
            href={`${API_BASE_URL}/api/supply-chain/template`}
            download="AtmoGraph_Supply_Chain_Template.xlsx"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "10px 18px",
              borderRadius: "8px",
              background: "rgba(232, 168, 56, 0.15)",
              border: "1px solid rgba(232, 168, 56, 0.35)",
              color: "#e8a838",
              fontSize: "13px",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            <Download size={14} />
            Download Excel Template
          </a>
        </div>
      )}

      {/* Canvas View */}
      {!loading && !error && flowNodes.length > 0 && (
        <div style={{ width: "100%", height: "calc(100% - 54px)", position: "relative" }}>
          <ReactFlow
            nodes={flowNodes}
            edges={flowEdges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            minZoom={0.25}
            maxZoom={2.0}
            onNodeClick={(_event, node) => {
              const original = graph?.nodes.find((item) => String(item.id) === String(node.id));
              if (original) setSelected(original);
            }}
            onPaneClick={() => setSelected(null)}
          >
            <Background color="rgba(255, 255, 255, 0.05)" gap={28} size={1} />
            <Controls
              style={{
                background: "#0e121c",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: "8px",
                fill: "#f8fafc",
                boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
              }}
            />
            <MiniMap
              style={{
                background: "#0a0e17",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: "10px",
                height: 120,
                width: 170,
              }}
              nodeColor={(node) => {
                if (node.data?.failed) return "#ef4444";
                if (node.data?.impacted) return "#f59e0b";
                return "#38bdf8";
              }}
            />
          </ReactFlow>

          {/* Tier Guide Footer Overlay */}
          <div
            style={{
              position: "absolute",
              bottom: 16,
              left: "50%",
              transform: "translateX(-50%)",
              background: "rgba(14, 18, 28, 0.85)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "30px",
              padding: "6px 18px",
              display: "flex",
              alignItems: "center",
              gap: 16,
              fontSize: "11px",
              color: "#94a3b8",
              zIndex: 10,
              pointerEvents: "none",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#a78bfa" }} />
              <span>Company Hub</span>
            </div>
            <span>→</span>
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#38bdf8" }} />
              <span>Tier-1 Suppliers</span>
            </div>
            <span>→</span>
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#e8a838" }} />
              <span>Raw Materials</span>
            </div>
            <span>→</span>
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f97316" }} />
              <span>Plants & Hubs</span>
            </div>
            <span>→</span>
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981" }} />
              <span>Finished SKUs</span>
            </div>
          </div>
        </div>
      )}

      {/* Node Detail Inspector Drawer */}
      {selected && (
        <div
          style={{
            position: "absolute",
            right: 20,
            top: 68,
            width: 340,
            maxHeight: "calc(100% - 90px)",
            overflowY: "auto",
            zIndex: 35,
            padding: 20,
            borderRadius: 14,
            background: "rgba(14, 18, 28, 0.97)",
            border: "1px solid rgba(232, 168, 56, 0.3)",
            boxShadow: "0 24px 48px rgba(0,0,0,0.7), 0 0 20px rgba(232, 168, 56, 0.15)",
            backdropFilter: "blur(20px)",
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 14 }}>
            <div>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  padding: "2px 8px",
                  borderRadius: "6px",
                  background: "rgba(232, 168, 56, 0.15)",
                  color: "#e8a838",
                  border: "1px solid rgba(232, 168, 56, 0.3)",
                }}
              >
                {selected.type}
              </span>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#f8fafc", margin: "6px 0 0 0" }}>
                {selected.name}
              </h3>
            </div>
            <button
              onClick={() => setSelected(null)}
              style={{
                width: 28,
                height: 28,
                borderRadius: 6,
                background: "rgba(255,255,255,0.06)",
                border: "none",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#94a3b8",
                cursor: "pointer",
              }}
            >
              <X size={15} />
            </button>
          </div>

          {/* Action: Simulate Shock if Supplier */}
          {normalizeText(selected.type) === "supplier" && (
            <button
              onClick={() => handleSimulateOutageOnNode(selected)}
              style={{
                width: "100%",
                padding: "10px",
                marginBottom: 16,
                borderRadius: "8px",
                background: "rgba(239, 68, 68, 0.18)",
                border: "1px solid rgba(239, 68, 68, 0.4)",
                color: "#f87171",
                fontSize: "12px",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
              }}
            >
              <Zap size={14} />
              <span>Simulate Disruption on this Supplier</span>
            </button>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {Object.entries(selected.properties ?? {}).map(([key, val]) => (
              <div
                key={key}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "7px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                  fontSize: "12px",
                }}
              >
                <span style={{ color: "#94a3b8", textTransform: "capitalize" }}>
                  {key.replace(/_/g, " ")}
                </span>
                <strong
                  style={{
                    color: "#f8fafc",
                    textAlign: "right",
                    maxWidth: 180,
                    wordBreak: "break-word",
                  }}
                >
                  {typeof val === "object" ? JSON.stringify(val) : String(val ?? "--")}
                </strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function SupplyGraph(props: SupplyGraphProps) {
  return (
    <ReactFlowProvider>
      <SupplyGraphInternal {...props} />
    </ReactFlowProvider>
  );
}

import { useState, useEffect, useCallback } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Building2,
  CheckCircle2,
  Clock,
  Globe,
  Loader2,
  Newspaper,
  Radio,
  Send,
  Sparkles,
  Truck,
  Zap,
} from "lucide-react";
import { analyzeNews } from "../services/api";
import {
  getSupplyChainCatalog,
  type SupplyChainCatalog,
} from "../services/supplyChainApi";

interface IncidentRadarPageProps {
  onNavigateToSimulator: (supplierId?: string) => void;
  onOpenWorkspaceModal?: () => void;
}

interface IncidentPreset {
  title: string;
  description: string;
  source: string;
  target?: string;
}

function getPresetsForBusiness(catalog: SupplyChainCatalog | null): IncidentPreset[] {
  const companyName = (catalog?.company?.company_name || "").toLowerCase();
  const industry = (catalog?.company?.industry || "").toLowerCase();

  // 1. AdilQadri / Attar & Perfumes
  if (
    companyName.includes("adil") ||
    industry.includes("perfume") ||
    industry.includes("attar")
  ) {
    return [
      {
        title: "Kannauj Hydro-Distillation Belt Flash Flooding & Flower Base Delay",
        description:
          "Heavy torrential monsoon downpour in Kannauj flooded low-lying deg-bhapka hydro-distillation units along the Ganges. Traditional Sandalwood, Mitti, and Damask Rose attar base shipments delayed by 5-7 days to formulation units.",
        source: "Kannauj Perfumery Guild Gazette",
        target: "Kannauj Attar Distillers (S001)",
      },
      {
        title: "JNPT Nhava Sheva Freight Chemical Tanker Dispatch Bottleneck",
        description:
          "Customs clearance bottleneck and driver strikes at Nhava Sheva port halt containerized DPG (Dipropylene Glycol) and IPM carrier oil tanker transit across the Mumbai-Thane highway corridor.",
        source: "Maritime Freight Intelligence",
        target: "Mumbai Carrier Oil Traders (S008)",
      },
      {
        title: "Firozabad Glass Industrial Cluster Natural Gas Pressure Drop",
        description:
          "Emergency pipeline maintenance by GAIL forces temporary kiln shutdown across Firozabad glass units, delaying production of 6ml and 12ml luxury octagonal perfume bottles.",
        source: "Uttar Pradesh Industrial Dispatch",
        target: "Firozabad Glass Bottle Manufacturers (S005)",
      },
      {
        title: "Western Express Corridor Rigid Packaging Box Transit Stoppage",
        description:
          "Truck union labor action along the Vasai-Navsari highway delays dispatch of premium embossed presentation gift boxes and metallic roller caps.",
        source: "National Highway Logistics Wire",
        target: "Vasai/Navsari Premium Packaging (S006)",
      },
    ];
  }

  // 2. Mohilya Couture / Surat Textiles
  if (
    companyName.includes("mohilya") ||
    industry.includes("textile") ||
    industry.includes("garment")
  ) {
    return [
      {
        title: "Surat Ring Road Textile Market Flooding & Transport Halt",
        description:
          "Heavy monsoon downpour causes severe waterlogging around Surat Ring Road and Sahara Gate. Fabric transport trucks delayed by 48-72 hours. Georgette and Chinon fabric shipments stalled.",
        source: "Surat Local News Feed",
        target: "Surat Ring Road Textile Hub",
      },
      {
        title: "Pandesara Dyeing Mill Power Grid Transformer Failure",
        description:
          "Power failure in Pandesara GIDC dyeing belt halts fabric processing for 3 days. Affected unit: Sachin and Pandesara dyeing and printing lines.",
        source: "Gujarat Industrial Dispatch",
        target: "Pandesara Dyeing Mills",
      },
      {
        title: "Bhagal Lace & Zari Artisan Strike in Old Surat",
        description:
          "Handicraft workers and lace suppliers in Bhagal market stage sudden 4-day strike over wage dispute, halting fancy lace and mirror trim dispatch to garment manufacturing units.",
        source: "Artisan Trade Wire",
        target: "Bhagal Artisan Guild",
      },
    ];
  }

  // 3. Dynamic generator for any custom business using its actual suppliers
  const suppliers = catalog?.suppliers || [];
  if (suppliers.length > 0) {
    return suppliers.slice(0, 4).map((s, idx) => {
      const city = s.city || s.country || "Regional";
      const scenarios = [
        {
          suffix: "Severe Logistics Hub Gridlock & Dispatch Halt",
          desc: `Major regional freight disruption and terminal congestion near ${city} has halted outgoing component shipments from ${s.name} for 48-72 hours.`,
        },
        {
          suffix: "Industrial Belt Substation Power Grid Failure",
          desc: `Power substation breakdown in ${city} has temporarily shut down operations at ${s.name}, delaying scheduled production deliveries.`,
        },
        {
          suffix: "Corridor Heavy Weather & Highway Freight Blockade",
          desc: `Severe adverse weather conditions around ${city} have blocked key arterial supply routes used by ${s.name}.`,
        },
        {
          suffix: "Local Transport Labor Dispute & Gate Stoppage",
          desc: `Wildcat transport labor dispute near ${city} has halted vehicle dispatches from ${s.name} to central assembly plants.`,
        },
      ];
      const sc = scenarios[idx % scenarios.length];
      return {
        title: `${city}: ${sc.suffix}`,
        description: sc.desc,
        source: `${city} Commercial News`,
        target: s.name,
      };
    });
  }

  return [
    {
      title: "Regional Highway Freight Corridor Congestion",
      description:
        "Severe logistics delays reported across main arterial supply routes affecting component deliveries.",
      source: "National Logistics Dispatch",
      target: "All Active Suppliers",
    },
  ];
}

export default function IncidentRadarPage({
  onNavigateToSimulator,
  onOpenWorkspaceModal,
}: IncidentRadarPageProps) {
  const [catalog, setCatalog] = useState<SupplyChainCatalog | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [source, setSource] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const cat = await getSupplyChainCatalog();
      setCatalog(cat);
      const presets = getPresetsForBusiness(cat);
      if (presets.length > 0) {
        setTitle(presets[0].title);
        setDescription(presets[0].description);
        setSource(presets[0].source);
      }
    } catch (err) {
      console.warn("Failed to load catalog for incident radar:", err);
    }
  }, []);

  useEffect(() => {
    void loadData();

    const handleWorkspaceChange = () => {
      void loadData();
      setResult(null);
      setError(null);
    };

    window.addEventListener("atmograph:workspace-changed", handleWorkspaceChange);
    return () => {
      window.removeEventListener("atmograph:workspace-changed", handleWorkspaceChange);
    };
  }, [loadData]);

  const presets = getPresetsForBusiness(catalog);
  const activeCompany = catalog?.company;

  const handleAnalyze = async () => {
    if (!title.trim() || !description.trim()) {
      setError("Please enter both an incident headline and description.");
      return;
    }

    setAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeNews(title, description, source, true);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze incident.");
    } finally {
      setAnalyzing(false);
    }
  };

  const selectPreset = (preset: IncidentPreset) => {
    setTitle(preset.title);
    setDescription(preset.description);
    setSource(preset.source);
    setResult(null);
    setError(null);
  };

  const businessImpact =
    result?.business_supply_chain ?? result?.data?.business_supply_chain;
  const matchedSuppliers =
    result?.matched_suppliers ?? businessImpact?.matched_suppliers ?? [];

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header-row">
        <div className="page-headline">
          <span className="eyebrow-tag">DISRUPTION INTELLIGENCE RADAR</span>
          <h2>Real-Time Incident & News Scanner</h2>
          <p>
            Scan breaking news, port bulletins, or weather disruptions. The AI engine extracts affected suppliers for{" "}
            <strong style={{ color: "#ececef" }}>
              {activeCompany?.company_name || "Active Business"}
            </strong>{" "}
            and predicts upstream/downstream ripple effects.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 14px",
              borderRadius: "9999px",
              background: "rgba(232, 168, 56, 0.12)",
              border: "1px solid rgba(232, 168, 56, 0.3)",
              fontSize: "12px",
              color: "#e8a838",
              fontWeight: 600,
            }}
          >
            <Building2 size={14} />
            <span>
              {activeCompany?.company_name
                ? activeCompany.company_name.length > 25
                  ? activeCompany.company_name.slice(0, 25) + "..."
                  : activeCompany.company_name
                : "Active Business"}
            </span>
            <span style={{ color: "#8e8e96", fontWeight: 400 }}>
              ({activeCompany?.industry || "Supply Chain"})
            </span>
          </div>

          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 12px",
              borderRadius: "9999px",
              background: "rgba(61, 214, 140, 0.1)",
              border: "1px solid rgba(61, 214, 140, 0.25)",
              fontSize: "11.5px",
              color: "#3dd68c",
              fontWeight: 600,
            }}
          >
            <Radio size={14} className="sc-spin" style={{ animationDuration: "3s" }} />
            Radar Active
          </span>
        </div>
      </div>

      {/* Preset Scenarios Selector Scoped to Active Business */}
      <div className="modern-card" style={{ padding: "18px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Sparkles size={16} color="#e8a838" />
            <strong style={{ fontSize: "13px", color: "#ececef" }}>
              Quick Scenario Presets for {activeCompany?.company_name || "Active Business"}:
            </strong>
          </div>
          <span style={{ fontSize: "11px", color: "#8e8e96" }}>
            Dynamically generated from {catalog?.suppliers?.length || 0} active suppliers
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "10px" }}>
          {presets.map((p, idx) => {
            const isSelected = title === p.title;
            return (
              <button
                key={idx}
                onClick={() => selectPreset(p)}
                style={{
                  textAlign: "left",
                  padding: "12px 14px",
                  background: isSelected
                    ? "rgba(232, 168, 56, 0.12)"
                    : "rgba(255, 255, 255, 0.02)",
                  border: isSelected
                    ? "1px solid rgba(232, 168, 56, 0.45)"
                    : "1px solid rgba(255, 255, 255, 0.07)",
                  borderRadius: "8px",
                  transition: "all 0.2s",
                  cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "6px" }}>
                  <strong
                    style={{
                      fontSize: "12px",
                      color: isSelected ? "#f0b848" : "#ececef",
                      display: "block",
                      lineHeight: 1.35,
                    }}
                  >
                    {p.title}
                  </strong>
                </div>

                {p.target && (
                  <div
                    style={{
                      color: "#4ade80",
                      fontSize: "10.5px",
                      marginTop: "6px",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    <Truck size={11} />
                    <span>Affects: {p.target}</span>
                  </div>
                )}

                <small
                  style={{
                    color: "#8e8e96",
                    fontSize: "10px",
                    marginTop: "4px",
                    display: "block",
                  }}
                >
                  Source: {p.source}
                </small>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2-Column: Input Form + Analysis Result */}
      <div className="main-grid">
        {/* Left: Input Form */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">INCIDENT INGESTION</span>
              <h3>Disruption Event Details</h3>
            </div>
            <Newspaper size={18} color="#e8a838" />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div>
              <label
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "#8e8e96",
                  textTransform: "uppercase",
                  display: "block",
                  marginBottom: 6,
                }}
              >
                Incident Headline / Title
              </label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Kannauj Distillation Belt Flooding & Sandalwood Base Delay..."
                style={{
                  width: "100%",
                  background: "#0e0e10",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  color: "#ececef",
                  fontSize: "13px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div>
              <label
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "#8e8e96",
                  textTransform: "uppercase",
                  display: "block",
                  marginBottom: 6,
                }}
              >
                Full Description & Context
              </label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the disruption, locations, suppliers, affected goods, estimated delay..."
                style={{
                  width: "100%",
                  background: "#0e0e10",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  color: "#ececef",
                  fontSize: "13px",
                  outline: "none",
                  resize: "vertical",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div>
              <label
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "#8e8e96",
                  textTransform: "uppercase",
                  display: "block",
                  marginBottom: 6,
                }}
              >
                Intelligence Source
              </label>
              <input
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="e.g. Regional Commercial Gazette, Trade Notice..."
                style={{
                  width: "100%",
                  background: "#0e0e10",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  color: "#ececef",
                  fontSize: "13px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            {error && (
              <div
                style={{
                  padding: "10px 14px",
                  background: "rgba(232, 93, 93, 0.1)",
                  border: "1px solid rgba(232, 93, 93, 0.25)",
                  borderRadius: "8px",
                  color: "#f87171",
                  fontSize: "12px",
                }}
              >
                {error}
              </div>
            )}

            <button
              className="primary-action-btn"
              disabled={analyzing}
              onClick={handleAnalyze}
              style={{
                width: "100%",
                justifyContent: "center",
                padding: "12px",
                marginTop: "4px",
                cursor: analyzing ? "not-allowed" : "pointer",
              }}
            >
              {analyzing ? (
                <>
                  <Loader2 size={16} className="sc-spin" />
                  Analyzing Disruption Impact...
                </>
              ) : (
                <>
                  <Send size={16} />
                  Analyze Disruption & Calculate Ripple Effect
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Analysis & Ripple Results */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">RADAR INTELLIGENCE</span>
              <h3>Impact & Entity Resolution</h3>
            </div>
            {result ? (
              <span
                style={{
                  color: "#3dd68c",
                  fontSize: "12px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <CheckCircle2 size={15} /> Analysis Complete
              </span>
            ) : (
              <Clock size={16} color="#8e8e96" />
            )}
          </div>

          {!result ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                color: "#8e8e96",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <Radio size={36} color="#2b2d31" />
              <div>
                <strong style={{ display: "block", color: "#ececef", marginBottom: "4px" }}>
                  Awaiting Incident Scan
                </strong>
                <p style={{ margin: 0, fontSize: "12px", maxWidth: "340px", lineHeight: 1.5 }}>
                  Select one of the business scenario presets above or type a breaking notice to resolve affected suppliers and simulate business shock waves.
                </p>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Event Meta summary */}
              <div
                style={{
                  padding: "14px 16px",
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "8px",
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                  gap: "12px",
                }}
              >
                <div>
                  <span style={{ fontSize: "10px", color: "#8e8e96", textTransform: "uppercase", display: "block" }}>
                    Detected Event Type
                  </span>
                  <strong style={{ fontSize: "12.5px", color: "#ececef" }}>
                    {result?.event?.event_type ?? result?.nlp?.event_type ?? "Supply Chain Shock"}
                  </strong>
                </div>

                <div>
                  <span style={{ fontSize: "10px", color: "#8e8e96", textTransform: "uppercase", display: "block" }}>
                    Assessed Severity
                  </span>
                  <span
                    style={{
                      display: "inline-block",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      marginTop: "2px",
                      background:
                        result?.event?.severity === "critical"
                          ? "rgba(232, 93, 93, 0.15)"
                          : result?.event?.severity === "high"
                          ? "rgba(232, 168, 56, 0.15)"
                          : "rgba(61, 214, 140, 0.15)",
                      color:
                        result?.event?.severity === "critical"
                          ? "#f87171"
                          : result?.event?.severity === "high"
                          ? "#f0b848"
                          : "#3dd68c",
                    }}
                  >
                    {result?.event?.severity ?? "Medium"}
                  </span>
                </div>

                <div>
                  <span style={{ fontSize: "10px", color: "#8e8e96", textTransform: "uppercase", display: "block" }}>
                    Detected Location
                  </span>
                  <strong style={{ fontSize: "12.5px", color: "#ececef" }}>
                    {typeof result?.event?.location === "string"
                      ? result.event.location
                      : typeof result?.location?.primary_location?.name === "string"
                      ? result.location.primary_location.name
                      : typeof result?.nlp?.entities?.location === "string"
                      ? result.nlp.entities.location
                      : "Identified Hub"}
                  </strong>
                </div>

                <div>
                  <span style={{ fontSize: "10px", color: "#8e8e96", textTransform: "uppercase", display: "block" }}>
                    Company Scoped
                  </span>
                  <strong style={{ fontSize: "12.5px", color: "#e8a838" }}>
                    {activeCompany?.company_name ? activeCompany.company_name.slice(0, 20) : "Active Account"}
                  </strong>
                </div>
              </div>

              {/* Matched Suppliers */}
              <div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#8e8e96",
                    textTransform: "uppercase",
                    display: "block",
                    marginBottom: "8px",
                  }}
                >
                  Affected Suppliers Resolved ({matchedSuppliers.length})
                </span>

                {matchedSuppliers.length === 0 ? (
                  <div
                    style={{
                      padding: "12px",
                      background: "rgba(232, 168, 56, 0.08)",
                      border: "1px solid rgba(232, 168, 56, 0.2)",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "#f0b848",
                    }}
                  >
                    No direct supplier name match found for this incident text. Try using one of the preset scenarios or mentioning a supplier city (e.g. Kannauj, Mumbai, Firozabad, Ahmedabad).
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {matchedSuppliers.map((sup: any, idx: number) => {
                      const supId = sup.supplier_id ?? sup.id ?? "";
                      const supName = sup.name ?? sup.supplier_name ?? "Supplier";
                      return (
                        <div
                          key={idx}
                          style={{
                            padding: "10px 14px",
                            background: "rgba(255, 255, 255, 0.03)",
                            border: "1px solid rgba(255, 255, 255, 0.08)",
                            borderRadius: "8px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                          }}
                        >
                          <div>
                            <strong style={{ fontSize: "12.5px", color: "#ececef", display: "block" }}>
                              {supName}
                            </strong>
                            <small style={{ color: "#8e8e96", fontSize: "11px" }}>
                              ID: {supId} {sup.city ? `· Location: ${sup.city}` : ""}
                            </small>
                          </div>

                          <button
                            className="secondary-btn"
                            onClick={() => onNavigateToSimulator(supId)}
                            style={{
                              padding: "5px 10px",
                              fontSize: "11px",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            <span>Simulate Impact</span>
                            <ArrowRight size={12} />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Simulation ripple impact snippet */}
              {businessImpact && (
                <div
                  style={{
                    padding: "16px",
                    background: "linear-gradient(135deg, rgba(232, 168, 56, 0.08) 0%, rgba(18, 22, 32, 0.95) 100%)",
                    border: "1px solid rgba(232, 168, 56, 0.3)",
                    borderRadius: "10px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <Zap size={16} color="#e8a838" />
                      <strong style={{ fontSize: "13px", color: "#f0b848" }}>
                        Automatic Business Ripple Shock Summary
                      </strong>
                    </div>
                    {matchedSuppliers.length > 0 && (
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: "rgba(239, 68, 68, 0.2)",
                          color: "#f87171",
                          border: "1px solid rgba(239, 68, 68, 0.35)",
                        }}
                      >
                        {matchedSuppliers.length} Supplier Disruption Active
                      </span>
                    )}
                  </div>

                  {/* Summary Metric Chips */}
                  {businessImpact.summary && typeof businessImpact.summary === "object" ? (
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "8px", marginBottom: "12px" }}>
                      <div style={{ padding: "8px 10px", background: "rgba(0,0,0,0.35)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <span style={{ fontSize: "10px", color: "#8e8e96", display: "block" }}>AFFECTED COMPONENTS</span>
                        <strong style={{ fontSize: "14px", color: "#f8fafc" }}>{businessImpact.summary.affected_components ?? 0}</strong>
                      </div>
                      <div style={{ padding: "8px 10px", background: "rgba(0,0,0,0.35)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <span style={{ fontSize: "10px", color: "#8e8e96", display: "block" }}>PLANTS AT RISK</span>
                        <strong style={{ fontSize: "14px", color: businessImpact.summary.production_stop ? "#f87171" : "#fbbf24" }}>
                          {businessImpact.summary.affected_plants ?? 0} {businessImpact.summary.production_stop ? "(HALT)" : ""}
                        </strong>
                      </div>
                      <div style={{ padding: "8px 10px", background: "rgba(0,0,0,0.35)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <span style={{ fontSize: "10px", color: "#8e8e96", display: "block" }}>AFFECTED PRODUCTS</span>
                        <strong style={{ fontSize: "14px", color: "#38bdf8" }}>{businessImpact.summary.affected_products ?? 0} SKUs</strong>
                      </div>
                      <div style={{ padding: "8px 10px", background: "rgba(0,0,0,0.35)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <span style={{ fontSize: "10px", color: "#8e8e96", display: "block" }}>MAX DELAY</span>
                        <strong style={{ fontSize: "14px", color: "#f0b848" }}>+{businessImpact.summary.max_delay_days ?? 0} Days</strong>
                      </div>
                    </div>
                  ) : null}

                  <p style={{ margin: 0, fontSize: "12px", color: "#ececef", lineHeight: 1.5 }}>
                    {typeof businessImpact.narrative === "string"
                      ? businessImpact.narrative
                      : typeof businessImpact.summary === "string"
                      ? businessImpact.summary
                      : "Supply shock successfully evaluated against business manufacturing dependencies and inventory buffers."}
                  </p>

                  {matchedSuppliers.length > 0 && (
                    <div style={{ marginTop: "12px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      <button
                        className="secondary-btn"
                        onClick={() => onNavigateToSimulator(matchedSuppliers[0]?.supplier_id || matchedSuppliers[0]?.id)}
                        style={{
                          padding: "6px 12px",
                          fontSize: "11.5px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          color: "#f0b848",
                          borderColor: "rgba(232, 168, 56, 0.4)",
                          cursor: "pointer",
                        }}
                      >
                        <Zap size={13} />
                        <span>Run Full Deep-Dive Simulation</span>
                        <ArrowRight size={12} />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

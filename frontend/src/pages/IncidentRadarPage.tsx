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
  initialEvent?: {
    id?: number;
    title?: string;
    description?: string;
    source?: string;
    activatedAt?: number;
  } | null;
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
  initialEvent,
  onNavigateToSimulator,
  onOpenWorkspaceModal,
}: IncidentRadarPageProps) {
  const [catalog, setCatalog] = useState<SupplyChainCatalog | null>(null);
  const [title, setTitle] = useState(initialEvent?.title || "");
  const [description, setDescription] = useState(initialEvent?.description || "");
  const [source, setSource] = useState(initialEvent?.source || "");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const cat = await getSupplyChainCatalog();
      setCatalog(cat);
      if (initialEvent && initialEvent.title) {
        setTitle(initialEvent.title);
        setDescription(initialEvent.description || "");
        setSource(initialEvent.source || "Historical Incident Archive");
        return;
      }
      const presets = getPresetsForBusiness(cat);
      if (presets.length > 0) {
        setTitle(presets[0].title);
        setDescription(presets[0].description);
        setSource(presets[0].source);
      }
    } catch (err) {
      console.warn("Failed to load catalog for incident radar:", err);
    }
  }, [initialEvent]);

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

  // When an event is activated from History, auto-load and auto-analyze it!
  useEffect(() => {
    if (initialEvent && initialEvent.title) {
      const activeTitle = initialEvent.title;
      const activeDesc = initialEvent.description || "";
      const activeSrc = initialEvent.source || "Historical Incident Archive";

      setTitle(activeTitle);
      setDescription(activeDesc);
      setSource(activeSrc);
      setResult(null);
      setError(null);

      void (async () => {
        setAnalyzing(true);
        try {
          const res = await analyzeNews(
            activeTitle.trim(),
            activeDesc.trim(),
            activeSrc,
            true
          );
          setResult(res);
        } catch (e: any) {
          setError(e?.message || "Failed to analyze activated incident.");
        } finally {
          setAnalyzing(false);
        }
      })();
    }
  }, [initialEvent]);

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
      const src = source.trim() || "Manual Incident Report";
      const response = await analyzeNews(title.trim(), description.trim(), src, true);
      setResult(response);
    } catch (err: any) {
      let msg = err instanceof Error ? err.message : String(err);
      if (typeof msg !== "string" || msg.includes("[object")) {
        msg = "Failed to analyze incident. Please check your connection or details.";
      }
      setError(msg);
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
    businessImpact?.matched_suppliers ?? result?.matched_suppliers ?? [];

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header-row">
        <div className="page-headline">
          <span className="eyebrow-tag">LIVE ALERTS & NEWS</span>
          <h2>Live News & Disruption Alerts</h2>
          <p>
            Check breaking news, weather, or port delays. The system automatically finds which suppliers are affected for{" "}
            <strong style={{ color: "#0f172a" }}>
              {activeCompany?.company_name || "Active Business"}
            </strong>{" "}
            and shows what happens to your deliveries.
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
              background: "rgba(37, 99, 235, 0.08)",
              border: "1px solid rgba(37, 99, 235, 0.2)",
              fontSize: "12px",
              color: "#2563eb",
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
            <span style={{ color: "#64748b", fontWeight: 400 }}>
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
              background: "rgba(22, 163, 74, 0.1)",
              border: "1px solid rgba(22, 163, 74, 0.25)",
              fontSize: "11.5px",
              color: "#16a34a",
              fontWeight: 600,
            }}
          >
            <Radio size={14} className="sc-spin" style={{ animationDuration: "3s" }} />
            Scanner Active
          </span>
        </div>
      </div>

      {/* Preset Scenarios Selector Scoped to Active Business */}
      <div className="modern-card" style={{ padding: "18px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Sparkles size={16} color="#2563eb" />
            <strong style={{ fontSize: "13px", color: "#0f172a" }}>
              Click an Example Alert to Test ({activeCompany?.company_name || "Active Business"}):
            </strong>
          </div>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Based on {catalog?.suppliers?.length || 0} active suppliers
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
                    ? "rgba(37, 99, 235, 0.08)"
                    : "#ffffff",
                  border: isSelected
                    ? "2px solid #2563eb"
                    : "1px solid #e2e8f0",
                  borderRadius: "8px",
                  transition: "all 0.2s",
                  cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "6px" }}>
                  <strong
                    style={{
                      fontSize: "12.5px",
                      color: isSelected ? "#2563eb" : "#0f172a",
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
                      color: "#16a34a",
                      fontSize: "11px",
                      marginTop: "6px",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      fontWeight: 500,
                    }}
                  >
                    <Truck size={11} />
                    <span>Affects: {p.target}</span>
                  </div>
                )}

                <small
                  style={{
                    color: "#64748b",
                    fontSize: "11px",
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
              <span className="panel-kicker">INCIDENT DETAILS</span>
              <h3>Alert Information</h3>
            </div>
            <Newspaper size={18} color="#2563eb" />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {initialEvent && initialEvent.title && (
              <div
                style={{
                  background: "#eff6ff",
                  border: "1px solid #bfdbfe",
                  borderRadius: "8px",
                  padding: "10px 12px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#1e40af" }}>
                  <CheckCircle2 size={16} color="#2563eb" style={{ flexShrink: 0 }} />
                  <span>
                    <strong>Loaded from Incident History:</strong> {initialEvent.title}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 600,
                    background: "#dbeafe",
                    color: "#1d4ed8",
                    padding: "2px 8px",
                    borderRadius: "6px",
                    whiteSpace: "nowrap",
                  }}
                >
                  Active Incident
                </span>
              </div>
            )}
            <div>
              <label
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "#64748b",
                  textTransform: "uppercase",
                  display: "block",
                  marginBottom: 6,
                }}
              >
                Alert Headline / Title
              </label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Flood near factory or port delay..."
                style={{
                  width: "100%",
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  color: "#0f172a",
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
                  color: "#64748b",
                  textTransform: "uppercase",
                  display: "block",
                  marginBottom: 6,
                }}
              >
                Description & What Happened
              </label>
              <textarea
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the delay, location, suppliers, parts affected, or days of delay..."
                style={{
                  width: "100%",
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  color: "#0f172a",
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
                  color: "#64748b",
                  textTransform: "uppercase",
                  display: "block",
                  marginBottom: 6,
                }}
              >
                News Source
              </label>
              <input
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="e.g. Local News, Supplier Notice, Highway Report..."
                style={{
                  width: "100%",
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  color: "#0f172a",
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
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: "8px",
                  color: "#b91c1c",
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
                background: "#2563eb",
                color: "#ffffff",
                cursor: analyzing ? "not-allowed" : "pointer",
              }}
            >
              {analyzing ? (
                <>
                  <Loader2 size={16} className="sc-spin" />
                  Checking Disruption Impact...
                </>
              ) : (
                <>
                  <Send size={16} />
                  Check Disruption Impact
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Analysis & Ripple Results */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">IMPACT RESULTS</span>
              <h3>How It Affects Your Business</h3>
            </div>
            {result ? (
              <span
                style={{
                  color: "#16a34a",
                  fontSize: "12px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                  fontWeight: 600,
                }}
              >
                <CheckCircle2 size={15} /> Check Complete
              </span>
            ) : (
              <Clock size={16} color="#64748b" />
            )}
          </div>

          {!result ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                color: "#64748b",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <Radio size={36} color="#cbd5e1" />
              <div>
                <strong style={{ display: "block", color: "#0f172a", marginBottom: "4px", fontSize: "15px" }}>
                  Ready to Test an Alert
                </strong>
                <p style={{ margin: 0, fontSize: "13px", maxWidth: "340px", lineHeight: 1.5 }}>
                  Click one of the example alerts above or type news details on the left, then click 'Check Disruption Impact'.
                </p>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Event Meta summary */}
              <div
                style={{
                  padding: "14px 16px",
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                  gap: "12px",
                }}
              >
                <div>
                  <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase", display: "block" }}>
                    Incident Type
                  </span>
                  <strong style={{ fontSize: "13px", color: "#0f172a" }}>
                    {result?.event?.event_type ?? result?.nlp?.event_type ?? "Supply Disruption"}
                  </strong>
                </div>

                <div>
                  <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase", display: "block" }}>
                    Severity Level
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
                          ? "#fee2e2"
                          : result?.event?.severity === "high"
                          ? "#fef3c7"
                          : "#dcfce7",
                      color:
                        result?.event?.severity === "critical"
                          ? "#dc2626"
                          : result?.event?.severity === "high"
                          ? "#d97706"
                          : "#16a34a",
                    }}
                  >
                    {result?.event?.severity ?? "Medium"}
                  </span>
                </div>

                <div>
                  <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase", display: "block" }}>
                    Location
                  </span>
                  <strong style={{ fontSize: "13px", color: "#0f172a" }}>
                    {typeof result?.event?.location === "string"
                      ? result.event.location
                      : typeof result?.location?.primary_location?.name === "string"
                      ? result.location.primary_location.name
                      : typeof result?.nlp?.entities?.location === "string"
                      ? result.nlp.entities.location
                      : "Identified City"}
                  </strong>
                </div>

                <div>
                  <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase", display: "block" }}>
                    Company
                  </span>
                  <strong style={{ fontSize: "13px", color: "#2563eb" }}>
                    {activeCompany?.company_name ? activeCompany.company_name.slice(0, 20) : "Active Business"}
                  </strong>
                </div>
              </div>

              {/* Matched Suppliers */}
              <div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#64748b",
                    textTransform: "uppercase",
                    display: "block",
                    marginBottom: "8px",
                  }}
                >
                  Affected Suppliers Found ({matchedSuppliers.length})
                </span>

                {matchedSuppliers.length === 0 ? (
                  <div
                    style={{
                      padding: "16px",
                      background: "#f0fdf4",
                      border: "1px solid #bbf7d0",
                      borderRadius: "8px",
                      fontSize: "13px",
                      color: "#166534",
                      lineHeight: 1.5,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <CheckCircle2 size={16} color="#16a34a" />
                      <strong style={{ fontSize: "13.5px" }}>Your Supply Chain Is Safe</strong>
                    </div>
                    <p style={{ margin: 0, fontSize: "12.5px", color: "#15803d" }}>
                      Good news! None of your 8 registered active suppliers operate in this reported disruption zone. Your factory shipments and inventory are safe.
                    </p>
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
                            padding: "12px 14px",
                            background: "#ffffff",
                            border: "1px solid #fecaca",
                            borderLeft: "4px solid #dc2626",
                            borderRadius: "8px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                          }}
                        >
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <AlertTriangle size={14} color="#dc2626" />
                              <strong style={{ fontSize: "13.5px", color: "#0f172a" }}>
                                {supName}
                              </strong>
                            </div>
                            <div style={{ color: "#64748b", fontSize: "11.5px", marginTop: "3px" }}>
                              ID: {supId} {sup.city ? `· Location: ${sup.city}` : ""}
                            </div>
                          </div>

                          <button
                            className="secondary-btn"
                            onClick={() => onNavigateToSimulator(supId)}
                            style={{
                              padding: "6px 12px",
                              fontSize: "12px",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              background: "#f1f5f9",
                              border: "1px solid #cbd5e1",
                              color: "#0f172a",
                              fontWeight: 600,
                            }}
                          >
                            <span>Test Delay</span>
                            <ArrowRight size={12} />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Simulation ripple impact snippet */}
              {businessImpact && matchedSuppliers.length > 0 && (
                <div
                  style={{
                    padding: "16px",
                    background: "rgba(37, 99, 235, 0.05)",
                    border: "1px solid rgba(37, 99, 235, 0.2)",
                    borderRadius: "10px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <Zap size={16} color="#2563eb" />
                      <strong style={{ fontSize: "13px", color: "#2563eb" }}>
                        How The Delay Spreads (Impact Summary)
                      </strong>
                    </div>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "4px",
                        background: "#fee2e2",
                        color: "#dc2626",
                        border: "1px solid #fecaca",
                      }}
                    >
                      {matchedSuppliers.length} Supplier Disruption Active
                    </span>
                  </div>

                  {/* Summary Metric Chips */}
                  {businessImpact.summary && typeof businessImpact.summary === "object" ? (
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "8px", marginBottom: "12px" }}>
                      <div style={{ padding: "8px 10px", background: "#ffffff", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                        <span style={{ fontSize: "10px", color: "#64748b", display: "block" }}>AFFECTED PARTS</span>
                        <strong style={{ fontSize: "14px", color: "#0f172a" }}>{businessImpact.summary.affected_components ?? 0} Raw Materials</strong>
                      </div>
                      <div style={{ padding: "8px 10px", background: "#ffffff", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                        <span style={{ fontSize: "10px", color: "#64748b", display: "block" }}>FACTORIES AT RISK</span>
                        <strong style={{ fontSize: "14px", color: businessImpact.summary.production_stop ? "#dc2626" : "#d97706" }}>
                          {businessImpact.summary.affected_plants ?? 0} Plants {businessImpact.summary.production_stop ? "(HALT)" : ""}
                        </strong>
                      </div>
                      <div style={{ padding: "8px 10px", background: "#ffffff", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                        <span style={{ fontSize: "10px", color: "#64748b", display: "block" }}>AFFECTED PRODUCTS</span>
                        <strong style={{ fontSize: "14px", color: "#2563eb" }}>{businessImpact.summary.affected_products ?? 0} Items</strong>
                      </div>
                      <div style={{ padding: "8px 10px", background: "#ffffff", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                        <span style={{ fontSize: "10px", color: "#64748b", display: "block" }}>ESTIMATED DELAY</span>
                        <strong style={{ fontSize: "14px", color: "#dc2626" }}>+{businessImpact.summary.max_delay_days ?? 0} Days</strong>
                      </div>
                    </div>
                  ) : null}

                  {/* Plain language explanation */}
                  <div
                    style={{
                      padding: "10px 12px",
                      background: businessImpact.summary?.production_stop ? "#fef2f2" : "#ffffff",
                      borderRadius: "6px",
                      border: `1px solid ${businessImpact.summary?.production_stop ? "#fecaca" : "#e2e8f0"}`,
                      marginBottom: "12px",
                      fontSize: "12.5px",
                      color: businessImpact.summary?.production_stop ? "#991b1b" : "#334155",
                      lineHeight: 1.5,
                    }}
                  >
                    <strong>
                      {businessImpact.summary?.production_stop
                        ? "🚨 PRODUCTION HALT RISK: "
                        : "⚠️ SHIPMENT DELAY ADVISORY: "}
                    </strong>
                    Incoming shipments from{" "}
                    <strong>{matchedSuppliers[0]?.name || "the affected supplier"}</strong>{" "}
                    are stalled. Because these raw material parts are delayed, your downstream manufacturing plants will suffer an estimated{" "}
                    <strong>+{businessImpact.summary?.max_delay_days ?? 0} days delay</strong>.
                  </div>

                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <button
                      className="sc-primary-button"
                      onClick={() => onNavigateToSimulator(matchedSuppliers[0]?.supplier_id || matchedSuppliers[0]?.id)}
                      style={{
                        padding: "8px 16px",
                        fontSize: "12.5px",
                        fontWeight: 600,
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        background: "#2563eb",
                        color: "#ffffff",
                        cursor: "pointer",
                        borderRadius: "6px",
                      }}
                    >
                      <Zap size={14} />
                      <span>Open What-If Simulator To Resolve</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bell,
  BellRing,
  Building2,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  ExternalLink,
  FileSpreadsheet,
  Globe,
  Loader2,
  Newspaper,
  Radio,
  RefreshCw,
  Send,
  Sparkles,
  Truck,
  Zap,
} from "lucide-react";
import { analyzeNews, ingestRssNews, getNewsMonitorStatus } from "../services/api";
import {
  getSupplyChainCatalog,
  type SupplyChainCatalog,
} from "../services/supplyChainApi";

interface MonitorStatusData {
  running: boolean;
  interval_seconds: number;
  feed_source: string;
  feed_url: string;
  total_scans_completed: number;
  last_run_at: string | null;
  last_articles_found: number;
  last_processed_count: number;
  last_skipped_count: number;
  last_failed_count: number;
  recent_detected_articles: Array<{
    title: string;
    description?: string;
    source?: string;
    url?: string;
    published_at?: string;
    detected_at?: string;
    status: string;
    event_id?: number;
    graph_id?: string;
    risk_score?: number;
    risk_level?: string;
    reason?: string;
    relevance_explanation?: string;
    is_business_relevant?: boolean;
  }>;
}

function formatNewsDateTime(dateStr?: string): { date: string; time: string; relative: string } {
  if (!dateStr) return { date: "Live Feed", time: "", relative: "Recent" };
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return { date: String(dateStr), time: "", relative: "" };

    const now = new Date();
    const diffHours = (now.getTime() - d.getTime()) / (1000 * 60 * 60);

    let relative = "";
    if (diffHours < 1) {
      relative = "Just now";
    } else if (diffHours < 24) {
      relative = `${Math.round(diffHours)}h ago`;
    } else {
      const diffDays = Math.round(diffHours / 24);
      relative = `${diffDays}d ago`;
    }

    const date = d.toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
    const time = d.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });

    return { date, time, relative };
  } catch {
    return { date: String(dateStr), time: "", relative: "" };
  }
}

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
  onNavigateToCatalog?: () => void;
}

interface IncidentPreset {
  title: string;
  description: string;
  source: string;
  target?: string;
}

function getPresetsForBusiness(catalog: SupplyChainCatalog | null): IncidentPreset[] {
  const suppliers = catalog?.suppliers || [];
  // If no suppliers are uploaded yet for this business, return no presets!
  if (suppliers.length === 0) {
    return [];
  }

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

  // 3. Dynamic generator for any custom business using its actual registered suppliers
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

export default function IncidentRadarPage({
  initialEvent,
  onNavigateToSimulator,
  onOpenWorkspaceModal,
  onNavigateToCatalog,
}: IncidentRadarPageProps) {
  const [catalog, setCatalog] = useState<SupplyChainCatalog | null>(null);
  const [title, setTitle] = useState(initialEvent?.title || "");
  const [description, setDescription] = useState(initialEvent?.description || "");
  const [source, setSource] = useState(initialEvent?.source || "");
  const [analyzing, setAnalyzing] = useState(false);
  const [scanningRss, setScanningRss] = useState(false);
  const [rssSuccessMessage, setRssSuccessMessage] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Live Crawler Audit State & Desktop Notifications
  const [monitorStatus, setMonitorStatus] = useState<MonitorStatusData | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState<boolean>(() => {
    return (
      typeof window !== "undefined" &&
      "Notification" in window &&
      Notification.permission === "granted"
    );
  });

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
      } else {
        setTitle("");
        setDescription("");
        setSource("");
      }
    } catch (err) {
      console.warn("Failed to load catalog for incident radar:", err);
    }
  }, [initialEvent]);

  const loadMonitorStatus = useCallback(async () => {
    try {
      const resp = await getNewsMonitorStatus();
      const data = resp?.data || resp;
      if (data) {
        setMonitorStatus(data);
      }
    } catch (err) {
      console.warn("Failed to load news monitor status:", err);
    }
  }, []);

  useEffect(() => {
    void loadData();
    void loadMonitorStatus();

    const interval = setInterval(() => {
      void loadMonitorStatus();
    }, 20000);

    const handleWorkspaceChange = () => {
      void loadData();
      void loadMonitorStatus();
      setResult(null);
      setError(null);
      setRssSuccessMessage(null);
    };

    window.addEventListener("atmograph:workspace-changed", handleWorkspaceChange);
    return () => {
      clearInterval(interval);
      window.removeEventListener("atmograph:workspace-changed", handleWorkspaceChange);
    };
  }, [loadData, loadMonitorStatus]);

  const requestNotificationPermission = async () => {
    if (typeof window === "undefined" || !("Notification" in window)) {
      alert("Desktop notifications are not supported on this browser.");
      return;
    }
    try {
      const perm = await Notification.requestPermission();
      if (perm === "granted") {
        setNotificationsEnabled(true);
        new Notification("🚨 AtmoGraph Disruption Alerts Enabled", {
          body: "You will now receive desktop notifications whenever supply chain disruptions are detected!",
        });
      } else {
        setNotificationsEnabled(false);
      }
    } catch (e) {
      console.warn("Error requesting notification permission:", e);
    }
  };

  const triggerDesktopNotification = (newsTitle: string, riskLevel: string, matchedCount: number) => {
    if (
      typeof window !== "undefined" &&
      "Notification" in window &&
      Notification.permission === "granted"
    ) {
      try {
        new Notification(`🚨 AtmoGraph Alert: ${riskLevel} Disruption Detected`, {
          body: `${newsTitle}\nPotential impact on ${matchedCount} supplier(s). Click to view in AtmoGraph.`,
        });
      } catch (e) {
        console.warn("Desktop notification trigger failed:", e);
      }
    }
  };

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

  const handleScanRss = async () => {
    setScanningRss(true);
    setRssSuccessMessage(null);
    setError(null);
    try {
      const resp = await ingestRssNews(5, true);
      const data = resp?.data || resp;
      const count = data?.processed_count ?? data?.articles_found ?? 0;
      setRssSuccessMessage(
        `Scanned live Google News RSS feeds successfully (${count} articles processed/updated).`
      );
      void loadData();
      void loadMonitorStatus();

      if (count > 0 && notificationsEnabled) {
        triggerDesktopNotification(
          "Live Web News Disruption Detected",
          "HIGH",
          count
        );
      }
    } catch (err: any) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Failed to scan web feeds: ${msg}`);
    } finally {
      setScanningRss(false);
    }
  };

  const loadArticleToTest = (art: {
    title: string;
    source?: string;
    url?: string;
    description?: string;
  }) => {
    setTitle(art.title);
    setDescription(
      art.description ||
        `Breaking supply chain disruption alert received via live feed (${art.source || "Google News Wire"}): ${art.title}`
    );
    setSource(art.source || "Google News Live Wire");
    setResult(null);
    setError(null);

    void (async () => {
      setAnalyzing(true);
      try {
        const src = art.source || "Google News Live Wire";
        const desc =
          art.description ||
          `Breaking supply chain disruption alert received via live feed (${art.source || "Google News Wire"}): ${art.title}`;
        const response = await analyzeNews(art.title.trim(), desc.trim(), src, true);
        setResult(response);
      } catch (err: any) {
        setError(err instanceof Error ? err.message : "Failed to analyze incident.");
      } finally {
        setAnalyzing(false);
      }
    })();
  };

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

    // Auto-analyze immediately for instant 1-click feedback
    void (async () => {
      setAnalyzing(true);
      try {
        const src = preset.source.trim() || "Incident Wire";
        const response = await analyzeNews(preset.title.trim(), preset.description.trim(), src, true);
        setResult(response);
      } catch (err: any) {
        let msg = err instanceof Error ? err.message : String(err);
        if (typeof msg !== "string" || msg.includes("[object")) {
          msg = "Failed to analyze incident. Please check your backend connection.";
        }
        setError(msg);
      } finally {
        setAnalyzing(false);
      }
    })();
  };

  const businessImpact =
    result?.business_supply_chain ?? result?.data?.business_supply_chain;
  const matchedSuppliers =
    businessImpact?.matched_suppliers ?? result?.matched_suppliers ?? [];

  const uniqueCities = Array.from(
    new Set(
      (catalog?.suppliers || [])
        .map((s) => s.city?.split(",")[0]?.split("/")[0]?.trim())
        .filter((c): c is string => Boolean(c && c.length > 2))
    )
  ).slice(0, 5);

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

          <button
            type="button"
            onClick={() => void handleScanRss()}
            disabled={scanningRss}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              borderRadius: "9999px",
              background: scanningRss ? "#64748b" : "#0f172a",
              border: "1px solid #1e293b",
              fontSize: "12px",
              color: "#ffffff",
              fontWeight: 600,
              cursor: scanningRss ? "not-allowed" : "pointer",
              transition: "all 0.2s ease",
            }}
            title="Fetch and scan live Google News RSS feeds now"
          >
            <RefreshCw size={13} className={scanningRss ? "sc-spin" : ""} />
            <span>{scanningRss ? "Scanning Live Feeds..." : "Scan Web Feeds"}</span>
          </button>

          <button
            type="button"
            onClick={() => void requestNotificationPermission()}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              borderRadius: "9999px",
              background: notificationsEnabled ? "rgba(16, 185, 129, 0.1)" : "#f1f5f9",
              border: notificationsEnabled
                ? "1px solid rgba(16, 185, 129, 0.3)"
                : "1px solid #cbd5e1",
              fontSize: "12px",
              color: notificationsEnabled ? "#059669" : "#475569",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            title="Receive desktop notification popups when disruptions are detected even when outside this tab"
          >
            {notificationsEnabled ? (
              <BellRing size={13} color="#059669" />
            ) : (
              <Bell size={13} />
            )}
            <span>{notificationsEnabled ? "Desktop Alerts ON" : "Enable Desktop Alerts"}</span>
          </button>
        </div>
      </div>

      {/* RSS Ingestion Feedback Notification */}
      {rssSuccessMessage && (
        <div
          style={{
            margin: "0 0 16px",
            padding: "10px 16px",
            borderRadius: "8px",
            background: "rgba(22, 163, 74, 0.08)",
            border: "1px solid rgba(22, 163, 74, 0.2)",
            color: "#16a34a",
            fontSize: "13px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <CheckCircle2 size={16} />
          <span>{rssSuccessMessage}</span>
        </div>
      )}

      {/* Business Scoping Guarantee Banner */}
      <div
        style={{
          padding: "12px 18px",
          marginBottom: "16px",
          borderRadius: "10px",
          background: "linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(30, 64, 175, 0.04) 100%)",
          border: "1px solid rgba(37, 99, 235, 0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: "13px",
          flexWrap: "wrap",
          gap: "10px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#1e40af" }}>
          <Sparkles size={16} color="#2563eb" />
          <span>
            <strong>Targeted specifically to:</strong>{" "}
            <strong>{activeCompany?.company_name || "Active Business"}</strong> ({activeCompany?.industry || "Supply Chain"})
          </span>
        </div>
        <div style={{ color: "#475569", fontSize: "12.5px" }}>
          📍 Monitored Supplier Hubs:{" "}
          <strong style={{ color: "#0f172a" }}>
            {uniqueCities.length > 0
              ? uniqueCities.join(", ")
              : (catalog?.suppliers?.length || 0) > 0
              ? "All Registered Supplier Cities"
              : "No Suppliers Registered Yet (0 hubs)"}
          </strong>
        </div>
      </div>

      {/* Hero Section: Live Disruption Alerts Cards Feed */}
      <div className="modern-card" style={{ padding: "18px 20px", marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px", flexWrap: "wrap", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <AlertTriangle size={18} color="#dc2626" />
            <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 700, color: "#0f172a" }}>
              Live Disruption Alerts for {activeCompany?.company_name || "Your Business"}
            </h3>
            <span style={{ fontSize: "11px", fontWeight: 700, padding: "2px 8px", borderRadius: "9999px", background: "#fee2e2", color: "#dc2626" }}>
              {(catalog?.suppliers?.length || 0) === 0 ? 0 : (monitorStatus?.recent_detected_articles?.length || 0)} Alerts Active
            </span>
          </div>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Click any alert below to see the complete impact breakdown and action plan
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "12px" }}>
          {(catalog?.suppliers?.length || 0) === 0 ? (
            <div
              style={{
                gridColumn: "1 / -1",
                padding: "36px 20px",
                textAlign: "center",
                background: "#f8fafc",
                borderRadius: "12px",
                border: "1px dashed #cbd5e1",
              }}
            >
              <div
                style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "50%",
                  background: "#eff6ff",
                  color: "#2563eb",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 12px",
                }}
              >
                <Truck size={24} />
              </div>
              <h4 style={{ margin: "0 0 6px", fontSize: "16px", fontWeight: 700, color: "#0f172a" }}>
                No Registered Suppliers Yet for {activeCompany?.company_name || "Your Business"}
              </h4>
              <p style={{ margin: "0 0 16px", fontSize: "13px", color: "#64748b", maxWidth: "500px", marginInline: "auto", lineHeight: 1.5 }}>
                AtmoGraph monitors live news, weather, and port status tailored directly to your supply chain hubs. Upload your supplier Excel sheet to activate automated live disruption detection.
              </p>
              <button
                type="button"
                className="primary-action-btn"
                style={{
                  padding: "9px 22px",
                  fontSize: "13px",
                  fontWeight: 600,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
                }}
                onClick={() => (onNavigateToCatalog ? onNavigateToCatalog() : onOpenWorkspaceModal?.())}
              >
                <FileSpreadsheet size={15} />
                <span>Upload Supply Chain Excel</span>
              </button>
            </div>
          ) : monitorStatus?.recent_detected_articles && monitorStatus.recent_detected_articles.length > 0 ? (
            monitorStatus.recent_detected_articles.map((art, idx) => {
              const isSelected = title === art.title;
              return (
                <div
                  key={idx}
                  onClick={() => loadArticleToTest(art)}
                  style={{
                    padding: "16px",
                    background: isSelected ? "rgba(37, 99, 235, 0.05)" : "#ffffff",
                    border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                    borderRadius: "10px",
                    boxShadow: isSelected ? "0 4px 12px rgba(37,99,235,0.12)" : "0 1px 3px rgba(0,0,0,0.04)",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", marginBottom: "8px" }}>
                      <span
                        style={{
                          fontSize: "10.5px",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: art.risk_level === "HIGH" ? "#fee2e2" : "#fef3c7",
                          color: art.risk_level === "HIGH" ? "#dc2626" : "#d97706",
                          textTransform: "uppercase",
                        }}
                      >
                        {art.risk_level === "HIGH" ? "🔴 High Disruption" : "🟡 Moderate Delay"}
                      </span>
                      {(() => {
                        const dt = formatNewsDateTime(art.published_at || art.detected_at);
                        return (
                          <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                            <span style={{ fontSize: "11px", fontWeight: 600, color: "#334155", display: "inline-flex", alignItems: "center", gap: "3px" }}>
                              <Calendar size={11} color="#64748b" />
                              {dt.date}
                            </span>
                            {dt.time && (
                              <span style={{ fontSize: "11px", color: "#64748b", display: "inline-flex", alignItems: "center", gap: "3px" }}>
                                <Clock size={11} color="#64748b" />
                                {dt.time}
                              </span>
                            )}
                            {dt.relative && (
                              <span style={{ fontSize: "10px", fontWeight: 600, padding: "1px 5px", background: "#f1f5f9", borderRadius: "3px", color: "#475569" }}>
                                {dt.relative}
                              </span>
                            )}
                          </div>
                        );
                      })()}
                    </div>

                    <h4 style={{ margin: "0 0 6px", fontSize: "13.5px", fontWeight: 700, color: "#0f172a", lineHeight: 1.4 }}>
                      {art.title}
                    </h4>

                    {art.relevance_explanation && (
                      <div
                        style={{
                          fontSize: "11.5px",
                          fontWeight: 600,
                          color: "#1d4ed8",
                          background: "#eff6ff",
                          padding: "4px 8px",
                          borderRadius: "6px",
                          border: "1px solid #dbeafe",
                          marginBottom: "10px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                        }}
                      >
                        <Truck size={12} /> {art.relevance_explanation}
                      </div>
                    )}

                    {art.description && (
                      <p style={{ margin: "0 0 10px", fontSize: "12px", color: "#475569", lineHeight: 1.45 }}>
                        {art.description.split("\n\n")[0]?.replace("WHAT HAPPENED:\n", "")?.slice(0, 150) + "..."}
                      </p>
                    )}
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      paddingTop: "10px",
                      borderTop: "1px solid #f1f5f9",
                    }}
                  >
                    <span style={{ fontSize: "11px", color: "#64748b" }}>{art.source || "Google News Feed"}</span>
                    <button
                      type="button"
                      style={{
                        padding: "5px 12px",
                        borderRadius: "6px",
                        background: isSelected ? "#2563eb" : "#f1f5f9",
                        color: isSelected ? "#ffffff" : "#2563eb",
                        border: "1px solid rgba(37, 99, 235, 0.2)",
                        fontSize: "11.5px",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      <Zap size={12} />
                      {isSelected ? "Active Incident" : "View Breakdown"}
                    </button>
                  </div>
                </div>
              );
            })
          ) : (
            <div
              style={{
                gridColumn: "1 / -1",
                padding: "30px 20px",
                textAlign: "center",
                background: "#f0fdf4",
                borderRadius: "12px",
                border: "1px solid #bbf7d0",
              }}
            >
              <div
                style={{
                  width: "44px",
                  height: "44px",
                  borderRadius: "50%",
                  background: "#dcfce7",
                  color: "#16a34a",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 10px",
                }}
              >
                <CheckCircle2 size={24} />
              </div>
              <h4 style={{ margin: "0 0 5px", fontSize: "15px", fontWeight: 700, color: "#166534" }}>
                All Monitored Supplier Hubs Clear (Past 72 Hours)
              </h4>
              <p style={{ margin: "0 0 12px", fontSize: "12.5px", color: "#15803d", maxWidth: "540px", marginInline: "auto", lineHeight: 1.5 }}>
                No active transit strikes, severe weather halts, or facility disruptions detected in the last 72 hours for {activeCompany?.company_name || "your active business"}. Google News RSS crawler is continuously inspecting live feeds.
              </p>
              <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", fontSize: "11.5px", color: "#166534", background: "#dcfce7", padding: "4px 14px", borderRadius: "9999px" }}>
                <Clock size={12} />
                <span>Last Verified: {monitorStatus?.last_run_at ? new Date(monitorStatus.last_run_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Live"} • Hubs Monitored: {uniqueCities.slice(0, 3).join(", ") || "All Registered Locations"}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Preset Scenarios Selector Scoped to Active Business */}
      {presets.length > 0 && (
        <div className="modern-card" style={{ padding: "16px 20px", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Sparkles size={16} color="#2563eb" />
              <strong style={{ fontSize: "13px", color: "#0f172a" }}>
                Quick 1-Click Disruption Tests ({activeCompany?.company_name || "Active Business"}):
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
                    padding: "10px 12px",
                    background: isSelected ? "rgba(37, 99, 235, 0.08)" : "#ffffff",
                    border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                    borderRadius: "8px",
                    transition: "all 0.2s",
                    cursor: "pointer",
                  }}
                >
                  <strong style={{ fontSize: "12px", color: isSelected ? "#2563eb" : "#0f172a", display: "block" }}>
                    {p.title}
                  </strong>
                  {p.target && (
                    <div style={{ color: "#16a34a", fontSize: "11px", marginTop: "4px", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                      <Truck size={11} /> Affects: {p.target}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 2-Column: Active Alert Details (with Collapsible Advanced Form) + Analysis Result */}
      <div className="main-grid">
        {/* Left: Active Alert Overview & Advanced Input */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">INCIDENT DETAILS</span>
              <h3>Selected Disruption Alert</h3>
            </div>
            <Newspaper size={18} color="#2563eb" />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {/* Clean summary of current active incident */}
            <div style={{ padding: "14px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
                Active Incident Headline:
              </span>
              <h4 style={{ margin: "4px 0 8px", fontSize: "14px", fontWeight: 700, color: "#0f172a" }}>
                {title || ((catalog?.suppliers?.length || 0) === 0 ? "No Disruption Alert Selected (0 Suppliers)" : "Select an alert or preset above")}
              </h4>
              <p style={{ margin: "0 0 10px", fontSize: "12.5px", color: "#475569", lineHeight: 1.5, whiteSpace: "pre-line" }}>
                {description || ((catalog?.suppliers?.length || 0) === 0 ? "Upload your supplier Excel sheet to activate automated disruption detection, or enter custom incident details in Advanced mode below." : "No description loaded.")}
              </p>
              <div style={{ fontSize: "11.5px", color: "#64748b" }}>
                Source: <strong>{source || "Live Feed"}</strong>
              </div>
            </div>

            <button
              className="primary-action-btn"
              disabled={analyzing}
              onClick={handleAnalyze}
              style={{
                width: "100%",
                justifyContent: "center",
                padding: "12px",
                background: "#2563eb",
                color: "#ffffff",
                cursor: analyzing ? "not-allowed" : "pointer",
                borderRadius: "8px",
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
                  Re-calculate Disruption Impact
                </>
              )}
            </button>

            {/* Collapsible Accordion for Advanced Custom Input & Crawler Logs */}
            <div style={{ border: "1px solid #e2e8f0", borderRadius: "8px", overflow: "hidden", marginTop: "4px" }}>
              <div
                onClick={() => setShowAdvanced(!showAdvanced)}
                style={{
                  padding: "10px 14px",
                  background: "#f8fafc",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  userSelect: "none",
                }}
              >
                <span style={{ fontSize: "12px", fontWeight: 600, color: "#475569" }}>
                  ⚙️ Advanced: Test Custom News & Crawler Audit
                </span>
                {showAdvanced ? <ChevronUp size={15} color="#64748b" /> : <ChevronDown size={15} color="#64748b" />}
              </div>

              {showAdvanced && (
                <div style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "10px", background: "#ffffff" }}>
                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
                      Custom Headline
                    </label>
                    <input
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g. Flooding on highway near factory..."
                      style={{ width: "100%", border: "1px solid #cbd5e1", borderRadius: "6px", padding: "8px 10px", fontSize: "12.5px", boxSizing: "border-box" }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
                      Custom Description
                    </label>
                    <textarea
                      rows={3}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Enter description..."
                      style={{ width: "100%", border: "1px solid #cbd5e1", borderRadius: "6px", padding: "8px 10px", fontSize: "12.5px", boxSizing: "border-box" }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
                      News Source
                    </label>
                    <input
                      value={source}
                      onChange={(e) => setSource(e.target.value)}
                      placeholder="e.g. Supplier Notice..."
                      style={{ width: "100%", border: "1px solid #cbd5e1", borderRadius: "6px", padding: "8px 10px", fontSize: "12.5px", boxSizing: "border-box" }}
                    />
                  </div>

                  <div style={{ fontSize: "11px", color: "#64748b", background: "#f8fafc", padding: "8px", borderRadius: "6px" }}>
                    Crawler Stats: {monitorStatus?.total_scans_completed || 3} scans completed • Feed: Google News RSS
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div style={{ padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "8px", color: "#b91c1c", fontSize: "12px" }}>
                {error}
              </div>
            )}
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
                      Good news! None of your {catalog?.suppliers?.length || "registered"} active suppliers operate in this reported disruption zone. Your factory shipments and inventory are safe.
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

                  {/* Plain language business translation dossier */}
                  <div
                    style={{
                      padding: "12px 14px",
                      background: businessImpact.summary?.production_stop ? "#fef2f2" : "#ffffff",
                      borderRadius: "8px",
                      border: `1px solid ${businessImpact.summary?.production_stop ? "#fecaca" : "#cbd5e1"}`,
                      marginBottom: "12px",
                      fontSize: "12.5px",
                      color: "#1e293b",
                      lineHeight: 1.6,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                      <Sparkles size={15} color="#2563eb" />
                      <strong style={{ fontSize: "13px", color: "#0f172a" }}>
                        Plain-Language Business Impact Breakdown:
                      </strong>
                    </div>

                    <ul style={{ margin: 0, paddingLeft: "18px", display: "flex", flexDirection: "column", gap: "5px" }}>
                      <li>
                        <strong>What happened:</strong> Disruption reported in{" "}
                        <span style={{ color: "#2563eb", fontWeight: 600 }}>
                          {typeof result?.event?.location === "string" ? result.event.location : "supplier corridor"}
                        </span>{" "}
                        delaying raw component dispatches.
                      </li>
                      <li>
                        <strong>Affected Supplier:</strong>{" "}
                        <span style={{ color: "#dc2626", fontWeight: 600 }}>
                          {matchedSuppliers[0]?.name || "Your supplier"}
                        </span>
                      </li>
                      <li>
                        <strong>Expected factory impact:</strong>{" "}
                        <span style={{ color: businessImpact.summary?.production_stop ? "#dc2626" : "#d97706", fontWeight: 600 }}>
                          +{businessImpact.summary?.max_delay_days ?? 0} days estimated delivery delay
                          {businessImpact.summary?.production_stop ? " (Assembly Line Halt)" : ""}
                        </span>
                      </li>
                      <li style={{ color: "#166534" }}>
                        <strong>💡 Recommended Operations Action:</strong> Check existing buffer inventory; consider rerouting via backup supplier or reserving express freight.
                      </li>
                    </ul>
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

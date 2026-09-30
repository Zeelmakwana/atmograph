import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Database,
  FileSpreadsheet,
  FileText,
  Globe2,
  RefreshCw,
  Rss,
  Sparkles,
  Upload,
  Workflow,
  XCircle,
} from "lucide-react";

import {
  getEvents,
  getGraphStatistics,
} from "../services/api";

import {
  getSupplyChainCatalog,
  importSupplyChainFile,
  validateSupplyChainFile,
  type SupplyChainCatalog,
  type SupplyChainImportResult,
  type SupplyChainValidationResult,
} from "../services/supplyChainApi";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";


type EventItem = {
  id: number;
  title: string;
  source?: string;
  event_type?: string;
  severity?: string;
  status?: string;
  created_at?: string;
};


function normalizeEvents(
  result: any
): EventItem[] {

  const data =
    result?.data ?? result;

  const events =
    Array.isArray(data)
      ? data
      : Array.isArray(
          data?.events
        )
        ? data.events
        : [];

  return events.map(
    (event: any) => ({
      id: Number(
        event?.id ?? 0
      ),

      title: String(
        event?.title ??
          "Untitled event"
      ),

      source:
        event?.source ??
        "manual",

      event_type:
        event?.event_type ??
        "unknown",

      severity:
        event?.severity ??
        "medium",

      status:
        event?.status ??
        "active",

      created_at:
        event?.created_at,
    })
  );
}


function sourceLabel(
  source: string
) {

  if (!source) {
    return "Manual";
  }

  if (
    source.toLowerCase() ===
    "manual"
  ) {
    return "Manual Intelligence";
  }

  return source;
}


function sourceIcon(
  source: string
) {

  const value =
    source.toLowerCase();

  if (
    value.includes("manual")
  ) {
    return (
      <FileText size={19} />
    );
  }

  if (
    value.includes("rss") ||
    value.includes("news")
  ) {
    return (
      <Rss size={19} />
    );
  }

  return (
    <Globe2 size={19} />
  );
}


function severityClass(
  severity: string
) {

  const value =
    severity.toLowerCase();

  if (
    value === "critical"
  ) {
    return "critical";
  }

  if (
    value === "high"
  ) {
    return "high";
  }

  if (
    value === "low"
  ) {
    return "low";
  }

  return "medium";
}


function formatNumber(
  value: number
) {
  return value.toLocaleString();
}


export default function DataSources() {

  const [
    events,
    setEvents,
  ] = useState<EventItem[]>(
    []
  );

  const [
    graphStats,
    setGraphStats,
  ] = useState<any>(null);

  const [
    catalog,
    setCatalog,
  ] =
    useState<SupplyChainCatalog | null>(
      null
    );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const [
    selectedFile,
    setSelectedFile,
  ] =
    useState<File | null>(
      null
    );

  const [
    validation,
    setValidation,
  ] =
    useState<SupplyChainValidationResult | null>(
      null
    );

  const [
    importResult,
    setImportResult,
  ] =
    useState<SupplyChainImportResult | null>(
      null
    );

  const [
    uploading,
    setUploading,
  ] = useState(false);

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null
    );


  const loadData =
    useCallback(async () => {

      try {

        setLoading(true);
        setError("");

        const [
          eventsResult,
          statsResult,
          catalogResult,
        ] = await Promise.all([
          getEvents(
            "",
            "",
            "",
            100
          ),

          getGraphStatistics(),

          getSupplyChainCatalog(),
        ]);

        setEvents(
          normalizeEvents(
            eventsResult
          )
        );

        setGraphStats(
          statsResult
        );

        setCatalog(
          catalogResult
        );

      } catch (
        exception
      ) {

        console.error(
          "Data source loading failed:",
          exception
        );

        setError(
          exception instanceof
            Error
            ? exception.message
            : "Unable to load data sources."
        );

      } finally {

        setLoading(false);

      }

    }, []);


  useEffect(() => {
    void loadData();
  }, [loadData]);


  const sourceSummary =
    useMemo(() => {

      const map =
        new Map<
          string,
          number
        >();

      events.forEach(
        (event) => {

          const source =
            sourceLabel(
              event.source ??
                "manual"
            );

          map.set(
            source,
            (map.get(
              source
            ) ?? 0) + 1
          );

        }
      );

      return Array.from(
        map.entries()
      )
        .map(
          ([
            source,
            count,
          ]) => ({
            source,
            count,
          })
        )
        .sort(
          (a, b) =>
            b.count -
            a.count
        );

    }, [events]);


  const activeEvents =
    events.filter(
      (event) =>
        event.status
          ?.toLowerCase() ===
        "active"
    ).length;


  const highRiskEvents =
    events.filter(
      (event) =>
        event.severity
          ?.toLowerCase() ===
          "high" ||
        event.severity
          ?.toLowerCase() ===
          "critical"
    ).length;


  const graphNodes =
    Number(
      graphStats?.data
        ?.total_nodes ??
        graphStats?.total_nodes ??
        0
    );


  const graphRelationships =
    Number(
      graphStats?.data
        ?.total_relationships ??
        graphStats?.total_relationships ??
        0
    );


  const latestEvents =
    [...events]
      .sort(
        (a, b) =>
          Number(b.id) -
          Number(a.id)
      )
      .slice(0, 8);


  function handleFile(
    file: File | undefined
  ) {

    if (!file) {
      return;
    }

    const extension =
      file.name
        .split(".")
        .pop()
        ?.toLowerCase();

    if (
      extension !== "xlsx" &&
      extension !== "xls"
    ) {

      setError(
        "Please select an .xlsx or .xls supply-chain workbook."
      );

      return;
    }

    if (
      file.size >
      25 * 1024 * 1024
    ) {

      setError(
        "File size must be 25 MB or less."
      );

      return;
    }

    setError("");
    setSelectedFile(file);
    setValidation(null);
    setImportResult(null);

  }


  async function handleValidate() {

    if (!selectedFile) {
      return;
    }

    try {

      setUploading(true);
      setError("");
      setImportResult(null);

      const result =
        await validateSupplyChainFile(
          selectedFile
        );

      setValidation(result);

      if (!result.success) {

        setError(
          result.errors.join(
            "\n"
          )
        );
      }

    } catch (
      exception
    ) {

      setError(
        exception instanceof
          Error
          ? exception.message
          : "Validation failed."
      );

    } finally {

      setUploading(false);

    }
  }


  async function handleImport() {

    if (
      !selectedFile ||
      !validation?.success
    ) {
      return;
    }

    try {

      setUploading(true);
      setError("");

      const result =
        await importSupplyChainFile(
          selectedFile
        );

      setImportResult(result);

      await loadData();

    } catch (
      exception
    ) {

      setError(
        exception instanceof
          Error
          ? exception.message
          : "Import failed."
      );

    } finally {

      setUploading(false);

    }
  }


  return (
    <div className="dashboard-content">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="page-heading">

        <div>

          <span className="eyebrow">
            DATA INGESTION
          </span>

          <h2>
            Data Sources
          </h2>

          <p>
            Manage supply-chain datasets and
            monitor AtmoGraph intelligence inputs.
          </p>

        </div>

        <button
          className="primary-button"
          onClick={
            loadData
          }
          disabled={
            loading ||
            uploading
          }
        >

          <RefreshCw
            size={15}
            className={
              loading
                ? "spin"
                : ""
            }
          />

          {loading
            ? "Syncing..."
            : "Refresh"}

        </button>

      </div>


      {error && (
        <div
          className="ripple-error"
          style={{
            whiteSpace:
              "pre-line",
          }}
        >

          <XCircle size={17} />

          <span>
            {error}
          </span>

        </div>
      )}


      {/* =====================================================
          SUPPLY CHAIN DATASET
      ===================================================== */}

      <section
        className="panel"
        style={{
          marginTop: 16,
        }}
      >

        <div className="panel-header">

          <div>

            <span className="panel-kicker">
              SUPPLY CHAIN DATA
            </span>

            <h3>
              Dataset Management
            </h3>

          </div>

          <FileSpreadsheet
            size={18}
          />

        </div>


        <div
          style={{
            padding: 16,
          }}
        >

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              flexWrap: "wrap",
            }}
          >

            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              style={{
                display: "none",
              }}
              onChange={(event) => {

                handleFile(
                  event.target.files?.[0]
                );

                event.target.value =
                  "";

              }}
            />


            <button
              className="primary-button"
              type="button"
              onClick={() =>
                fileInputRef.current?.click()
              }
              disabled={uploading}
            >

              <Upload size={15} />

              Select Excel

            </button>


            <div
              style={{
                flex: 1,
                minWidth: 240,
              }}
            >

              <strong
                style={{
                  display:
                    "block",
                  fontSize: 12,
                }}
              >

                {selectedFile
                  ? selectedFile.name
                  : "No dataset selected"}

              </strong>

              <small
                style={{
                  opacity: 0.55,
                }}
              >

                {selectedFile
                  ? `${(
                      selectedFile.size /
                      1024 /
                      1024
                    ).toFixed(2)} MB`
                  : "Supported: .xlsx / .xls · Maximum 25 MB"}

              </small>

            </div>


            <button
              className="primary-button"
              type="button"
              onClick={
                handleValidate
              }
              disabled={
                !selectedFile ||
                uploading
              }
            >

              <CheckCircle2 size={15} />

              {uploading
                ? "Processing..."
                : "Validate"}

            </button>


            <button
              className="primary-button"
              type="button"
              onClick={
                handleImport
              }
              disabled={
                !selectedFile ||
                !validation?.success ||
                uploading
              }
            >

              <Database size={15} />

              Import Dataset

            </button>

          </div>


          {/* =================================================
              VALIDATION RESULT
          ================================================= */}

          {validation && (
            <div
              style={{
                marginTop: 16,
                padding: 14,
                border:
                  "1px solid rgba(120,150,180,.15)",
                borderRadius: 10,
              }}
            >

              <div
                style={{
                  display:
                    "flex",
                  alignItems:
                    "center",
                  gap: 9,
                  marginBottom: 12,
                }}
              >

                {validation.success ? (
                  <CheckCircle2
                    size={17}
                  />
                ) : (
                  <XCircle
                    size={17}
                  />
                )}

                <strong>

                  {validation.success
                    ? "Dataset validation passed"
                    : "Dataset validation failed"}

                </strong>

              </div>


              <div
                style={{
                  display:
                    "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit,minmax(150px,1fr))",
                  gap: 8,
                }}
              >

                {Object.entries(
                  validation.row_counts
                ).map(
                  ([
                    sheet,
                    count,
                  ]) => (

                    <div
                      key={sheet}
                      style={{
                        padding:
                          "9px 10px",
                        border:
                          "1px solid rgba(120,150,180,.1)",
                        borderRadius: 8,
                      }}
                    >

                      <span
                        style={{
                          display:
                            "block",
                          fontSize: 8,
                          opacity: 0.5,
                        }}
                      >
                        {sheet}
                      </span>

                      <strong
                        style={{
                          fontSize: 13,
                        }}
                      >
                        {formatNumber(
                          count
                        )}
                      </strong>

                    </div>

                  )
                )}

              </div>


              {validation.warnings.length >
                0 && (
                <div
                  style={{
                    marginTop: 12,
                    fontSize: 10,
                    opacity: 0.7,
                  }}
                >

                  <strong>
                    Warnings
                  </strong>

                  {validation.warnings.map(
                    (
                      warning,
                      index
                    ) => (
                      <div
                        key={
                          index
                        }
                      >
                        {warning}
                      </div>
                    )
                  )}

                </div>
              )}


              {validation.errors.length >
                0 && (
                <div
                  style={{
                    marginTop: 12,
                    fontSize: 10,
                  }}
                >

                  <strong>
                    Errors
                  </strong>

                  {validation.errors.map(
                    (
                      validationError,
                      index
                    ) => (
                      <div
                        key={
                          index
                        }
                      >
                        {validationError}
                      </div>
                    )
                  )}

                </div>
              )}

            </div>
          )}


          {/* =================================================
              IMPORT RESULT
          ================================================= */}

          {importResult && (
            <div
              style={{
                marginTop: 12,
                padding: 14,
                border:
                  "1px solid rgba(50,170,130,.22)",
                borderRadius: 10,
                background:
                  "rgba(30,130,105,.08)",
              }}
            >

              <div
                style={{
                  display:
                    "flex",
                  alignItems:
                    "center",
                  gap: 9,
                }}
              >

                <CheckCircle2
                  size={17}
                />

                <strong>
                  Dataset imported successfully
                </strong>

              </div>


              <div
                style={{
                  marginTop: 10,
                  fontSize: 10,
                  opacity: 0.7,
                }}
              >

                PostgreSQL updated and
                Neo4j business graph synchronized.

              </div>


              <div
                style={{
                  display:
                    "flex",
                  gap: 16,
                  marginTop: 12,
                  flexWrap:
                    "wrap",
                  fontSize: 9,
                }}
              >

                <span>
                  Graph Nodes:{" "}
                  <strong>
                    {
                      importResult
                        .neo4j_sync
                        .graph
                        .nodes
                    }
                  </strong>
                </span>

                <span>
                  Relationships:{" "}
                  <strong>
                    {
                      importResult
                        .neo4j_sync
                        .graph
                        .relationships
                    }
                  </strong>
                </span>

              </div>

            </div>
          )}

        </div>

      </section>


      {/* =====================================================
          BUSINESS DATA OVERVIEW
      ===================================================== */}

      {catalog && (
        <section
          className="source-overview-grid"
          style={{
            marginTop: 14,
          }}
        >

          <OverviewCard
            icon={
              <Database size={20} />
            }
            label="SUPPLIERS"
            value={
              catalog.suppliers.length
            }
            description="Business supplier records"
          />

          <OverviewCard
            icon={
              <Workflow size={20} />
            }
            label="PLANTS"
            value={
              catalog.plants.length
            }
            description="Manufacturing locations"
          />

          <OverviewCard
            icon={
              <FileText size={20} />
            }
            label="PRODUCTS"
            value={
              catalog.products.length
            }
            description="Products in dataset"
          />

          <OverviewCard
            icon={
              <Database size={20} />
            }
            label="COMPONENTS"
            value={
              catalog.components.length
            }
            description="Supply components"
          />

        </section>
      )}


      {/* =====================================================
          SOURCE OVERVIEW
      ===================================================== */}

      <section className="source-overview-grid">

        <OverviewCard
          icon={
            <Database size={20} />
          }
          label="INGESTED EVENTS"
          value={
            events.length
          }
          description="Structured intelligence records"
        />

        <OverviewCard
          icon={
            <Activity size={20} />
          }
          label="ACTIVE EVENTS"
          value={
            activeEvents
          }
          description="Currently active disruptions"
        />

        <OverviewCard
          icon={
            <Sparkles size={20} />
          }
          label="HIGH-RISK EVENTS"
          value={
            highRiskEvents
          }
          description="High and critical severity"
        />

        <OverviewCard
          icon={
            <Workflow size={20} />
          }
          label="GRAPH ENTITIES"
          value={
            graphNodes
          }
          description={`${graphRelationships} connected relationships`}
        />

      </section>


      {/* =====================================================
          INGESTION PIPELINE
      ===================================================== */}

      <section className="panel source-pipeline-panel">

        <div className="panel-header">

          <div>

            <span className="panel-kicker">
              INTELLIGENCE PIPELINE
            </span>

            <h3>
              Data Processing Flow
            </h3>

          </div>

          <CheckCircle2 size={18} />

        </div>


        <div className="source-pipeline">

          <PipelineStep
            icon={
              <FileSpreadsheet size={18} />
            }
            number="01"
            title="Excel Dataset"
            description="Company supply-chain data"
          />

          <PipelineArrow />

          <PipelineStep
            icon={
              <CheckCircle2 size={18} />
            }
            number="02"
            title="Validation"
            description="Schema and relationship checks"
          />

          <PipelineArrow />

          <PipelineStep
            icon={
              <Database size={18} />
            }
            number="03"
            title="SQL Database"
            description="Structured business records"
          />

          <PipelineArrow />

          <PipelineStep
            icon={
              <Workflow size={18} />
            }
            number="04"
            title="Neo4j Graph"
            description="Supply-chain relationships"
          />

          <PipelineArrow />

          <PipelineStep
            icon={
              <Activity size={18} />
            }
            number="05"
            title="GNN + Risk"
            description="Impact intelligence"
          />

        </div>

      </section>


      {/* =====================================================
          SOURCE CARDS + LATEST EVENTS
      ===================================================== */}

      <div className="source-main-grid">

        <section className="panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                CONNECTED SOURCES
              </span>

              <h3>
                Source Inventory
              </h3>

            </div>

            <span className="source-count">
              {
                sourceSummary.length
              } sources
            </span>

          </div>


          {sourceSummary.length ===
          0 ? (
            <div className="source-empty">
              No ingestion sources found.
            </div>
          ) : (
            <div className="source-list">

              {sourceSummary.map(
                (
                  item
                ) => (
                  <div
                    className="source-item"
                    key={
                      item.source
                    }
                  >

                    <div className="source-item-icon">
                      {sourceIcon(
                        item.source
                      )}
                    </div>

                    <div className="source-item-content">

                      <strong>
                        {item.source}
                      </strong>

                      <span>
                        {item.count} event
                        {item.count !==
                        1
                          ? "s"
                          : ""} ingested
                      </span>

                    </div>

                    <div className="source-item-status">
                      <span className="status-dot" />
                      ACTIVE
                    </div>

                  </div>
                )
              )}

            </div>
          )}

        </section>


        <section className="panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                RECENT INGESTION
              </span>

              <h3>
                Latest Events
              </h3>

            </div>

            <Clock3 size={18} />

          </div>


          {latestEvents.length ===
          0 ? (
            <div className="source-empty">
              No events available.
            </div>
          ) : (
            <div className="recent-source-events">

              {latestEvents.map(
                (event) => (
                  <div
                    className="recent-source-event"
                    key={
                      event.id
                    }
                  >

                    <div className="recent-source-event-number">
                      #{event.id}
                    </div>

                    <div className="recent-source-event-content">

                      <strong>
                        {event.title}
                      </strong>

                      <span>
                        {sourceLabel(
                          event.source ??
                            "manual"
                        )}
                        {" · "}
                        {event.event_type}
                      </span>

                    </div>

                    <span
                      className={`source-severity ${severityClass(
                        event.severity ??
                          "medium"
                      )}`}
                    >
                      {(
                        event.severity ??
                        "medium"
                      ).toUpperCase()}
                    </span>

                  </div>
                )
              )}

            </div>
          )}

        </section>

      </div>


      {/* =====================================================
          DATA QUALITY
      ===================================================== */}

      <section className="panel source-quality-panel">

        <div className="panel-header">

          <div>

            <span className="panel-kicker">
              DATA QUALITY
            </span>

            <h3>
              Ingestion Integrity
            </h3>

          </div>

          <CheckCircle2 size={18} />

        </div>


        <div className="quality-grid">

          <QualityItem
            title="Event Records"
            value={
              events.length
            }
            description="Successfully stored"
          />

          <QualityItem
            title="Graph Nodes"
            value={
              graphNodes
            }
            description="Available in Neo4j"
          />

          <QualityItem
            title="Graph Links"
            value={
              graphRelationships
            }
            description="Relationships synchronized"
          />

          <QualityItem
            title="Pipeline"
            value="READY"
            description="Excel → SQL → Graph → GNN"
          />

        </div>

      </section>

    </div>
  );
}


/* ============================================================
   SMALL COMPONENTS
============================================================ */

function OverviewCard({
  icon,
  label,
  value,
  description,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  description: string;
}) {
  return (
    <div className="source-overview-card">

      <div className="source-overview-icon">
        {icon}
      </div>

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {description}
      </small>

    </div>
  );
}


function PipelineStep({
  icon,
  number,
  title,
  description,
}: {
  icon: React.ReactNode;
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="pipeline-step">

      <div className="pipeline-step-number">
        {number}
      </div>

      <div className="pipeline-step-icon">
        {icon}
      </div>

      <strong>
        {title}
      </strong>

      <span>
        {description}
      </span>

    </div>
  );
}


function PipelineArrow() {
  return (
    <div className="pipeline-arrow">
      <ArrowRight size={17} />
    </div>
  );
}


function QualityItem({
  title,
  value,
  description,
}: {
  title: string;
  value: string | number;
  description: string;
}) {
  return (
    <div className="quality-item">

      <div>

        <span>
          {title}
        </span>

        <strong>
          {value}
        </strong>

      </div>

      <small>
        {description}
      </small>

    </div>
  );
}
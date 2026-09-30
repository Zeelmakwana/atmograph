import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type DragEvent,
} from "react";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Database,
  Download,
  Factory,
  FileSpreadsheet,
  Layers,
  Loader2,
  Network,
  Package,
  RefreshCw,
  Search,
  Truck,
  UploadCloud,
  Warehouse,
  Zap,
} from "lucide-react";

import {
  getSupplyChainCatalog,
  getTemplateDownloadUrl,
  importSupplyChainFile,
  syncNeo4jGraph,
  validateSupplyChainFile,
  type SupplyChainCatalog,
  type SupplyChainImportResult,
  type SupplyChainValidationResult,
} from "../../services/supplyChainApi";

interface ExcelDataImportProps {
  onSelectSupplierForSimulation?: (supplierId: string) => void;
  onNavigateToGraph?: () => void;
}

type CatalogTab = "suppliers" | "plants" | "components" | "products" | "warehouses";

export default function ExcelDataImport({
  onSelectSupplierForSimulation,
  onNavigateToGraph,
}: ExcelDataImportProps) {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [validating, setValidating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [syncingGraph, setSyncingGraph] = useState(false);

  const [validationResult, setValidationResult] = useState<SupplyChainValidationResult | null>(null);
  const [importResult, setImportResult] = useState<SupplyChainImportResult | null>(null);
  const [catalog, setCatalog] = useState<SupplyChainCatalog | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<CatalogTab>("suppliers");
  const [searchQuery, setSearchQuery] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadCatalog = useCallback(async () => {
    try {
      setCatalogLoading(true);
      const data = await getSupplyChainCatalog();
      setCatalog(data);
    } catch (err) {
      console.warn("Failed to load catalog:", err);
    } finally {
      setCatalogLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      handleFileSelected(droppedFile);
    }
  };

  const handleFileSelected = (selectedFile: File) => {
    const ext = selectedFile.name.toLowerCase();
    if (!ext.endsWith(".xlsx") && !ext.endsWith(".xls")) {
      setError("Please select a valid Excel workbook (.xlsx or .xls).");
      return;
    }

    setFile(selectedFile);
    setError(null);
    setValidationResult(null);
    setImportResult(null);
  };

  const handleValidate = async () => {
    if (!file) return;
    setValidating(true);
    setError(null);
    try {
      const result = await validateSupplyChainFile(file);
      setValidationResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed.");
    } finally {
      setValidating(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setError(null);
    try {
      const result = await importSupplyChainFile(file);
      setImportResult(result);
      await loadCatalog();
      window.dispatchEvent(new CustomEvent("atmograph:workspace-changed"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed.");
    } finally {
      setImporting(false);
    }
  };

  const handleSyncGraph = async () => {
    setSyncingGraph(true);
    setError(null);
    try {
      await syncNeo4jGraph();
      await loadCatalog();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Graph synchronization failed.");
    } finally {
      setSyncingGraph(false);
    }
  };

  const filteredSuppliers = useMemo(() => {
    if (!catalog?.suppliers) return [];
    const q = searchQuery.toLowerCase().trim();
    if (!q) return catalog.suppliers;
    return catalog.suppliers.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.supplier_id.toLowerCase().includes(q) ||
        (s.city && s.city.toLowerCase().includes(q)) ||
        (s.country && s.country.toLowerCase().includes(q))
    );
  }, [catalog?.suppliers, searchQuery]);

  const filteredPlants = useMemo(() => {
    if (!catalog?.plants) return [];
    const q = searchQuery.toLowerCase().trim();
    if (!q) return catalog.plants;
    return catalog.plants.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.plant_id.toLowerCase().includes(q) ||
        (p.city && p.city.toLowerCase().includes(q)) ||
        (p.country && p.country.toLowerCase().includes(q))
    );
  }, [catalog?.plants, searchQuery]);

  const filteredComponents = useMemo(() => {
    if (!catalog?.components) return [];
    const q = searchQuery.toLowerCase().trim();
    if (!q) return catalog.components;
    return catalog.components.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.component_id.toLowerCase().includes(q) ||
        (c.category && c.category.toLowerCase().includes(q))
    );
  }, [catalog?.components, searchQuery]);

  const filteredProducts = useMemo(() => {
    if (!catalog?.products) return [];
    const q = searchQuery.toLowerCase().trim();
    if (!q) return catalog.products;
    return catalog.products.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.product_id.toLowerCase().includes(q) ||
        (p.category && p.category.toLowerCase().includes(q))
    );
  }, [catalog?.products, searchQuery]);

  const filteredWarehouses = useMemo(() => {
    if (!catalog?.warehouses) return [];
    const q = searchQuery.toLowerCase().trim();
    if (!q) return catalog.warehouses;
    return catalog.warehouses.filter(
      (w) =>
        w.name.toLowerCase().includes(q) ||
        w.warehouse_id.toLowerCase().includes(q) ||
        (w.city && w.city.toLowerCase().includes(q)) ||
        (w.country && w.country.toLowerCase().includes(q))
    );
  }, [catalog?.warehouses, searchQuery]);

  return (
    <div className="sc-page">
      {/* Header */}
      <div className="page-header-row">
        <div className="page-headline">
          <span className="eyebrow-tag">DATA MANAGEMENT ENGINE</span>
          <h2>Business Supply Chain Excel Import</h2>
          <p>
            Upload your company's multi-tier supply chain spreadsheets (.xlsx) to build your operational SQL dataset
            and topological Neo4j knowledge graph.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <a
            href={getTemplateDownloadUrl()}
            download="AtmoGraph_Supply_Chain_Template.xlsx"
            className="sc-primary-button"
            style={{
              background: "#1e293b",
              border: "1px solid rgba(255,255,255,0.12)",
              color: "#f8fafc",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "7px",
            }}
          >
            <Download size={15} />
            Download Excel Template
          </a>

          <button
            className="sc-primary-button"
            onClick={handleSyncGraph}
            disabled={syncingGraph}
            style={{
              background: "linear-gradient(135deg, #d4942c 0%, #e8a838 50%, #f0b848 100%)",
              color: "#0a0a0b",
            }}
          >
            {syncingGraph ? (
              <>
                <Loader2 size={15} className="sc-spin" />
                Syncing Graph...
              </>
            ) : (
              <>
                <Network size={15} />
                Sync Neo4j Graph
              </>
            )}
          </button>
        </div>
      </div>

      {/* Upload Zone Card */}
      <div className="sc-panel" style={{ padding: "24px" }}>
        <div className="sc-panel-header" style={{ marginBottom: "16px", borderBottom: "none", paddingBottom: 0 }}>
          <div className="sc-panel-title-icon">
            <UploadCloud size={18} />
          </div>
          <div>
            <strong style={{ fontSize: "15px" }}>Upload Supply Chain Workbook</strong>
            <span>Multi-sheet Excel workbook with Suppliers, Plants, Components, Products, Allocations & Routes</span>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files?.[0]) {
              handleFileSelected(e.target.files[0]);
            }
          }}
        />

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${dragActive ? "#e8a838" : "rgba(255, 255, 255, 0.12)"}`,
            borderRadius: "10px",
            background: dragActive ? "rgba(232, 168, 56, 0.08)" : "rgba(20, 20, 22, 0.6)",
            padding: "32px 20px",
            textAlign: "center",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
        >
          <div
            style={{
              width: "52px",
              height: "52px",
              borderRadius: "50%",
              background: "rgba(99, 102, 241, 0.12)",
              color: "#e8a838",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 14px",
            }}
          >
            <FileSpreadsheet size={26} />
          </div>

          {file ? (
            <div>
              <strong style={{ fontSize: "15px", color: "#f8fafc", display: "block" }}>{file.name}</strong>
              <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                {(file.size / (1024 * 1024)).toFixed(2)} MB · Click or drop another file to replace
              </span>
            </div>
          ) : (
            <div>
              <strong style={{ fontSize: "15px", color: "#f8fafc", display: "block" }}>
                Drag & Drop your Business Excel spreadsheet here
              </strong>
              <span style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px", display: "block" }}>
                or click to browse your computer (.xlsx, .xls up to 25MB)
              </span>
            </div>
          )}
        </div>

        {file && (
          <div style={{ display: "flex", gap: "12px", marginTop: "18px", alignItems: "center" }}>
            <button
              className="sc-primary-button"
              onClick={handleValidate}
              disabled={validating || importing}
              style={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.15)" }}
            >
              {validating ? (
                <>
                  <Loader2 size={16} className="sc-spin" />
                  Validating Structure...
                </>
              ) : (
                <>
                  <CheckCircle2 size={16} color="#38bdf8" />
                  Validate Workbook
                </>
              )}
            </button>

            <button
              className="sc-primary-button"
              onClick={handleImport}
              disabled={importing || validating}
              style={{
                background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                fontWeight: 600,
              }}
            >
              {importing ? (
                <>
                  <Loader2 size={16} className="sc-spin" />
                  Importing & Synchronizing...
                </>
              ) : (
                <>
                  <Database size={16} />
                  Import to Database & Graph
                </>
              )}
            </button>

            <span style={{ fontSize: "12px", color: "#94a3b8", marginLeft: "auto" }}>
              {validationResult ? "Structure validated. Ready for database ingestion." : "Validate or directly import."}
            </span>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div
          className="active-banner"
          style={{ background: "rgba(239, 68, 68, 0.12)", borderColor: "rgba(239, 68, 68, 0.3)" }}
        >
          <div className="active-banner-left">
            <div className="active-banner-icon">
              <AlertCircle size={18} />
            </div>
            <div>
              <div className="active-banner-title">Operation Error</div>
              <div className="active-banner-sub" style={{ whiteSpace: "pre-wrap" }}>
                {error}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Validation Result Box */}
      {validationResult && !importResult && (
        <div
          className="sc-panel"
          style={{
            padding: "20px",
            borderLeft: validationResult.success ? "4px solid #10b981" : "4px solid #ef4444",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
            {validationResult.success ? (
              <CheckCircle2 size={20} color="#34d399" />
            ) : (
              <AlertCircle size={20} color="#f87171" />
            )}
            <div>
              <strong style={{ color: "#f8fafc", fontSize: "15px" }}>
                {validationResult.success
                  ? "Workbook Validation Successful"
                  : "Validation Found Structural Issues"}
              </strong>
              <small style={{ display: "block", color: "#94a3b8" }}>
                {validationResult.sheets_validated.length} of {validationResult.sheets_found.length} sheets validated
              </small>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
              gap: "10px",
              marginTop: "12px",
            }}
          >
            {Object.entries(validationResult.row_counts).map(([sheet, count]) => (
              <div
                key={sheet}
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "6px",
                  padding: "10px",
                }}
              >
                <div style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>{sheet}</div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "#f8fafc", marginTop: "2px" }}>
                  {count} rows
                </div>
              </div>
            ))}
          </div>

          {validationResult.warnings && validationResult.warnings.length > 0 && (
            <div style={{ marginTop: "14px", fontSize: "12px", color: "#fbbf24" }}>
              <strong>Warnings:</strong>
              <ul style={{ margin: "4px 0 0 18px" }}>
                {validationResult.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Import Result Success Box */}
      {importResult && (
        <div
          className="sc-panel"
          style={{
            padding: "20px",
            borderLeft: "4px solid #10b981",
            background: "rgba(16, 185, 129, 0.05)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
            <CheckCircle2 size={22} color="#34d399" />
            <div>
              <strong style={{ color: "#f8fafc", fontSize: "16px" }}>
                Supply Chain Ingestion Completed Successfully
              </strong>
              <small style={{ display: "block", color: "#94a3b8" }}>
                Database tables populated and {importResult.neo4j_sync?.graph?.nodes ?? 0} Neo4j graph nodes
                synchronized.
              </small>
            </div>
            <button
              className="sc-primary-button"
              style={{ marginLeft: "auto", background: "#4f46e5" }}
              onClick={onNavigateToGraph}
            >
              <Network size={15} />
              Open Network Graph
            </button>
          </div>
        </div>
      )}

      {/* Live Business Catalog Section */}
      <div className="sc-panel">
        <div className="sc-panel-header" style={{ padding: "16px 20px" }}>
          <div className="sc-panel-title-icon">
            <Building2 size={16} />
          </div>
          <div>
            <strong>Active Business Data Catalog</strong>
            <span>Currently imported operational entities and facilities</span>
          </div>

          <button
            className="sc-icon-button"
            title="Refresh Catalog"
            style={{ marginLeft: "auto" }}
            onClick={loadCatalog}
            disabled={catalogLoading}
          >
            <RefreshCw size={14} className={catalogLoading ? "sc-spin" : ""} />
          </button>
        </div>

        {/* Catalog Tabs */}
        <div
          style={{
            display: "flex",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            padding: "0 20px",
            gap: "8px",
            background: "rgba(11, 15, 23, 0.4)",
          }}
        >
          <button
            className={`sc-tab-button ${activeTab === "suppliers" ? "active" : ""}`}
            onClick={() => setActiveTab("suppliers")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "suppliers" ? "2px solid #e8a838" : "2px solid transparent",
              color: activeTab === "suppliers" ? "#f8fafc" : "#94a3b8",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Truck size={15} />
            Suppliers ({catalog?.suppliers?.length ?? 0})
          </button>

          <button
            className={`sc-tab-button ${activeTab === "plants" ? "active" : ""}`}
            onClick={() => setActiveTab("plants")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "plants" ? "2px solid #e8a838" : "2px solid transparent",
              color: activeTab === "plants" ? "#f8fafc" : "#94a3b8",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Factory size={15} />
            Plants ({catalog?.plants?.length ?? 0})
          </button>

          <button
            className={`sc-tab-button ${activeTab === "components" ? "active" : ""}`}
            onClick={() => setActiveTab("components")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "components" ? "2px solid #e8a838" : "2px solid transparent",
              color: activeTab === "components" ? "#f8fafc" : "#94a3b8",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Layers size={15} />
            Components ({catalog?.components?.length ?? 0})
          </button>

          <button
            className={`sc-tab-button ${activeTab === "products" ? "active" : ""}`}
            onClick={() => setActiveTab("products")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "products" ? "2px solid #e8a838" : "2px solid transparent",
              color: activeTab === "products" ? "#f8fafc" : "#94a3b8",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Package size={15} />
            Products ({catalog?.products?.length ?? 0})
          </button>

          <button
            className={`sc-tab-button ${activeTab === "warehouses" ? "active" : ""}`}
            onClick={() => setActiveTab("warehouses")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "warehouses" ? "2px solid #e8a838" : "2px solid transparent",
              color: activeTab === "warehouses" ? "#f8fafc" : "#94a3b8",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Warehouse size={15} />
            Warehouses ({catalog?.warehouses?.length ?? 0})
          </button>
        </div>

        {/* Filter / Search input */}
        <div style={{ padding: "14px 20px", borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "#0b0f17",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "6px",
              padding: "6px 12px",
              maxWidth: "360px",
            }}
          >
            <Search size={14} color="#94a3b8" />
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                color: "#f8fafc",
                fontSize: "12px",
                outline: "none",
                width: "100%",
              }}
            />
          </div>
        </div>

        {/* Tables Content */}
        <div className="sc-table-wrap">
          {activeTab === "suppliers" && (
            <div className="sc-table col-5">
              <div className="sc-table-head">
                <span>SUPPLIER ID</span>
                <span>NAME</span>
                <span>LOCATION</span>
                <span>LOCATION STATUS</span>
                <span>ACTIONS</span>
              </div>
              {filteredSuppliers.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8", fontSize: "13px" }}>
                  No suppliers found. Upload an Excel spreadsheet above to populate.
                </div>
              ) : (
                filteredSuppliers.map((s) => (
                  <div className="sc-table-row" key={s.supplier_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8a838" }}>{s.supplier_id}</span>
                    <strong style={{ color: "#f8fafc" }}>{s.name}</strong>
                    <span>
                      {s.city ?? "HQ"}, {s.country ?? "Global"}
                    </span>
                    <span>
                      <span className={`status-badge ${s.location_known ? "badge-running" : "badge-buffered"}`}>
                        {s.location_known ? "KNOWN GEO" : "APPROXIMATE"}
                      </span>
                    </span>
                    <span>
                      <button
                        className="sc-primary-button"
                        style={{ padding: "4px 10px", fontSize: "11px" }}
                        onClick={() => onSelectSupplierForSimulation?.(s.supplier_id)}
                      >
                        <Zap size={12} />
                        Simulate Outage
                      </button>
                    </span>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "plants" && (
            <div className="sc-table col-4">
              <div className="sc-table-head">
                <span>PLANT ID</span>
                <span>NAME</span>
                <span>COMPANY</span>
                <span>LOCATION</span>
              </div>
              {filteredPlants.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8", fontSize: "13px" }}>
                  No plants found.
                </div>
              ) : (
                filteredPlants.map((p) => (
                  <div className="sc-table-row" key={p.plant_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8a838" }}>{p.plant_id}</span>
                    <strong style={{ color: "#f8fafc" }}>{p.name}</strong>
                    <span>{p.company_id ?? "--"}</span>
                    <span>
                      {p.city ?? "HQ"}, {p.country ?? "Global"}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "components" && (
            <div className="sc-table col-3">
              <div className="sc-table-head">
                <span>COMPONENT ID</span>
                <span>NAME</span>
                <span>CATEGORY</span>
              </div>
              {filteredComponents.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8", fontSize: "13px" }}>
                  No components found.
                </div>
              ) : (
                filteredComponents.map((c) => (
                  <div className="sc-table-row" key={c.component_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8a838" }}>{c.component_id}</span>
                    <strong style={{ color: "#f8fafc" }}>{c.name}</strong>
                    <span style={{ textTransform: "capitalize" }}>{c.category ?? "General"}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "products" && (
            <div className="sc-table col-3">
              <div className="sc-table-head">
                <span>PRODUCT ID</span>
                <span>NAME</span>
                <span>CATEGORY</span>
              </div>
              {filteredProducts.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8", fontSize: "13px" }}>
                  No finished products found.
                </div>
              ) : (
                filteredProducts.map((p) => (
                  <div className="sc-table-row" key={p.product_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8a838" }}>{p.product_id}</span>
                    <strong style={{ color: "#f8fafc" }}>{p.name}</strong>
                    <span style={{ textTransform: "capitalize" }}>{p.category ?? "Finished Good"}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "warehouses" && (
            <div className="sc-table col-3">
              <div className="sc-table-head">
                <span>WAREHOUSE ID</span>
                <span>NAME</span>
                <span>LOCATION</span>
              </div>
              {filteredWarehouses.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8", fontSize: "13px" }}>
                  No warehouses found.
                </div>
              ) : (
                filteredWarehouses.map((w) => (
                  <div className="sc-table-row" key={w.warehouse_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#e8a838" }}>{w.warehouse_id}</span>
                    <strong style={{ color: "#f8fafc" }}>{w.name}</strong>
                    <span>
                      {w.city ?? "HQ"}, {w.country ?? "Global"}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

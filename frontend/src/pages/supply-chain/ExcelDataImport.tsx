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
          <span className="eyebrow-tag">UPLOAD DATA</span>
          <h2>Upload Supply Chain Excel File</h2>
          <p>
            Upload your company's Excel file (.xlsx) with suppliers, factories, and parts to update your system and run disruption tests.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <a
            href={getTemplateDownloadUrl()}
            download="AtmoGraph_Supply_Chain_Template.xlsx"
            className="sc-primary-button"
            style={{
              background: "#ffffff",
              border: "1px solid #cbd5e1",
              color: "#0f172a",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "7px",
            }}
          >
            <Download size={15} color="#2563eb" />
            Download Blank Template
          </a>

          <button
            className="sc-primary-button"
            onClick={handleSyncGraph}
            disabled={syncingGraph}
            style={{
              background: "#2563eb",
              color: "#ffffff",
            }}
          >
            {syncingGraph ? (
              <>
                <Loader2 size={15} className="sc-spin" />
                Updating Map...
              </>
            ) : (
              <>
                <Network size={15} />
                Update Supply Map
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
            <strong style={{ fontSize: "15px" }}>Upload Excel Spreadsheet</strong>
            <span>Spreadsheet with sheets for Suppliers, Factories, Parts, Products, and Warehouses</span>
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
            border: `2px dashed ${dragActive ? "#2563eb" : "#cbd5e1"}`,
            borderRadius: "10px",
            background: dragActive ? "rgba(37, 99, 235, 0.08)" : "#f8fafc",
            padding: "36px 20px",
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
              background: "rgba(37, 99, 235, 0.1)",
              color: "#2563eb",
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
              <strong style={{ fontSize: "15px", color: "#0f172a", display: "block" }}>{file.name}</strong>
              <span style={{ fontSize: "12px", color: "#64748b" }}>
                {(file.size / (1024 * 1024)).toFixed(2)} MB · Click or drop another file to replace
              </span>
            </div>
          ) : (
            <div>
              <strong style={{ fontSize: "15px", color: "#0f172a", display: "block" }}>
                Drag & Drop your Excel file here
              </strong>
              <span style={{ fontSize: "13px", color: "#64748b", marginTop: "4px", display: "block" }}>
                or click to choose a file from your computer (.xlsx, .xls up to 25MB)
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
              style={{ background: "#ffffff", border: "1px solid #cbd5e1", color: "#0f172a" }}
            >
              {validating ? (
                <>
                  <Loader2 size={16} className="sc-spin" />
                  Checking File...
                </>
              ) : (
                <>
                  <CheckCircle2 size={16} color="#2563eb" />
                  Check File First
                </>
              )}
            </button>

            <button
              className="sc-primary-button"
              onClick={handleImport}
              disabled={importing || validating}
              style={{
                background: "#2563eb",
                color: "#ffffff",
                fontWeight: 600,
              }}
            >
              {importing ? (
                <>
                  <Loader2 size={16} className="sc-spin" />
                  Saving & Updating...
                </>
              ) : (
                <>
                  <Database size={16} />
                  Save to Database & Map
                </>
              )}
            </button>

            <span style={{ fontSize: "12px", color: "#64748b", marginLeft: "auto" }}>
              {validationResult ? "File looks good! Click 'Save to Database & Map'." : "Check file first or save directly."}
            </span>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div
          className="active-banner"
          style={{ background: "#fef2f2", borderColor: "#fecaca" }}
        >
          <div className="active-banner-left">
            <div className="active-banner-icon" style={{ background: "#fee2e2", color: "#dc2626" }}>
              <AlertCircle size={18} />
            </div>
            <div>
              <div className="active-banner-title" style={{ color: "#991b1b" }}>Something Went Wrong</div>
              <div className="active-banner-sub" style={{ color: "#b91c1c", whiteSpace: "pre-wrap" }}>
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
            borderLeft: validationResult.success ? "4px solid #16a34a" : "4px solid #dc2626",
            background: "#ffffff",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
            {validationResult.success ? (
              <CheckCircle2 size={20} color="#16a34a" />
            ) : (
              <AlertCircle size={20} color="#dc2626" />
            )}
            <div>
              <strong style={{ color: "#0f172a", fontSize: "15px" }}>
                {validationResult.success
                  ? "File Check Passed Successfully"
                  : "We Found Some Issues in the File"}
              </strong>
              <small style={{ display: "block", color: "#64748b" }}>
                {validationResult.sheets_validated.length} of {validationResult.sheets_found.length} sheets checked
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
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                  padding: "10px",
                }}
              >
                <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>{sheet}</div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "#0f172a", marginTop: "2px" }}>
                  {count} items
                </div>
              </div>
            ))}
          </div>

          {validationResult.warnings && validationResult.warnings.length > 0 && (
            <div style={{ marginTop: "14px", fontSize: "12px", color: "#d97706" }}>
              <strong>Notice:</strong>
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
            borderLeft: "4px solid #16a34a",
            background: "rgba(22, 163, 74, 0.08)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
            <CheckCircle2 size={22} color="#16a34a" />
            <div>
              <strong style={{ color: "#0f172a", fontSize: "16px" }}>
                Excel File Uploaded Successfully!
              </strong>
              <small style={{ display: "block", color: "#475569" }}>
                Your data is saved and {importResult.neo4j_sync?.graph?.nodes ?? 0} points are ready on the map.
              </small>
            </div>
            <button
              className="sc-primary-button"
              style={{ marginLeft: "auto", background: "#2563eb", color: "#ffffff" }}
              onClick={onNavigateToGraph}
            >
              <Network size={15} />
              Open Supply Chain Map
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
            <strong>Current Business Catalog</strong>
            <span>Suppliers, factories, parts, and warehouses saved in the system</span>
          </div>

          <button
            className="sc-icon-button"
            title="Refresh Catalog"
            style={{ marginLeft: "auto", background: "#f1f5f9", border: "1px solid #cbd5e1", color: "#0f172a" }}
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
            borderBottom: "1px solid #e2e8f0",
            padding: "0 20px",
            gap: "8px",
            background: "#f8fafc",
          }}
        >
          <button
            className={`sc-tab-button ${activeTab === "suppliers" ? "active" : ""}`}
            onClick={() => setActiveTab("suppliers")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "suppliers" ? "2px solid #2563eb" : "2px solid transparent",
              color: activeTab === "suppliers" ? "#2563eb" : "#64748b",
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
              borderBottom: activeTab === "plants" ? "2px solid #2563eb" : "2px solid transparent",
              color: activeTab === "plants" ? "#2563eb" : "#64748b",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Factory size={15} />
            Factories ({catalog?.plants?.length ?? 0})
          </button>

          <button
            className={`sc-tab-button ${activeTab === "components" ? "active" : ""}`}
            onClick={() => setActiveTab("components")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "components" ? "2px solid #2563eb" : "2px solid transparent",
              color: activeTab === "components" ? "#2563eb" : "#64748b",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Layers size={15} />
            Parts ({catalog?.components?.length ?? 0})
          </button>

          <button
            className={`sc-tab-button ${activeTab === "products" ? "active" : ""}`}
            onClick={() => setActiveTab("products")}
            style={{
              padding: "12px 14px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "products" ? "2px solid #2563eb" : "2px solid transparent",
              color: activeTab === "products" ? "#2563eb" : "#64748b",
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
              borderBottom: activeTab === "warehouses" ? "2px solid #2563eb" : "2px solid transparent",
              color: activeTab === "warehouses" ? "#2563eb" : "#64748b",
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
        <div style={{ padding: "14px 20px", borderBottom: "1px solid #e2e8f0" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "#ffffff",
              border: "1px solid #cbd5e1",
              borderRadius: "6px",
              padding: "6px 12px",
              maxWidth: "360px",
            }}
          >
            <Search size={14} color="#64748b" />
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                color: "#0f172a",
                fontSize: "13px",
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
                <span>MAP STATUS</span>
                <span>ACTIONS</span>
              </div>
              {filteredSuppliers.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                  No suppliers found. Upload an Excel spreadsheet above to add suppliers.
                </div>
              ) : (
                filteredSuppliers.map((s) => (
                  <div className="sc-table-row" key={s.supplier_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#2563eb", fontWeight: 600 }}>{s.supplier_id}</span>
                    <strong style={{ color: "#0f172a" }}>{s.name}</strong>
                    <span style={{ color: "#475569" }}>
                      {s.city ?? "HQ"}, {s.country ?? "Global"}
                    </span>
                    <span>
                      <span className={`status-badge ${s.location_known ? "badge-running" : "badge-buffered"}`}>
                        {s.location_known ? "EXACT LOCATION" : "APPROXIMATE"}
                      </span>
                    </span>
                    <span>
                      <button
                        className="sc-primary-button"
                        style={{ padding: "5px 12px", fontSize: "12px", background: "#f1f5f9", border: "1px solid #cbd5e1", color: "#0f172a" }}
                        onClick={() => onSelectSupplierForSimulation?.(s.supplier_id)}
                      >
                        <Zap size={12} color="#2563eb" />
                        Test Delay
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
                <span>FACTORY ID</span>
                <span>NAME</span>
                <span>COMPANY</span>
                <span>LOCATION</span>
              </div>
              {filteredPlants.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                  No factories found.
                </div>
              ) : (
                filteredPlants.map((p) => (
                  <div className="sc-table-row" key={p.plant_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#2563eb", fontWeight: 600 }}>{p.plant_id}</span>
                    <strong style={{ color: "#0f172a" }}>{p.name}</strong>
                    <span style={{ color: "#475569" }}>{p.company_id ?? "--"}</span>
                    <span style={{ color: "#475569" }}>
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
                <span>PART ID</span>
                <span>NAME</span>
                <span>CATEGORY</span>
              </div>
              {filteredComponents.length === 0 ? (
                <div style={{ padding: "24px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                  No parts found.
                </div>
              ) : (
                filteredComponents.map((c) => (
                  <div className="sc-table-row" key={c.component_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#2563eb", fontWeight: 600 }}>{c.component_id}</span>
                    <strong style={{ color: "#0f172a" }}>{c.name}</strong>
                    <span style={{ textTransform: "capitalize", color: "#475569" }}>{c.category ?? "General"}</span>
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
                <div style={{ padding: "24px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                  No finished products found.
                </div>
              ) : (
                filteredProducts.map((p) => (
                  <div className="sc-table-row" key={p.product_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#2563eb", fontWeight: 600 }}>{p.product_id}</span>
                    <strong style={{ color: "#0f172a" }}>{p.name}</strong>
                    <span style={{ textTransform: "capitalize", color: "#475569" }}>{p.category ?? "Finished Good"}</span>
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
                <div style={{ padding: "24px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                  No warehouses found.
                </div>
              ) : (
                filteredWarehouses.map((w) => (
                  <div className="sc-table-row" key={w.warehouse_id}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#2563eb", fontWeight: 600 }}>{w.warehouse_id}</span>
                    <strong style={{ color: "#0f172a" }}>{w.name}</strong>
                    <span style={{ color: "#475569" }}>
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

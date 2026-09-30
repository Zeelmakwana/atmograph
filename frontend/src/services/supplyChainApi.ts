import { request, getAuthHeaders } from "./api";


export interface SupplyChainSupplier {
  supplier_id: string;
  name: string;
  country?: string | null;
  city?: string | null;
  location_known?: boolean;
}


export interface SupplyChainPlant {
  plant_id: string;
  name: string;
  company_id?: string | null;
  country?: string | null;
  city?: string | null;
}


export interface SupplyChainProduct {
  product_id: string;
  name: string;
  category?: string | null;
}


export interface SupplyChainComponent {
  component_id: string;
  name: string;
  category?: string | null;
}


export interface SupplyChainWarehouse {
  warehouse_id: string;
  name: string;
  country?: string | null;
  city?: string | null;
}


export interface SupplyChainCompany {
  company_id: string;
  company_name: string;
  industry?: string | null;
}


export interface SupplyChainCatalog {
  success: boolean;
  company?: SupplyChainCompany | null;
  suppliers: SupplyChainSupplier[];
  plants: SupplyChainPlant[];
  products: SupplyChainProduct[];
  components: SupplyChainComponent[];
  warehouses: SupplyChainWarehouse[];
}


export interface SupplyChainValidationResult {
  success: boolean;
  stage: string;
  filename: string;
  sheets_found: string[];
  sheets_validated: string[];
  row_counts: Record<string, number>;
  warnings: string[];
  errors: string[];
}


export interface SupplyChainImportResult {
  success: boolean;
  stage: string;
  filename: string;

  database: {
    success: boolean;
    stage: string;
    filename: string;
    counts: Record<string, number>;
    warnings: string[];
    errors: string[];
  };

  neo4j_sync: {
    success: boolean;
    stage: string;
    counts: Record<string, number>;
    graph: {
      nodes: number;
      relationships: number;
    };
    errors: string[];
  };
}


export interface SimulationComponent {
  component_id: string;
  component_name: string;
  plant_id: string;
  plant_name: string;

  failed_supplier_id: string;

  gross_lost_supply: number;
  alternative_recovery: number;
  gross_shortage: number;

  inventory_quantity: number;
  inventory_coverage_days: number | null;

  daily_demand: number;
  net_shortage: number;
  estimated_delay_days: number;

  production_stop: boolean;

  risk_score: number;
  risk_level: string;
  confidence: number;

  alternative_suppliers?: Array<{
    supplier_id: string;
    allocation_pct: number;
    allocated_capacity_units: number;
    spare_capacity_units: number;
    recoverable_supply_units: number;
    lead_time_days: number | null;
    criticality: string | null;
  }>;
}


export interface SimulationProduct {
  product_id: string;
  product_name: string;
  component_id: string;
  component_name: string;

  exposure_status?: "buffered" | "shortage";

  gross_component_exposure?: number;
  component_shortage?: number;
  estimated_product_shortage?: number;

  daily_demand_units?: number;
  inventory_protected?: number;
  production_stop?: boolean;

  risk_score?: number;
  risk_level?: string;
}


export interface SimulationPlant {
  plant_id: string;
  plant_name: string;
  affected_components: number;
  affected_products: number;
  max_delay_days: number;
  risk_score: number;
  risk_level: string;
  production_stop: boolean;
}


export interface SimulationSummary {
  affected_components: number;
  affected_products: number;
  affected_plants: number;

  gross_lost_supply: number;
  alternative_recovery: number;

  gross_shortage: number;
  net_shortage: number;

  max_delay_days: number;
  max_risk_score: number;

  production_stop: boolean;

  products_buffered?: number;
  products_with_shortage?: number;
}


export interface SupplierFailureSimulation {
  success: boolean;
  simulation_type: string;

  supplier: {
    supplier_id: string;
    name: string;
    country?: string | null;
    city?: string | null;
  };

  components: SimulationComponent[];
  products: SimulationProduct[];
  plants: SimulationPlant[];

  summary: SimulationSummary;
}


// ============================================================
// CATALOG
// ============================================================

export function getSupplyChainSuppliers() {
  return request<{
    success: boolean;
    suppliers: SupplyChainSupplier[];
  }>(
    "/api/supply-chain/suppliers"
  );
}


export function getSupplyChainCatalog() {
  return request<SupplyChainCatalog>(
    "/api/supply-chain/catalog"
  );
}

export function getTemplateDownloadUrl() {
  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000";
  return `${baseUrl}/api/supply-chain/template`;
}

export function syncNeo4jGraph() {
  return request<{
    success: boolean;
    stage: string;
    counts: Record<string, number>;
    graph: {
      nodes: number;
      relationships: number;
    };
    errors: string[];
  }>("/api/supply-chain/sync-graph", {
    method: "POST",
  });
}


// ============================================================
// VALIDATION
// ============================================================

export async function validateSupplyChainFile(
  file: File
): Promise<SupplyChainValidationResult> {

  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000";

  const formData =
    new FormData();

  formData.append(
    "file",
    file
  );

  const response =
    await fetch(
      `${baseUrl}/api/supply-chain/validate`,
      {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
        },
        body: formData,
      }
    );

  const payload =
    await response.json();

  if (!response.ok) {
    throw new Error(
      payload?.detail?.errors?.join?.(
        "\n"
      ) ||
      payload?.detail ||
      "File validation failed."
    );
  }

  return payload;
}


// ============================================================
// IMPORT
// ============================================================

export async function importSupplyChainFile(
  file: File
): Promise<SupplyChainImportResult> {

  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000";

  const formData =
    new FormData();

  formData.append(
    "file",
    file
  );

  const response =
    await fetch(
      `${baseUrl}/api/supply-chain/import`,
      {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
        },
        body: formData,
      }
    );

  const payload =
    await response.json();

  if (!response.ok) {
    const detail =
      payload?.detail;

    if (
      typeof detail ===
      "object"
    ) {
      const errors =
        detail?.errors ??
        detail?.database?.errors ??
        detail?.neo4j_sync?.errors ??
        [];

      throw new Error(
        Array.isArray(errors)
          ? errors.join("\n")
          : JSON.stringify(
              detail
            )
      );
    }

    throw new Error(
      detail ||
      "Supply-chain import failed."
    );
  }

  return payload;
}


// ============================================================
// SIMULATOR
// ============================================================

export function simulateSupplierFailure(
  supplierId: string
) {
  return request<SupplierFailureSimulation>(
    "/api/supply-chain/simulate",
    {
      method: "POST",
      body: JSON.stringify({
        supplier_id: supplierId,
      }),
    }
  );
}


// ============================================================
// WORKSPACE MANAGEMENT
// ============================================================

export interface BusinessWorkspace {
  workspace_id: string;
  company_id: string;
  company_name: string;
  industry: string;
  owner_name?: string | null;
  location?: string | null;
  suppliers_count: number;
  plants_count: number;
  is_active: boolean;
  badge: string;
  description: string;
}

export interface WorkspacesResponse {
  success: boolean;
  active_workspace_id: string;
  active_company: {
    company_id: string;
    company_name: string;
    industry: string;
    suppliers_count: number;
    plants_count: number;
  };
  workspaces: BusinessWorkspace[];
}

export function getWorkspaces() {
  return request<WorkspacesResponse>("/api/supply-chain/workspaces");
}

export function switchWorkspace(workspaceId: string) {
  return request<WorkspacesResponse>("/api/supply-chain/workspaces/switch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: workspaceId }),
  });
}

export function registerWorkspace(
  companyName: string,
  industry: string,
  ownerName?: string,
  location?: string
) {
  return request<any>("/api/supply-chain/workspaces/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      company_name: companyName,
      industry,
      owner_name: ownerName,
      location,
    }),
  });
}

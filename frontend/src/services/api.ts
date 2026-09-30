const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

function buildUrl(endpoint: string) {
  const base = API_BASE_URL.replace(/\/+$/, "");
  const path = endpoint.startsWith("/")
    ? endpoint
    : `/${endpoint}`;

  return `${base}${path}`;
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("atmograph_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function unwrap<T = any>(payload: any): T {
  if (
    payload &&
    typeof payload === "object" &&
    "data" in payload &&
    payload.data !== undefined
  ) {
    return payload.data as T;
  }

  return payload as T;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(
    buildUrl(endpoint),
    {
      ...options,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...(options.headers || {}),
      },
    }
  );

  const text = await response.text();

  let payload: any = null;

  try {
    payload = text
      ? JSON.parse(text)
      : null;
  } catch {
    payload = text;
  }

  if (!response.ok) {
    const message =
      payload?.detail ||
      payload?.message ||
      payload?.error ||
      `Request failed with status ${response.status}`;

    throw new Error(String(message));
  }

  return payload as T;
}

/* ============================================================
   NORMALIZERS
============================================================ */

export function normalizeListResponse(
  payload: any
): any[] {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload?.data)) {
    return payload.data;
  }

  if (Array.isArray(payload?.events)) {
    return payload.events;
  }

  if (Array.isArray(payload?.items)) {
    return payload.items;
  }

  if (Array.isArray(payload?.results)) {
    return payload.results;
  }

  return [];
}

export function normalizeObjectResponse(
  payload: any
): any {
  if (
    payload &&
    typeof payload === "object" &&
    payload.data &&
    typeof payload.data === "object" &&
    !Array.isArray(payload.data)
  ) {
    return payload.data;
  }

  return payload ?? {};
}

/* ============================================================
   GRAPH
============================================================ */

export function getGraphStatistics() {
  return request<any>(
    "/api/graph/statistics"
  );
}

export function getEventGraph(
  eventId: number,
  maxDepth = 4
) {
  return request<any>(
    `/api/graph/event/${eventId}?max_depth=${maxDepth}`
  );
}

export function getAffectedSuppliers(
  eventId: number
) {
  return request<any>(
    `/api/graph/event/${eventId}/suppliers`
  );
}

export function getAffectedProducts(
  eventId: number
) {
  return request<any>(
    `/api/graph/event/${eventId}/products`
  );
}

export function getRipplePaths(
  eventId: number,
  maxDepth = 5
) {
  return request<any>(
    `/api/graph/event/${eventId}/ripple?max_depth=${maxDepth}`
  );
}

/* ============================================================
   BUSINESS SUPPLY CHAIN GRAPH
============================================================ */

export function getBusinessSupplyChainGraph() {
  return request<any>(
    "/api/supply-chain/business-graph"
  );
}

/* ============================================================
   GNN GRAPH
============================================================ */

export function getGnnGraph(
  graphId: string,
  maxDepth = 3
) {
  return request<any>(
    `/api/graph-intelligence/gnn-graph/${encodeURIComponent(
      graphId
    )}?max_depth=${maxDepth}`
  );
}

export function getGnnPrediction(
  graphId: string
) {
  return request<any>(
    `/api/graph-intelligence/gnn-predict/${encodeURIComponent(
      graphId
    )}`
  );
}

/* ============================================================
   EVENT IMPACT GRAPH
============================================================ */

export function getEventImpactGraph(
  eventId: number
) {
  return request<any>(
    `/api/graph-intelligence/event-impact/${eventId}`
  );
}

export function getHybridPrediction(
  eventId: number,
  graphId: string
) {
  return request<any>(
    `/api/graph-intelligence/hybrid-predict/${eventId}/${encodeURIComponent(
      graphId
    )}`
  );
}

/* ============================================================
   EVENTS
============================================================ */

export function getEvents(
  search = "",
  severity = "",
  status = "",
  limit = 100
) {
  const params = new URLSearchParams();

  if (search.trim()) {
    params.set(
      "search",
      search.trim()
    );
  }

  if (severity.trim()) {
    params.set(
      "severity",
      severity.trim()
    );
  }

  if (status.trim()) {
    params.set(
      "status",
      status.trim()
    );
  }

  params.set(
    "limit",
    String(limit)
  );

  return request<any>(
    `/api/events?${params.toString()}`
  );
}

/* ============================================================
   NEWS INTELLIGENCE
============================================================ */

export function analyzeNews(
  title: string,
  description: string,
  source = "manual",
  autoSimulate = true
) {
  return request<any>(
    "/api/news-intelligence/analyze",
    {
      method: "POST",

      body: JSON.stringify({
        title,
        description,
        source,
        auto_simulate: autoSimulate,
      }),
    }
  );
}

export function ingestNews(
  title: string,
  description: string,
  source = "manual"
) {
  return request<any>(
    "/api/news/analyze",
    {
      method: "POST",

      body: JSON.stringify({
        title,
        description,
        source,
      }),
    }
  );
}

/* ============================================================
   HEALTH
============================================================ */

export function getBackendHealth() {
  return request<any>(
    "/health"
  );
}

export function getNlpHealth() {
  return request<any>(
    "/api/nlp/analyze",
    {
      method: "POST",

      body: JSON.stringify({
        title: "Health check",
        description:
          "Supply chain health check",
      }),
    }
  );
}

export {
  API_BASE_URL,
  unwrap,
  request,
  getAuthHeaders,
};
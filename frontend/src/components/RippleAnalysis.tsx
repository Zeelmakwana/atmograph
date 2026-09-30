import {
  AlertTriangle,
  Boxes,
  GitBranch,
  Package,
  RefreshCw,
  ShieldAlert,
  Truck,
} from "lucide-react";

import {
  getAffectedProducts,
  getAffectedSuppliers,
  getRipplePaths,
} from "../services/api";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

type Props = {
  eventId: number | null;
};

type BusinessComponent = {
  component_id?: string;
  component_name?: string;
  plant_id?: string;
  plant_name?: string;
  inventory_quantity?: number;
  inventory_coverage_days?: number;
  gross_lost_supply?: number;
  alternative_recovery?: number;
  net_shortage?: number;
  estimated_delay_days?: number;
  production_stop?: boolean;
  risk_score?: number;
  risk_level?: string;
  confidence?: number;
};

type BusinessProduct = {
  product_id?: string;
  product_name?: string;
  component_id?: string;
  component_name?: string;
  exposure_status?: string;
  estimated_product_shortage?: number;
  estimated_delay_days?: number;
  production_stop?: boolean;
  risk_score?: number;
  risk_level?: string;
};

type BusinessSupplier = {
  supplier_id?: string;
  name?: string;
  country?: string;
  city?: string;
  match_score?: number;
};

type BusinessPlant = {
  plant_id?: string;
  plant_name?: string;
  affected_components?: number;
  affected_products?: number;
  max_delay_days?: number;
  max_risk_score?: number;
  production_stop?: boolean;
  risk_level?: string;
};

type BusinessSimulation = {
  supplier?: {
    supplier_id?: string;
    name?: string;
    country?: string;
    city?: string;
  };

  components?: BusinessComponent[];

  products?: BusinessProduct[];

  plants?: BusinessPlant[];

  summary?: {
    affected_components?: number;
    affected_products?: number;
    affected_plants?: number;
    gross_lost_supply?: number;
    alternative_recovery?: number;
    gross_shortage?: number;
    net_shortage?: number;
    max_delay_days?: number;
    max_risk_score?: number;
    production_stop?: boolean;
  };
};

type BusinessData = {
  suppliers: BusinessSupplier[];

  simulations: BusinessSimulation[];

  summary: {
    affected_components: number;
    affected_products: number;
    affected_plants: number;
    gross_lost_supply: number;
    alternative_recovery: number;
    net_shortage: number;
    max_risk: number;
    production_stop: boolean;
  };

  confidence: number;
};

function unwrap(value: any) {
  return value?.data ?? value;
}

function getList(
  value: any,
  keys: string[] = []
): any[] {
  const data = unwrap(value);

  if (Array.isArray(data)) {
    return data;
  }

  for (const key of keys) {
    if (Array.isArray(data?.[key])) {
      return data[key];
    }
  }

  return [];
}

function normalizeNumber(
  value: unknown
): number {
  const number =
    Number(value);

  return Number.isFinite(
    number
  )
    ? number
    : 0;
}

function normalizeBusiness(
  value: any
): BusinessData | null {
  if (!value) {
    return null;
  }

  const root =
    value?.business_supply_chain ??
    value?.data?.business_supply_chain ??
    value;

  const summary =
    root?.summary;

  const suppliers: BusinessSupplier[] =
    Array.isArray(
      root?.matched_suppliers
    )
      ? root.matched_suppliers
      : Array.isArray(
          root?.suppliers
        )
        ? root.suppliers
        : [];

  const simulations: BusinessSimulation[] =
    Array.isArray(
      root?.simulation?.simulations
    )
      ? root.simulation.simulations
          .map(
            (item: any): BusinessSimulation =>
              item?.simulation ??
              item
          )
          .filter(
            (
              item: BusinessSimulation
            ): boolean =>
              Boolean(item)
          )
      : Array.isArray(
          root?.simulations
        )
        ? root.simulations
            .map(
              (item: any): BusinessSimulation =>
                item?.simulation ??
                item
            )
            .filter(
              (
                item: BusinessSimulation
              ): boolean =>
                Boolean(item)
            )
        : [];

  if (
    !summary &&
    suppliers.length === 0 &&
    simulations.length === 0
  ) {
    return null;
  }

  const riskValues: number[] =
    simulations.map(
      (
        simulation: BusinessSimulation
      ): number =>
        normalizeNumber(
          simulation.summary
            ?.max_risk_score
        )
    );

  const maxRisk =
    Math.max(
      normalizeNumber(
        summary?.max_risk
      ),
      ...riskValues
    );

  const confidenceValues: number[] =
    simulations.flatMap(
      (
        simulation: BusinessSimulation
      ): number[] =>
        (simulation.components ??
          [])
          .map(
            (
              component: BusinessComponent
            ): number =>
              normalizeNumber(
                component.confidence
              )
          )
          .filter(
            (
              value: number
            ): boolean =>
              value > 0
          )
    );

  const confidence =
    confidenceValues.length > 0
      ? Math.min(
          1,
          confidenceValues.reduce(
            (
              sum: number,
              value: number
            ): number =>
              sum + value,
            0
          ) /
            confidenceValues.length
        )
      : 1;

  return {
    suppliers,

    simulations,

    summary: {
      affected_components:
        normalizeNumber(
          summary?.affected_components
        ),

      affected_products:
        normalizeNumber(
          summary?.affected_products
        ),

      affected_plants:
        normalizeNumber(
          summary?.affected_plants
        ),

      gross_lost_supply:
        normalizeNumber(
          summary?.gross_lost_supply
        ),

      alternative_recovery:
        normalizeNumber(
          summary?.alternative_recovery
        ),

      net_shortage:
        normalizeNumber(
          summary?.net_shortage
        ),

      max_risk:
        maxRisk,

      production_stop:
        Boolean(
          summary?.production_stop
        ),
    },

    confidence,
  };
}

function getStoredBusiness():
  BusinessData | null {
  try {
    const raw =
      localStorage.getItem(
        "atmograph:last-supplier-simulation"
      );

    if (!raw) {
      return null;
    }

    return normalizeBusiness(
      JSON.parse(raw)
    );
  } catch {
    return null;
  }
}

function formatNumber(
  value: number
): string {
  return new Intl.NumberFormat(
    "en-US",
    {
      maximumFractionDigits: 2,
    }
  ).format(value);
}

function getRiskLevel(
  score: number
): string {
  if (score >= 80) {
    return "critical";
  }

  if (score >= 60) {
    return "high";
  }

  if (score >= 40) {
    return "medium";
  }

  return "low";
}

export default function RippleAnalysis({
  eventId,
}: Props) {
  const [
    suppliers,
    setSuppliers,
  ] = useState<any[]>([]);

  const [
    products,
    setProducts,
  ] = useState<any[]>([]);

  const [
    ripple,
    setRipple,
  ] = useState<any[]>([]);

  const [
    business,
    setBusiness,
  ] =
    useState<BusinessData | null>(
      getStoredBusiness
    );

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const load = useCallback(
    async () => {
      if (!eventId) {
        setSuppliers([]);
        setProducts([]);
        setRipple([]);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [
          supplierResult,
          productResult,
          rippleResult,
        ] = await Promise.all([
          getAffectedSuppliers(
            eventId
          ),

          getAffectedProducts(
            eventId
          ),

          getRipplePaths(
            eventId,
            5
          ),
        ]);

        setSuppliers(
          getList(
            supplierResult,
            [
              "suppliers",
              "affected_suppliers",
            ]
          )
        );

        setProducts(
          getList(
            productResult,
            [
              "products",
              "affected_products",
            ]
          )
        );

        setRipple(
          getList(
            rippleResult,
            [
              "paths",
              "ripple_paths",
              "relationships",
            ]
          )
        );

        const latest =
          getStoredBusiness();

        if (latest) {
          setBusiness(
            latest
          );
        }
      } catch (err: any) {
        setError(
          err?.message ||
            "Unable to load ripple analysis."
        );
      } finally {
        setLoading(false);
      }
    },
    [eventId]
  );

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const handleSimulation =
      (event: Event) => {
        const customEvent =
          event as CustomEvent;

        const next =
          normalizeBusiness(
            customEvent.detail
          );

        if (next) {
          setBusiness(next);
        }
      };

    window.addEventListener(
      "atmograph:supplier-simulation",
      handleSimulation
    );

    return () => {
      window.removeEventListener(
        "atmograph:supplier-simulation",
        handleSimulation
      );
    };
  }, []);

  const businessComponents =
    useMemo(
      (): BusinessComponent[] =>
        business?.simulations.flatMap(
          (
            simulation: BusinessSimulation
          ): BusinessComponent[] =>
            simulation.components ??
            []
        ) ?? [],
      [business]
    );

  const businessProducts =
    useMemo(
      (): BusinessProduct[] =>
        business?.simulations.flatMap(
          (
            simulation: BusinessSimulation
          ): BusinessProduct[] =>
            simulation.products ??
            []
        ) ?? [],
      [business]
    );

  const businessPlants =
    useMemo(
      (): BusinessPlant[] =>
        business?.simulations.flatMap(
          (
            simulation: BusinessSimulation
          ): BusinessPlant[] =>
            simulation.plants ??
            []
        ) ?? [],
      [business]
    );

  return (
    <div className="dashboard-content">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="page-heading">

        <div>

          <span className="eyebrow">
            RIPPLE INTELLIGENCE
          </span>

          <h2>
            Ripple Analysis
          </h2>

          <p>
            Trace the disruption from the
            failed supplier through components,
            plants and products.
          </p>

        </div>

        <button
          className="primary-button"
          onClick={load}
          disabled={loading}
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
            ? "Loading..."
            : "Refresh"}

        </button>

      </div>

      {error && (
        <div className="ripple-error">

          <AlertTriangle
            size={17}
          />

          <span>
            {error}
          </span>

        </div>
      )}

      {/* =====================================================
          BUSINESS SUMMARY
      ===================================================== */}

      {business && (
        <section className="ripple-summary-grid">

          <SummaryCard
            icon={
              <ShieldAlert size={20} />
            }
            label="BUSINESS RISK"
            value={
              business.summary.max_risk.toFixed(
                0
              )
            }
            level={getRiskLevel(
              business.summary.max_risk
            )}
          />

          <SummaryCard
            icon={
              <Truck size={20} />
            }
            label="SUPPLIERS"
            value={
              business.suppliers.length
            }
          />

          <SummaryCard
            icon={
              <Boxes size={20} />
            }
            label="COMPONENTS"
            value={
              business.summary
                .affected_components
            }
          />

          <SummaryCard
            icon={
              <Package size={20} />
            }
            label="PRODUCTS"
            value={
              business.summary
                .affected_products
            }
          />

        </section>
      )}

      {/* =====================================================
          BUSINESS RIPPLE FLOW
      ===================================================== */}

      {business && (
        <section className="panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                BUSINESS IMPACT PROPAGATION
              </span>

              <h3>
                Actual Supply Chain Ripple
              </h3>

            </div>

            <GitBranch size={18} />

          </div>

          <div className="ripple-flow">

            {/* EVENT */}

            <div className="ripple-event-node">

              <div className="ripple-node-icon">

                <AlertTriangle
                  size={18}
                />

              </div>

              <div className="ripple-node-content">

                <span className="ripple-node-type">
                  EVENT
                </span>

                <strong>
                  Event #{eventId}
                </strong>

                <small>
                  Supply-chain disruption
                </small>

              </div>

            </div>

            <div className="ripple-arrow">
              ↓
            </div>

            {/* SUPPLIERS */}

            <div className="ripple-stage">

              <div className="ripple-stage-title">
                Failed / Exposed Suppliers
              </div>

              <div className="ripple-node-grid">

                {business.suppliers.map(
                  (
                    supplier: BusinessSupplier,
                    index: number
                  ) => (

                    <div
                      className="ripple-entity-card"
                      key={
                        supplier.supplier_id ??
                        index
                      }
                    >

                      <div className="ripple-node-icon">

                        <Truck
                          size={17}
                        />

                      </div>

                      <div className="ripple-node-content">

                        <span className="ripple-node-type">
                          SUPPLIER
                        </span>

                        <strong>
                          {supplier.name ??
                            supplier.supplier_id ??
                            "Unknown supplier"}
                        </strong>

                        <small>
                          {supplier.country ??
                            "Business supplier"}
                        </small>

                      </div>

                    </div>

                  )
                )}

              </div>

            </div>

            <div className="ripple-arrow">
              ↓
            </div>

            {/* COMPONENTS */}

            <div className="ripple-stage">

              <div className="ripple-stage-title">
                Affected Components
              </div>

              <div className="ripple-node-grid">

                {businessComponents.map(
                  (
                    component: BusinessComponent,
                    index: number
                  ) => (

                    <div
                      className="ripple-entity-card"
                      key={
                        component.component_id ??
                        index
                      }
                    >

                      <div className="ripple-node-icon">

                        <Boxes
                          size={17}
                        />

                      </div>

                      <div className="ripple-node-content">

                        <span className="ripple-node-type">
                          COMPONENT
                        </span>

                        <strong>
                          {component.component_name ??
                            "Unknown component"}
                        </strong>

                        <small>

                          Inventory{" "}
                          {formatNumber(
                            normalizeNumber(
                              component.inventory_quantity
                            )
                          )}

                          {" • "}

                          {formatNumber(
                            normalizeNumber(
                              component.inventory_coverage_days
                            )
                          )}

                          days coverage

                        </small>

                      </div>

                    </div>

                  )
                )}

              </div>

            </div>

            <div className="ripple-arrow">
              ↓
            </div>

            {/* PLANTS */}

            <div className="ripple-stage">

              <div className="ripple-stage-title">
                Affected Plants
              </div>

              <div className="ripple-node-grid">

                {businessPlants.map(
                  (
                    plant: BusinessPlant,
                    index: number
                  ) => (

                    <div
                      className="ripple-entity-card"
                      key={
                        plant.plant_id ??
                        index
                      }
                    >

                      <div className="ripple-node-icon">

                        <GitBranch
                          size={17}
                        />

                      </div>

                      <div className="ripple-node-content">

                        <span className="ripple-node-type">
                          PLANT
                        </span>

                        <strong>
                          {plant.plant_name ??
                            "Unknown plant"}
                        </strong>

                        <small>

                          {plant.production_stop
                            ? "Production stop"
                            : "Production running"}

                        </small>

                      </div>

                    </div>

                  )
                )}

              </div>

            </div>

            <div className="ripple-arrow">
              ↓
            </div>

            {/* PRODUCTS */}

            <div className="ripple-stage">

              <div className="ripple-stage-title">
                Affected Products
              </div>

              <div className="ripple-node-grid">

                {businessProducts.map(
                  (
                    product: BusinessProduct,
                    index: number
                  ) => (

                    <div
                      className="ripple-entity-card"
                      key={
                        product.product_id ??
                        index
                      }
                    >

                      <div className="ripple-node-icon">

                        <Package
                          size={17}
                        />

                      </div>

                      <div className="ripple-node-content">

                        <span className="ripple-node-type">
                          PRODUCT
                        </span>

                        <strong>
                          {product.product_name ??
                            "Unknown product"}
                        </strong>

                        <small>

                          {String(
                            product.exposure_status ??
                              "exposed"
                          ).toUpperCase()}

                        </small>

                      </div>

                    </div>

                  )
                )}

              </div>

            </div>

          </div>

        </section>
      )}

      {/* =====================================================
          BUSINESS IMPACT SUMMARY
      ===================================================== */}

      {business && (
        <section className="panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                IMPACT QUANTIFICATION
              </span>

              <h3>
                Ripple Impact Summary
              </h3>

            </div>

          </div>

          <div className="ripple-summary-grid">

            <SummaryCard
              icon={
                <Boxes size={20} />
              }
              label="GROSS LOST SUPPLY"
              value={formatNumber(
                business.summary
                  .gross_lost_supply
              )}
            />

            <SummaryCard
              icon={
                <Truck size={20} />
              }
              label="ALTERNATIVE RECOVERY"
              value={formatNumber(
                business.summary
                  .alternative_recovery
              )}
            />

            <SummaryCard
              icon={
                <ShieldAlert size={20} />
              }
              label="NET SHORTAGE"
              value={formatNumber(
                business.summary
                  .net_shortage
              )}
              level={
                business.summary
                  .net_shortage > 0
                  ? "high"
                  : "low"
              }
            />

            <SummaryCard
              icon={
                <GitBranch size={20} />
              }
              label="CONFIDENCE"
              value={`${(
                business.confidence *
                100
              ).toFixed(0)}%`}
            />

          </div>

        </section>
      )}

      {/* =====================================================
          COMPONENT DETAILS
      ===================================================== */}

      {business &&
        businessComponents.length >
          0 && (

          <section className="panel">

            <div className="panel-header">

              <div>

                <span className="panel-kicker">
                  COMPONENT IMPACT
                </span>

                <h3>
                  Component Exposure
                </h3>

              </div>

              <span className="panel-count">
                {
                  businessComponents.length
                }
              </span>

            </div>

            <div className="connected-entities">

              {businessComponents.map(
                (
                  component: BusinessComponent,
                  index: number
                ) => (

                  <EntityRow
                    key={
                      component.component_id ??
                      index
                    }
                    type="Component"
                    name={
                      component.component_name ??
                      "Unknown component"
                    }
                    icon={
                      <Boxes size={16} />
                    }
                  />

                )
              )}

            </div>

          </section>

        )}

      {/* =====================================================
          LEGACY GRAPH DATA
      ===================================================== */}

      <section className="panel">

        <div className="panel-header">

          <div>

            <span className="panel-kicker">
              GRAPH CONNECTIVITY
            </span>

            <h3>
              Legacy Graph Paths
            </h3>

            <p>
              Additional canonical Neo4j
              relationships for this event.
              These are secondary to the
              business simulation above.
            </p>

          </div>

          <GitBranch size={18} />

        </div>

        <div className="ripple-summary-grid">

          <SummaryCard
            icon={
              <Truck size={20} />
            }
            label="GRAPH SUPPLIERS"
            value={
              suppliers.length
            }
          />

          <SummaryCard
            icon={
              <Package size={20} />
            }
            label="GRAPH PRODUCTS"
            value={
              products.length
            }
          />

          <SummaryCard
            icon={
              <GitBranch size={20} />
            }
            label="GRAPH LINKS"
            value={
              ripple.length
            }
          />

        </div>

      </section>

      {/* =====================================================
          LEGACY PATH LIST
      ===================================================== */}

      <section className="panel">

        <div className="panel-header">

          <div>

            <span className="panel-kicker">
              CANONICAL GRAPH
            </span>

            <h3>
              Downstream Graph Paths
            </h3>

          </div>

        </div>

        {ripple.length === 0 ? (

          <div className="empty-state">

            No canonical downstream paths
            were returned for this event.
            Business impact is shown above.

          </div>

        ) : (

          <div className="ripple-path-list">

            {ripple.map(
              (
                path: any,
                index: number
              ) => (

                <div
                  className="ripple-path-item"
                  key={index}
                >

                  <GitBranch
                    size={16}
                  />

                  <span>
                    {formatPath(
                      path
                    )}
                  </span>

                </div>

              )
            )}

          </div>

        )}

      </section>

    </div>
  );
}

function SummaryCard({
  icon,
  label,
  value,
  level,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  level?: string;
}) {
  return (
    <div
      className={`panel ripple-summary-card ${
        level
          ? `metric-${level}`
          : ""
      }`}
    >

      <div className="ripple-summary-icon">
        {icon}
      </div>

      <div className="ripple-summary-content">

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

      </div>

    </div>
  );
}

function EntityRow({
  type,
  name,
  icon,
}: {
  type: string;
  name: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="connected-entity-row">

      <div className="connected-entity-icon">
        {icon}
      </div>

      <div className="connected-entity-main">

        <strong>
          {name}
        </strong>

        <span>
          {type}
        </span>

      </div>

    </div>
  );
}

function formatPath(
  path: any
): string {
  if (typeof path === "string") {
    return path;
  }

  if (Array.isArray(path)) {
    return path
      .map(
        (item: any): string =>
          item?.name ??
          item?.title ??
          item?.id ??
          String(item)
      )
      .join(" → ");
  }

  if (path?.path) {
    return formatPath(
      path.path
    );
  }

  if (
    path?.source &&
    path?.target
  ) {
    return `${path.source} → ${path.target}`;
  }

  return (
    path?.name ??
    path?.title ??
    "Connected graph path"
  );
}
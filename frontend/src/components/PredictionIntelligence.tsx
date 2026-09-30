import {
  AlertTriangle,
  Brain,
  Boxes,
  Calculator,
  Clock3,
  RefreshCw,
  ShieldAlert,
  Target,
  Truck,
} from "lucide-react";

import {
  getHybridPrediction,
  getGnnPrediction,
} from "../services/api";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

type PredictionIntelligenceProps = {
  eventId: number;
  graphId: string;
};

type BusinessComponent = {
  component_id?: string;
  component_name?: string;
  plant_id?: string;
  plant_name?: string;
  gross_lost_supply?: number;
  alternative_recovery?: number;
  gross_shortage?: number;
  inventory_quantity?: number;
  inventory_coverage_days?: number;
  daily_demand?: number;
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
  gross_component_exposure?: number;
  component_shortage?: number;
  estimated_product_shortage?: number;
  daily_demand_units?: number;
  estimated_delay_days?: number;
  inventory_protected?: boolean;
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
  match_reasons?: string[];
};

type BusinessSimulation = {
  success?: boolean;
  status?: string;

  supplier?: {
    supplier_id?: string;
    name?: string;
    country?: string;
    city?: string;
  };

  components?: BusinessComponent[];

  products?: BusinessProduct[];

  plants?: Array<{
    plant_id?: string;
    plant_name?: string;
    affected_components?: number;
    affected_products?: number;
    max_delay_days?: number;
    max_risk_score?: number;
    production_stop?: boolean;
    risk_level?: string;
  }>;

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
    products_buffered?: number;
    products_with_shortage?: number;
  };
};

type BusinessIntelligence = {
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

type PredictionData = {
  baseRisk: number;
  gnnRisk: number;
  hybridRisk: number;
  riskLevel: string;
  delayDays: number;
  suppliers: string[];
  products: string[];

  nodePredictions: Array<{
    node: string;
    node_type?: string;
    risk_score: number;
  }>;

  ruleWeight: number;
  gnnWeight: number;
};

function normalizeRisk(value: unknown): number {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : 0;
}

function getRiskLevel(score: number): string {
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

function normalizeBusinessResult(
  value: any
): BusinessIntelligence | null {
  if (!value) {
    return null;
  }

  const root =
    value?.business_supply_chain ??
    value?.data?.business_supply_chain ??
    value;

  const summary =
    root?.summary;

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
            (item: BusinessSimulation) =>
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
              (item: BusinessSimulation) =>
                Boolean(item)
            )
        : [];

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

  if (
    !summary &&
    simulations.length === 0 &&
    suppliers.length === 0
  ) {
    return null;
  }

  const allSummaries =
    simulations
      .map(
        (
          item: BusinessSimulation
        ) => item.summary
      )
      .filter(
        (
          item:
            | BusinessSimulation["summary"]
            | undefined
        ): item is NonNullable<
          BusinessSimulation["summary"]
        > => Boolean(item)
      );

  const maxRisk = Math.max(
    normalizeRisk(
      summary?.max_risk
    ),
    ...allSummaries.map(
      (
        item: NonNullable<
          BusinessSimulation["summary"]
        >
      ): number =>
        normalizeRisk(
          item.max_risk_score
        )
    )
  );

  const confidenceValues: number[] =
    simulations.flatMap(
      (
        simulation: BusinessSimulation
      ): number[] =>
        (simulation.components ?? [])
          .map(
            (
              component: BusinessComponent
            ): number =>
              normalizeRisk(
                component.confidence
              )
          )
          .filter(
            (value: number): boolean =>
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
        normalizeRisk(
          summary?.affected_components
        ),

      affected_products:
        normalizeRisk(
          summary?.affected_products
        ),

      affected_plants:
        normalizeRisk(
          summary?.affected_plants
        ),

      gross_lost_supply:
        normalizeRisk(
          summary?.gross_lost_supply
        ),

      alternative_recovery:
        normalizeRisk(
          summary?.alternative_recovery
        ),

      net_shortage:
        normalizeRisk(
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

function getStoredBusinessSimulation():
  BusinessIntelligence | null {
  try {
    const raw =
      localStorage.getItem(
        "atmograph:last-supplier-simulation"
      );

    if (!raw) {
      return null;
    }

    return normalizeBusinessResult(
      JSON.parse(raw)
    );
  } catch {
    return null;
  }
}

function extractPrediction(
  hybrid: any,
  gnn: any
): PredictionData {
  const hybridData =
    hybrid?.data ??
    hybrid;

  const prediction =
    hybridData?.prediction ??
    hybridData;

  const base =
    prediction?.base_prediction ??
    {};

  const gnnPrediction =
    prediction?.gnn_prediction ??
    gnn?.data ??
    gnn ??
    {};

  const hybridPrediction =
    prediction?.hybrid_prediction ??
    {};

  const baseRisk =
    normalizeRisk(
      base?.risk_score
    );

  const gnnRisk =
    normalizeRisk(
      gnnPrediction?.risk_score
    );

  const hybridRisk =
    normalizeRisk(
      hybridPrediction?.risk_score ??
        prediction?.risk_score
    );

  const nodePredictions =
    Array.isArray(
      gnnPrediction?.node_predictions
    )
      ? gnnPrediction.node_predictions
      : Array.isArray(
          prediction?.node_predictions
        )
        ? prediction.node_predictions
        : [];

  return {
    baseRisk,

    gnnRisk,

    hybridRisk,

    riskLevel:
      String(
        hybridPrediction?.risk_level ??
          prediction?.risk_level ??
          getRiskLevel(
            hybridRisk
          )
      ).toLowerCase(),

    delayDays:
      normalizeRisk(
        base?.estimated_delay_days
      ),

    suppliers:
      Array.isArray(
        base?.affected_suppliers
      )
        ? base.affected_suppliers
        : [],

    products:
      Array.isArray(
        base?.affected_products
      )
        ? base.affected_products
        : [],

    nodePredictions:
      nodePredictions.map(
        (item: any) => ({
          node: String(
            item?.node ??
              "Unknown"
          ),

          node_type:
            item?.node_type ??
            item?.nodeType,

          risk_score:
            normalizeRisk(
              item?.risk_score ??
                item?.score
            ),
        })
      ),

    ruleWeight:
      normalizeRisk(
        prediction?.weights
          ?.rule_based
      ),

    gnnWeight:
      normalizeRisk(
        prediction?.weights
          ?.gnn
      ),
  };
}

function RiskBadge({
  level,
}: {
  level: string;
}) {
  return (
    <span
      className={`prediction-risk-badge ${level}`}
    >
      <span />
      {level.toUpperCase()}
    </span>
  );
}

function MetricCard({
  icon,
  label,
  value,
  suffix,
  description,
  level,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  suffix?: string;
  description: string;
  level?: string;
}) {
  return (
    <div
      className={`prediction-metric-card ${
        level
          ? `metric-${level}`
          : ""
      }`}
    >
      <div className="prediction-metric-icon">
        {icon}
      </div>

      <span className="prediction-metric-label">
        {label}
      </span>

      <strong>
        {value}

        {suffix && (
          <small>
            {suffix}
          </small>
        )}
      </strong>

      <span className="prediction-metric-description">
        {description}
      </span>
    </div>
  );
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

export default function PredictionIntelligence({
  eventId,
  graphId,
}: PredictionIntelligenceProps) {
  const [
    prediction,
    setPrediction,
  ] =
    useState<PredictionData | null>(
      null
    );

  const [
    business,
    setBusiness,
  ] =
    useState<BusinessIntelligence | null>(
      getStoredBusinessSimulation
    );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const loadPrediction =
    useCallback(async () => {
      try {
        setLoading(true);
        setError("");

        const [
          hybridResult,
          gnnResult,
        ] = await Promise.all([
          getHybridPrediction(
            eventId,
            graphId
          ),

          getGnnPrediction(
            graphId
          ),
        ]);

        setPrediction(
          extractPrediction(
            hybridResult,
            gnnResult
          )
        );

        const latestBusiness =
          getStoredBusinessSimulation();

        if (latestBusiness) {
          setBusiness(
            latestBusiness
          );
        }
      } catch (exception) {
        console.error(
          "Prediction loading failed:",
          exception
        );

        setError(
          exception instanceof Error
            ? exception.message
            : "Unable to load prediction."
        );
      } finally {
        setLoading(false);
      }
    }, [
      eventId,
      graphId,
    ]);

  useEffect(() => {
    loadPrediction();
  }, [loadPrediction]);

  useEffect(() => {
    const handleSimulation =
      (event: Event) => {
        const customEvent =
          event as CustomEvent;

        const next =
          normalizeBusinessResult(
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

  const averageNodeRisk =
    useMemo(() => {
      if (
        !prediction ||
        prediction
          .nodePredictions
          .length === 0
      ) {
        return 0;
      }

      const total =
        prediction
          .nodePredictions
          .reduce(
            (
              sum: number,
              item: {
                node: string;
                node_type?: string;
                risk_score: number;
              }
            ): number =>
              sum +
              item.risk_score,
            0
          );

      return (
        total /
        prediction
          .nodePredictions
          .length
      );
    }, [prediction]);

  const businessRisk =
    business?.summary.max_risk ??
    0;

  const businessRiskLevel =
    getRiskLevel(
      businessRisk
    );

  const businessDelay =
    business?.simulations.reduce(
      (
        max: number,
        simulation: BusinessSimulation
      ): number =>
        Math.max(
          max,
          ...(simulation.components ??
            []).map(
            (
              component: BusinessComponent
            ): number =>
              normalizeRisk(
                component.estimated_delay_days
              )
          )
        ),
      0
    ) ?? 0;

  if (loading) {
    return (
      <div className="prediction-loading">
        <RefreshCw
          size={20}
          className="spin"
        />

        <span>
          Running prediction intelligence...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="prediction-error">

        <AlertTriangle
          size={18}
        />

        <div>

          <strong>
            Prediction unavailable
          </strong>

          <span>
            {error}
          </span>

        </div>

        <button
          className="primary-button"
          onClick={loadPrediction}
        >
          Retry
        </button>

      </div>
    );
  }

  return (
    <div className="dashboard-content">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="page-heading">

        <div>

          <span className="eyebrow">
            PREDICTIVE INTELLIGENCE
          </span>

          <h2>
            Risk Predictions
          </h2>

          <p>
            Business supply-chain impact is
            the primary decision signal for
            Event #{eventId}.
          </p>

        </div>

        <button
          className="primary-button"
          onClick={loadPrediction}
        >

          <RefreshCw
            size={15}
          />

          Recalculate

        </button>

      </div>

      {/* =====================================================
          PRIMARY BUSINESS RISK
      ===================================================== */}

      {business && (
        <section className="prediction-hero">

          <div className="prediction-hero-main">

            <div className="prediction-hero-icon">

              <ShieldAlert
                size={25}
              />

            </div>

            <div>

              <span>
                BUSINESS SUPPLY-CHAIN RISK
              </span>

              <div className="prediction-hero-score">

                {businessRisk.toFixed(
                  0
                )}

              </div>

              <RiskBadge
                level={
                  businessRiskLevel
                }
              />

            </div>

          </div>

          <div className="prediction-hero-details">

            <div>

              <span>
                COMPONENTS
              </span>

              <strong>
                {
                  business.summary
                    .affected_components
                }
              </strong>

            </div>

            <div>

              <span>
                PRODUCTS
              </span>

              <strong>
                {
                  business.summary
                    .affected_products
                }
              </strong>

            </div>

            <div>

              <span>
                PLANTS
              </span>

              <strong>
                {
                  business.summary
                    .affected_plants
                }
              </strong>

            </div>

            <div>

              <span>
                CONFIDENCE
              </span>

              <strong>

                {(
                  business.confidence *
                  100
                ).toFixed(0)}

                <small>
                  %
                </small>

              </strong>

            </div>

          </div>

        </section>
      )}

      {/* =====================================================
          BUSINESS METRICS
      ===================================================== */}

      {business && (
        <section className="prediction-metrics-grid">

          <MetricCard
            icon={
              <Boxes size={19} />
            }
            label="GROSS LOST SUPPLY"
            value={formatNumber(
              business.summary
                .gross_lost_supply
            )}
            description="Supply exposed by failed supplier"
          />

          <MetricCard
            icon={
              <Truck size={19} />
            }
            label="ALTERNATIVE RECOVERY"
            value={formatNumber(
              business.summary
                .alternative_recovery
            )}
            description="Recoverable supply from alternatives"
          />

          <MetricCard
            icon={
              <Target size={19} />
            }
            label="NET SHORTAGE"
            value={formatNumber(
              business.summary
                .net_shortage
            )}
            description="Remaining shortage after inventory and recovery"
            level={
              business.summary
                .net_shortage > 0
                ? "high"
                : "low"
            }
          />

          <MetricCard
            icon={
              <Clock3 size={19} />
            }
            label="ESTIMATED DELAY"
            value={formatNumber(
              businessDelay
            )}
            suffix="days"
            description="Maximum simulated business delay"
          />

        </section>
      )}

      {/* =====================================================
          DECISION STATUS
      ===================================================== */}

      {business && (
        <section className="panel prediction-method-panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                DECISION INTELLIGENCE
              </span>

              <h3>
                Current Supply Chain Status
              </h3>

            </div>

            <Target size={18} />

          </div>

          <div className="prediction-composition">

            <div className="composition-block">

              <div className="composition-top">

                <ShieldAlert
                  size={17}
                />

                <span>
                  RISK
                </span>

              </div>

              <strong>
                {businessRisk.toFixed(
                  0
                )}
              </strong>

              <div className="composition-weight">
                {businessRiskLevel.toUpperCase()}
              </div>

            </div>

            <div className="composition-operator">
              →
            </div>

            <div className="composition-block">

              <div className="composition-top">

                <Boxes
                  size={17}
                />

                <span>
                  NET SHORTAGE
                </span>

              </div>

              <strong>
                {formatNumber(
                  business.summary
                    .net_shortage
                )}
              </strong>

              <div className="composition-weight">
                units
              </div>

            </div>

            <div className="composition-operator">
              →
            </div>

            <div className="composition-block composition-result">

              <div className="composition-top">

                <Target
                  size={17}
                />

                <span>
                  PRODUCTION
                </span>

              </div>

              <strong>
                {
                  business.summary
                    .production_stop
                    ? "STOP"
                    : "RUNNING"
                }
              </strong>

              <div className="composition-weight">

                {
                  business.summary
                    .production_stop
                    ? "IMMEDIATE ACTION REQUIRED"
                    : "INVENTORY BUFFER AVAILABLE"
                }

              </div>

            </div>

          </div>

        </section>
      )}

      {/* =====================================================
          SUPPLIERS / PRODUCTS
      ===================================================== */}

      {business && (
        <div className="prediction-impact-grid">

          <section className="panel">

            <div className="panel-header">

              <div>

                <span className="panel-kicker">
                  BUSINESS EXPOSURE
                </span>

                <h3>
                  Affected Suppliers
                </h3>

              </div>

              <Truck size={18} />

            </div>

            {business.suppliers.length ===
            0 ? (

              <div className="prediction-empty">
                No matched business suppliers.
              </div>

            ) : (

              <div className="prediction-entity-list">

                {business.suppliers.map(
                  (
                    supplier: BusinessSupplier,
                    index: number
                  ) => (

                    <div
                      className="prediction-entity"
                      key={
                        supplier.supplier_id ??
                        index
                      }
                    >

                      <div className="prediction-entity-icon">

                        <Truck
                          size={16}
                        />

                      </div>

                      <span>
                        {supplier.name ??
                          supplier.supplier_id ??
                          "Unknown supplier"}
                      </span>

                      <small>
                        {supplier.match_score ??
                          0}
                        %
                      </small>

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
                  PRODUCTION EXPOSURE
                </span>

                <h3>
                  Affected Products
                </h3>

              </div>

              <Boxes size={18} />

            </div>

            {business.simulations
              .flatMap(
                (
                  simulation: BusinessSimulation
                ) =>
                  simulation.products ??
                  []
              ).length === 0 ? (

              <div className="prediction-empty">
                No affected products.
              </div>

            ) : (

              <div className="prediction-entity-list">

                {business.simulations
                  .flatMap(
                    (
                      simulation: BusinessSimulation
                    ) =>
                      simulation.products ??
                      []
                  )
                  .map(
                    (
                      product: BusinessProduct,
                      index: number
                    ) => (

                      <div
                        className="prediction-entity"
                        key={
                          product.product_id ??
                          index
                        }
                      >

                        <div className="prediction-entity-icon product">

                          <Boxes
                            size={16}
                          />

                        </div>

                        <span>
                          {product.product_name ??
                            "Unknown product"}
                        </span>

                        <small>

                          {String(
                            product.exposure_status ??
                              "exposed"
                          ).toUpperCase()}

                        </small>

                      </div>

                    )
                  )}

              </div>

            )}

          </section>

        </div>
      )}

      {/* =====================================================
          COMPONENT IMPACT
      ===================================================== */}

      {business && (
        <section className="panel prediction-node-panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                COMPONENT FORENSICS
              </span>

              <h3>
                Component-Level Exposure
              </h3>

            </div>

            <span className="prediction-node-count">

              {
                business.simulations
                  .flatMap(
                    (
                      simulation: BusinessSimulation
                    ) =>
                      simulation.components ??
                      []
                  ).length
              }

              {" "}components

            </span>

          </div>

          <div className="prediction-node-table">

            <div className="prediction-table-head">

              <span>
                COMPONENT
              </span>

              <span>
                INVENTORY
              </span>

              <span>
                COVERAGE
              </span>

              <span>
                RISK
              </span>

            </div>

            {business.simulations
              .flatMap(
                (
                  simulation: BusinessSimulation
                ) =>
                  simulation.components ??
                  []
              )
              .map(
                (
                  component: BusinessComponent,
                  index: number
                ) => {

                  const risk =
                    normalizeRisk(
                      component.risk_score
                    );

                  const level =
                    String(
                      component.risk_level ??
                        getRiskLevel(
                          risk
                        )
                    ).toLowerCase();

                  return (
                    <div
                      className="prediction-table-row"
                      key={
                        component.component_id ??
                        index
                      }
                    >

                      <div className="prediction-node-name">

                        <div>
                          <Boxes
                            size={14}
                          />
                        </div>

                        <strong>
                          {component.component_name ??
                            "Unknown component"}
                        </strong>

                      </div>

                      <span>
                        {formatNumber(
                          normalizeRisk(
                            component.inventory_quantity
                          )
                        )}
                      </span>

                      <span>
                        {formatNumber(
                          normalizeRisk(
                            component.inventory_coverage_days
                          )
                        )}
                        d
                      </span>

                      <RiskBadge
                        level={level}
                      />

                    </div>
                  );
                }
              )}

          </div>

        </section>
      )}

      {/* =====================================================
          MODEL DIAGNOSTICS
      ===================================================== */}

      {prediction && (
        <section className="panel prediction-method-panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                MODEL DIAGNOSTICS
              </span>

              <h3>
                Graph Model Diagnostics
              </h3>

              <p>
                Legacy rule-based and GNN
                outputs are supporting diagnostics.
                Business simulation remains the
                primary decision signal.
              </p>

            </div>

            <Brain size={18} />

          </div>

          <div className="prediction-composition">

            <div className="composition-block">

              <div className="composition-top">

                <Calculator
                  size={17}
                />

                <span>
                  RULE ENGINE
                </span>

              </div>

              <strong>
                {prediction.baseRisk.toFixed(
                  2
                )}
              </strong>

            </div>

            <div className="composition-operator">
              +
            </div>

            <div className="composition-block">

              <div className="composition-top">

                <Brain
                  size={17}
                />

                <span>
                  GNN
                </span>

              </div>

              <strong>
                {prediction.gnnRisk.toFixed(
                  2
                )}
              </strong>

            </div>

            <div className="composition-operator">
              =
            </div>

            <div className="composition-block">

              <div className="composition-top">

                <Target
                  size={17}
                />

                <span>
                  HYBRID
                </span>

              </div>

              <strong>
                {prediction.hybridRisk.toFixed(
                  2
                )}
              </strong>

              <div className="composition-weight">
                Supporting signal
              </div>

            </div>

          </div>

          <div className="prediction-note">

            <Brain size={14} />

            <span>
              Node-average GNN risk:{" "}
              {averageNodeRisk.toFixed(2)}
              . This diagnostic is not used
              as the primary business risk
              displayed above.
            </span>

          </div>

        </section>
      )}

      {/* =====================================================
          FOOTNOTE
      ===================================================== */}

      <div className="prediction-note">

        <AlertTriangle
          size={14}
        />

        <span>
          Business risk combines the actual
          supply-chain structure, supplier
          allocation, inventory, alternative
          capacity, demand, dependencies and
          simulation results. Unknown information
          is not treated as confirmed impact.
        </span>

      </div>

    </div>
  );
}
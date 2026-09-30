import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertTriangle,
  Boxes,
  Factory,
  Network,
  Package,
  RefreshCw,
  Truck,
} from "lucide-react";

import {
  getEventImpactGraph,
} from "../../services/api";


interface EventImpactOverlayProps {
  eventId?: number | null;
}


interface ImpactResponse {
  success?: boolean;

  event_id?: number;

  event?: {
    id?: number;
    title?: string;
    event_type?: string;
    location?: string | null;
    severity?: string;
    status?: string;
  };

  counts?: {
    nodes?: number;
    relationships?: number;
    suppliers?: number;
    components?: number;
    plants?: number;
    products?: number;
  };

  affected_node_ids?: string[];

  failed_node_ids?: string[];

  nodes?: Array<{
    id?: string;
    type?: string;
    name?: string;
    affected?: boolean;
    failed?: boolean;
    properties?: Record<
      string,
      unknown
    >;
  }>;

  relationships?: Array<{
    source?: string;
    target?: string;
    relationship?: string;
    affected?: boolean;
  }>;
}


function number(
  value: unknown
): number {
  const parsed =
    Number(value);

  return Number.isFinite(
    parsed
  )
    ? parsed
    : 0;
}


function title(
  value: unknown
): string {
  return String(
    value ?? ""
  );
}


function severityClass(
  severity?: string
) {
  const value =
    String(
      severity ?? "unknown"
    )
      .toLowerCase();

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
    value === "medium"
  ) {
    return "medium";
  }

  return "low";
}


export default function EventImpactOverlay({
  eventId,
}: EventImpactOverlayProps) {

  const [
    data,
    setData,
  ] =
    useState<
      ImpactResponse | null
    >(null);

  const [
    loading,
    setLoading,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState("");


  const load =
    useCallback(
      async () => {

        if (
          !eventId
        ) {
          setData(null);
          return;
        }

        setLoading(true);
        setError("");

        try {

          const result =
            await getEventImpactGraph(
              eventId
            );

          setData(
            result
          );

        } catch (
          err: any
        ) {

          console.error(
            "Event impact graph error:",
            err
          );

          setData(null);

          setError(
            err?.message ??
              "Unable to load event impact graph."
          );

        } finally {

          setLoading(false);

        }

      },
      [eventId]
    );


  useEffect(() => {

    void load();

  }, [load]);


  const affectedNodes =
    useMemo(
      () =>
        Array.isArray(
          data?.nodes
        )
          ? data.nodes.filter(
              node =>
                node.affected
            )
          : [],
      [data]
    );


  const affectedRelationships =
    useMemo(
      () =>
        Array.isArray(
          data?.relationships
        )
          ? data.relationships.filter(
              relationship =>
                relationship.affected
            )
          : [],
      [data]
    );


  if (!eventId) {

    return (
      <section className="panel event-impact-overlay">

        <div className="panel-kicker">
          EVENT GRAPH OVERLAY
        </div>

        <div className="empty-state">

          <Network
            size={18}
          />

          <span>
            Run an intelligence analysis
            to activate the event impact graph.
          </span>

        </div>

      </section>
    );
  }


  return (
    <section className="panel event-impact-overlay">

      <div className="result-header">

        <div>

          <span className="panel-kicker">
            EVENT GRAPH OVERLAY
          </span>

          <h3>
            Operational impact map
          </h3>

          <p>
            Event #{eventId} mapped against
            the canonical business supply chain.
          </p>

        </div>

        <button
          className="secondary-button"
          onClick={() =>
            void load()
          }
          disabled={loading}
          title="Refresh impact graph"
        >
          <RefreshCw
            size={14}
          />

          {loading
            ? "Loading..."
            : "Refresh"}
        </button>

      </div>


      {error && (

        <div className="empty-state">

          <AlertTriangle
            size={16}
          />

          {error}

        </div>

      )}


      {loading && !data && (

        <div className="empty-state">

          <RefreshCw
            size={16}
          />

          Loading operational impact...

        </div>
      )}


      {data && !error && (

        <>

          <div className="event-impact-event">

            <div>

              <span className="panel-kicker">
                ACTIVE EVENT
              </span>

              <strong>
                {title(
                  data.event?.title
                ) ||
                  `Event #${eventId}`}
              </strong>

            </div>

            <div
              className={`risk-badge ${severityClass(
                data.event?.severity
              )}`}
            >
              {String(
                data.event?.severity ??
                  "unknown"
              ).toUpperCase()}
            </div>

          </div>


          <div className="result-kpi-grid">

            <div className="result-kpi">

              <span>
                <Truck size={12} />
                SUPPLIERS
              </span>

              <strong>
                {number(
                  data.counts?.suppliers
                )}
              </strong>

            </div>


            <div className="result-kpi">

              <span>
                <Boxes size={12} />
                COMPONENTS
              </span>

              <strong>
                {number(
                  data.counts?.components
                )}
              </strong>

            </div>


            <div className="result-kpi">

              <span>
                <Factory size={12} />
                PLANTS
              </span>

              <strong>
                {number(
                  data.counts?.plants
                )}
              </strong>

            </div>


            <div className="result-kpi">

              <span>
                <Package size={12} />
                PRODUCTS
              </span>

              <strong>
                {number(
                  data.counts?.products
                )}
              </strong>

            </div>

          </div>


          <div className="event-impact-flow">

            <div className="event-impact-flow-node event">

              <AlertTriangle
                size={16}
              />

              <span>
                EVENT
              </span>

              <strong>
                #{eventId}
              </strong>

            </div>


            <div className="event-impact-arrow">
              →
            </div>


            <div className="event-impact-flow-node failed">

              <Truck
                size={16}
              />

              <span>
                SUPPLIERS
              </span>

              <strong>
                {number(
                  data.counts?.suppliers
                )}
              </strong>

            </div>


            <div className="event-impact-arrow">
              →
            </div>


            <div className="event-impact-flow-node">

              <Boxes
                size={16}
              />

              <span>
                COMPONENTS
              </span>

              <strong>
                {number(
                  data.counts?.components
                )}
              </strong>

            </div>


            <div className="event-impact-arrow">
              →
            </div>


            <div className="event-impact-flow-node">

              <Factory
                size={16}
              />

              <span>
                PLANTS
              </span>

              <strong>
                {number(
                  data.counts?.plants
                )}
              </strong>

            </div>


            <div className="event-impact-arrow">
              →
            </div>


            <div className="event-impact-flow-node">

              <Package
                size={16}
              />

              <span>
                PRODUCTS
              </span>

              <strong>
                {number(
                  data.counts?.products
                )}
              </strong>

            </div>

          </div>


          <div className="event-impact-details">

            <div>

              <span>
                AFFECTED NODES
              </span>

              <strong>
                {affectedNodes.length}
              </strong>

            </div>


            <div>

              <span>
                AFFECTED RELATIONSHIPS
              </span>

              <strong>
                {
                  affectedRelationships.length
                }
              </strong>

            </div>


            <div>

              <span>
                LOCATION
              </span>

              <strong>
                {title(
                  data.event?.location
                ) || "Unknown"}
              </strong>

            </div>


            <div>

              <span>
                EVENT TYPE
              </span>

              <strong>
                {title(
                  data.event?.event_type
                ) ||
                  "Unknown"}
              </strong>

            </div>

          </div>


          <div className="event-impact-note">

            <Network
              size={14}
            />

            <span>
              This overlay uses the operational
              business supply-chain relationships.
              GNN prediction remains a separate
              predictive signal.
            </span>

          </div>

        </>
      )}

    </section>
  );
}
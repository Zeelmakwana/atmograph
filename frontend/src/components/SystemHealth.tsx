import {
  Activity,
  Brain,
  CheckCircle2,
  Database,
  GitBranch,
  Network,
  RefreshCw,
  Server,
  XCircle,
} from "lucide-react";

import {
  getGraphStatistics,
  getGnnPrediction,
} from "../services/api";

import { connectAtmoGraphWebSocket } from "../services/websocket";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

type Status =
  | "online"
  | "offline"
  | "checking";

type HealthState = {
  api: Status;
  neo4j: Status;
  database: Status;
  gnn: Status;
  nlp: Status;
  websocket: Status;
};

const initialHealth: HealthState = {
  api: "checking",
  neo4j: "checking",
  database: "checking",
  gnn: "checking",
  nlp: "checking",
  websocket: "checking",
};

function unwrap(value: any) {
  return value?.data ?? value;
}

function StatusIcon({
  status,
}: {
  status: Status;
}) {
  if (status === "online") {
    return <CheckCircle2 size={18} />;
  }

  if (status === "offline") {
    return <XCircle size={18} />;
  }

  return (
    <RefreshCw
      size={18}
      className="spin"
    />
  );
}

function statusLabel(status: Status) {
  if (status === "online") {
    return "ONLINE";
  }

  if (status === "offline") {
    return "OFFLINE";
  }

  return "CHECKING";
}

export default function SystemHealth() {
  const [health, setHealth] =
    useState<HealthState>(
      initialHealth
    );

  const [graphStats, setGraphStats] =
    useState<any>(null);

  const [lastChecked, setLastChecked] =
    useState("--");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const websocketRef =
    useRef<WebSocket | null>(null);

  const checkHealth =
    useCallback(async () => {
      setLoading(true);
      setError("");

      setHealth(initialHealth);

      let api: Status = "offline";
      let neo4j: Status = "offline";
      let database: Status = "offline";
      let gnn: Status = "offline";
      let nlp: Status = "offline";
      let websocket: Status = "offline";

      /*
       * --------------------------------------------------------
       * FASTAPI
       * --------------------------------------------------------
       */

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/health`,
            {
              signal:
                AbortSignal.timeout(5000),
            }
          );

        api = response.ok
          ? "online"
          : "offline";
      } catch {
        api = "offline";
      }

      /*
       * --------------------------------------------------------
       * NEO4J
       * --------------------------------------------------------
       */

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/api/graph/status`,
            {
              signal:
                AbortSignal.timeout(5000),
            }
          );

        if (!response.ok) {
          throw new Error(
            "Neo4j status failed"
          );
        }

        const result =
          await response.json();

        const data =
          unwrap(result);

        neo4j =
          data?.connected === true ||
          data?.success === true
            ? "online"
            : "offline";
      } catch {
        neo4j = "offline";
      }

      /*
       * --------------------------------------------------------
       * DATABASE / GRAPH DATA
       * --------------------------------------------------------
       */

      try {
        const result =
          await getGraphStatistics();

        const data =
          unwrap(result);

        setGraphStats(data);

        database =
          "online";
      } catch {
        database = "offline";
      }

      /*
       * --------------------------------------------------------
       * GNN
       *
       * Don't use a hard-coded event_23 anymore.
       *
       * Test the model using the newest event returned
       * from /api/events.
       * --------------------------------------------------------
       */

      try {
        const eventsResponse =
          await fetch(
            `${API_BASE_URL}/api/events?limit=1`,
            {
              signal:
                AbortSignal.timeout(5000),
            }
          );

        let graphId =
          "event_25";

        if (eventsResponse.ok) {
          const eventsResult =
            await eventsResponse.json();

          const eventsData =
            unwrap(eventsResult);

          const events =
            Array.isArray(eventsData)
              ? eventsData
              : Array.isArray(
                    eventsData?.events
                  )
                ? eventsData.events
                : [];

          if (events.length > 0) {
            const event =
              events[0];

            graphId =
              String(
                event?.graph_id ||
                `event_${
                  event?.id ??
                  event?.event_id
                }`
              );
          }
        }

        const prediction =
          await getGnnPrediction(
            graphId
          );

        const data =
          unwrap(prediction);

        /*
         * The endpoint successfully responding means
         * the GNN inference service is available.
         *
         * Don't require a particular property name
         * such as model_loaded.
         */

        gnn =
          prediction != null &&
          data != null
            ? "online"
            : "offline";
      } catch {
        gnn = "offline";
      }

      /*
       * --------------------------------------------------------
       * NLP
       *
       * Use the actual NLP POST endpoint.
       * It does not create an Event; it only analyzes text.
       * --------------------------------------------------------
       */

      try {
        const response =
          await fetch(
            `${API_BASE_URL}/api/nlp/analyze`,
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
              },
              body: JSON.stringify({
                title:
                  "Health check",
                description:
                  "Supply chain disruption health check",
              }),
              signal:
                AbortSignal.timeout(10000),
            }
          );

        nlp =
          response.ok
            ? "online"
            : "offline";
      } catch {
        nlp = "offline";
      }

      /*
       * --------------------------------------------------------
       * WEBSOCKET
       *
       * Actually open a WebSocket and mark it online only
       * when the browser receives a successful open event.
       * --------------------------------------------------------
       */

      try {
        const socket =
          connectAtmoGraphWebSocket(
            () => {
              setHealth(
                (current) => ({
                  ...current,
                  websocket:
                    "online",
                })
              );
            },
            () => {
              setHealth(
                (current) => ({
                  ...current,
                  websocket:
                    "offline",
                })
              );
            },
            () => {
              setHealth(
                (current) => ({
                  ...current,
                  websocket:
                    "offline",
                })
              );
            }
          );

        websocketRef.current =
          socket;

        await new Promise<void>(
          (resolve) => {
            const timeout =
              window.setTimeout(
                () => {
                  resolve();
                },
                3000
              );

            socket.addEventListener(
              "open",
              () => {
                window.clearTimeout(
                  timeout
                );

                websocket =
                  "online";

                resolve();
              },
              {
                once: true,
              }
            );

            socket.addEventListener(
              "error",
              () => {
                window.clearTimeout(
                  timeout
                );

                websocket =
                  "offline";

                resolve();
              },
              {
                once: true,
              }
            );
          }
        );
      } catch {
        websocket = "offline";
      }

      setHealth({
        api,
        neo4j,
        database,
        gnn,
        nlp,
        websocket,
      });

      setLastChecked(
        new Date().toLocaleTimeString()
      );

      if (
        api === "offline" ||
        neo4j === "offline" ||
        database === "offline"
      ) {
        setError(
          "One or more core services are unavailable."
        );
      }

      setLoading(false);
    }, []);

  useEffect(() => {
    checkHealth();

    return () => {
      if (
        websocketRef.current
      ) {
        websocketRef.current.close();
        websocketRef.current =
          null;
      }
    };
  }, [checkHealth]);

  const totalNodes =
    Number(
      graphStats?.total_nodes ??
      0
    );

  const totalRelationships =
    Number(
      graphStats?.total_relationships ??
      0
    );

  const onlineCount =
    Object.values(
      health
    ).filter(
      (status) =>
        status === "online"
    ).length;

  const totalServices =
    Object.keys(
      health
    ).length;

  const allOperational =
    onlineCount ===
    totalServices;

  return (
    <div className="dashboard-content">

      <div className="page-heading">
        <div>
          <span className="eyebrow">
            SYSTEM MONITORING
          </span>

          <h2>
            System Health
          </h2>

          <p>
            Live status of AtmoGraph's
            intelligence infrastructure.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={checkHealth}
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
            ? "Checking..."
            : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="ripple-error">
          <XCircle size={17} />

          <span>
            {error}
          </span>
        </div>
      )}

      <section className="health-overview">

        <div className="health-overview-card">
          <div className="health-overview-icon">
            <Activity size={21} />
          </div>

          <div>
            <span>
              PLATFORM STATUS
            </span>

            <strong>
              {allOperational
                ? "ALL SYSTEMS OPERATIONAL"
                : `${totalServices - onlineCount} SERVICE${
                    totalServices -
                      onlineCount ===
                    1
                      ? ""
                      : "S"
                  } UNAVAILABLE`}
            </strong>
          </div>
        </div>

        <div className="health-overview-card">
          <div className="health-overview-icon">
            <Network size={21} />
          </div>

          <div>
            <span>
              GRAPH NODES
            </span>

            <strong>
              {totalNodes}
            </strong>
          </div>
        </div>

        <div className="health-overview-card">
          <div className="health-overview-icon">
            <GitBranch size={21} />
          </div>

          <div>
            <span>
              RELATIONSHIPS
            </span>

            <strong>
              {totalRelationships}
            </strong>
          </div>
        </div>

        <div className="health-overview-card">
          <div className="health-overview-icon">
            <Activity size={21} />
          </div>

          <div>
            <span>
              LAST CHECK
            </span>

            <strong>
              {lastChecked}
            </strong>
          </div>
        </div>

      </section>

      <section className="health-grid">

        <HealthCard
          icon={<Server size={20} />}
          title="FastAPI"
          description="Application API"
          status={health.api}
        />

        <HealthCard
          icon={<Network size={20} />}
          title="Neo4j"
          description="Knowledge graph"
          status={health.neo4j}
        />

        <HealthCard
          icon={<Database size={20} />}
          title="Database"
          description="Application data"
          status={health.database}
        />

        <HealthCard
          icon={<Brain size={20} />}
          title="AtmoGraph GNN"
          description="Graph neural network"
          status={health.gnn}
        />

        <HealthCard
          icon={<Brain size={20} />}
          title="spaCy NLP"
          description="Entity extraction"
          status={health.nlp}
        />

        <HealthCard
          icon={<Activity size={20} />}
          title="WebSocket"
          description="Live intelligence"
          status={health.websocket}
        />

      </section>

      <section className="panel health-details">

        <div className="panel-header">
          <div>
            <span className="panel-kicker">
              INFRASTRUCTURE
            </span>

            <h3>
              AtmoGraph Runtime
            </h3>
          </div>
        </div>

        <div className="runtime-grid">

          <div>
            <span>API</span>
            <strong>
              {API_BASE_URL}
            </strong>
          </div>

          <div>
            <span>
              GRAPH ENGINE
            </span>

            <strong>
              Neo4j
            </strong>
          </div>

          <div>
            <span>
              ML ENGINE
            </span>

            <strong>
              PyTorch + PyG
            </strong>
          </div>

          <div>
            <span>
              NLP ENGINE
            </span>

            <strong>
              spaCy
            </strong>
          </div>

        </div>

      </section>

    </div>
  );
}

function HealthCard({
  icon,
  title,
  description,
  status,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  status: Status;
}) {
  return (
    <div
      className={`health-card health-${status}`}
    >
      <div className="health-card-icon">
        {icon}
      </div>

      <div className="health-card-content">
        <strong>
          {title}
        </strong>

        <span>
          {description}
        </span>
      </div>

      <div className="health-card-status">
        <StatusIcon
          status={status}
        />

        <span>
          {statusLabel(status)}
        </span>
      </div>
    </div>
  );
}
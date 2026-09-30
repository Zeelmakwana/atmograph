import { useEffect, useMemo, useState } from "react";

type HistoricalEvent = {
  id?: number;
  event_id?: number;
  title?: string;
  description?: string;
  source?: string;
  event_type?: string;
  location?: string | null;
  severity?: string;
  status?: string;
  graph_id?: string;
  cluster_id?: string;
  created_at?: string | null;
};

type Props = {
  onActivate?: (event: HistoricalEvent) => void | Promise<void>;
};

const API_BASE =
  "http://127.0.0.1:8000";

function eventIdOf(event: HistoricalEvent) {
  const value = Number(
    event?.id ??
      event?.event_id ??
      0
  );

  return Number.isFinite(value) && value > 0
    ? value
    : null;
}

function severityClass(value: unknown) {
  return String(value ?? "unknown")
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, "");
}

function formatDate(value: unknown) {
  if (!value) {
    return "--";
  }

  const date = new Date(String(value));

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

export default function HistoricalIntelligence({
  onActivate,
}: Props) {
  const [events, setEvents] = useState<
    HistoricalEvent[]
  >([]);

  const [clusters, setClusters] = useState<any[]>(
    []
  );

  const [timeline, setTimeline] = useState<
    HistoricalEvent[]
  >([]);

  const [replay, setReplay] = useState<any>(
    null
  );

  const [selectedEvent, setSelectedEvent] =
    useState<HistoricalEvent | null>(null);

  const [search, setSearch] =
    useState("");

  const [severity, setSeverity] =
    useState("");

  const [eventType, setEventType] =
    useState("");

  const [tab, setTab] =
    useState<
      "history" |
      "clusters" |
      "timeline" |
      "replay"
    >("history");

  const [loading, setLoading] =
    useState(false);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [activeEventId, setActiveEventId] =
    useState<number | null>(null);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError("");

      const params = new URLSearchParams();

      params.set("limit", "500");

      if (search.trim()) {
        params.set(
          "search",
          search.trim()
        );
      }

      if (severity) {
        params.set(
          "severity",
          severity
        );
      }

      if (eventType) {
        params.set(
          "event_type",
          eventType
        );
      }

      const response = await fetch(
        `${API_BASE}/api/historical-intelligence/history?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error(
          `History request failed: ${response.status}`
        );
      }

      const data = await response.json();

      setEvents(
        Array.isArray(data?.events)
          ? data.events
          : []
      );

      setClusters(
        Array.isArray(data?.clusters)
          ? data.clusters
          : []
      );
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load historical intelligence."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadClusters = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/historical-intelligence/clusters?limit=500`
      );

      if (!response.ok) {
        return;
      }

      const data = await response.json();

      setClusters(
        Array.isArray(data?.clusters)
          ? data.clusters
          : []
      );
    } catch (err) {
      console.error(
        "Unable to load clusters:",
        err
      );
    }
  };

  const loadTimeline = async (
    event: HistoricalEvent
  ) => {
    const id = eventIdOf(event);

    if (!id) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");

      setSelectedEvent(event);

      const response = await fetch(
        `${API_BASE}/api/historical-intelligence/timeline/${id}`
      );

      if (!response.ok) {
        throw new Error(
          `Timeline request failed: ${response.status}`
        );
      }

      const data = await response.json();

      setTimeline(
        Array.isArray(data?.timeline)
          ? data.timeline
          : []
      );

      setTab("timeline");
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load event timeline."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const loadReplay = async (
    event: HistoricalEvent
  ) => {
    const id = eventIdOf(event);

    if (!id) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");

      setSelectedEvent(event);

      const response = await fetch(
        `${API_BASE}/api/historical-intelligence/replay/${id}`
      );

      if (!response.ok) {
        throw new Error(
          `Replay request failed: ${response.status}`
        );
      }

      const data = await response.json();

      setReplay(
        data?.replay ?? null
      );

      setTab("replay");
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load event replay."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const activateEvent = async (
    event: HistoricalEvent
  ) => {
    const id = eventIdOf(event);

    if (!id) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");

      setSelectedEvent(event);
      setActiveEventId(id);

      if (onActivate) {
        await onActivate(event);
      }

      setTab("history");
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to activate historical event."
      );
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    void loadHistory();
    void loadClusters();

    const handleWorkspaceChange = () => {
      void loadHistory();
      void loadClusters();
    };

    window.addEventListener("atmograph:workspace-changed", handleWorkspaceChange);

    const stored = Number(
      localStorage.getItem(
        "atmograph_active_event_id"
      ) ?? ""
    );

    if (
      Number.isFinite(stored) &&
      stored > 0
    ) {
      setActiveEventId(stored);
    }

    return () => {
      window.removeEventListener("atmograph:workspace-changed", handleWorkspaceChange);
    };
  }, []);

  const eventTypes = useMemo(() => {
    return Array.from(
      new Set(
        events
          .map(
            (event) =>
              event.event_type
          )
          .filter(Boolean)
      )
    ).sort();
  }, [events]);

  const activeCluster = useMemo(() => {
    if (!selectedEvent) {
      return null;
    }

    return (
      clusters.find(
        (cluster) =>
          Array.isArray(
            cluster?.event_ids
          ) &&
          cluster.event_ids.includes(
            eventIdOf(selectedEvent)
          )
      ) ?? null
    );
  }, [
    clusters,
    selectedEvent,
  ]);

  return (
    <section
      className="panel historical-intelligence"
      style={{
        marginTop: 18,
      }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-kicker">
            HISTORICAL INTELLIGENCE
          </span>

          <h3>
            Event History & Replay
          </h3>

          <p>
            Browse previous disruptions,
            discover related event families,
            inspect timelines and activate
            historical events across AtmoGraph.
          </p>
        </div>

        <span className="success-badge">
          ● BUSINESS HISTORY
        </span>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "minmax(0, 1fr) 150px 190px auto",
          gap: 8,
          padding: "14px 16px",
          borderBottom:
            "1px solid rgba(148,163,184,0.12)",
        }}
      >
        <input
          value={search}
          onChange={(event) =>
            setSearch(event.target.value)
          }
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              void loadHistory();
            }
          }}
          placeholder="Search historical events..."
        />

        <select
          value={severity}
          onChange={(event) => {
            setSeverity(
              event.target.value
            );
          }}
        >
          <option value="">
            All severity
          </option>

          <option value="critical">
            Critical
          </option>

          <option value="high">
            High
          </option>

          <option value="medium">
            Medium
          </option>

          <option value="low">
            Low
          </option>
        </select>

        <select
          value={eventType}
          onChange={(event) => {
            setEventType(
              event.target.value
            );
          }}
        >
          <option value="">
            All event types
          </option>

          {eventTypes.map(
            (type) => (
              <option
                key={type}
                value={type}
              >
                {type}
              </option>
            )
          )}
        </select>

        <button
          className="secondary-button"
          onClick={() =>
            void loadHistory()
          }
          disabled={loading}
        >
          {loading
            ? "Loading..."
            : "Refresh"}
        </button>
      </div>

      <div
        style={{
          display: "flex",
          gap: 4,
          padding: "10px 16px",
          borderBottom:
            "1px solid rgba(148,163,184,0.12)",
        }}
      >
        {(
          [
            ["history", "Event History"],
            ["clusters", "Clusters"],
            ["timeline", "Timeline"],
            ["replay", "Replay"],
          ] as const
        ).map(
          ([value, label]) => (
            <button
              key={value}
              className={
                tab === value
                  ? "primary-button"
                  : "secondary-button"
              }
              style={{
                padding:
                  "7px 12px",
              }}
              onClick={() =>
                setTab(value)
              }
            >
              {label}
            </button>
          )
        )}
      </div>

      {error && (
        <div
          className="settings-success"
          style={{
            margin: 14,
          }}
        >
          {error}
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(4, minmax(0, 1fr))",
          gap: 8,
          padding: 14,
        }}
      >
        <div className="result-kpi">
          <span>EVENTS</span>
          <strong>
            {events.length}
          </strong>
        </div>

        <div className="result-kpi">
          <span>EVENT FAMILIES</span>
          <strong>
            {clusters.length}
          </strong>
        </div>

        <div className="result-kpi">
          <span>ACTIVE EVENT</span>
          <strong>
            {activeEventId
              ? `#${activeEventId}`
              : "--"}
          </strong>
        </div>

        <div className="result-kpi">
          <span>ACTIVE CLUSTER</span>
          <strong>
            {activeCluster?.cluster_id ??
              "--"}
          </strong>
        </div>
      </div>

      {tab === "history" && (
        <div
          style={{
            display: "grid",
            gap: 8,
            padding: "0 14px 16px",
          }}
        >
          {events.map(
            (event) => {
              const id =
                eventIdOf(event);

              const isActive =
                id === activeEventId;

              return (
                <div
                  key={id}
                  className="detail-card"
                  style={{
                    border:
                      isActive
                        ? "1px solid rgba(34,197,94,0.55)"
                        : undefined,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent:
                        "space-between",
                      gap: 16,
                      alignItems:
                        "flex-start",
                    }}
                  >
                    <div
                      style={{
                        flex: 1,
                      }}
                    >
                      <div
                        style={{
                          display:
                            "flex",
                          gap: 8,
                          alignItems:
                            "center",
                          flexWrap:
                            "wrap",
                        }}
                      >
                        <strong>
                          #{id}{" "}
                          {event.title ??
                            "Untitled event"}
                        </strong>

                        <span
                          className={`risk-badge ${severityClass(
                            event.severity
                          )}`}
                        >
                          {String(
                            event.severity ??
                              "unknown"
                          ).toUpperCase()}
                        </span>
                      </div>

                      <p
                        style={{
                          marginTop: 7,
                        }}
                      >
                        {event.description ??
                          "No description available."}
                      </p>

                      <small>
                        {event.location ??
                          "Location unknown"}{" "}
                        •{" "}
                        {event.source ??
                          "unknown source"}{" "}
                        •{" "}
                        {formatDate(
                          event.created_at
                        )}
                      </small>
                    </div>

                    <div
                      style={{
                        display:
                          "flex",
                        gap: 6,
                        flexWrap:
                          "wrap",
                        justifyContent:
                          "flex-end",
                      }}
                    >
                      <button
                        className="secondary-button"
                        onClick={() =>
                          void loadTimeline(
                            event
                          )
                        }
                      >
                        Timeline
                      </button>

                      <button
                        className="secondary-button"
                        onClick={() =>
                          void loadReplay(
                            event
                          )
                        }
                      >
                        Replay
                      </button>

                      <button
                        className="primary-button"
                        onClick={() =>
                          void activateEvent(
                            event
                          )
                        }
                        disabled={
                          actionLoading &&
                          isActive
                        }
                      >
                        {isActive
                          ? "ACTIVE"
                          : "Activate"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            }
          )}

          {!events.length &&
            !loading && (
              <div className="empty-state">
                No historical events found.
              </div>
            )}
        </div>
      )}

      {tab === "clusters" && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(2, minmax(0, 1fr))",
            gap: 10,
            padding: "0 14px 16px",
          }}
        >
          {clusters.map(
            (cluster) => (
              <div
                key={
                  cluster.cluster_id
                }
                className="detail-card"
              >
                <strong>
                  {cluster.cluster_id}
                </strong>

                <p>
                  {cluster.event_count ??
                    0}{" "}
                  related events
                </p>

                <div
                  style={{
                    display:
                      "flex",
                    gap: 5,
                    flexWrap:
                      "wrap",
                    marginTop: 8,
                  }}
                >
                  {(
                    cluster.event_ids ??
                    []
                  ).map(
                    (id: number) => (
                      <button
                        key={id}
                        className="secondary-button"
                        style={{
                          padding:
                            "4px 8px",
                        }}
                        onClick={() => {
                          const event =
                            events.find(
                              (item) =>
                                eventIdOf(
                                  item
                                ) === id
                            );

                          if (event) {
                            void activateEvent(
                              event
                            );
                          }
                        }}
                      >
                        #{id}
                      </button>
                    )
                  )}
                </div>
              </div>
            )
          )}
        </div>
      )}

      {tab === "timeline" && (
        <div
          style={{
            padding:
              "0 14px 16px",
          }}
        >
          <div
            className="detail-card"
            style={{
              marginBottom: 10,
            }}
          >
            <strong>
              {selectedEvent
                ? `Timeline for Event #${eventIdOf(
                    selectedEvent
                  )}`
                : "Select an event"}
            </strong>

            {selectedEvent && (
              <p>
                {selectedEvent.title}
              </p>
            )}
          </div>

          {timeline.map(
            (event) => {
              const id =
                eventIdOf(event);

              const isCurrent =
                id ===
                eventIdOf(
                  selectedEvent ??
                    {}
                );

              return (
                <div
                  key={id}
                  className="detail-card"
                  style={{
                    marginBottom: 8,
                    borderLeft:
                      isCurrent
                        ? "3px solid #22c55e"
                        : "3px solid #60a5fa",
                  }}
                >
                  <div
                    style={{
                      display:
                        "flex",
                      justifyContent:
                        "space-between",
                      gap: 12,
                    }}
                  >
                    <strong>
                      #{id} —{" "}
                      {event.title}
                    </strong>

                    <span
                      className={`risk-badge ${severityClass(
                        event.severity
                      )}`}
                    >
                      {String(
                        event.severity ??
                          "unknown"
                      ).toUpperCase()}
                    </span>
                  </div>

                  <small>
                    {formatDate(
                      event.created_at
                    )}{" "}
                    •{" "}
                    {event.source ??
                      "unknown"}
                  </small>

                  <p>
                    {event.description}
                  </p>
                </div>
              );
            }
          )}

          {!timeline.length && (
            <div className="empty-state">
              Select an event from Event
              History and open Timeline.
            </div>
          )}
        </div>
      )}

      {tab === "replay" && (
        <div
          style={{
            padding:
              "0 14px 16px",
          }}
        >
          <div
            className="settings-success"
            style={{
              marginBottom: 10,
            }}
          >
            Business source of truth:
            business_supply_chain. Historical
            replay does not allow ML/GNN to
            overwrite business facts. ML override:
            NO.
          </div>

          {replay ? (
            <>
              <div
                style={{
                  display:
                    "grid",
                  gridTemplateColumns:
                    "repeat(4, minmax(0, 1fr))",
                  gap: 8,
                }}
              >
                <div className="result-kpi">
                  <span>EVENT</span>
                  <strong>
                    #
                    {
                      replay.event_id
                    }
                  </strong>
                </div>

                <div className="result-kpi">
                  <span>GRAPH</span>
                  <strong>
                    {replay.graph_id ??
                      "--"}
                  </strong>
                </div>

                <div className="result-kpi">
                  <span>NODES</span>
                  <strong>
                    {
                      replay
                        ?.event_impact_graph
                        ?.counts
                        ?.nodes ??
                      0
                    }
                  </strong>
                </div>

                <div className="result-kpi">
                  <span>RELATIONSHIPS</span>
                  <strong>
                    {
                      replay
                        ?.event_impact_graph
                        ?.counts
                        ?.relationships ??
                      0
                    }
                  </strong>
                </div>
              </div>

              <div
                className="detail-card"
                style={{
                  marginTop: 10,
                }}
              >
                <strong>
                  {replay?.event?.title ??
                    `Event #${replay.event_id}`}
                </strong>

                <p>
                  {replay?.event
                    ?.description ??
                    "Historical operational replay."}
                </p>

                <div
                  className="result-kpi-grid"
                  style={{
                    marginTop: 10,
                  }}
                >
                  <div className="result-kpi">
                    <span>
                      SUPPLIERS
                    </span>
                    <strong>
                      {
                        replay
                          ?.event_impact_graph
                          ?.counts
                          ?.suppliers ??
                        0
                      }
                    </strong>
                  </div>

                  <div className="result-kpi">
                    <span>
                      COMPONENTS
                    </span>
                    <strong>
                      {
                        replay
                          ?.event_impact_graph
                          ?.counts
                          ?.components ??
                        0
                      }
                    </strong>
                  </div>

                  <div className="result-kpi">
                    <span>
                      PLANTS
                    </span>
                    <strong>
                      {
                        replay
                          ?.event_impact_graph
                          ?.counts
                          ?.plants ??
                        0
                      }
                    </strong>
                  </div>

                  <div className="result-kpi">
                    <span>
                      PRODUCTS
                    </span>
                    <strong>
                      {
                        replay
                          ?.event_impact_graph
                          ?.counts
                          ?.products ??
                        0
                      }
                    </strong>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div
              className="detail-card"
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                alignItems: "center",
              }}
            >
              <span>
                Select an event and open Replay
                to inspect the operational impact
                graph.
              </span>

              {selectedEvent && (
                <button
                  className="primary-button"
                  onClick={() =>
                    void loadReplay(
                      selectedEvent
                    )
                  }
                >
                  Run Replay
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

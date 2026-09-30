
interface OperationalTimelineProps {
  intelligence: any;
}

function number(value: unknown, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function format(value: unknown, suffix = "") {
  const n = Number(value);
  if (!Number.isFinite(n)) return "--";
  return `${Math.round(n * 100) / 100}${suffix}`;
}

function statusClass(status: string) {
  switch (status) {
    case "STOPPED":
      return { border: "#ef4444", text: "#ef4444" };
    case "REDUCED":
      return { border: "#f97316", text: "#f97316" };
    case "AT_RISK":
      return { border: "#eab308", text: "#eab308" };
    case "BUFFERED":
      return { border: "#22c55e", text: "#22c55e" };
    default:
      return { border: "#64748b", text: "#64748b" };
  }
}

export default function OperationalTimeline({
  intelligence,
}: OperationalTimelineProps) {
  const timeline = intelligence?.operational_timeline;

  if (!timeline) {
    return null;
  }

  const summary = timeline.summary ?? {};
  const components = Array.isArray(timeline.components)
    ? timeline.components
    : [];
  const recommendations = Array.isArray(timeline.recommendations)
    ? timeline.recommendations
    : [];

  const productionStatus = String(
    timeline.production_status ?? "UNKNOWN"
  ).toUpperCase();

  const status = statusClass(productionStatus);

  return (
    <div
      className="detail-card"
      style={{ marginTop: 16 }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-kicker">
            OPERATIONAL TIMELINE
          </span>
          <h3>Inventory & Production Outlook</h3>
        </div>

        <div
          style={{
            border: `1px solid ${status.border}`,
            color: status.text,
            borderRadius: 999,
            padding: "6px 10px",
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.08em",
          }}
        >
          {productionStatus}
        </div>
      </div>

      <div className="result-kpi-grid">
        <div className="result-kpi">
          <span>MIN BUFFER</span>
          <strong>{format(summary.minimum_buffer_days, " d")}</strong>
        </div>

        <div className="result-kpi">
          <span>FIRST SHORTAGE</span>
          <strong>
            {summary.first_shortage_day == null
              ? "--"
              : format(summary.first_shortage_day, " d")}
          </strong>
        </div>

        <div className="result-kpi">
          <span>FIRST RECOVERY</span>
          <strong>
            {summary.first_recovery_day == null
              ? "--"
              : format(summary.first_recovery_day, " d")}
          </strong>
        </div>

        <div className="result-kpi">
          <span>NET SHORTAGE</span>
          <strong>
            {number(summary.net_shortage).toLocaleString()}
          </strong>
        </div>
      </div>

      {components.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div className="panel-kicker">
            COMPONENT TIMELINE
          </div>

          <div style={{ display: "grid", gap: 10, marginTop: 10 }}>
            {components.map((component: any, index: number) => {
              const componentStatus = String(
                component.status ?? "UNKNOWN"
              ).toUpperCase();
              const colors = statusClass(componentStatus);

              return (
                <div
                  key={`${component.component_id}-${component.plant_id}-${index}`}
                  style={{
                    border: "1px solid rgba(148, 163, 184, 0.16)",
                    borderRadius: 10,
                    padding: 12,
                    background: "rgba(15, 23, 42, 0.28)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 12,
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <strong>
                        {component.component_name ??
                          component.component_id ??
                          "Unknown component"}
                      </strong>
                      <div style={{ opacity: 0.65, fontSize: 12, marginTop: 3 }}>
                        {component.plant_name ?? component.plant_id ?? "Unknown plant"}
                      </div>
                    </div>

                    <span
                      style={{
                        color: colors.text,
                        fontSize: 11,
                        fontWeight: 700,
                      }}
                    >
                      {componentStatus}
                    </span>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                      gap: 8,
                      marginTop: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 10, opacity: 0.55 }}>INVENTORY</div>
                      <strong>{number(component.inventory_units).toLocaleString()}</strong>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, opacity: 0.55 }}>BUFFER</div>
                      <strong>{format(component.buffer_days, " d")}</strong>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, opacity: 0.55 }}>RECOVERY</div>
                      <strong>{number(component.recovery_units).toLocaleString()}</strong>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, opacity: 0.55 }}>RECOVERY ETA</div>
                      <strong>{format(component.first_recovery_day, " d")}</strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <div className="panel-kicker">RECOMMENDED ACTIONS</div>

        <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
          {recommendations.map((item: any, index: number) => (
            <div
              key={index}
              style={{
                borderLeft: "3px solid rgba(148, 163, 184, 0.45)",
                padding: "8px 10px",
              }}
            >
              <strong style={{ fontSize: 12 }}>
                {String(item.priority ?? "info").toUpperCase()}
              </strong>
              <div style={{ marginTop: 3 }}>
                {item.action ?? "Continue monitoring."}
              </div>
              {item.reason && (
                <div style={{ opacity: 0.58, fontSize: 12, marginTop: 3 }}>
                  {item.reason}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

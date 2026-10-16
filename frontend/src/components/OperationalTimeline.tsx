
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
      style={{ marginTop: 16, background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "20px" }}
    >
      <div className="panel-header" style={{ marginBottom: 14 }}>
        <div>
          <span className="panel-kicker" style={{ color: "#64748b", fontSize: 11, fontWeight: 700 }}>
            TIME & RECOVERY ESTIMATE
          </span>
          <h3 style={{ color: "#0f172a", fontSize: 16, margin: "2px 0 0" }}>Factory Buffer & Stock Timeline</h3>
        </div>

        <div
          style={{
            border: `1px solid ${status.border}`,
            color: status.text,
            background: `${status.border}15`,
            borderRadius: 999,
            padding: "4px 12px",
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.08em",
          }}
        >
          {productionStatus === "STOPPED" ? "FACTORY WILL STOP" : productionStatus}
        </div>
      </div>

      <div className="result-kpi-grid">
        <div className="result-kpi">
          <span>MIN STOCK BUFFER</span>
          <strong>{format(summary.minimum_buffer_days, " Days")}</strong>
        </div>

        <div className="result-kpi">
          <span>FIRST DAY OF SHORTAGE</span>
          <strong>
            {summary.first_shortage_day == null
              ? "Day 0"
              : `Day ${format(summary.first_shortage_day)}`}
          </strong>
        </div>

        <div className="result-kpi">
          <span>ESTIMATED RECOVERY</span>
          <strong>
            {summary.first_recovery_day == null
              ? "--"
              : `${format(summary.first_recovery_day)} Days`}
          </strong>
        </div>

        <div className="result-kpi">
          <span>NET SHORTAGE</span>
          <strong style={{ color: number(summary.net_shortage) > 0 ? "#dc2626" : "#16a34a" }}>
            {number(summary.net_shortage).toLocaleString()}
          </strong>
        </div>
      </div>

      {components.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div className="panel-kicker" style={{ color: "#64748b", fontSize: 11, fontWeight: 700, marginBottom: 8 }}>
            PARTS RUNOUT TIMELINE
          </div>

          <div style={{ display: "grid", gap: 10, marginTop: 8 }}>
            {components.map((component: any, index: number) => {
              const componentStatus = String(
                component.status ?? "UNKNOWN"
              ).toUpperCase();
              const colors = statusClass(componentStatus);

              return (
                <div
                  key={`${component.component_id}-${component.plant_id}-${index}`}
                  style={{
                    border: "1px solid #e2e8f0",
                    borderRadius: 10,
                    padding: 14,
                    background: "#f8fafc",
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
                      <strong style={{ color: "#0f172a", fontSize: 14 }}>
                        {component.component_name ??
                          component.component_id ??
                          "Unknown component"}
                      </strong>
                      <div style={{ color: "#64748b", fontSize: 12, marginTop: 2 }}>
                        Factory: {component.plant_name ?? component.plant_id ?? "Factory Unit"}
                      </div>
                    </div>

                    <span
                      style={{
                        color: colors.text,
                        background: `${colors.border}15`,
                        padding: "2px 8px",
                        borderRadius: 6,
                        border: `1px solid ${colors.border}40`,
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
                      marginTop: 12,
                      background: "#ffffff",
                      border: "1px solid #e2e8f0",
                      borderRadius: 8,
                      padding: "8px 12px",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 10, color: "#64748b", fontWeight: 600 }}>CURRENT STOCK</div>
                      <strong style={{ color: "#0f172a", fontSize: 13 }}>{number(component.inventory_units).toLocaleString()}</strong>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, color: "#64748b", fontWeight: 600 }}>DAYS RUNWAY</div>
                      <strong style={{ color: "#d97706", fontSize: 13 }}>{format(component.buffer_days, " d")}</strong>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, color: "#64748b", fontWeight: 600 }}>BACKUP RECOVERY</div>
                      <strong style={{ color: "#16a34a", fontSize: 13 }}>{number(component.recovery_units).toLocaleString()}</strong>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, color: "#64748b", fontWeight: 600 }}>EXPECTED RECOVERY</div>
                      <strong style={{ color: "#2563eb", fontSize: 13 }}>{format(component.first_recovery_day, " d")}</strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ marginTop: 20 }}>
        <div className="panel-kicker" style={{ color: "#64748b", fontSize: 11, fontWeight: 700, marginBottom: 8 }}>
          SUGGESTED NEXT STEPS
        </div>

        <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
          {recommendations.map((item: any, index: number) => (
            <div
              key={index}
              style={{
                borderLeft: "4px solid #2563eb",
                background: "#f8fafc",
                borderRadius: "0 8px 8px 0",
                padding: "10px 14px",
                border: "1px solid #e2e8f0",
                borderLeftWidth: "4px",
              }}
            >
              <strong style={{ fontSize: 12, color: "#2563eb", textTransform: "uppercase" }}>
                {String(item.priority ?? "info")}
              </strong>
              <div style={{ marginTop: 2, color: "#0f172a", fontSize: 13, fontWeight: 500 }}>
                {item.action ?? "Continue monitoring."}
              </div>
              {item.reason && (
                <div style={{ color: "#64748b", fontSize: 12, marginTop: 2 }}>
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

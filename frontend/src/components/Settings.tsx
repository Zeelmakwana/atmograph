import {
  Bell,
  CheckCircle2,
  Database,
  Gauge,
  Network,
  RefreshCw,
  Save,
  Server,
  Shield,
  SlidersHorizontal,
  Sparkles,
  Wifi,
} from "lucide-react";

import {
  useState,
} from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

export default function Settings() {
  const [
    autoRefresh,
    setAutoRefresh,
  ] = useState(true);

  const [
    notifications,
    setNotifications,
  ] = useState(true);

  const [
    liveUpdates,
    setLiveUpdates,
  ] = useState(true);

  const [
    graphDepth,
    setGraphDepth,
  ] = useState("3");

  const [
    predictionMode,
    setPredictionMode,
  ] = useState(
    "hybrid"
  );

  const [
    saved,
    setSaved,
  ] = useState(false);

  function savePreferences() {
    localStorage.setItem(
      "atmograph_settings",
      JSON.stringify({
        autoRefresh,
        notifications,
        liveUpdates,
        graphDepth,
        predictionMode,
      })
    );

    setSaved(true);

    window.setTimeout(
      () => {
        setSaved(false);
      },
      2200
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
            CONFIGURATION
          </span>

          <h2>
            Settings
          </h2>

          <p>
            Configure AtmoGraph intelligence,
            graph and dashboard preferences.
          </p>

        </div>

        <button
          className="primary-button"
          onClick={
            savePreferences
          }
        >

          {saved ? (
            <CheckCircle2 size={15} />
          ) : (
            <Save size={15} />
          )}

          {saved
            ? "Saved"
            : "Save Preferences"}

        </button>

      </div>


      {/* =====================================================
          SUCCESS
      ===================================================== */}

      {saved && (
        <div className="settings-success">

          <CheckCircle2
            size={17}
          />

          <span>
            Preferences saved successfully.
          </span>

        </div>
      )}


      {/* =====================================================
          SETTINGS GRID
      ===================================================== */}

      <div className="settings-grid">

        {/* -------------------------------------------------
            DASHBOARD
        ------------------------------------------------- */}

        <section className="panel settings-panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                DASHBOARD
              </span>

              <h3>
                Dashboard Preferences
              </h3>

            </div>

            <Gauge size={18} />

          </div>


          <div className="settings-options">

            <ToggleSetting
              icon={
                <RefreshCw size={17} />
              }
              title="Automatic Refresh"
              description="Refresh dashboard intelligence when the selected event changes."
              enabled={
                autoRefresh
              }
              onChange={
                setAutoRefresh
              }
            />


            <ToggleSetting
              icon={
                <Bell size={17} />
              }
              title="Notifications"
              description="Show application notifications for important intelligence updates."
              enabled={
                notifications
              }
              onChange={
                setNotifications
              }
            />


            <ToggleSetting
              icon={
                <Wifi size={17} />
              }
              title="Live Updates"
              description="Receive real-time updates through the AtmoGraph WebSocket channel."
              enabled={
                liveUpdates
              }
              onChange={
                setLiveUpdates
              }
            />

          </div>

        </section>


        {/* -------------------------------------------------
            GRAPH
        ------------------------------------------------- */}

        <section className="panel settings-panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                GRAPH ENGINE
              </span>

              <h3>
                Graph Preferences
              </h3>

            </div>

            <Network size={18} />

          </div>


          <div className="settings-form">

            <label>
              <span>
                MAX GRAPH DEPTH
              </span>

              <select
                value={
                  graphDepth
                }
                onChange={(event) =>
                  setGraphDepth(
                    event.target.value
                  )
                }
              >
                <option value="1">
                  1 level
                </option>

                <option value="2">
                  2 levels
                </option>

                <option value="3">
                  3 levels
                </option>

                <option value="4">
                  4 levels
                </option>

                <option value="5">
                  5 levels
                </option>
              </select>

              <small>
                Controls how far supply-chain
                relationships are traversed.
              </small>

            </label>


            <label>
              <span>
                PREDICTION MODE
              </span>

              <select
                value={
                  predictionMode
                }
                onChange={(event) =>
                  setPredictionMode(
                    event.target.value
                  )
                }
              >
                <option value="hybrid">
                  Hybrid Intelligence
                </option>

                <option value="gnn">
                  GNN Prediction
                </option>

                <option value="rule">
                  Rule-Based Risk
                </option>
              </select>

              <small>
                Select the prediction output
                emphasized by the dashboard.
              </small>

            </label>

          </div>

        </section>


        {/* -------------------------------------------------
            INTELLIGENCE
        ------------------------------------------------- */}

        <section className="panel settings-panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                INTELLIGENCE ENGINE
              </span>

              <h3>
                AI Configuration
              </h3>

            </div>

            <Sparkles size={18} />

          </div>


          <div className="settings-engine-list">

            <EngineRow
              icon={
                <Sparkles size={16} />
              }
              title="spaCy NLP"
              value="en_core_web_sm"
              status="ACTIVE"
            />

            <EngineRow
              icon={
                <Network size={16} />
              }
              title="Neo4j"
              value="Knowledge Graph"
              status="ACTIVE"
            />

            <EngineRow
              icon={
                <Sparkles size={16} />
              }
              title="AtmoGraphGNN"
              value="PyTorch Geometric"
              status="ACTIVE"
            />

            <EngineRow
              icon={
                <Shield size={16} />
              }
              title="Hybrid Risk Engine"
              value="Rule + GNN"
              status="ACTIVE"
            />

          </div>

        </section>


        {/* -------------------------------------------------
            SYSTEM
        ------------------------------------------------- */}

        <section className="panel settings-panel">

          <div className="panel-header">

            <div>

              <span className="panel-kicker">
                RUNTIME
              </span>

              <h3>
                System Configuration
              </h3>

            </div>

            <Server size={18} />

          </div>


          <div className="runtime-settings">

            <RuntimeRow
              icon={
                <Server size={16} />
              }
              label="API Endpoint"
              value={
                API_BASE_URL
              }
            />

            <RuntimeRow
              icon={
                <Database size={16} />
              }
              label="Database"
              value="Application Database"
            />

            <RuntimeRow
              icon={
                <Network size={16} />
              }
              label="Graph Database"
              value="Neo4j"
            />

            <RuntimeRow
              icon={
                <Sparkles size={16} />
              }
              label="ML Runtime"
              value="PyTorch + PyG"
            />

          </div>

        </section>

      </div>


      {/* =====================================================
          CONFIGURATION SUMMARY
      ===================================================== */}

      <section className="panel settings-summary">

        <div className="panel-header">

          <div>

            <span className="panel-kicker">
              ACTIVE CONFIGURATION
            </span>

            <h3>
              Current Preferences
            </h3>

          </div>

          <SlidersHorizontal
            size={18}
          />

        </div>


        <div className="settings-summary-grid">

          <SummaryItem
            label="AUTO REFRESH"
            value={
              autoRefresh
                ? "Enabled"
                : "Disabled"
            }
          />

          <SummaryItem
            label="LIVE UPDATES"
            value={
              liveUpdates
                ? "Enabled"
                : "Disabled"
            }
          />

          <SummaryItem
            label="NOTIFICATIONS"
            value={
              notifications
                ? "Enabled"
                : "Disabled"
            }
          />

          <SummaryItem
            label="GRAPH DEPTH"
            value={`${graphDepth} levels`}
          />

          <SummaryItem
            label="PREDICTION"
            value={
              predictionMode ===
              "hybrid"
                ? "Hybrid Intelligence"
                : predictionMode ===
                    "gnn"
                  ? "GNN Prediction"
                  : "Rule-Based Risk"
            }
          />

        </div>

      </section>


      {/* =====================================================
          FOOTER NOTE
      ===================================================== */}

      <div className="settings-note">

        <Shield size={14} />

        <span>
          Settings are stored locally for the
          dashboard client. Core AtmoGraph
          backend services remain controlled by
          the application runtime.
        </span>

      </div>

    </div>
  );
}


/* ============================================================
   TOGGLE
============================================================ */

function ToggleSetting({
  icon,
  title,
  description,
  enabled,
  onChange,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  enabled: boolean;
  onChange: (
    value: boolean
  ) => void;
}) {
  return (
    <div className="settings-toggle-row">

      <div className="settings-toggle-icon">
        {icon}
      </div>

      <div className="settings-toggle-content">

        <strong>
          {title}
        </strong>

        <span>
          {description}
        </span>

      </div>

      <button
        type="button"
        className={`settings-switch ${
          enabled
            ? "enabled"
            : ""
        }`}
        onClick={() =>
          onChange(
            !enabled
          )
        }
        aria-label={
          title
        }
      >
        <span />
      </button>

    </div>
  );
}


/* ============================================================
   ENGINE ROW
============================================================ */

function EngineRow({
  icon,
  title,
  value,
  status,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  status: string;
}) {
  return (
    <div className="settings-engine-row">

      <div className="settings-engine-icon">
        {icon}
      </div>

      <div>

        <strong>
          {title}
        </strong>

        <span>
          {value}
        </span>

      </div>

      <div className="settings-active">
        <span />
        {status}
      </div>

    </div>
  );
}


/* ============================================================
   RUNTIME ROW
============================================================ */

function RuntimeRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="runtime-setting-row">

      <div className="runtime-setting-icon">
        {icon}
      </div>

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


/* ============================================================
   SUMMARY
============================================================ */

function SummaryItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="settings-summary-item">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}
import {
  useEffect,
  useState,
} from "react";

import {
  AlertTriangle,
  CalendarDays,
  Clock3,
  TrendingDown,
} from "lucide-react";

import {
  getHybridPrediction,
} from "../../services/api";


type Props = {
  eventId: number;
  graphId: string;
};


function unwrap(value: any): any {

  if (
    value &&
    typeof value === "object" &&
    value.data !== undefined
  ) {
    return value.data;
  }

  return value;
}


function getPrediction(
  value: any
): any {

  const root =
    unwrap(value);

  if (
    root?.hybrid_prediction ||
    root?.base_prediction ||
    root?.gnn_prediction
  ) {
    return root;
  }

  if (
    root?.prediction
  ) {
    return getPrediction(
      root.prediction
    );
  }

  if (
    root?.result
  ) {
    return getPrediction(
      root.result
    );
  }

  if (
    root?.data
  ) {
    return getPrediction(
      root.data
    );
  }

  return root ?? {};
}


function numberValue(
  object: any,
  keys: string[]
): number {

  for (
    const key of keys
  ) {

    const value =
      Number(
        object?.[key]
      );

    if (
      Number.isFinite(value)
    ) {
      return value;
    }
  }

  return 0;
}


function level(
  value: number
): string {

  if (value >= 80) {
    return "CRITICAL";
  }

  if (value >= 60) {
    return "HIGH";
  }

  if (value >= 40) {
    return "MEDIUM";
  }

  return "LOW";
}


export default function PredictionTimeline({
  eventId,
  graphId,
}: Props) {

  const [
    prediction,
    setPrediction,
  ] = useState<any>(null);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  useEffect(
    () => {

      let active = true;


      async function load() {

        setLoading(true);
        setError("");


        try {

          const response =
            await getHybridPrediction(
              eventId,
              graphId
            );


          if (!active) {
            return;
          }


          setPrediction(
            getPrediction(response)
          );

        } catch (err: any) {

          if (!active) {
            return;
          }

          setError(
            err?.message ??
            "Unable to load prediction timeline."
          );

        } finally {

          if (active) {
            setLoading(false);
          }

        }

      }


      load();


      return () => {
        active = false;
      };

    },
    [
      eventId,
      graphId,
    ]
  );


  if (loading) {

    return (
      <div className="timeline-empty">
        Loading prediction scenarios...
      </div>
    );

  }


  if (error) {

    return (
      <div className="timeline-empty">
        {error}
      </div>
    );

  }


  if (!prediction) {

    return (
      <div className="timeline-empty">
        Prediction data unavailable.
      </div>
    );

  }


  const hybrid =
    prediction.hybrid_prediction ??
    {};


  const base =
    prediction.base_prediction ??
    {};


  const currentRisk =
    numberValue(
      hybrid,
      [
        "risk_score",
        "riskScore",
      ]
    );


  const currentDelay =
    numberValue(
      base,
      [
        "estimated_delay_days",
        "estimatedDelayDays",
      ]
    );


  /*
   * IMPORTANT:
   *
   * These are scenario projections,
   * not trained future forecasts.
   */

  const scenarios = [

    {
      label: "CURRENT",
      horizon: "30 DAYS",
      risk: currentRisk,
      delay: currentDelay,
      description:
        "Current disruption scenario",
    },

    {
      label: "RECOVERY",
      horizon: "60 DAYS",
      risk:
        currentRisk * 0.90,
      delay:
        currentDelay * 0.75,
      description:
        "Moderate recovery scenario",
    },

    {
      label: "STABILIZED",
      horizon: "90 DAYS",
      risk:
        currentRisk * 0.70,
      delay:
        currentDelay * 0.50,
      description:
        "Longer recovery scenario",
    },

  ];


  return (
    <div className="timeline-wrapper">

      <div className="timeline-track">

        {scenarios.map(
          (
            item,
            index
          ) => (

            <div
              className="timeline-card"
              key={item.horizon}
            >

              <div className="timeline-card-top">

                <div>

                  <span className="panel-kicker">
                    {item.label}
                  </span>

                  <h4>
                    {item.horizon}
                  </h4>

                </div>


                {index === 0 ? (
                  <Clock3 size={19} />
                ) : (
                  <CalendarDays size={19} />
                )}

              </div>


              <div className="timeline-risk">

                <strong>
                  {item.risk.toFixed(2)}
                </strong>

                <span
                  className={
                    `risk-badge ${
                      item.risk >= 80
                        ? "critical"
                        : item.risk >= 60
                          ? "high"
                          : item.risk >= 40
                            ? "medium"
                            : "low"
                    }`
                  }
                >
                  {level(item.risk)}
                </span>

              </div>


              <div className="timeline-delay">

                <TrendingDown
                  size={15}
                />

                <span>
                  {item.delay.toFixed(1)}
                  {" "}
                  days estimated delay
                </span>

              </div>


              <p>
                {item.description}
              </p>

            </div>

          )
        )}

      </div>


      <div className="timeline-note">

        <AlertTriangle
          size={14}
        />

        <span>
          Scenario projection based on
          current hybrid risk. It is not
          a trained 30/60/90-day forecast.
        </span>

      </div>

    </div>
  );
}
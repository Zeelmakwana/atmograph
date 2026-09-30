import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getGraphStatistics,
  getHybridPrediction,
  getEventImpactGraph,
} from "../services/api";

function unwrap(value: any): any {
  if (value?.data !== undefined) {
    return value.data;
  }

  return value;
}

export function useDashboard(
  eventId: number | null,
  graphId: string
) {
  const [statistics, setStatistics] =
    useState<any>(null);

  const [prediction, setPrediction] =
    useState<any>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const requestIdRef =
    useRef(0);

  const refresh = useCallback(
    async () => {
      if (
        !eventId ||
        !Number.isFinite(eventId) ||
        !graphId
      ) {
        setStatistics(null);
        setPrediction(null);
        setLoading(false);
        return;
      }

      const requestId =
        ++requestIdRef.current;

      setLoading(true);
      setError("");

      try {
        /*
         * Dashboard uses three sources:
         *
         * 1. Graph statistics
         * 2. Hybrid rule + GNN prediction
         * 3. Operational event-impact graph
         *
         * The hybrid prediction endpoint does not
         * currently contain the canonical affected
         * supplier/product arrays, so event-impact
         * provides those operational counts.
         */
        const [
          statisticsResult,
          predictionResult,
          eventImpactResult,
        ] = await Promise.all([
          getGraphStatistics(),

          getHybridPrediction(
            eventId,
            graphId
          ),

          getEventImpactGraph(
            eventId
          ),
        ]);

        /*
         * Ignore an older request if a newer
         * event has already been selected.
         */
        if (
          requestId !==
          requestIdRef.current
        ) {
          return;
        }

        const statisticsData =
          unwrap(
            statisticsResult
          );

        const predictionData =
          unwrap(
            predictionResult
          );

        const eventImpactData =
          unwrap(
            eventImpactResult
          );

        /*
         * ====================================================
         * OPERATIONAL IMPACT
         * ====================================================
         *
         * Event Impact Graph is the operational
         * source for affected entities on Dashboard.
         */
        const impactCounts =
          eventImpactData?.counts ??
          {};

        const affectedSupplierCount =
          Number(
            impactCounts?.suppliers ?? 0
          );

        const affectedProductCount =
          Number(
            impactCounts?.products ?? 0
          );

        const affectedComponentCount =
          Number(
            impactCounts?.components ?? 0
          );

        const affectedPlantCount =
          Number(
            impactCounts?.plants ?? 0
          );

        /*
         * Preserve the complete hybrid prediction
         * and add operational impact information.
         *
         * This avoids changing the existing Dashboard
         * component contract.
         */
        const dashboardPrediction = {
          ...predictionData,

          affected_suppliers:
            Array.isArray(
              predictionData?.affected_suppliers
            ) &&
            predictionData.affected_suppliers.length > 0
              ? predictionData.affected_suppliers
              : new Array(
                  affectedSupplierCount
                ).fill(null),

          affected_products:
            Array.isArray(
              predictionData?.affected_products
            ) &&
            predictionData.affected_products.length > 0
              ? predictionData.affected_products
              : new Array(
                  affectedProductCount
                ).fill(null),

          event_impact:
            eventImpactData,

          business_impact_counts: {
            affected_suppliers:
              affectedSupplierCount,

            affected_products:
              affectedProductCount,

            affected_components:
              affectedComponentCount,

            affected_plants:
              affectedPlantCount,
          },
        };

        setStatistics(
          statisticsData
        );

        setPrediction(
          dashboardPrediction
        );
      } catch (err: any) {
        if (
          requestId !==
          requestIdRef.current
        ) {
          return;
        }

        setStatistics(null);
        setPrediction(null);

        setError(
          err?.message ||
            "Unable to load dashboard data."
        );
      } finally {
        if (
          requestId ===
          requestIdRef.current
        ) {
          setLoading(false);
        }
      }
    },
    [
      eventId,
      graphId,
    ]
  );

  useEffect(() => {
    void refresh();

    return () => {
      requestIdRef.current += 1;
    };
  }, [refresh]);

  return {
    statistics,
    prediction,
    loading,
    error,
    refresh,
  };
}
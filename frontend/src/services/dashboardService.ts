import {
  getGraphStatistics,
  getGnnPrediction,
} from "./api";

export async function loadDashboardData() {
  const [graphStats] = await Promise.all([
    getGraphStatistics(),
  ]);

  return {
    graphStats,
  };
}

export async function loadEventPrediction(graphId: string) {
  return getGnnPrediction(graphId);
}
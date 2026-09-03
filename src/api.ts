import { GraphNodeData, GraphEdgeData, GNNPredictionResponse } from './types';
import { INITIAL_NODES, INITIAL_EDGES } from './mockData';

const BASE_URL = 'http://localhost:8000/api';

export const fetchGraphData = async (): Promise<{ nodes: GraphNodeData[]; edges: GraphEdgeData[] }> => {
  try {
    const res = await fetch(`${BASE_URL}/graph`);
    if (!res.ok) throw new Error('Backend offline');
    return await res.json();
  } catch {
    return { nodes: INITIAL_NODES, edges: INITIAL_EDGES };
  }
};

export const simulateRippleEffect = async (_newsText: string): Promise<GNNPredictionResponse[]> => {
  try {
    const res = await fetch(`${BASE_URL}/predict-ripple`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ news: _newsText }),
    });
    if (!res.ok) throw new Error('API error');
    return await res.json();
  } catch {
    return [
      { targetNodeId: 'n4', predictedDelayDays: 18, riskScore: 0.95, contributingFactors: ['Dockworker strike', 'Berth congestion'], pathTrace: ['n4'] },
      { targetNodeId: 'n9', predictedDelayDays: 15, riskScore: 0.81, contributingFactors: ['Missing semiconductor modules', 'Single source port'], pathTrace: ['n4', 'n9'] },
      { targetNodeId: 'n11', predictedDelayDays: 12, riskScore: 0.74, contributingFactors: ['Intermodal freight halt', 'Storage overflow'], pathTrace: ['n4', 'n11'] },
      { targetNodeId: 'n14', predictedDelayDays: 16, riskScore: 0.88, contributingFactors: ['Downstream fulfillment freeze'], pathTrace: ['n4', 'n11', 'n14'] },
      { targetNodeId: 'n15', predictedDelayDays: 21, riskScore: 0.91, contributingFactors: ['Complete inventory dry-out'], pathTrace: ['n4', 'n11', 'n14', 'n15'] }
    ];
  }
};

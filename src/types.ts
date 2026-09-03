export type NodeType = 'Supplier' | 'Manufacturer' | 'Port' | 'Warehouse' | 'Distribution' | 'Retailer';

export type RiskLevel = 'normal' | 'moderate' | 'severe';

export interface GraphNodeData {
  id: string;
  label: string;
  type: NodeType;
  country: string;
  capacity: number;
  currentStatus: 'Operational' | 'Disrupted' | 'Delayed' | 'Critical';
  riskScore: number;
  predictedDelayDays: number;
  contributingFactors?: string[];
  upstreamNodes?: string[];
  downstreamNodes?: string[];
}

export interface GraphEdgeData {
  id: string;
  source: string;
  target: string;
  relationshipType: string;
  leadTimeDays: number;
  isImpacted: boolean;
}

export interface DisruptionEvent {
  eventId: string;
  rawText: string;
  extractedEntities: string[];
  severity: 'Low' | 'Medium' | 'High' | 'Catastrophic';
  timestamp: string;
}

export interface GNNPredictionResponse {
  targetNodeId: string;
  predictedDelayDays: number;
  riskScore: number;
  contributingFactors: string[];
  pathTrace: string[];
}

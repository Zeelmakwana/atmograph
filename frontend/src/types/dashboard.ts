export interface DashboardMetrics {
  networkRisk: number;
  activeEvents: number;
  affectedSuppliers: number;
  predictedDelay: number;
}

export interface RiskDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface DashboardEvent {
  id: number;
  title: string;
  description?: string;
  event_type?: string;
  severity?: string;
  location?: string;
  status?: string;
  source?: string;
  event_time?: string;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  riskDistribution: RiskDistribution;
  events: DashboardEvent[];
}
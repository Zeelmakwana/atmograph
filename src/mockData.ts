import { GraphNodeData, GraphEdgeData } from './types';

export const INITIAL_NODES: GraphNodeData[] = [
  { id: 'n1', label: 'Lithium Mines AU', type: 'Supplier', country: 'Australia', capacity: 95, currentStatus: 'Operational', riskScore: 0.05, predictedDelayDays: 0 },
  { id: 'n2', label: 'Rare Earth Extraction', type: 'Supplier', country: 'Chile', capacity: 90, currentStatus: 'Operational', riskScore: 0.12, predictedDelayDays: 0 },
  { id: 'n3', label: 'Silicon Wafer Fab', type: 'Supplier', country: 'Taiwan', capacity: 98, currentStatus: 'Operational', riskScore: 0.08, predictedDelayDays: 1 },
  { id: 'n4', label: 'Rotterdam Terminal Port', type: 'Port', country: 'Netherlands', capacity: 40, currentStatus: 'Disrupted', riskScore: 0.88, predictedDelayDays: 18 },
  { id: 'n5', label: 'Port of Shanghai', type: 'Port', country: 'China', capacity: 92, currentStatus: 'Operational', riskScore: 0.15, predictedDelayDays: 2 },
  { id: 'n6', label: 'Port of Los Angeles', type: 'Port', country: 'USA', capacity: 85, currentStatus: 'Operational', riskScore: 0.22, predictedDelayDays: 3 },
  { id: 'n7', label: 'TSMC Advanced Foundry', type: 'Manufacturer', country: 'Taiwan', capacity: 96, currentStatus: 'Operational', riskScore: 0.10, predictedDelayDays: 1 },
  { id: 'n8', label: 'Shenzhen Microelectronics', type: 'Manufacturer', country: 'China', capacity: 88, currentStatus: 'Operational', riskScore: 0.25, predictedDelayDays: 4 },
  { id: 'n9', label: 'Bavaria Auto Assembly', type: 'Manufacturer', country: 'Germany', capacity: 55, currentStatus: 'Delayed', riskScore: 0.74, predictedDelayDays: 14 },
  { id: 'n10', label: 'Texas Hardware Assembly', type: 'Manufacturer', country: 'USA', capacity: 82, currentStatus: 'Operational', riskScore: 0.30, predictedDelayDays: 5 },
  { id: 'n11', label: 'Frankfurt Central Hub', type: 'Warehouse', country: 'Germany', capacity: 60, currentStatus: 'Delayed', riskScore: 0.68, predictedDelayDays: 12 },
  { id: 'n12', label: 'Chicago Central Logistics', type: 'Warehouse', country: 'USA', capacity: 89, currentStatus: 'Operational', riskScore: 0.18, predictedDelayDays: 2 },
  { id: 'n13', label: 'West Coast Dist. Center', type: 'Distribution', country: 'USA', capacity: 91, currentStatus: 'Operational', riskScore: 0.14, predictedDelayDays: 1 },
  { id: 'n14', label: 'Benelux Distribution', type: 'Distribution', country: 'Belgium', capacity: 48, currentStatus: 'Critical', riskScore: 0.82, predictedDelayDays: 16 },
  { id: 'n15', label: 'European Tech Retailers', type: 'Retailer', country: 'Germany', capacity: 50, currentStatus: 'Critical', riskScore: 0.85, predictedDelayDays: 20 },
  { id: 'n16', label: 'North America BestBuy Hub', type: 'Retailer', country: 'USA', capacity: 88, currentStatus: 'Operational', riskScore: 0.20, predictedDelayDays: 3 },
];

export const INITIAL_EDGES: GraphEdgeData[] = [
  { id: 'e1-7', source: 'n1', target: 'n7', relationshipType: 'SUPPLIES_RAW', leadTimeDays: 10, isImpacted: false },
  { id: 'e2-8', source: 'n2', target: 'n8', relationshipType: 'SUPPLIES_MINERALS', leadTimeDays: 14, isImpacted: false },
  { id: 'e3-7', source: 'n3', target: 'n7', relationshipType: 'SUPPLIES_WAFERS', leadTimeDays: 5, isImpacted: false },
  { id: 'e7-5', source: 'n7', target: 'n5', relationshipType: 'SHIPS_VIA', leadTimeDays: 2, isImpacted: false },
  { id: 'e5-4', source: 'n5', target: 'n4', relationshipType: 'MARITIME_ROUTE', leadTimeDays: 24, isImpacted: true },
  { id: 'e5-6', source: 'n5', target: 'n6', relationshipType: 'PACIFIC_ROUTE', leadTimeDays: 16, isImpacted: false },
  { id: 'e8-4', source: 'n8', target: 'n4', relationshipType: 'MARITIME_ROUTE', leadTimeDays: 22, isImpacted: true },
  { id: 'e4-9', source: 'n4', target: 'n9', relationshipType: 'INLAND_FREIGHT', leadTimeDays: 3, isImpacted: true },
  { id: 'e4-11', source: 'n4', target: 'n11', relationshipType: 'RAIL_CARGO', leadTimeDays: 2, isImpacted: true },
  { id: 'e6-10', source: 'n6', target: 'n10', relationshipType: 'INTERSTATE_TRUCK', leadTimeDays: 4, isImpacted: false },
  { id: 'e9-11', source: 'n9', target: 'n11', relationshipType: 'TRANSFERS_TO', leadTimeDays: 1, isImpacted: true },
  { id: 'e10-12', source: 'n10', target: 'n12', relationshipType: 'TRANSFERS_TO', leadTimeDays: 2, isImpacted: false },
  { id: 'e11-14', source: 'n11', target: 'n14', relationshipType: 'REGIONAL_ROUTE', leadTimeDays: 2, isImpacted: true },
  { id: 'e12-13', source: 'n12', target: 'n13', relationshipType: 'REGIONAL_ROUTE', leadTimeDays: 3, isImpacted: false },
  { id: 'e14-15', source: 'n14', target: 'n15', relationshipType: 'FULFILLMENT', leadTimeDays: 1, isImpacted: true },
  { id: 'e13-16', source: 'n13', target: 'n16', relationshipType: 'FULFILLMENT', leadTimeDays: 2, isImpacted: false },
];

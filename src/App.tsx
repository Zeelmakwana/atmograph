import React, { useState, useCallback, useMemo, memo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  MarkerType,
  Handle,
  Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Network, Activity, ShieldAlert, Cpu, 
  Flame, Play, X, Clock
} from 'lucide-react';

type NodeType = 'Supplier' | 'Manufacturer' | 'Port' | 'Warehouse' | 'Distribution' | 'Retailer';

interface GraphNodeData {
  id: string;
  label: string;
  type: NodeType;
  country: string;
  capacity: number;
  currentStatus: string;
  riskScore: number;
  predictedDelayDays: number;
  contributingFactors?: string[];
  [key: string]: unknown;
}

const INITIAL_NODES: GraphNodeData[] = [
  { id: 'n1', label: 'Lithium Mines AU', type: 'Supplier', country: 'Australia', capacity: 95, currentStatus: 'Operational', riskScore: 0.05, predictedDelayDays: 0 },
  { id: 'n2', label: 'Rare Earth Extraction', type: 'Supplier', country: 'Chile', capacity: 90, currentStatus: 'Operational', riskScore: 0.12, predictedDelayDays: 0 },
  { id: 'n3', label: 'Silicon Wafer Fab', type: 'Supplier', country: 'Taiwan', capacity: 98, currentStatus: 'Operational', riskScore: 0.08, predictedDelayDays: 1 },
  { id: 'n4', label: 'Rotterdam Terminal Port', type: 'Port', country: 'Netherlands', capacity: 40, currentStatus: 'Disrupted', riskScore: 0.88, predictedDelayDays: 18, contributingFactors: ['Dockworker strike', 'Berth congestion'] },
  { id: 'n5', label: 'Port of Shanghai', type: 'Port', country: 'China', capacity: 92, currentStatus: 'Operational', riskScore: 0.15, predictedDelayDays: 2 },
  { id: 'n6', label: 'Port of Los Angeles', type: 'Port', country: 'USA', capacity: 85, currentStatus: 'Operational', riskScore: 0.22, predictedDelayDays: 3 },
  { id: 'n7', label: 'TSMC Advanced Foundry', type: 'Manufacturer', country: 'Taiwan', capacity: 96, currentStatus: 'Operational', riskScore: 0.10, predictedDelayDays: 1 },
  { id: 'n8', label: 'Shenzhen Microelectronics', type: 'Manufacturer', country: 'China', capacity: 88, currentStatus: 'Operational', riskScore: 0.25, predictedDelayDays: 4 },
  { id: 'n9', label: 'Bavaria Auto Assembly', type: 'Manufacturer', country: 'Germany', capacity: 55, currentStatus: 'Delayed', riskScore: 0.74, predictedDelayDays: 14, contributingFactors: ['Missing semiconductor modules'] },
  { id: 'n10', label: 'Texas Hardware Assembly', type: 'Manufacturer', country: 'USA', capacity: 82, currentStatus: 'Operational', riskScore: 0.30, predictedDelayDays: 5 },
  { id: 'n11', label: 'Frankfurt Central Hub', type: 'Warehouse', country: 'Germany', capacity: 60, currentStatus: 'Delayed', riskScore: 0.68, predictedDelayDays: 12, contributingFactors: ['Intermodal freight halt'] },
  { id: 'n12', label: 'Chicago Central Logistics', type: 'Warehouse', country: 'USA', capacity: 89, currentStatus: 'Operational', riskScore: 0.18, predictedDelayDays: 2 },
  { id: 'n13', label: 'West Coast Dist. Center', type: 'Distribution', country: 'USA', capacity: 91, currentStatus: 'Operational', riskScore: 0.14, predictedDelayDays: 1 },
  { id: 'n14', label: 'Benelux Distribution', type: 'Distribution', country: 'Belgium', capacity: 48, currentStatus: 'Critical', riskScore: 0.82, predictedDelayDays: 16, contributingFactors: ['Downstream fulfillment freeze'] },
  { id: 'n15', label: 'European Tech Retailers', type: 'Retailer', country: 'Germany', capacity: 50, currentStatus: 'Critical', riskScore: 0.85, predictedDelayDays: 20, contributingFactors: ['Inventory depletion'] },
  { id: 'n16', label: 'North America Hub', type: 'Retailer', country: 'USA', capacity: 88, currentStatus: 'Operational', riskScore: 0.20, predictedDelayDays: 3 },
];

const INITIAL_EDGES = [
  { id: 'e1-7', source: 'n1', target: 'n7', isImpacted: false },
  { id: 'e2-8', source: 'n2', target: 'n8', isImpacted: false },
  { id: 'e3-7', source: 'n3', target: 'n7', isImpacted: false },
  { id: 'e7-5', source: 'n7', target: 'n5', isImpacted: false },
  { id: 'e5-4', source: 'n5', target: 'n4', isImpacted: true },
  { id: 'e5-6', source: 'n5', target: 'n6', isImpacted: false },
  { id: 'e8-4', source: 'n8', target: 'n4', isImpacted: true },
  { id: 'e4-9', source: 'n4', target: 'n9', isImpacted: true },
  { id: 'e4-11', source: 'n4', target: 'n11', isImpacted: true },
  { id: 'e6-10', source: 'n6', target: 'n10', isImpacted: false },
  { id: 'e9-11', source: 'n9', target: 'n11', isImpacted: true },
  { id: 'e10-12', source: 'n10', target: 'n12', isImpacted: false },
  { id: 'e11-14', source: 'n11', target: 'n14', isImpacted: true },
  { id: 'e12-13', source: 'n12', target: 'n13', isImpacted: false },
  { id: 'e14-15', source: 'n14', target: 'n15', isImpacted: true },
  { id: 'e13-16', source: 'n13', target: 'n16', isImpacted: false },
];

const COORDINATES: Record<string, { x: number; y: number }> = {
  n1: { x: 40, y: 100 }, n2: { x: 40, y: 260 }, n3: { x: 40, y: 420 },
  n7: { x: 280, y: 260 }, n8: { x: 280, y: 420 },
  n5: { x: 520, y: 180 }, n6: { x: 520, y: 420 },
  n4: { x: 760, y: 140 }, n10: { x: 760, y: 420 },
  n9: { x: 1000, y: 80 }, n11: { x: 1000, y: 240 }, n12: { x: 1000, y: 420 },
  n14: { x: 1240, y: 180 }, n13: { x: 1240, y: 420 },
  n15: { x: 1480, y: 180 }, n16: { x: 1480, y: 420 },
};

const CustomNode = memo(({ data, selected }: { data: GraphNodeData; selected: boolean }) => {
  const isSevere = data.riskScore >= 0.75;
  const isModerate = data.riskScore >= 0.35 && data.riskScore < 0.75;

  const borderColor = isSevere ? '#f43f5e' : isModerate ? '#f59e0b' : 'rgba(16, 185, 129, 0.5)';
  const glow = isSevere ? '0 0 15px rgba(244, 63, 94, 0.5)' : isModerate ? '0 0 8px rgba(245, 158, 11, 0.3)' : 'none';

  return (
    <div style={{
      padding: '12px 16px',
      backgroundColor: '#0f172a',
      borderRadius: '12px',
      border: `2px solid ${borderColor}`,
      boxShadow: selected ? '0 0 0 2px #22d3ee' : glow,
      minWidth: '200px',
      color: '#f8fafc',
      fontFamily: 'sans-serif'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: '#94a3b8' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
        <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', fontWeight: 600 }}>{data.type}</span>
        <span style={{
          fontSize: '9px',
          padding: '2px 6px',
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontWeight: 700,
          background: isSevere ? '#881337' : isModerate ? '#78350f' : '#064e3b',
          color: isSevere ? '#fda4af' : isModerate ? '#fcd34d' : '#6ee7b7'
        }}>
          {(data.riskScore * 100).toFixed(0)}% RISK
        </span>
      </div>
      <div style={{ fontWeight: 600, fontSize: '13px', marginBottom: '2px' }}>{data.label}</div>
      <div style={{ fontSize: '11px', color: '#64748b' }}>{data.country}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', paddingTop: '6px', borderTop: '1px solid #1e293b', fontSize: '11px' }}>
        <span style={{ color: '#64748b' }}>Delay</span>
        <span style={{ fontFamily: 'monospace', fontWeight: 600, color: isSevere ? '#f43f5e' : '#f8fafc' }}>+{data.predictedDelayDays}d</span>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#94a3b8' }} />
    </div>
  );
});

export default function App() {
  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [timelineStep, setTimelineStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [newsText, setNewsText] = useState('');

  const initialFlowNodes: Node[] = useMemo(() => {
    return INITIAL_NODES.map((n) => ({
      id: n.id,
      type: 'custom',
      position: COORDINATES[n.id] || { x: 100, y: 100 },
      data: n,
    }));
  }, []);

  const initialFlowEdges: Edge[] = useMemo(() => {
    return INITIAL_EDGES.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      animated: e.isImpacted,
      style: { stroke: e.isImpacted ? '#f43f5e' : '#475569', strokeWidth: e.isImpacted ? 2.5 : 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: e.isImpacted ? '#f43f5e' : '#475569' },
    }));
  }, []);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialFlowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialFlowEdges);

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node.data as unknown as GraphNodeData);
  }, []);

  const handleSimulate = async () => {
    if (!newsText.trim()) return;
    setIsLoading(true);
    setTimeout(() => {
      setNodes((nds) =>
        nds.map((node) => {
          const d = node.data as unknown as GraphNodeData;
          if (['n4', 'n9', 'n11', 'n14', 'n15'].includes(node.id)) {
            return {
              ...node,
              data: {
                ...d,
                riskScore: 0.92,
                predictedDelayDays: d.predictedDelayDays + 8,
                contributingFactors: ['Disruption shockwave', 'Supply blockage', 'Port backlog']
              }
            };
          }
          return node;
        })
      );
      setEdges((eds) =>
        eds.map((edge) => {
          const isHigh = ['n4', 'n9', 'n11', 'n14', 'n15'].includes(edge.target);
          return {
            ...edge,
            animated: isHigh,
            style: { stroke: isHigh ? '#f43f5e' : '#475569', strokeWidth: isHigh ? 2.5 : 1.5 },
            markerEnd: { type: MarkerType.ArrowClosed, color: isHigh ? '#f43f5e' : '#475569' },
          };
        })
      );
      setIsLoading(false);
    }, 600);
  };

  const handleTimelineChange = (step: number) => {
    setTimelineStep(step);
    setNodes((nds) =>
      nds.map((node) => {
        const d = node.data as unknown as GraphNodeData;
        const multiplier = 1 + step * 0.4;
        return {
          ...node,
          data: {
            ...d,
            predictedDelayDays: Math.round(d.predictedDelayDays * multiplier),
            riskScore: Math.min(1.0, d.riskScore * (1 + step * 0.1)),
          },
        };
      })
    );
  };

  const criticalCount = nodes.filter((n) => ((n.data as unknown as GraphNodeData).riskScore >= 0.75)).length;

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#020617', color: '#f8fafc', overflow: 'hidden', margin: 0, padding: 0 }}>
      {/* Header */}
      <header style={{ height: '60px', borderBottom: '1px solid #1e293b', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#0f172a', flexShrink: 0, zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Network style={{ width: 22, height: 22, color: '#22d3ee' }} />
          <div>
            <h1 style={{ fontSize: '15px', fontWeight: 700, margin: 0 }}>AtmoGraph</h1>
            <p style={{ fontSize: '11px', color: '#64748b', margin: 0 }}>Supply Chain Ripple Effect Predictor</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399' }}>
            <Activity style={{ width: 14, height: 14 }} />
            <span>Inference Engine Active</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderLeft: '1px solid #1e293b', paddingLeft: '16px' }}>
            <span>Nodes: <b>{nodes.length}</b></span>
            <span style={{ color: '#f43f5e' }}>Critical: <b>{criticalCount}</b></span>
          </div>
        </div>
      </header>

      {/* Main Viewport */}
      <div style={{ flex: 1, position: 'relative', width: '100%', height: 'calc(100vh - 60px)' }}>
        {/* Input Panel */}
        <div style={{ position: 'absolute', top: 16, left: 16, zIndex: 10, width: '310px', backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '14px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f43f5e', fontSize: '12px', fontWeight: 700, marginBottom: '8px' }}>
            <Flame style={{ width: 14, height: 14 }} />
            <span>Simulate Disruption Event</span>
          </div>
          <div style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
            <button onClick={() => setNewsText('Port of Rotterdam dockworker strike halting European container logistics')} style={{ fontSize: '10px', backgroundColor: '#1e293b', color: '#94a3b8', border: '1px solid #334155', borderRadius: '4px', padding: '3px 6px', cursor: 'pointer' }}>
              Rotterdam Strike
            </button>
            <button onClick={() => setNewsText('Taiwan semiconductor fab hit by severe power outage affecting wafer output')} style={{ fontSize: '10px', backgroundColor: '#1e293b', color: '#94a3b8', border: '1px solid #334155', borderRadius: '4px', padding: '3px 6px', cursor: 'pointer' }}>
              Chip Shortage
            </button>
          </div>
          <textarea
            value={newsText}
            onChange={(e) => setNewsText(e.target.value)}
            placeholder="Type or click a preset above..."
            style={{ width: '100%', height: '60px', backgroundColor: '#020617', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '8px', fontSize: '11px', boxSizing: 'border-box', outline: 'none', resize: 'none' }}
          />
          <button
            onClick={handleSimulate}
            disabled={isLoading || !newsText.trim()}
            style={{ width: '100%', marginTop: '8px', padding: '8px', backgroundColor: '#0891b2', color: '#020617', fontWeight: 700, fontSize: '11px', borderRadius: '6px', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
          >
            <Play style={{ width: 12, height: 12, fill: '#020617' }} />
            {isLoading ? 'Computing GNN Ripple...' : 'Simulate Propagation'}
          </button>
        </div>

        {/* Network Canvas */}
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#1e293b" gap={20} size={1.5} />
          <Controls />
        </ReactFlow>

        {/* Details Drawer */}
        {selectedNode && (
          <div style={{ position: 'absolute', top: 0, right: 0, width: '300px', height: '100%', backgroundColor: '#0f172a', borderLeft: '1px solid #1e293b', padding: '16px', zIndex: 20, boxSizing: 'border-box' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '10px', textTransform: 'uppercase', color: '#22d3ee', fontWeight: 600 }}>{selectedNode.type}</span>
                <h3 style={{ fontSize: '15px', fontWeight: 700, margin: '2px 0' }}>{selectedNode.label}</h3>
              </div>
              <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <X style={{ width: 18, height: 18 }} />
              </button>
            </div>
            <div style={{ backgroundColor: selectedNode.riskScore >= 0.75 ? 'rgba(136, 19, 55, 0.3)' : 'rgba(6, 78, 59, 0.3)', border: `1px solid ${selectedNode.riskScore >= 0.75 ? '#881337' : '#064e3b'}`, borderRadius: '8px', padding: '12px', marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '11px' }}>
                <span style={{ color: '#94a3b8' }}>Predicted Delay:</span>
                <span style={{ fontWeight: 700, color: selectedNode.riskScore >= 0.75 ? '#f43f5e' : '#34d399' }}>+{selectedNode.predictedDelayDays} Days</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                <span style={{ color: '#94a3b8' }}>Risk Factor:</span>
                <span style={{ fontWeight: 700, color: selectedNode.riskScore >= 0.75 ? '#f43f5e' : '#34d399' }}>{(selectedNode.riskScore * 100).toFixed(0)}%</span>
              </div>
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: '1.6' }}>
              <div><b>Country:</b> {selectedNode.country}</div>
              <div><b>Capacity:</b> {selectedNode.capacity}%</div>
              <div><b>Status:</b> {selectedNode.currentStatus}</div>
            </div>
          </div>
        )}

        {/* Timeline Scrubber */}
        <div style={{ position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)', zIndex: 10, backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '30px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Clock style={{ width: 14, height: 14, color: '#22d3ee' }} />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8' }}>Horizon:</span>
          {[
            { label: 'Real-Time', val: 0 },
            { label: '+30 Days', val: 1 },
            { label: '+60 Days', val: 2 },
            { label: '+90 Days', val: 3 },
          ].map((s) => (
            <button
              key={s.val}
              onClick={() => handleTimelineChange(s.val)}
              style={{
                fontSize: '11px',
                padding: '4px 10px',
                borderRadius: '20px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: timelineStep === s.val ? '#06b6d4' : '#1e293b',
                color: timelineStep === s.val ? '#020617' : '#94a3b8',
                fontWeight: timelineStep === s.val ? 700 : 500
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

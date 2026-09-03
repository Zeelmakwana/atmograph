import React from 'react';
import { X, AlertTriangle, ShieldCheck, Route, Activity } from 'lucide-react';
import { GraphNodeData } from '../types';

interface Props {
  node: GraphNodeData | null;
  onClose: () => void;
}

export const ImpactDetailsPanel: React.FC<Props> = ({ node, onClose }) => {
  if (!node) return null;

  const isSevere = node.riskScore >= 0.75;
  const isModerate = node.riskScore >= 0.35 && node.riskScore < 0.75;

  return (
    <div className="w-80 bg-slate-900 border-l border-slate-800 p-5 overflow-y-auto flex flex-col gap-4 shadow-2xl z-20">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono uppercase text-cyan-400">{node.type}</span>
          <h2 className="text-base font-bold text-slate-100">{node.label}</h2>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-100 p-1 rounded-lg">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className={`p-3 rounded-xl border ${
        isSevere ? 'bg-rose-950/40 border-rose-800/80 text-rose-200' :
        isModerate ? 'bg-amber-950/40 border-amber-800/80 text-amber-200' :
        'bg-emerald-950/40 border-emerald-800/80 text-emerald-200'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          {isSevere ? <AlertTriangle className="w-4 h-4 text-rose-400" /> : <ShieldCheck className="w-4 h-4 text-emerald-400" />}
          <span className="font-bold text-xs tracking-wide">Impact Assessment</span>
        </div>
        <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800/60 font-mono">
          <div>
            <div className="text-[10px] text-slate-400">Delay</div>
            <div className="text-lg font-bold">+{node.predictedDelayDays} Days</div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400">Risk</div>
            <div className="text-lg font-bold">{(node.riskScore * 100).toFixed(0)}%</div>
          </div>
        </div>
      </div>

      <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl space-y-2 text-xs">
        <div className="flex items-center gap-2 font-semibold text-slate-300 mb-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span>Telemetry</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Country:</span> <span className="text-slate-200">{node.country}</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Capacity:</span> <span className="text-slate-200 font-mono">{node.capacity}%</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Status:</span> <span className="text-slate-200">{node.currentStatus}</span>
        </div>
      </div>

      <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl space-y-2 text-xs">
        <div className="flex items-center gap-2 font-semibold text-slate-300 mb-2">
          <Route className="w-4 h-4 text-purple-400" />
          <span>Contributing Factors</span>
        </div>
        <ul className="space-y-1 text-slate-400">
          {node.contributingFactors && node.contributingFactors.length > 0 ? (
            node.contributingFactors.map((factor, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-rose-400 font-bold">•</span>
                <span>{factor}</span>
              </li>
            ))
          ) : (
            <li className="italic text-slate-500">Nominal upstream status.</li>
          )}
        </ul>
      </div>
    </div>
  );
};

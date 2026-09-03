import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Factory, Anchor, Warehouse, Truck, ShoppingBag, Pickaxe } from 'lucide-react';
import { GraphNodeData } from '../types';

const getNodeIcon = (type: string) => {
  switch (type) {
    case 'Supplier': return <Pickaxe className="w-4 h-4 text-emerald-400" />;
    case 'Port': return <Anchor className="w-4 h-4 text-cyan-400" />;
    case 'Manufacturer': return <Factory className="w-4 h-4 text-blue-400" />;
    case 'Warehouse': return <Warehouse className="w-4 h-4 text-amber-400" />;
    case 'Distribution': return <Truck className="w-4 h-4 text-purple-400" />;
    case 'Retailer': return <ShoppingBag className="w-4 h-4 text-pink-400" />;
    default: return <Factory className="w-4 h-4 text-gray-400" />;
  }
};

export const CustomNode = memo(({ data, selected }: { data: GraphNodeData; selected: boolean }) => {
  const isSevere = data.riskScore >= 0.75;
  const isModerate = data.riskScore >= 0.35 && data.riskScore < 0.75;

  const borderClass = isSevere 
    ? 'border-rose-500 shadow-[0_0_18px_rgba(244,63,94,0.6)] animate-pulse'
    : isModerate 
    ? 'border-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.3)]' 
    : 'border-emerald-500/50 shadow-[0_0_8px_rgba(16,185,129,0.15)]';

  return (
    <div className={`px-4 py-3 bg-slate-900/90 backdrop-blur-md rounded-xl border-2 transition-all duration-300 min-w-[210px] ${borderClass} ${selected ? 'ring-2 ring-cyan-400' : ''}`}>
      <Handle type="target" position={Position.Left} className="w-2.5 h-2.5 bg-slate-400 border border-slate-900" />
      
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          {getNodeIcon(data.type)}
          <span className="text-[11px] font-semibold tracking-wide uppercase text-slate-400">{data.type}</span>
        </div>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
          isSevere ? 'bg-rose-950 text-rose-300 border border-rose-800' :
          isModerate ? 'bg-amber-950 text-amber-300 border border-amber-800' :
          'bg-emerald-950 text-emerald-300 border border-emerald-800'
        }`}>
          {(data.riskScore * 100).toFixed(0)}% RISK
        </span>
      </div>

      <div className="font-semibold text-slate-100 text-sm truncate">{data.label}</div>
      <div className="text-xs text-slate-400 mb-2">{data.country}</div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px]">
        <span className="text-slate-500">Delay</span>
        <span className={`font-mono font-semibold ${isSevere ? 'text-rose-400' : isModerate ? 'text-amber-400' : 'text-slate-300'}`}>
          +{data.predictedDelayDays}d
        </span>
      </div>

      <Handle type="source" position={Position.Right} className="w-2.5 h-2.5 bg-slate-400 border border-slate-900" />
    </div>
  );
});

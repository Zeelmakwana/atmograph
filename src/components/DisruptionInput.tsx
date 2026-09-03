import React, { useState } from 'react';
import { Flame, Play, Sparkles } from 'lucide-react';

interface Props {
  onSimulate: (text: string) => void;
  isLoading: boolean;
}

export const DisruptionInput: React.FC<Props> = ({ onSimulate, isLoading }) => {
  const [text, setText] = useState('');

  const PRESETS = [
    { title: 'Rotterdam Strike', text: 'Indefinite strike declared at Port of Rotterdam. Container operations completely halted with backlog growing by 40,000 TEU daily.' },
    { title: 'Taiwan Chip Shortage', text: 'Severe energy grid disruption in Hsinchu Science Park, reducing semiconductor wafer fabrication capacity by 65%.' },
    { title: 'Panama Canal Drought', text: 'Daily transit slots through Panama Canal reduced by 40% due to historical low water levels, forcing maritime rerouting.' }
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col gap-3">
      <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
        <Flame className="w-4 h-4" />
        <span>Inject Disruption</span>
      </div>

      <div className="flex gap-2 flex-wrap">
        {PRESETS.map((p, idx) => (
          <button
            key={idx}
            onClick={() => setText(p.text)}
            className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700 transition flex items-center gap-1"
          >
            <Sparkles className="w-3 h-3 text-cyan-400" />
            {p.title}
          </button>
        ))}
      </div>

      <textarea
        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none h-20"
        placeholder="Paste disruption news..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <button
        disabled={isLoading || !text.trim()}
        onClick={() => onSimulate(text)}
        className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2 text-xs uppercase tracking-wider transition"
      >
        <Play className="w-4 h-4 fill-slate-950" />
        {isLoading ? 'Running GNN Inference...' : 'Simulate Ripple'}
      </button>
    </div>
  );
};

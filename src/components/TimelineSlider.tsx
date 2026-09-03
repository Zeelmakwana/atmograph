import React from 'react';
import { Clock } from 'lucide-react';

interface Props {
  currentStep: number;
  onChange: (step: number) => void;
}

export const TimelineSlider: React.FC<Props> = ({ currentStep, onChange }) => {
  const steps = [
    { label: 'T0: Real-Time', val: 0 },
    { label: '+30 Days', val: 1 },
    { label: '+60 Days', val: 2 },
    { label: '+90 Days', val: 3 },
  ];

  return (
    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 px-5 py-2.5 rounded-full shadow-2xl flex items-center gap-4">
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
        <Clock className="w-4 h-4 text-cyan-400" />
        <span>Horizon:</span>
      </div>
      <div className="flex gap-1.5">
        {steps.map((s) => (
          <button
            key={s.val}
            onClick={() => onChange(s.val)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition ${
              currentStep === s.val
                ? 'bg-cyan-500 text-slate-950 font-bold'
                : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
};

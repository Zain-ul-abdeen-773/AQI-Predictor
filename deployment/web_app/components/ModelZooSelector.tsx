'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Award, Sparkles } from 'lucide-react';

export interface ModelZooEntry {
  id: string;
  name: string;
  category: string;
  r2: number;
  rmse: number;
  mae: number;
  is_default: boolean;
  description?: string;
}

interface ModelZooSelectorProps {
  modelList: ModelZooEntry[];
  activeModelId: string;
  onModelChange: (newId: string) => void;
  isFetching?: boolean;
}

export default function ModelZooSelector({
  modelList = [],
  activeModelId,
  onModelChange,
  isFetching = false,
}: ModelZooSelectorProps) {
  const currentModel = modelList.find((m) => m.id === activeModelId) || modelList[0];

  return (
    <div className="relative z-30 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 p-4 rounded-2xl bg-[#0D1B2A]/80 backdrop-blur-xl border border-sky-400/[0.08] shadow-lg">
      <div className="flex items-center gap-3.5">
        <div className="p-3 rounded-xl bg-gradient-to-br from-sky-500/15 to-blue-600/10 border border-sky-500/20 text-sky-400">
          <Cpu className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">Active Model</span>
            {currentModel?.is_default && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-sky-500/15 text-sky-300 text-[10px] font-semibold border border-sky-500/20">
                <Award className="w-2.5 h-2.5" /> Best R²
              </span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-slate-100 tracking-tight mt-0.5">
            {currentModel?.name || 'Loading...'}
          </h3>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full lg:w-auto">
        <div className="flex items-center gap-4 px-4 py-2 rounded-xl bg-[#080F1A]/60 border border-white/[0.05] text-[11px] text-slate-400">
          <div className="flex flex-col">
            <span className="text-[9px] uppercase text-slate-500 tracking-wider">R²</span>
            <span className="font-mono font-bold text-sky-400 text-sm">{currentModel?.r2?.toFixed(3) || '—'}</span>
          </div>
          <div className="h-6 w-px bg-white/[0.06]" />
          <div className="flex flex-col">
            <span className="text-[9px] uppercase text-slate-500 tracking-wider">RMSE</span>
            <span className="font-mono font-semibold text-slate-200 text-sm">{currentModel?.rmse?.toFixed(2) || '—'}</span>
          </div>
          <div className="h-6 w-px bg-white/[0.06]" />
          <div className="flex flex-col">
            <span className="text-[9px] uppercase text-slate-500 tracking-wider">MAE</span>
            <span className="font-mono font-semibold text-slate-300 text-sm">{currentModel?.mae?.toFixed(2) || '—'}</span>
          </div>
        </div>

        <div className="relative min-w-[240px]">
          <select
            value={activeModelId}
            onChange={(e) => onModelChange(e.target.value)}
            disabled={isFetching}
            aria-label="Select prediction model"
            className="w-full appearance-none bg-white/[0.05] hover:bg-white/[0.08] transition-colors border border-sky-400/[0.12] rounded-xl px-4 py-2.5 text-sm font-medium text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500/30 cursor-pointer pr-9"
          >
            {modelList.map((entry) => (
              <option key={entry.id} value={entry.id} className="bg-[#0D1B2A] text-white py-2">
                {entry.name} — R² {entry.r2.toFixed(3)} {entry.is_default ? '★' : ''}
              </option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
            <Sparkles className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-sky-400' : ''}`} />
          </div>
        </div>
      </div>
    </div>
  );
}

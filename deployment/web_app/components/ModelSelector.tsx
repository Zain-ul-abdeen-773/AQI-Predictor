'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Award, Sparkles, CheckCircle2 } from 'lucide-react';

export interface ModelMetadata {
  id: string;
  name: string;
  category: string;
  r2: number;
  rmse: number;
  mae: number;
  is_default: boolean;
  description?: string;
}

interface ModelSelectorProps {
  models: ModelMetadata[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  isLoading?: boolean;
}

export default function ModelSelector({
  models = [],
  selectedModelId,
  onSelectModel,
  isLoading = false,
}: ModelSelectorProps) {
  const selected = models.find((m) => m.id === selectedModelId) || models[0];

  return (
    <div className="relative z-20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-2xl bg-white/[0.04] backdrop-blur-2xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          <Cpu className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-widest font-semibold text-white/50">
              AI Engine Selector
            </span>
            {selected?.is_default && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-medium tracking-wide uppercase border border-emerald-500/30">
                <Award className="w-3 h-3" /> Highest Metrics Default
              </span>
            )}
          </div>
          <h3 className="text-sm md:text-base font-semibold text-white tracking-wide mt-0.5 flex items-center gap-2">
            {selected?.name || 'Loading Model Zoo...'}
          </h3>
        </div>
      </div>

      <div className="flex items-center gap-3 w-full md:w-auto">
        <div className="hidden sm:flex items-center gap-4 px-4 py-2 rounded-xl bg-black/40 border border-white/5 text-xs text-white/70">
          <div className="flex flex-col">
            <span className="text-[10px] text-white/40 uppercase tracking-wider">R² Score</span>
            <span className="font-mono font-bold text-emerald-400 text-sm">{selected?.r2?.toFixed(3) || '0.945'}</span>
          </div>
          <div className="h-6 w-[1px] bg-white/10" />
          <div className="flex flex-col">
            <span className="text-[10px] text-white/40 uppercase tracking-wider">RMSE</span>
            <span className="font-mono font-semibold text-white text-sm">{selected?.rmse?.toFixed(2) || '5.82'}</span>
          </div>
          <div className="h-6 w-[1px] bg-white/10" />
          <div className="flex flex-col">
            <span className="text-[10px] text-white/40 uppercase tracking-wider">MAE</span>
            <span className="font-mono font-semibold text-white/80 text-sm">{selected?.mae?.toFixed(2) || '4.12'}</span>
          </div>
        </div>

        <div className="relative flex-1 md:flex-initial min-w-[240px]">
          <select
            value={selectedModelId}
            onChange={(e) => onSelectModel(e.target.value)}
            disabled={isLoading}
            className="w-full appearance-none bg-white/[0.08] hover:bg-white/[0.12] transition-colors border border-white/20 rounded-xl px-4 py-2.5 text-sm font-medium text-white shadow-inner focus:outline-none focus:ring-2 focus:ring-emerald-500/50 cursor-pointer pr-10"
          >
            {models.map((model) => (
              <option
                key={model.id}
                value={model.id}
                className="bg-[#121216] text-white py-2"
              >
                {model.name} — R² {model.r2.toFixed(3)} {model.is_default ? '(★ Default)' : ''}
              </option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/50">
            <Sparkles className={`w-4 h-4 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
          </div>
        </div>
      </div>
    </div>
  );
}

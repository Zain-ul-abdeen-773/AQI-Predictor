'use client';

import React from 'react';
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
    <div className="relative z-30 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 p-6 rounded-3xl bg-[#F2F4F8] shadow-neumorphic border border-white/80 transition-all duration-300">
      {/* Left: Active Model Overview */}
      <div className="flex items-center gap-4">
        <div className="p-3.5 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-inset border border-white flex items-center justify-center text-[#0284C7]">
          <Cpu className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2.5">
            <span className="text-xs uppercase tracking-wider font-bold text-[#64748B]">
              Active Regression Engine
            </span>
            {currentModel?.is_default && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-[#F2F4F8] shadow-neumorphic-sm text-[#0284C7] text-[11px] font-bold border border-white">
                <Award className="w-3 h-3 text-[#0284C7]" /> Benchmark Leader
              </span>
            )}
          </div>
          <h3 className="text-lg font-bold text-[#2D3748] tracking-tight mt-1">
            {currentModel?.name || 'Loading...'}
          </h3>
        </div>
      </div>

      {/* Right: Validation Metrics & Model Selector */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full lg:w-auto">
        {/* Cross-Validation Telemetry */}
        <div className="flex items-center gap-5 px-5 py-3 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-inset border border-white text-xs text-[#475569]">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase font-semibold text-[#94A3B8] tracking-wider">R² Accuracy</span>
            <span className="font-mono font-extrabold text-[#0284C7] text-base">
              {currentModel?.r2?.toFixed(3) || '—'}
            </span>
          </div>
          <div className="h-8 w-px bg-[#D1D9E6]/60" />
          <div className="flex flex-col">
            <span className="text-[10px] uppercase font-semibold text-[#94A3B8] tracking-wider">RMSE</span>
            <span className="font-mono font-bold text-[#2D3748] text-base">
              {currentModel?.rmse?.toFixed(2) || '—'}
            </span>
          </div>
          <div className="h-8 w-px bg-[#D1D9E6]/60" />
          <div className="flex flex-col">
            <span className="text-[10px] uppercase font-semibold text-[#94A3B8] tracking-wider">MAE</span>
            <span className="font-mono font-bold text-[#475569] text-base">
              {currentModel?.mae?.toFixed(2) || '—'}
            </span>
          </div>
        </div>

        {/* Tactile Model Selector Dropdown */}
        <div className="relative min-w-[260px]">
          <select
            value={activeModelId}
            onChange={(e) => onModelChange(e.target.value)}
            disabled={isFetching}
            aria-label="Select prediction model"
            className="w-full appearance-none bg-[#F2F4F8] hover:bg-[#EAEFF7] transition-all shadow-neumorphic-sm border border-white rounded-2xl px-5 py-3.5 text-sm font-bold text-[#2D3748] focus:outline-none focus:ring-2 focus:ring-[#0284C7]/40 cursor-pointer pr-10"
          >
            {modelList.map((entry) => (
              <option key={entry.id} value={entry.id} className="bg-[#F2F4F8] text-[#2D3748] font-semibold py-2">
                {entry.name} — R² {entry.r2.toFixed(3)} {entry.is_default ? '★' : ''}
              </option>
            ))}
          </select>
          <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-[#64748B]">
            <Sparkles className={`w-4 h-4 ${isFetching ? 'animate-spin text-[#0284C7]' : ''}`} />
          </div>
        </div>
      </div>
    </div>
  );
}

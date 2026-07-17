'use client';

import React from 'react';

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
    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 p-6 rounded-md border border-neutral-200/60 bg-white/70 backdrop-blur-sm">
      {/* Left: Active Model Architecture Identity */}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-medium tracking-tight text-neutral-400">
            ENGINE ARCHITECTURE
          </span>
          {currentModel?.is_default && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[#0066FF]/10 text-[#0066FF]">
              BENCHMARK LEADER
            </span>
          )}
        </div>
        <h3 className="text-xl font-semibold tracking-tight text-[#090A0F] mt-1">
          {currentModel?.name || 'Loading...'}
        </h3>
        <span className="text-xs text-neutral-500 mt-0.5">
          {currentModel?.category} pipeline • Out-of-sample 5-fold TimeSeriesSplit validation
        </span>
      </div>

      {/* Right: Validation Metrics & Model Selector Dropdown */}
      <div className="flex flex-wrap items-center gap-5 w-full md:w-auto">
        {/* Verification Metrics Table */}
        <div className="flex items-center gap-6 px-4 py-2 rounded-md border border-neutral-200/60 bg-neutral-50/60 text-xs">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-neutral-400">R² ACCURACY</span>
            <span className="font-mono font-semibold text-[#0066FF] text-sm">
              {currentModel?.r2?.toFixed(3) || '—'}
            </span>
          </div>
          <div className="h-6 w-px bg-neutral-200" />
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-neutral-400">RMSE</span>
            <span className="font-mono font-medium text-[#090A0F] text-sm">
              {currentModel?.rmse?.toFixed(2) || '—'}
            </span>
          </div>
          <div className="h-6 w-px bg-neutral-200" />
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-neutral-400">MAE</span>
            <span className="font-mono font-medium text-neutral-600 text-sm">
              {currentModel?.mae?.toFixed(2) || '—'}
            </span>
          </div>
        </div>

        {/* Model Dropdown Selector */}
        <div className="relative min-w-[240px] flex-1 md:flex-none">
          <select
            value={activeModelId}
            onChange={(e) => onModelChange(e.target.value)}
            disabled={isFetching}
            aria-label="Select prediction model"
            className="w-full appearance-none bg-white hover:bg-neutral-50 transition-colors border border-neutral-200/80 rounded-md px-4 py-2.5 text-xs font-medium text-[#090A0F] focus:outline-none focus:border-[#0066FF] cursor-pointer pr-8 shadow-2xs"
          >
            {modelList.map((entry) => (
              <option key={entry.id} value={entry.id} className="text-[#090A0F] font-medium py-1">
                {entry.name} (R² {entry.r2.toFixed(3)}) {entry.is_default ? '★' : ''}
              </option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-neutral-400 font-mono text-xs">
            {isFetching ? '...' : '▼'}
          </div>
        </div>
      </div>
    </div>
  );
}

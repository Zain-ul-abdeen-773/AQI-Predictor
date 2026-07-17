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
    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 p-6 rounded-2xl border border-slate-700/50 bg-slate-800/40 backdrop-blur-xl shadow-xl">
      {/* Left: Active Model Architecture Identity */}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-medium tracking-tight text-slate-400">
            ENGINE ARCHITECTURE
          </span>
          {currentModel?.is_default && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">
              BENCHMARK LEADER
            </span>
          )}
        </div>
        <h3 className="text-xl font-semibold tracking-tight text-white mt-1">
          {currentModel?.name || 'Loading...'}
        </h3>
        <span className="text-xs text-slate-400 mt-0.5">
          {currentModel?.category} pipeline • Out-of-sample 5-fold TimeSeriesSplit validation
        </span>
      </div>

      {/* Right: Validation Metrics & Model Selector Dropdown */}
      <div className="flex flex-wrap items-center gap-5 w-full md:w-auto">
        {/* Verification Metrics Table */}
        <div className="flex items-center gap-6 px-4 py-2 rounded-xl border border-slate-700/50 bg-slate-900/50 text-xs shadow-inner">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-slate-500">R² ACCURACY</span>
            <span className="font-mono font-semibold text-blue-400 text-sm">
              {currentModel?.r2?.toFixed(4) || '—'}
            </span>
          </div>
          <div className="h-6 w-px bg-slate-700" />
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-slate-500">RMSE</span>
            <span className="font-mono text-slate-300 text-sm">
              {currentModel?.rmse?.toFixed(2) || '—'}
            </span>
          </div>
          <div className="h-6 w-px bg-slate-700" />
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-slate-500">MAE</span>
            <span className="font-mono text-slate-300 text-sm">
              {currentModel?.mae?.toFixed(2) || '—'}
            </span>
          </div>
        </div>

        {/* Action Select */}
        <div className="relative">
          <select
            value={activeModelId}
            onChange={(e) => onModelChange(e.target.value)}
            disabled={isFetching}
            className="appearance-none bg-slate-900/80 border border-slate-700/80 text-white font-medium text-sm rounded-xl px-5 py-2.5 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer disabled:opacity-50 hover:bg-slate-800 transition-colors"
          >
            {modelList.map((m) => (
              <option key={m.id} value={m.id}>
                Switch to {m.name}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

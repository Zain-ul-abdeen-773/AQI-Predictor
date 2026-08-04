'use client';

import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';

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
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [glowPos, setGlowPos] = useState({ x: 50, y: 50 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setTilt({
      x: (y - 0.5) * -8,
      y: (x - 0.5) * 8,
    });
    setGlowPos({ x: x * 100, y: y * 100 });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
    setGlowPos({ x: 50, y: 50 });
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      style={{
        transform: `perspective(1200px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
        transformStyle: 'preserve-3d',
      }}
      className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-6 p-6 rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-2xl shadow-2xl overflow-hidden transition-transform duration-200 ease-out"
    >
      {/* Dynamic glow that follows cursor */}
      <div
        className="absolute inset-0 pointer-events-none opacity-40 transition-opacity duration-500"
        style={{
          background: `radial-gradient(600px circle at ${glowPos.x}% ${glowPos.y}%, rgba(56,189,248,0.08), transparent 50%)`,
        }}
      />

      {/* Left: Active Model Identity */}
      <div className="relative z-10 flex flex-col" style={{ transform: 'translateZ(20px)' }}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-medium tracking-tight text-slate-400">
            ENGINE ARCHITECTURE
          </span>
          {currentModel?.is_default && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.2)]"
            >
              CHAMPION
            </motion.span>
          )}
        </div>
        <h3 className="text-xl font-bold tracking-tight text-white mt-1.5">
          {currentModel?.name || 'Loading...'}
        </h3>
        <span className="text-xs text-slate-400 mt-0.5">
          {currentModel?.category} &middot; 5-fold TimeSeriesSplit validation
        </span>
      </div>

      {/* Right: Metrics & Selector */}
      <div className="relative z-10 flex flex-wrap items-center gap-5 w-full md:w-auto" style={{ transform: 'translateZ(15px)' }}>
        {/* Metrics */}
        <div className="flex items-center gap-5 px-5 py-3 rounded-xl border border-white/[0.06] bg-black/20 backdrop-blur-md text-xs shadow-inner">
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-mono text-slate-500">R²</span>
            <motion.span
              key={currentModel?.r2}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="font-mono font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300 text-base"
            >
              {currentModel?.r2?.toFixed(4) || '—'}
            </motion.span>
          </div>
          <div className="h-8 w-px bg-white/10" />
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-mono text-slate-500">RMSE</span>
            <span className="font-mono font-semibold text-slate-200 text-sm">
              {currentModel?.rmse?.toFixed(2) || '—'}
            </span>
          </div>
          <div className="h-8 w-px bg-white/10" />
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-mono text-slate-500">MAE</span>
            <span className="font-mono font-semibold text-slate-200 text-sm">
              {currentModel?.mae?.toFixed(2) || '—'}
            </span>
          </div>
        </div>

        {/* Selector */}
        <div className="relative group">
          <select
            value={activeModelId}
            onChange={(e) => onModelChange(e.target.value)}
            disabled={isFetching}
            aria-label="Select prediction model"
            className="appearance-none bg-black/30 border border-white/[0.08] text-white font-medium text-sm rounded-xl px-5 py-2.5 pr-10 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500/50 cursor-pointer disabled:opacity-50 hover:bg-white/[0.04] hover:border-white/[0.12] transition-all duration-200 backdrop-blur-md"
          >
            {modelList.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.category})
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 group-hover:text-cyan-400 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

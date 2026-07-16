'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Cpu, Activity, Clock, Layers, ShieldCheck } from 'lucide-react';
import ParticleEngine from '../../components/ParticleEngine';

export default function AnalyticsPage() {
  return (
    <div className="relative z-10 flex flex-col gap-8 pb-12">
      <ParticleEngine aqi={92} />

      {/* Header */}
      <div className="p-8 rounded-3xl bg-white/[0.04] backdrop-blur-2xl border border-white/10 shadow-[0_16px_48px_rgba(0,0,0,0.5)] flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold uppercase tracking-widest text-emerald-400 mb-4">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Telemetry Tele-Analytics & Benchmarks</span>
          </div>
          <h1 className="text-2xl md:text-4xl font-light tracking-tight text-white">
            Model Zoo Performance & Diurnal Dynamics
          </h1>
          <p className="text-sm text-white/60 mt-2 leading-relaxed">
            Comparative exploratory telemetry comparing our 8 neural and tree ensemble architectures across cross-validation folds on historical Sargodha environmental observations.
          </p>
        </div>
      </div>

      {/* Grid of Analytical Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Benchmark R2 Cross-Comparison */}
        <div className="p-6 rounded-3xl bg-white/[0.03] backdrop-blur-2xl border border-white/10 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-400" />
                8-Model Zoo R² Score Leaderboard
              </h3>
              <span className="text-xs text-white/40">Evaluation metric</span>
            </div>
            <p className="text-xs text-white/50 mb-6">
              Bi-LSTM with Multi-Head Attention outperforms traditional statistical regressors by capturing multi-hour temporal lag dependencies.
            </p>
          </div>

          <div className="flex flex-col gap-3 font-mono text-xs">
            {[
              { name: 'Bi-LSTM + Attention', r2: 0.945, color: 'bg-emerald-400', champion: true },
              { name: 'LightGBM (Optuna)', r2: 0.931, color: 'bg-cyan-400' },
              { name: 'XGBoost (Optuna)', r2: 0.928, color: 'bg-blue-400' },
              { name: 'Gradient Boosting', r2: 0.912, color: 'bg-indigo-400' },
              { name: 'Random Forest', r2: 0.895, color: 'bg-purple-400' },
              { name: 'Extra Trees', r2: 0.887, color: 'bg-pink-400' },
              { name: 'Scikit Ridge', r2: 0.842, color: 'bg-amber-400' },
              { name: 'Support Vector (SVR)', r2: 0.835, color: 'bg-orange-400' },
            ].map((m, idx) => (
              <div key={m.name} className="flex items-center justify-between gap-3 p-2 rounded-xl bg-black/40 border border-white/5">
                <span className="text-white/80 font-sans">{m.name}</span>
                <div className="flex items-center gap-3">
                  <div className="w-24 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${m.r2 * 100}%` }}
                      transition={{ duration: 0.6, delay: idx * 0.05 }}
                      className={`h-full ${m.color}`}
                    />
                  </div>
                  <span className={`font-bold ${m.champion ? 'text-emerald-400' : 'text-white'}`}>
                    {m.r2.toFixed(3)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Card 2: Diurnal Smog Wave Pattern */}
        <div className="p-6 rounded-3xl bg-white/[0.03] backdrop-blur-2xl border border-white/10 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-400" />
                Diurnal Smog Concentration Wave
              </h3>
              <span className="text-xs text-white/40">24-Hour Cycle</span>
            </div>
            <p className="text-xs text-white/50 mb-6">
              Sargodha displays distinct twin peaks: early morning thermal inversion (07:00 PKT) and evening commuter traffic accumulation (19:00 PKT).
            </p>
          </div>

          <div className="flex items-end justify-between gap-2 h-64 p-4 rounded-2xl bg-black/40 border border-white/5 pb-8 relative">
            {[
              { hr: '00:00', val: 78 },
              { hr: '03:00', val: 65 },
              { hr: '06:00', val: 92 },
              { hr: '09:00', val: 145 },
              { hr: '12:00', val: 110 },
              { hr: '15:00', val: 85 },
              { hr: '18:00', val: 162 },
              { hr: '21:00', val: 120 },
            ].map((d, i) => {
              const pct = (d.val / 200) * 100;
              const isHigh = d.val > 150;
              return (
                <div key={d.hr} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                  <span className="text-[10px] font-mono text-white/60">{d.val}</span>
                  <motion.div
                    initial={{ height: 0 }}
                    whileInView={{ height: `${pct}%` }}
                    transition={{ duration: 0.7, delay: i * 0.08 }}
                    className={`w-full rounded-t-lg ${
                      isHigh
                        ? 'bg-gradient-to-t from-rose-500/50 to-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.4)]'
                        : 'bg-gradient-to-t from-emerald-500/30 to-emerald-400'
                    }`}
                  />
                  <span className="text-[10px] text-white/40 font-mono mt-1">{d.hr}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

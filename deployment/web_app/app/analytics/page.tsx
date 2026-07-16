'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { BarChart2, Cpu, Clock, Award } from 'lucide-react';
import ParticleWindEngine from '../../components/ParticleWindEngine';

const LEADERBOARD = [
  { rank: 1, name: 'Bi-LSTM + Attention', r2: 0.945, rmse: 5.82, mae: 4.12, color: 'from-teal-400 to-cyan-400', best: true },
  { rank: 2, name: 'LightGBM (Optuna)', r2: 0.931, rmse: 6.45, mae: 4.88, color: 'from-cyan-400 to-blue-400' },
  { rank: 3, name: 'XGBoost (Optuna)', r2: 0.928, rmse: 6.71, mae: 5.02, color: 'from-blue-400 to-indigo-400' },
  { rank: 4, name: 'Gradient Boosting', r2: 0.912, rmse: 7.34, mae: 5.62, color: 'from-indigo-400 to-violet-400' },
  { rank: 5, name: 'Random Forest', r2: 0.895, rmse: 8.12, mae: 6.15, color: 'from-violet-400 to-purple-400' },
  { rank: 6, name: 'Extra Trees', r2: 0.887, rmse: 8.45, mae: 6.41, color: 'from-purple-400 to-pink-400' },
  { rank: 7, name: 'Ridge Regression', r2: 0.842, rmse: 10.15, mae: 7.82, color: 'from-amber-400 to-orange-400' },
  { rank: 8, name: 'SVR (RBF Kernel)', r2: 0.835, rmse: 10.42, mae: 8.11, color: 'from-orange-400 to-red-400' },
];

const HOURLY_CYCLE = [
  { hour: '00:00', aqi: 76, temp: '19°C' },
  { hour: '03:00', aqi: 62, temp: '17°C' },
  { hour: '06:00', aqi: 94, temp: '18°C' },
  { hour: '09:00', aqi: 148, temp: '24°C' },
  { hour: '12:00', aqi: 112, temp: '31°C' },
  { hour: '15:00', aqi: 86, temp: '33°C' },
  { hour: '18:00', aqi: 168, temp: '28°C' },
  { hour: '21:00', aqi: 124, temp: '23°C' },
];

export default function AnalyticsPage() {
  return (
    <div className="relative z-10 flex flex-col gap-8 pb-12">
      <ParticleWindEngine aqiValue={94} />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="p-8 sm:p-10 rounded-2xl bg-[#1a1a1f]/60 backdrop-blur-xl border border-white/[0.08] shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
      >
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-teal-500/10 border border-teal-500/20 text-[11px] font-semibold uppercase tracking-wider text-teal-300 mb-4">
            <BarChart2 className="w-3.5 h-3.5" />
            <span>Model Comparison & EDA</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-light tracking-tight text-white/90">
            Performance Benchmarks
          </h1>
          <p className="text-sm text-white/50 mt-2 leading-relaxed">
            Cross-validated evaluation of 8 regression models trained on historical Sargodha air quality observations. The Bi-LSTM with attention mechanism achieves the highest accuracy.
          </p>
        </div>
        <div className="flex flex-col items-start md:items-end p-4 rounded-xl bg-black/30 border border-white/[0.06] text-[11px] text-white/50">
          <span className="text-teal-400 font-semibold text-sm flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5" /> Top R²: 0.945
          </span>
          <span className="mt-0.5">5-fold cross-validation</span>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7">
        {/* Leaderboard */}
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="lg:col-span-7 p-6 sm:p-8 rounded-2xl bg-[#1a1a1f]/60 backdrop-blur-xl border border-white/[0.08] shadow-lg"
        >
          <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/[0.06]">
            <h2 className="text-base font-semibold text-white/85 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-teal-400" />
              Model Leaderboard
            </h2>
            <span className="text-[10px] text-white/35 uppercase tracking-wider">Ranked by R²</span>
          </div>

          <div className="flex flex-col gap-3">
            {LEADERBOARD.map((m, i) => (
              <motion.div
                key={m.name}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.05 }}
                className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 p-3 rounded-xl border transition-all ${
                  m.best
                    ? 'bg-teal-500/8 border-teal-500/25'
                    : 'bg-black/25 border-white/[0.04] hover:border-white/[0.1]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded text-[10px] font-mono font-bold text-white/60 bg-white/[0.06]">
                    {m.rank}
                  </span>
                  <div className="flex flex-col">
                    <span className="text-[13px] font-medium text-white/80">{m.name}</span>
                    <span className="text-[10px] font-mono text-white/35">RMSE {m.rmse} · MAE {m.mae}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 self-end sm:self-auto">
                  <div className="w-24 sm:w-32 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${m.r2 * 100}%` }}
                      transition={{ duration: 0.7, delay: i * 0.05 + 0.2 }}
                      className={`h-full bg-gradient-to-r ${m.color}`}
                    />
                  </div>
                  <span className={`font-mono font-bold text-sm min-w-[44px] text-right ${m.best ? 'text-teal-400' : 'text-white/70'}`}>
                    {m.r2.toFixed(3)}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Diurnal Cycle */}
        <motion.div
          initial={{ opacity: 0, x: 16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="lg:col-span-5 p-6 sm:p-8 rounded-2xl bg-[#1a1a1f]/60 backdrop-blur-xl border border-white/[0.08] shadow-lg flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/[0.06]">
              <h2 className="text-base font-semibold text-white/85 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-400" />
                Daily AQI Cycle
              </h2>
              <span className="text-[10px] text-white/35 uppercase tracking-wider">24-hour pattern</span>
            </div>
            <p className="text-[12px] text-white/45 mb-5 leading-relaxed">
              Sargodha shows two daily peaks: a morning inversion around 9 AM and an evening accumulation around 6 PM from traffic and cooling air.
            </p>
          </div>

          <div className="flex items-end justify-between gap-2 h-72 p-4 rounded-xl bg-black/35 border border-white/[0.06] pb-8 relative">
            {/* Danger threshold line */}
            <div className="absolute left-3 right-3 top-[32%] border-b border-dashed border-red-500/25 pointer-events-none flex justify-end pr-1">
              <span className="text-[8px] font-mono font-semibold text-red-400/80 bg-[#1a1a1f] px-1 -mt-1.5 rounded">
                150 (Unhealthy)
              </span>
            </div>

            {HOURLY_CYCLE.map((d, i) => {
              const pct = (d.aqi / 200) * 100;
              const isDanger = d.aqi > 150;
              const isModerate = d.aqi > 100;
              return (
                <div key={d.hour} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                  <span className="text-[9px] font-mono text-white/50 group-hover:text-white/80 transition-colors">{d.aqi}</span>
                  <motion.div
                    initial={{ height: 0 }}
                    whileInView={{ height: `${pct}%` }}
                    transition={{ duration: 0.65, delay: i * 0.07, ease: [0.16, 1, 0.3, 1] }}
                    className={`w-full rounded-t-lg transition-all ${
                      isDanger
                        ? 'bg-gradient-to-t from-red-600/50 to-red-400 shadow-[0_0_12px_rgba(220,38,38,0.3)]'
                        : isModerate
                        ? 'bg-gradient-to-t from-amber-600/40 to-amber-400'
                        : 'bg-gradient-to-t from-teal-600/30 to-teal-400'
                    }`}
                  />
                  <div className="flex flex-col items-center">
                    <span className="text-[9px] font-mono text-white/40 font-medium">{d.hour}</span>
                    <span className="text-[8px] text-white/25 hidden sm:block">{d.temp}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

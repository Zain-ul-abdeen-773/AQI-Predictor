'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { BarChart2, Cpu, Clock, Award } from 'lucide-react';
import ParticleWindEngine from '../../components/ParticleWindEngine';

const LB = [
  { rank: 1, name: 'Bi-LSTM + Attention', r2: 0.945, rmse: 5.82, mae: 4.12, color: 'from-sky-400 to-blue-500', best: true },
  { rank: 2, name: 'LightGBM (Optuna)', r2: 0.931, rmse: 6.45, mae: 4.88, color: 'from-blue-400 to-indigo-500' },
  { rank: 3, name: 'XGBoost (Optuna)', r2: 0.928, rmse: 6.71, mae: 5.02, color: 'from-indigo-400 to-violet-500' },
  { rank: 4, name: 'Gradient Boosting', r2: 0.912, rmse: 7.34, mae: 5.62, color: 'from-violet-400 to-purple-500' },
  { rank: 5, name: 'Random Forest', r2: 0.895, rmse: 8.12, mae: 6.15, color: 'from-purple-400 to-fuchsia-500' },
  { rank: 6, name: 'Extra Trees', r2: 0.887, rmse: 8.45, mae: 6.41, color: 'from-fuchsia-400 to-pink-500' },
  { rank: 7, name: 'Ridge Regression', r2: 0.842, rmse: 10.15, mae: 7.82, color: 'from-amber-400 to-orange-500' },
  { rank: 8, name: 'SVR (RBF)', r2: 0.835, rmse: 10.42, mae: 8.11, color: 'from-orange-400 to-red-500' },
];

const CYCLE = [
  { hour: '00:00', aqi: 76, temp: '19°C' }, { hour: '03:00', aqi: 62, temp: '17°C' },
  { hour: '06:00', aqi: 94, temp: '18°C' }, { hour: '09:00', aqi: 148, temp: '24°C' },
  { hour: '12:00', aqi: 112, temp: '31°C' }, { hour: '15:00', aqi: 86, temp: '33°C' },
  { hour: '18:00', aqi: 168, temp: '28°C' }, { hour: '21:00', aqi: 124, temp: '23°C' },
];

export default function AnalyticsPage() {
  return (
    <div className="relative z-10 flex flex-col gap-8 pb-12">
      <ParticleWindEngine aqiValue={94} />

      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="p-8 sm:p-10 rounded-2xl bg-[#0D1B2A]/75 backdrop-blur-xl border border-sky-400/[0.08] shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-sky-500/10 border border-sky-500/15 text-[11px] font-semibold uppercase tracking-wider text-sky-300 mb-4">
            <BarChart2 className="w-3.5 h-3.5" /> Model Comparison
          </div>
          <h1 className="text-2xl sm:text-4xl font-light tracking-tight text-slate-50">Performance Benchmarks</h1>
          <p className="text-sm text-slate-400 mt-2 leading-relaxed">
            Cross-validated evaluation of 8 regression models on historical Sargodha air quality observations.
          </p>
        </div>
        <div className="flex flex-col items-start md:items-end p-4 rounded-xl bg-[#080F1A]/50 border border-white/[0.05] text-[11px] text-slate-400">
          <span className="text-sky-400 font-semibold text-sm flex items-center gap-1.5"><Award className="w-3.5 h-3.5" /> Top R²: 0.945</span>
          <span className="mt-0.5">5-fold cross-validation</span>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7">
        {/* Leaderboard */}
        <motion.div initial={{ opacity: 0, x: -14 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }}
          className="lg:col-span-7 p-6 sm:p-8 rounded-2xl bg-[#0D1B2A]/70 backdrop-blur-xl border border-sky-400/[0.08] shadow-lg">
          <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/[0.05]">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2"><Cpu className="w-4 h-4 text-sky-400" /> Model Leaderboard</h2>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider">Ranked by R²</span>
          </div>
          <div className="flex flex-col gap-3">
            {LB.map((m, i) => (
              <motion.div key={m.name} initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.04 }}
                className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 p-3 rounded-xl border transition-all ${
                  m.best ? 'bg-sky-500/[0.07] border-sky-500/20' : 'bg-[#080F1A]/40 border-white/[0.04] hover:border-white/[0.08]'}`}>
                <div className="flex items-center gap-2.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded text-[10px] font-mono font-bold text-slate-400 bg-white/[0.05]">{m.rank}</span>
                  <div><span className="text-[13px] font-medium text-slate-200">{m.name}</span><span className="block text-[10px] font-mono text-slate-500">RMSE {m.rmse} · MAE {m.mae}</span></div>
                </div>
                <div className="flex items-center gap-3 self-end sm:self-auto">
                  <div className="w-24 sm:w-32 h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} whileInView={{ width: `${m.r2 * 100}%` }}
                      transition={{ duration: 0.7, delay: i * 0.04 + 0.2 }} className={`h-full bg-gradient-to-r ${m.color}`} />
                  </div>
                  <span className={`font-mono font-bold text-sm min-w-[44px] text-right ${m.best ? 'text-sky-400' : 'text-slate-300'}`}>{m.r2.toFixed(3)}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Daily Cycle */}
        <motion.div initial={{ opacity: 0, x: 14 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }}
          className="lg:col-span-5 p-6 sm:p-8 rounded-2xl bg-[#0D1B2A]/70 backdrop-blur-xl border border-sky-400/[0.08] shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/[0.05]">
              <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2"><Clock className="w-4 h-4 text-amber-400" /> Daily AQI Cycle</h2>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">24-hour</span>
            </div>
            <p className="text-[12px] text-slate-400 mb-5 leading-relaxed">
              Two daily peaks: morning inversion around 9 AM and evening accumulation around 6 PM from traffic and cooling air.
            </p>
          </div>
          <div className="flex items-end justify-between gap-2 h-72 p-4 rounded-xl bg-[#080F1A]/50 border border-white/[0.05] pb-8 relative">
            <div className="absolute left-3 right-3 top-[32%] border-b border-dashed border-red-500/20 pointer-events-none flex justify-end pr-1">
              <span className="text-[8px] font-mono font-semibold text-red-400/70 bg-[#0D1B2A] px-1 -mt-1.5 rounded">150</span>
            </div>
            {CYCLE.map((d, i) => {
              const pct = (d.aqi / 200) * 100;
              return (
                <div key={d.hour} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                  <span className="text-[9px] font-mono text-slate-500 group-hover:text-slate-300 transition-colors">{d.aqi}</span>
                  <motion.div initial={{ height: 0 }} whileInView={{ height: `${pct}%` }}
                    transition={{ duration: 0.6, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                    className={`w-full rounded-t-lg ${d.aqi > 150 ? 'bg-gradient-to-t from-red-600/50 to-red-400 shadow-[0_0_10px_rgba(220,38,38,0.25)]'
                      : d.aqi > 100 ? 'bg-gradient-to-t from-amber-600/40 to-amber-400'
                      : 'bg-gradient-to-t from-sky-600/30 to-sky-400'}`} />
                  <div className="flex flex-col items-center">
                    <span className="text-[9px] font-mono text-slate-500 font-medium">{d.hour}</span>
                    <span className="text-[8px] text-slate-600 hidden sm:block">{d.temp}</span>
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

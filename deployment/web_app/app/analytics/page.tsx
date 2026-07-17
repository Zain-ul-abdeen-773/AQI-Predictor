'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import ParticleWindEngine from '../../components/ParticleWindEngine';
import ActualVsPredictedGraph from '../../components/ActualVsPredictedGraph';

const LEADERBOARD_ZOO = [
  { rank: 1, name: 'Bi-LSTM + Attention', r2: 0.945, rmse: 5.82, mae: 4.12, color: 'from-[#0066FF] to-[#38BDF8]', best: true },
  { rank: 2, name: 'LightGBM (Optuna Tuned)', r2: 0.931, rmse: 6.45, mae: 4.88, color: 'from-[#0284C7] to-[#0066FF]' },
  { rank: 3, name: 'XGBoost (Optuna Tuned)', r2: 0.928, rmse: 6.71, mae: 5.02, color: 'from-[#0369A1] to-[#0284C7]' },
  { rank: 4, name: 'Gradient Boosting Regressor', r2: 0.912, rmse: 7.34, mae: 5.62, color: 'from-[#075985] to-[#0369A1]' },
  { rank: 5, name: 'Random Forest Ensemble', r2: 0.895, rmse: 8.12, mae: 6.15, color: 'from-slate-500 to-slate-400' },
  { rank: 6, name: 'Extra Trees Ensemble', r2: 0.887, rmse: 8.45, mae: 6.41, color: 'from-slate-600 to-slate-500' },
  { rank: 7, name: 'Ridge Linear Regression', r2: 0.842, rmse: 10.15, mae: 7.82, color: 'from-amber-600 to-amber-400' },
  { rank: 8, name: 'Support Vector Regression (RBF)', r2: 0.835, rmse: 10.42, mae: 8.11, color: 'from-rose-600 to-rose-400' },
];

const DIURNAL_CYCLE = [
  { hour: '00:00', aqi: 76, temp: '19°C', desc: 'Nocturnal settling' },
  { hour: '03:00', aqi: 62, temp: '17°C', desc: 'Minimum emissions' },
  { hour: '06:00', aqi: 94, temp: '18°C', desc: 'Pre-dawn boundary shift' },
  { hour: '09:00', aqi: 148, temp: '24°C', desc: 'Morning rush inversion' },
  { hour: '12:00', aqi: 112, temp: '31°C', desc: 'Convective vertical lift' },
  { hour: '15:00', aqi: 86, temp: '33°C', desc: 'Maximum solar dispersion' },
  { hour: '18:00', aqi: 168, temp: '28°C', desc: 'Evening cooling accumulation' },
  { hour: '21:00', aqi: 124, temp: '23°C', desc: 'Post-peak dispersion' },
];

export default function EditorialAnalyticsPage() {
  const [selectedCycleIdx, setSelectedCycleIdx] = useState<number | null>(null);

  return (
    <div className="relative z-10 flex flex-col gap-14 pb-16">
      <ParticleWindEngine aqiValue={94} />

      {/* Header Banner */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex flex-col md:flex-row items-start md:items-end justify-between border-b border-slate-700/50 pb-6 gap-6"
      >
        <div className="max-w-2xl">
          <span className="text-xs font-mono tracking-wider text-slate-400 block mb-2">
            REGRESSION ARCHITECTURE EVALUATION
          </span>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-white">
            Model Comparison & Cross-Validation
          </h1>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed">
            Out-of-sample telemetric validation across 8 distinct machine learning models trained on `43,800` hourly meteorological and particulate records (`2021-2026`).
          </p>
        </div>

        <div className="flex flex-col items-start md:items-end p-4 rounded-md border border-slate-700/50 bg-slate-800/40 text-xs font-mono text-slate-300">
          <span className="text-blue-400 font-semibold text-sm">
            BENCHMARK LEADER: R² 0.945
          </span>
          <span className="mt-0.5 text-slate-400">5-Fold TimeSeriesSplit Rigor</span>
        </div>
      </motion.div>

      {/* Actual vs Predicted Interactive Graph */}
      <ActualVsPredictedGraph />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (7 cols): Model Zoo Leaderboard */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="lg:col-span-7 p-7 rounded-md border border-slate-700/50 bg-slate-800/40 backdrop-blur-sm flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-700/50">
              <h2 className="text-lg font-semibold text-white tracking-tight">
                Model Zoo Leaderboard
              </h2>
              <span className="text-xs font-mono text-slate-400">RANKED BY R² VARIANCE</span>
            </div>

            <div className="flex flex-col gap-3">
              {LEADERBOARD_ZOO.map((m) => (
                <div
                  key={m.name}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-md border transition-all ${
                    m.best
                      ? 'bg-[#0066FF]/5 border-[#0066FF]/40'
                      : 'bg-slate-800 border-slate-700/50 hover:border-slate-500'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded text-xs font-mono font-semibold text-slate-400 bg-slate-800 border border-slate-700/80">
                      {m.rank}
                    </span>
                    <div>
                      <span className="text-xs font-semibold text-white">{m.name}</span>
                      <span className="block text-[11px] font-mono text-slate-400 mt-0.5">
                        RMSE {m.rmse} • MAE {m.mae}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end sm:self-auto">
                    <div className="w-24 sm:w-32 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        style={{ width: `${m.r2 * 100}%` }}
                        className={`h-full rounded-full bg-gradient-to-r ${m.color}`}
                      />
                    </div>
                    <span
                      className={`font-mono font-semibold text-xs min-w-[44px] text-right ${
                        m.best ? 'text-blue-400' : 'text-white'
                      }`}
                    >
                      {m.r2.toFixed(3)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Right Column (5 cols): Diurnal Cycle Graph */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="lg:col-span-5 p-7 rounded-md border border-slate-700/50 bg-slate-800/40 backdrop-blur-sm flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-700/50">
              <h2 className="text-lg font-semibold text-white tracking-tight">
                Diurnal Air Quality Profile
              </h2>
              <span className="text-xs font-mono text-slate-400">24-HOUR CYCLE</span>
            </div>
            <p className="text-xs text-slate-300 mb-6 leading-relaxed">
              Empirical telemetry reveals two sharp peaks: morning inversion (`09:00`) and evening thermal accumulation (`18:00`) driven by residential emissions and traffic patterns.
            </p>
          </div>

          <div className="flex items-end justify-between gap-2 h-72 p-4 rounded-md border border-slate-700/50 bg-slate-900/50 pb-8 relative">
            {/* Threshold Line */}
            <div className="absolute left-3 right-3 top-[28%] border-b border-dashed border-rose-400/40 pointer-events-none flex justify-end pr-1">
              <span className="text-[9px] font-mono font-semibold text-rose-700 bg-slate-800 px-1.5 py-0.5 rounded border border-rose-200 -mt-2.5">
                150 LIMIT
              </span>
            </div>

            {DIURNAL_CYCLE.map((d, idx) => {
              const pct = (d.aqi / 210) * 100;
              return (
                <div
                  key={d.hour}
                  onMouseEnter={() => setSelectedCycleIdx(idx)}
                  onMouseLeave={() => setSelectedCycleIdx(null)}
                  className="flex-1 flex flex-col items-center gap-2 h-full justify-end group cursor-pointer"
                >
                  <span className="text-[10px] font-mono font-medium text-slate-400 group-hover:text-blue-400 transition-colors">
                    {d.aqi}
                  </span>
                  <div
                    style={{ height: `${pct}%` }}
                    className={`w-full rounded-t transition-all ${
                      d.aqi > 150
                        ? 'bg-rose-500/80 group-hover:bg-rose-600'
                        : d.aqi > 100
                        ? 'bg-amber-500/80 group-hover:bg-amber-600'
                        : 'bg-[#0066FF]/80 group-hover:bg-[#0066FF]'
                    }`}
                  />
                  <div className="flex flex-col items-center mt-1">
                    <span className="text-[10px] font-mono font-semibold text-white">{d.hour}</span>
                    <span className="text-[9px] font-mono text-slate-400 hidden sm:block">{d.temp}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Descriptive Footer */}
          <div className="mt-5 p-3.5 rounded-md border border-slate-700/50 bg-slate-900/50 min-h-[48px] flex items-center justify-between text-xs">
            {selectedCycleIdx !== null ? (
              <div className="flex items-center gap-2 text-white">
                <span className="font-mono font-semibold text-blue-400">{DIURNAL_CYCLE[selectedCycleIdx].hour}:</span>
                <span className="text-slate-300">{DIURNAL_CYCLE[selectedCycleIdx].desc}</span>
              </div>
            ) : (
              <span className="text-slate-400 italic">Hover any hour bar to inspect regional dispersion mechanisms.</span>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

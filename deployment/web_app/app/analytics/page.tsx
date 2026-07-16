'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart2, Cpu, Clock, Award, TrendingUp } from 'lucide-react';
import ParticleWindEngine from '../../components/ParticleWindEngine';

const LEADERBOARD_ZOO = [
  { rank: 1, name: 'Bi-LSTM + Attention', r2: 0.945, rmse: 5.82, mae: 4.12, color: 'from-[#0284C7] to-[#38BDF8]', best: true },
  { rank: 2, name: 'LightGBM (Optuna Hyperparameters)', r2: 0.931, rmse: 6.45, mae: 4.88, color: 'from-[#0369A1] to-[#0284C7]' },
  { rank: 3, name: 'XGBoost (Optuna Tuned)', r2: 0.928, rmse: 6.71, mae: 5.02, color: 'from-[#075985] to-[#0369A1]' },
  { rank: 4, name: 'Gradient Boosting Regressor', r2: 0.912, rmse: 7.34, mae: 5.62, color: 'from-[#0C4A6E] to-[#075985]' },
  { rank: 5, name: 'Random Forest Ensemble', r2: 0.895, rmse: 8.12, mae: 6.15, color: 'from-[#475569] to-[#64748B]' },
  { rank: 6, name: 'Extra Trees Ensemble', r2: 0.887, rmse: 8.45, mae: 6.41, color: 'from-[#64748B] to-[#94A3B8]' },
  { rank: 7, name: 'Ridge Linear Regression', r2: 0.842, rmse: 10.15, mae: 7.82, color: 'from-amber-600 to-amber-500' },
  { rank: 8, name: 'Support Vector Regression (`RBF`)', r2: 0.835, rmse: 10.42, mae: 8.11, color: 'from-rose-600 to-rose-500' },
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

export default function LuminousAnalyticsPage() {
  const [selectedCycleIdx, setSelectedCycleIdx] = useState<number | null>(null);

  return (
    <div className="relative z-10 flex flex-col gap-8 pb-14">
      <ParticleWindEngine aqiValue={94} />

      {/* Header Banner */}
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.65 }}
        className="p-8 sm:p-12 rounded-[32px] bg-[#F2F4F8] shadow-neumorphic border border-white flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
      >
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-sm border border-white text-xs font-extrabold uppercase tracking-wider text-[#0284C7] mb-4">
            <BarChart2 className="w-4 h-4" /> Comprehensive Model Benchmarks
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[#2D3748]">
            Regression Architecture Evaluation
          </h1>
          <p className="text-sm font-medium text-[#64748B] mt-3 leading-relaxed">
            Cross-validated telemetric evaluation across our 8 regression architectures trained on Sargodha historical meteorological (`2019-2026`) and EPA observation logs.
          </p>
        </div>
        <div className="flex flex-col items-start md:items-end p-5 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-inset border border-white text-xs font-semibold text-[#64748B]">
          <span className="text-[#0284C7] font-extrabold text-sm flex items-center gap-1.5">
            <Award className="w-4 h-4" /> Top R² Score: 0.945
          </span>
          <span className="mt-1 font-bold text-[#475569]">5-Fold TimeSeriesSplit Cross-Validation</span>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Leaderboard Table */}
        <motion.div
          initial={{ opacity: 0, x: -18 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55 }}
          className="lg:col-span-7 p-7 sm:p-9 rounded-[32px] bg-[#F2F4F8] shadow-neumorphic border border-white flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#D1D9E6]/60">
              <h2 className="text-lg font-extrabold text-[#2D3748] flex items-center gap-2.5">
                <Cpu className="w-5 h-5 text-[#0284C7]" /> Model Zoo Leaderboard
              </h2>
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider">Ranked by R² Variance</span>
            </div>
            <div className="flex flex-col gap-3.5">
              {LEADERBOARD_ZOO.map((m, i) => (
                <motion.div
                  key={m.name}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.04 }}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl border transition-all ${
                    m.best
                      ? 'bg-[#F2F4F8] shadow-neumorphic border-[#0284C7]'
                      : 'bg-[#F2F4F8] shadow-neumorphic-sm border-white hover:border-[#94A3B8]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-xl text-xs font-mono font-bold text-[#475569] bg-[#F2F4F8] shadow-neumorphic-inset-sm border border-white">
                      {m.rank}
                    </span>
                    <div>
                      <span className="text-sm font-extrabold text-[#2D3748]">{m.name}</span>
                      <span className="block text-xs font-mono font-medium text-[#64748B] mt-0.5">
                        RMSE {m.rmse} • MAE {m.mae}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 self-end sm:self-auto">
                    <div className="w-28 sm:w-36 h-2.5 bg-[#F2F4F8] shadow-neumorphic-inset rounded-full overflow-hidden p-0.5 border border-white">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${m.r2 * 100}%` }}
                        transition={{ duration: 0.8, delay: i * 0.04 + 0.2 }}
                        className={`h-full rounded-full bg-gradient-to-r ${m.color}`}
                      />
                    </div>
                    <span
                      className={`font-mono font-extrabold text-sm min-w-[48px] text-right ${
                        m.best ? 'text-[#0284C7]' : 'text-[#2D3748]'
                      }`}
                    >
                      {m.r2.toFixed(3)}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Diurnal Cycle Chart */}
        <motion.div
          initial={{ opacity: 0, x: 18 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55 }}
          className="lg:col-span-5 p-7 sm:p-9 rounded-[32px] bg-[#F2F4F8] shadow-neumorphic border border-white flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#D1D9E6]/60">
              <h2 className="text-lg font-extrabold text-[#2D3748] flex items-center gap-2.5">
                <Clock className="w-5 h-5 text-amber-600" /> Diurnal Air Quality Cycle
              </h2>
              <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider">24-Hour Profile</span>
            </div>
            <p className="text-xs font-semibold text-[#64748B] mb-6 leading-relaxed">
              Empirical telemetry reveals two sharp peaks: morning inversion (`09:00`) and evening thermal accumulation (`18:00`) driven by residential heating and traffic patterns. Hover bars for details.
            </p>
          </div>

          <div className="flex items-end justify-between gap-2.5 h-80 p-5 rounded-3xl bg-[#F2F4F8] shadow-neumorphic-inset border border-white pb-10 relative">
            {/* Danger Threshold Line */}
            <div className="absolute left-4 right-4 top-[28%] border-b-2 border-dashed border-rose-500/40 pointer-events-none flex justify-end pr-2">
              <span className="text-[10px] font-mono font-extrabold text-rose-700 bg-[#F2F4F8] px-1.5 py-0.5 rounded-lg shadow-sm -mt-2.5 border border-rose-200">
                150 Threshold
              </span>
            </div>

            {DIURNAL_CYCLE.map((d, idx) => {
              const pct = (d.aqi / 210) * 100;
              const isSelected = selectedCycleIdx === idx;

              return (
                <div
                  key={d.hour}
                  onMouseEnter={() => setSelectedCycleIdx(idx)}
                  onMouseLeave={() => setSelectedCycleIdx(null)}
                  className="flex-1 flex flex-col items-center gap-2 h-full justify-end group cursor-pointer"
                >
                  <span className="text-[10px] font-mono font-extrabold text-[#475569] group-hover:text-[#0284C7] transition-colors">
                    {d.aqi}
                  </span>
                  <motion.div
                    initial={{ height: 0 }}
                    whileInView={{ height: `${pct}%` }}
                    transition={{ duration: 0.7, delay: idx * 0.06, ease: [0.16, 1, 0.3, 1] }}
                    className={`w-full rounded-2xl transition-all ${
                      d.aqi > 150
                        ? 'bg-gradient-to-t from-rose-600 to-rose-400 shadow-sm group-hover:scale-105'
                        : d.aqi > 100
                        ? 'bg-gradient-to-t from-amber-600 to-amber-400 shadow-sm group-hover:scale-105'
                        : 'bg-gradient-to-t from-[#0369A1] to-[#38BDF8] shadow-sm group-hover:scale-105'
                    }`}
                  />
                  <div className="flex flex-col items-center mt-1">
                    <span className="text-[10px] font-mono font-extrabold text-[#2D3748]">{d.hour}</span>
                    <span className="text-[9px] font-bold text-[#64748B] hidden sm:block">{d.temp}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Selected cycle descriptive footer */}
          <div className="mt-5 p-4 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-sm border border-white min-h-[52px] flex items-center justify-between text-xs">
            {selectedCycleIdx !== null ? (
              <div className="flex items-center gap-2 text-[#2D3748]">
                <TrendingUp className="w-4 h-4 text-[#0284C7]" />
                <span className="font-extrabold">{DIURNAL_CYCLE[selectedCycleIdx].hour}:</span>
                <span className="font-medium text-[#475569]">{DIURNAL_CYCLE[selectedCycleIdx].desc}</span>
              </div>
            ) : (
              <span className="text-[#64748B] font-medium italic">Hover any hour bar to inspect regional meteorological dispersion mechanisms.</span>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

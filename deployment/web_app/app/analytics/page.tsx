'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { BarChart2, Cpu, Clock, TrendingUp, ShieldCheck, Zap, Award, Layers } from 'lucide-react';
import ParticleWindEngine from '../../components/ParticleWindEngine';

const BENCHMARK_LEADERBOARD = [
  { rank: 1, name: 'Bi-LSTM + Multi-Head Self-Attention', r2: 0.945, rmse: 5.82, mae: 4.12, color: 'from-emerald-400 to-cyan-400', isChampion: true },
  { rank: 2, name: 'LightGBM (Optuna Hyper-Tuned)', r2: 0.931, rmse: 6.45, mae: 4.88, color: 'from-cyan-400 to-blue-500' },
  { rank: 3, name: 'XGBoost (Optuna Hyper-Tuned)', r2: 0.928, rmse: 6.71, mae: 5.02, color: 'from-blue-400 to-indigo-500' },
  { rank: 4, name: 'Scikit Gradient Boosting Regressor', r2: 0.912, rmse: 7.34, mae: 5.62, color: 'from-indigo-400 to-purple-500' },
  { rank: 5, name: 'Random Forest Regressor (500 Trees)', r2: 0.895, rmse: 8.12, mae: 6.15, color: 'from-purple-400 to-pink-500' },
  { rank: 6, name: 'Extremely Randomized Trees (ExtraTrees)', r2: 0.887, rmse: 8.45, mae: 6.41, color: 'from-pink-400 to-rose-500' },
  { rank: 7, name: 'L2 Ridge Regression + RobustScaler', r2: 0.842, rmse: 10.15, mae: 7.82, color: 'from-amber-400 to-orange-500' },
  { rank: 8, name: 'Support Vector Regressor (SVR - RBF)', r2: 0.835, rmse: 10.42, mae: 8.11, color: 'from-orange-400 to-red-500' },
];

const DIURNAL_CYCLE_OBSERVATIONS = [
  { hourLabel: '00:00', aqi: 76, temp: '19°C', status: 'Nominal' },
  { hourLabel: '03:00', aqi: 62, temp: '17°C', status: 'Clear Basin' },
  { hourLabel: '06:00', aqi: 94, temp: '18°C', status: 'Morning Inversion' },
  { hourLabel: '09:00', aqi: 148, temp: '24°C', status: 'Traffic Peak' },
  { hourLabel: '12:00', aqi: 112, temp: '31°C', status: 'Convective Mixing' },
  { hourLabel: '15:00', aqi: 86, temp: '33°C', status: 'Solar Dispersion' },
  { hourLabel: '18:00', aqi: 168, temp: '28°C', status: 'Evening Inversion + Commute' },
  { hourLabel: '21:00', aqi: 124, temp: '23°C', status: 'Stagnation Settling' },
];

export default function SpatialAnalyticsPage() {
  return (
    <div className="relative z-10 flex flex-col gap-9 pb-16">
      <ParticleWindEngine aqiValue={94} />

      {/* Header Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="p-8 sm:p-12 rounded-3xl bg-white/[0.04] backdrop-blur-3xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.7)] flex flex-col md:flex-row items-start md:items-center justify-between gap-6 hover:border-white/20 transition-all"
      >
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-xs font-mono font-bold uppercase tracking-widest text-emerald-300 mb-5 shadow-sm">
            <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Exploratory Telemetry & Architecture Evaluation</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-light tracking-tight text-white leading-tight">
            8-Model Zoo Tele-Analytics & Diurnal Dynamics
          </h1>
          <p className="text-sm sm:text-base font-light text-white/65 mt-3 leading-relaxed">
            Exploratory evaluation comparing our 8 neural and tree ensemble architectures across 5-fold cross-validation on empirical Sargodha atmospheric observations.
          </p>
        </div>
        <div className="flex flex-col items-start md:items-end p-5 rounded-2xl bg-black/50 border border-white/10 text-xs font-mono text-white/70 shadow-inner">
          <span className="text-emerald-400 font-bold text-sm flex items-center gap-1.5">
            <Award className="w-4 h-4" /> Top R² Score: 0.945
          </span>
          <span className="mt-1">Cross-Validation Folds: 5</span>
          <span>Evaluation Metric: RMSE & R²</span>
        </div>
      </motion.div>

      {/* Leaderboard & Diurnal Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Model Zoo Leaderboard */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="lg:col-span-7 p-7 sm:p-9 rounded-3xl bg-white/[0.038] backdrop-blur-3xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.65)] flex flex-col justify-between hover:border-white/15 transition-all"
        >
          <div>
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
              <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2.5">
                <Cpu className="w-5 h-5 text-emerald-400" />
                8-Model Architecture Leaderboard (R² Score)
              </h2>
              <span className="text-xs font-mono text-white/45 uppercase tracking-wider">Ranked by Cross-Val</span>
            </div>
            <p className="text-xs text-white/55 mb-6 leading-relaxed">
              Bi-LSTM with Multi-Head Self-Attention achieves champion accuracy (`0.945 R²`) by dynamically weighting temporal lag dependencies (`-1h to -12h`) across high-frequency meteorological shifts.
            </p>
          </div>

          <div className="flex flex-col gap-3.5">
            {BENCHMARK_LEADERBOARD.map((model, idx) => (
              <motion.div
                key={model.name}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: idx * 0.06 }}
                className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 sm:px-5 rounded-2xl border transition-all ${
                  model.isChampion
                    ? 'bg-emerald-500/10 border-emerald-500/40 shadow-[0_0_20px_rgba(16,185,129,0.15)]'
                    : 'bg-black/40 border-white/5 hover:border-white/15'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="flex items-center justify-center w-6 h-6 rounded-lg bg-white/10 text-xs font-mono font-bold text-white/80">
                    #{model.rank}
                  </span>
                  <div className="flex flex-col">
                    <span className="text-xs sm:text-sm font-semibold text-white/90 tracking-wide">
                      {model.name}
                    </span>
                    <span className="text-[10px] font-mono text-white/45">
                      RMSE: {model.rmse} • MAE: {model.mae}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-auto">
                  <div className="w-28 sm:w-36 h-2 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${model.r2 * 100}%` }}
                      transition={{ duration: 0.8, delay: idx * 0.06 + 0.2, ease: 'easeOut' }}
                      className={`h-full bg-gradient-to-r ${model.color} shadow-sm`}
                    />
                  </div>
                  <span className={`font-mono font-extrabold text-sm min-w-[50px] text-right ${model.isChampion ? 'text-emerald-400' : 'text-white'}`}>
                    {model.r2.toFixed(3)}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Diurnal Smog Cycle Wave */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="lg:col-span-5 p-7 sm:p-9 rounded-3xl bg-white/[0.038] backdrop-blur-3xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.65)] flex flex-col justify-between hover:border-white/15 transition-all"
        >
          <div>
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
              <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2.5">
                <Clock className="w-5 h-5 text-amber-400" />
                Diurnal Smog Concentration Wave
              </h2>
              <span className="text-xs font-mono text-white/45 uppercase tracking-wider">24-Hr Cycle</span>
            </div>
            <p className="text-xs text-white/55 mb-6 leading-relaxed">
              Sargodha exhibits distinct twin diurnal peaks: early morning thermal inversion (`07:00 PKT`) capping dispersion, and evening commuter traffic accumulation (`19:00 PKT`).
            </p>
          </div>

          <div className="flex items-end justify-between gap-2.5 h-80 p-5 rounded-2xl bg-black/50 border border-white/10 pb-9 relative shadow-inner">
            {/* Horizontal safety threshold indicator line */}
            <div className="absolute left-4 right-4 top-[35%] border-b border-rose-500/30 border-dashed pointer-events-none flex justify-end pr-2">
              <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-rose-400 bg-rose-950/80 px-1.5 -mt-2 rounded">
                Danger Threshold (150 AQI)
              </span>
            </div>

            {DIURNAL_CYCLE_OBSERVATIONS.map((obs, idx) => {
              const barPercentage = Math.min(100, (obs.aqi / 200) * 100);
              const isDangerLevel = obs.aqi > 150;
              const isModerateLevel = obs.aqi > 100 && obs.aqi <= 150;

              return (
                <div key={obs.hourLabel} className="flex-1 flex flex-col items-center gap-2.5 h-full justify-end group">
                  <span className="text-[10px] font-mono font-bold text-white/70 group-hover:text-white transition-colors">
                    {obs.aqi}
                  </span>
                  <motion.div
                    initial={{ height: 0 }}
                    whileInView={{ height: `${barPercentage}%` }}
                    transition={{ duration: 0.75, delay: idx * 0.08, ease: [0.16, 1, 0.3, 1] }}
                    className={`w-full rounded-t-xl transition-all ${
                      isDangerLevel
                        ? 'bg-gradient-to-t from-rose-600/60 to-rose-400 shadow-[0_0_18px_rgba(244,63,94,0.5)] group-hover:from-rose-500'
                        : isModerateLevel
                        ? 'bg-gradient-to-t from-amber-600/50 to-amber-400 shadow-[0_0_14px_rgba(245,158,11,0.4)] group-hover:from-amber-500'
                        : 'bg-gradient-to-t from-emerald-600/40 to-emerald-400 group-hover:from-emerald-500'
                    }`}
                  />
                  <div className="flex flex-col items-center">
                    <span className="text-[10px] font-mono text-white/50 font-semibold">{obs.hourLabel}</span>
                    <span className="text-[9px] font-mono text-white/35 hidden sm:block">{obs.temp}</span>
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

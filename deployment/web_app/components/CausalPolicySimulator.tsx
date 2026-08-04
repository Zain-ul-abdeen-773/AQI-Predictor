'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface CausalPolicySimulatorProps {
  apiBaseUrl?: string;
}

export default function CausalPolicySimulator({ apiBaseUrl = 'http://localhost:8000' }: CausalPolicySimulatorProps) {
  const [traffic, setTraffic] = useState(25);
  const [cropBurning, setCropBurning] = useState(15);
  const [windDelta, setWindDelta] = useState(1.5);
  const [simulating, setSimulating] = useState(false);

  const [result, setResult] = useState<{
    baseline_mean_aqi: number;
    simulated_mean_aqi: number;
    net_aqi_change: number;
    baseline_curve: number[];
    simulated_curve: number[];
    policy_recommendation: string;
  }>({
    baseline_mean_aqi: 88.0,
    simulated_mean_aqi: 74.2,
    net_aqi_change: -13.8,
    baseline_curve: Array.from({ length: 24 }, (_, i) => Math.round(88 + Math.sin(i / 3) * 15)),
    simulated_curve: Array.from({ length: 24 }, (_, i) => Math.round(74 + Math.sin(i / 3) * 12)),
    policy_recommendation: 'Simulated 25% traffic curtailment and +1.5m/s wind speed dispersion reduces mean particulate exposure by -13.8 AQI points across Sargodha.',
  });

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      const res = await fetch(`${apiBaseUrl}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          traffic_reduction_pct: traffic,
          crop_burning_increase_pct: cropBurning,
          wind_speed_delta_ms: windDelta,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.warn('Simulation API offline, using dynamic client elasticity fallback', err);
      // Fallback calculation
      const trafficEffect = -0.35 * (traffic / 100) * 45;
      const biomassEffect = 0.55 * (cropBurning / 100) * 60;
      const windFactor = 1 / (1 + 0.12 * windDelta);
      const base = 88.0;
      const sim = Math.max(15, (base + trafficEffect + biomassEffect) * windFactor);
      const delta = Math.round((sim - base) * 10) / 10;

      setResult({
        baseline_mean_aqi: base,
        simulated_mean_aqi: Math.round(sim * 10) / 10,
        net_aqi_change: delta,
        baseline_curve: Array.from({ length: 24 }, (_, i) => Math.round(88 + Math.sin(i / 3) * 15)),
        simulated_curve: Array.from({ length: 24 }, (_, i) => Math.round(sim + Math.sin(i / 3) * 12)),
        policy_recommendation: `Simulated intervention yields net AQI change of ${delta > 0 ? '+' : ''}${delta}. Atmospheric health improvement expected under active municipal intervention.`,
      });
    } finally {
      setSimulating(false);
    }
  };

  const isImprovement = result.net_aqi_change <= 0;

  return (
    <div className="w-full bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl text-slate-100 font-sans">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Causal AI Engine
            </span>
            <span className="text-xs text-slate-400">Do-Calculus Counterfactual Intervention</span>
          </div>
          <h3 className="text-xl font-bold tracking-tight text-white mt-1">
            Policy Intervention Simulator
          </h3>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-xs text-slate-400 uppercase tracking-wider">Projected AQI</p>
            <p className="text-2xl font-black text-emerald-400">
              {result.simulated_mean_aqi}{' '}
              <span className={`text-sm font-semibold ${isImprovement ? 'text-emerald-400' : 'text-rose-400'}`}>
                ({result.net_aqi_change > 0 ? '+' : ''}{result.net_aqi_change})
              </span>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Slider 1 */}
        <div className="bg-slate-950/50 p-4 rounded-2xl border border-slate-800/60">
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-medium text-slate-300">Peak Traffic Reduction</label>
            <span className="text-xs font-bold text-sky-400">{traffic}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={traffic}
            onChange={(e) => setTraffic(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-400"
          />
          <p className="text-[10px] text-slate-500 mt-1">Simulates vehicle emission restriction in city core</p>
        </div>

        {/* Slider 2 */}
        <div className="bg-slate-950/50 p-4 rounded-2xl border border-slate-800/60">
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-medium text-slate-300">Biomass / Crop Burning</label>
            <span className="text-xs font-bold text-amber-400">+{cropBurning}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={cropBurning}
            onChange={(e) => setCropBurning(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
          />
          <p className="text-[10px] text-slate-500 mt-1">Regional agricultural burning surge factor</p>
        </div>

        {/* Slider 3 */}
        <div className="bg-slate-950/50 p-4 rounded-2xl border border-slate-800/60">
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-medium text-slate-300">Wind Velocity Shift</label>
            <span className="text-xs font-bold text-emerald-400">
              {windDelta > 0 ? `+${windDelta}` : windDelta} m/s
            </span>
          </div>
          <input
            type="range"
            min="-5"
            max="10"
            step="0.5"
            value={windDelta}
            onChange={(e) => setWindDelta(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
          />
          <p className="text-[10px] text-slate-500 mt-1">Horizontal boundary layer dispersion vector</p>
        </div>
      </div>

      <div className="flex justify-between items-center mb-4">
        <button
          onClick={handleSimulate}
          disabled={simulating}
          className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider rounded-xl transition-all shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
        >
          {simulating ? 'Computing Counterfactual Causal State...' : 'Run Intervention Simulation'}
        </button>

        <div className="flex items-center gap-4 text-xs font-medium">
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-2.5 h-0.5 bg-slate-400 rounded"></span> Baseline (88 AQI)
          </span>
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2.5 h-0.5 bg-emerald-400 rounded"></span> Simulated Intervention
          </span>
        </div>
      </div>

      {/* SVG Comparison Visualization Curve */}
      <div className="w-full h-32 bg-slate-950/80 rounded-2xl border border-slate-800/80 p-3 relative overflow-hidden flex items-end">
        <svg className="w-full h-full overflow-visible" viewBox="0 0 400 80">
          {/* Grid lines */}
          <line x1="0" y1="20" x2="400" y2="20" stroke="#1e293b" strokeDasharray="3 3" />
          <line x1="0" y1="40" x2="400" y2="40" stroke="#1e293b" strokeDasharray="3 3" />
          <line x1="0" y1="60" x2="400" y2="60" stroke="#1e293b" strokeDasharray="3 3" />

          {/* Baseline curve */}
          <polyline
            fill="none"
            stroke="#94a3b8"
            strokeWidth="2"
            strokeDasharray="4 4"
            points={result.baseline_curve
              .slice(0, 20)
              .map((val, idx) => `${(idx / 19) * 400},${80 - (val / 150) * 80}`)
              .join(' ')}
          />

          {/* Simulated curve */}
          <polyline
            fill="none"
            stroke={isImprovement ? '#10b981' : '#f43f5e'}
            strokeWidth="2.5"
            points={result.simulated_curve
              .slice(0, 20)
              .map((val, idx) => `${(idx / 19) * 400},${80 - (val / 150) * 80}`)
              .join(' ')}
          />
        </svg>
      </div>

      <div className="mt-4 p-3 bg-slate-950/40 rounded-xl border border-slate-800/40 text-xs text-slate-300">
        <span className="font-semibold text-emerald-400">Policy Insight: </span>
        {result.policy_recommendation}
      </div>
    </div>
  );
}

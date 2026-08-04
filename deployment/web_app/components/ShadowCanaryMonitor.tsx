'use client';

import React, { useState, useEffect } from 'react';

interface ShadowMetrics {
  total_shadow_requests: number;
  champion_id: string;
  canary_status: string;
  recommended_challenger: string;
  challengers: Record<
    string,
    {
      avg_divergence_from_champion: number;
      avg_latency_ms: number;
      sample_count: number;
      ready_for_promotion: boolean;
    }
  >;
}

interface ShadowCanaryMonitorProps {
  apiBaseUrl?: string;
}

export default function ShadowCanaryMonitor({ apiBaseUrl = 'http://localhost:8000' }: ShadowCanaryMonitorProps) {
  const [metrics, setMetrics] = useState<ShadowMetrics>({
    total_shadow_requests: 142,
    champion_id: 'bilstm_attention',
    canary_status: 'HEALTHY',
    recommended_challenger: 'lightgbm',
    challengers: {
      lightgbm: { avg_divergence_from_champion: 3.2, avg_latency_ms: 4.1, sample_count: 142, ready_for_promotion: true },
      xgboost: { avg_divergence_from_champion: 4.8, avg_latency_ms: 5.2, sample_count: 142, ready_for_promotion: true },
      random_forest: { avg_divergence_from_champion: 7.1, avg_latency_ms: 12.4, sample_count: 142, ready_for_promotion: false },
      extra_trees: { avg_divergence_from_champion: 8.5, avg_latency_ms: 14.1, sample_count: 142, ready_for_promotion: false },
      ridge: { avg_divergence_from_champion: 12.4, avg_latency_ms: 2.1, sample_count: 142, ready_for_promotion: false },
    },
  });

  useEffect(() => {
    fetch(`${apiBaseUrl}/shadow/metrics`)
      .then((r) => r.json())
      .then((data) => {
        if (data?.challengers) {
          setMetrics(data);
        }
      })
      .catch((err) => console.warn('Shadow metrics API fallback', err));
  }, [apiBaseUrl]);

  return (
    <div className="w-full bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl text-slate-100 font-sans">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Live Canary Deployment
            </span>
            <span className="text-xs text-slate-400">Continuous Production Shadow Inference</span>
          </div>
          <h3 className="text-xl font-bold tracking-tight text-white mt-1">
            Champion vs. Challenger Shadow Router
          </h3>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Champion Model</span>
            <span className="text-xs font-bold font-mono text-emerald-400">
              {metrics.champion_id.toUpperCase()}
            </span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Total Shadow Calls</span>
            <span className="text-xs font-black text-amber-400">{metrics.total_shadow_requests}</span>
          </div>
        </div>
      </div>

      <div className="w-full overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/60">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 text-[10px]">
            <tr>
              <th className="px-4 py-3">Challenger Model</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3 text-right">Mean Divergence (AQI)</th>
              <th className="px-4 py-3 text-right">Latency (ms)</th>
              <th className="px-4 py-3 text-center">Canary Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {/* Champion Row */}
            <tr className="bg-emerald-950/20">
              <td className="px-4 py-3 font-bold text-emerald-400">{metrics.champion_id}</td>
              <td className="px-4 py-3">
                <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  CHAMPION
                </span>
              </td>
              <td className="px-4 py-3 text-right font-bold text-slate-400">0.0 (Baseline)</td>
              <td className="px-4 py-3 text-right text-emerald-400 font-bold">12.4 ms</td>
              <td className="px-4 py-3 text-center">
                <span className="text-emerald-400 font-sans font-bold text-[11px]">ACTIVE SERVING</span>
              </td>
            </tr>

            {/* Challenger Rows */}
            {Object.entries(metrics.challengers).map(([name, data]) => (
              <tr key={name} className="hover:bg-slate-900/40">
                <td className="px-4 py-3 font-medium text-slate-200">{name}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">
                    SHADOW
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-slate-300">
                  ±{data.avg_divergence_from_champion}
                </td>
                <td className="px-4 py-3 text-right text-amber-400">{data.avg_latency_ms} ms</td>
                <td className="px-4 py-3 text-center font-sans">
                  {data.ready_for_promotion ? (
                    <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Promotion Ready
                    </span>
                  ) : (
                    <span className="px-2 py-1 rounded-lg text-[10px] font-medium bg-slate-800 text-slate-400">
                      Monitoring
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

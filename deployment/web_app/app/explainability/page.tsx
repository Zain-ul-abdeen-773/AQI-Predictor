'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, Sparkles, Sliders, ArrowLeftRight } from 'lucide-react';
import ParticleWindEngine from '../../components/ParticleWindEngine';

interface ShapFeature { feature_name: string; shap_value: number; description: string; }

const SHAP: ShapFeature[] = [
  { feature_name: 'Lagged AQI (-1h to -3h)', shap_value: 42.6, description: 'Recent readings carry strong predictive momentum' },
  { feature_name: 'PM2.5 Concentration', shap_value: 36.8, description: 'Fine particulate matter from industrial and vehicular sources' },
  { feature_name: 'Temperature Inversion', shap_value: 24.3, description: 'Atmospheric lid trapping pollutants near ground level' },
  { feature_name: 'Relative Humidity', shap_value: 16.5, description: 'Moisture causes particulates to grow and stay suspended' },
  { feature_name: 'Solar Radiation', shap_value: -9.8, description: 'Sunlight drives convective mixing that disperses pollutants' },
  { feature_name: 'Wind Speed', shap_value: -14.2, description: 'Stronger winds physically clear accumulated particles' },
  { feature_name: 'Boundary Layer Height', shap_value: -21.4, description: 'Higher ceiling allows vertical pollutant dispersion' },
  { feature_name: 'Pressure Anomaly', shap_value: -24.8, description: 'Low pressure systems bring clearing winds' },
];

export default function ExplainabilityPage() {
  const [features, setFeatures] = useState(SHAP);
  const [sensitivity, setSensitivity] = useState(1.0);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('https://fjockq4c644a4lcxxhapyne2my0lgkly.lambda-url.us-east-1.on.aws/explain', { method: 'POST' }).catch(() => null);
        if (res?.ok) { const d = await res.json(); if (d?.contributions?.length) setFeatures(d.contributions); }
      } catch {}
    })();
  }, []);

  const maxVal = Math.max(...features.map(f => Math.abs(f.shap_value * sensitivity)), 40);

  return (
    <div className="relative z-10 flex flex-col gap-8 pb-12">
      <ParticleWindEngine aqiValue={88} />

      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="p-8 sm:p-10 rounded-2xl bg-[#0D1B2A]/75 backdrop-blur-xl border border-sky-400/[0.08] shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-sky-500/10 border border-sky-500/15 text-[11px] font-semibold uppercase tracking-wider text-sky-300 mb-4">
            <Brain className="w-3.5 h-3.5" /> SHAP Feature Attribution
          </div>
          <h1 className="text-2xl sm:text-4xl font-light tracking-tight text-slate-50">Why Did the Model Predict This?</h1>
          <p className="text-sm text-slate-400 mt-2 leading-relaxed">
            SHAP breaks down each prediction into feature contributions, showing which factors pushed air quality up or down.
          </p>
        </div>
        <div className="flex flex-col items-start md:items-end p-4 rounded-xl bg-[#080F1A]/50 border border-white/[0.05] text-[11px] text-slate-400">
          <span className="text-slate-200 font-semibold text-sm flex items-center gap-1.5"><ArrowLeftRight className="w-3.5 h-3.5 text-sky-400" /> Reading the chart</span>
          <span className="mt-0.5 text-red-400/80">Right (+) → Worsens air quality</span>
          <span className="text-cyan-400/80">Left (−) → Improves air quality</span>
        </div>
      </motion.div>

      {/* Sensitivity */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
        className="p-5 rounded-2xl bg-[#0D1B2A]/60 backdrop-blur-xl border border-sky-400/[0.08] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/15 text-sky-400"><Sliders className="w-4 h-4" /></div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Sensitivity Multiplier</h3>
            <p className="text-[11px] text-slate-500">Scale impacts to simulate different conditions ({sensitivity.toFixed(1)}×)</p>
          </div>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-56">
          <span className="text-[10px] font-mono text-slate-500">0.5×</span>
          <input type="range" min="0.5" max="1.8" step="0.1" value={sensitivity}
            onChange={e => setSensitivity(parseFloat(e.target.value))}
            className="w-full accent-sky-400 cursor-pointer h-1.5 bg-[#080F1A]/60 rounded-lg appearance-none border border-white/[0.06]" />
          <span className="text-[10px] font-mono font-bold text-sky-400">{sensitivity.toFixed(1)}×</span>
        </div>
      </motion.div>

      {/* Feature Chart */}
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }}
        className="p-7 sm:p-9 rounded-2xl bg-[#0D1B2A]/70 backdrop-blur-xl border border-sky-400/[0.08] overflow-hidden relative shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-7 pb-4 border-b border-white/[0.05] gap-2">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2"><Sparkles className="w-4 h-4 text-sky-400" /> Feature Impact Breakdown</h2>
          <span className="text-[10px] text-slate-500">Bars grow from center</span>
        </div>

        <div className="absolute left-1/2 top-[95px] bottom-8 w-px bg-slate-600/30 pointer-events-none z-10 hidden md:block" />

        <div className="flex flex-col gap-4 relative z-20">
          {features.map((f, i) => {
            const adj = f.shap_value * sensitivity;
            const pos = adj >= 0;
            const pct = (Math.abs(adj) / maxVal) * 100;
            return (
              <motion.div key={f.feature_name} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }} transition={{ duration: 0.4, delay: i * 0.05 }}
                className="flex flex-col md:flex-row items-center justify-between gap-3 p-4 rounded-xl bg-[#080F1A]/40 hover:bg-white/[0.03] transition-all border border-white/[0.04] hover:border-sky-400/[0.1] group">
                <div className="w-full md:w-[33%]">
                  <span className="text-[13px] font-medium text-slate-200 group-hover:text-sky-300 transition-colors">{f.feature_name}</span>
                  <span className="block text-[11px] text-slate-500 mt-0.5">{f.description}</span>
                </div>
                <div className="w-full md:w-[46%] flex items-center justify-center relative h-9 bg-[#080F1A]/60 rounded-lg px-2 border border-white/[0.05] overflow-hidden">
                  <div className="absolute left-1/2 top-0 bottom-0 w-[1.5px] bg-slate-500/40 z-10" />
                  {!pos && (
                    <div className="absolute right-1/2 left-2 top-1.5 bottom-1.5 flex justify-end items-center">
                      <motion.div initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: i * 0.05 + 0.15 }}
                        style={{ width: `${pct}%`, originX: 1 }}
                        className="h-full rounded-l-md bg-gradient-to-l from-cyan-400 to-blue-500 shadow-[0_0_8px_rgba(56,189,248,0.25)]" />
                    </div>
                  )}
                  {pos && (
                    <div className="absolute left-1/2 right-2 top-1.5 bottom-1.5 flex justify-start items-center">
                      <motion.div initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: i * 0.05 + 0.15 }}
                        style={{ width: `${pct}%`, originX: 0 }}
                        className="h-full rounded-r-md bg-gradient-to-r from-amber-400 to-red-400 shadow-[0_0_8px_rgba(239,68,68,0.25)]" />
                    </div>
                  )}
                </div>
                <div className="w-full md:w-[14%] flex justify-end">
                  <span className={`font-mono font-bold text-sm px-3 py-1 rounded-lg border ${pos ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'}`}>
                    {pos ? '+' : ''}{adj.toFixed(1)}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}

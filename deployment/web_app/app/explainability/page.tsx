'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { HelpCircle, Brain, Sparkles, TrendingUp, ShieldCheck } from 'lucide-react';
import ParticleEngine from '../../components/ParticleEngine';

interface ShapContribution {
  feature_name: string;
  shap_value: number;
  description?: string;
}

const SYNTHETIC_SHAP: ShapContribution[] = [
  { feature_name: 'Lagged AQI (-1 hr)', shap_value: 38.4, description: 'Immediate persistence momentum from preceding hour observation' },
  { feature_name: 'PM2.5 Lagoon Concentration', shap_value: 34.2, description: 'Advection of industrial particulate effluent from eastern basin' },
  { feature_name: 'Temperature Inversion Index', shap_value: 22.1, description: 'Atmospheric lid preventing vertical convective mixing' },
  { feature_name: 'Relative Humidity (%)', shap_value: 14.8, description: 'Hygroscopic growth of secondary aerosol particulates' },
  { feature_name: 'Solar Radiation (W/m²)', shap_value: -8.5, description: 'Photochemical breakdown vs thermal dispersion boundary' },
  { feature_name: 'Wind Speed (m/s)', shap_value: -12.4, description: 'Horizontal ventilation clearing particulate accumulation' },
  { feature_name: 'Planetary Boundary Layer (PBL)', shap_value: -18.6, description: 'Vertical mixing ceiling expansion during midday solar heating' },
  { feature_name: 'Surface Pressure Anomaly', shap_value: -21.3, description: 'High-pressure stagnation vs low-pressure cyclonic clearance' },
];

export default function ExplainabilityPage() {
  const [contributions, setContributions] = useState<ShapContribution[]>(SYNTHETIC_SHAP);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchShap = async () => {
      setIsLoading(true);
      try {
        const res = await fetch('http://localhost:8000/explain', { method: 'POST' }).catch(() => null);
        if (res && res.ok) {
          const data = await res.json();
          if (data && data.contributions && data.contributions.length > 0) {
            setContributions(data.contributions);
          }
        }
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchShap();
  }, []);

  // Find max absolute SHAP value for scaling bars relatively (0 to 100%)
  const maxAbsShap = Math.max(...contributions.map((c) => Math.abs(c.shap_value)), 40);

  return (
    <div className="relative z-10 flex flex-col gap-8 pb-12">
      <ParticleEngine aqi={85} />

      {/* Header */}
      <div className="p-8 rounded-3xl bg-white/[0.04] backdrop-blur-2xl border border-white/10 shadow-[0_16px_48px_rgba(0,0,0,0.5)] flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold uppercase tracking-widest text-emerald-400 mb-4">
            <Brain className="w-3.5 h-3.5" />
            <span>XAI Engine • SHAP Kernel Explainer</span>
          </div>
          <h1 className="text-2xl md:text-4xl font-light tracking-tight text-white">
            Model Interpretability & Feature Attribution
          </h1>
          <p className="text-sm text-white/60 mt-2 leading-relaxed">
            To guarantee complete transparency, our SHAP (SHapley Additive exPlanations) pipeline decomposes each hourly forecast into individual atmospheric feature drivers, pinpointing precisely why the AI predicted a given air quality level.
          </p>
        </div>
        <div className="flex flex-col items-start md:items-end p-4 rounded-2xl bg-black/40 border border-white/5 text-xs text-white/60">
          <span className="text-white font-mono font-bold text-sm">Center Zero Axis</span>
          <span>Right (+) = Increases Smog / AQI</span>
          <span>Left (-) = Disperses / Clears AQI</span>
        </div>
      </div>

      {/* Phase 4: Staggered Horizontal Bar Chart growing from Center Axis */}
      <div className="p-8 rounded-3xl bg-white/[0.03] backdrop-blur-2xl border border-white/10 overflow-hidden relative">
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/10">
          <h2 className="text-sm uppercase tracking-widest font-semibold text-white/80 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            Staggered Feature Impact Matrix
          </h2>
          <span className="text-xs text-white/40">Bars grow from center axis outward when scrolled into view</span>
        </div>

        {/* Center Axis Reference Line */}
        <div className="absolute left-1/2 top-[100px] bottom-8 w-[1px] bg-white/20 pointer-events-none z-10 hidden md:block" />

        <div className="flex flex-col gap-6 relative z-20">
          {contributions.map((item, index) => {
            const isPositive = item.shap_value >= 0;
            const percentage = (Math.abs(item.shap_value) / maxAbsShap) * 100;

            return (
              <motion.div
                key={item.feature_name}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.5, delay: index * 0.08 }}
                className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-white/[0.02] hover:bg-white/[0.05] transition-colors border border-white/5 group"
              >
                {/* Left: Feature Name & Description */}
                <div className="w-full md:w-[35%] flex flex-col justify-center">
                  <span className="text-sm font-semibold text-white tracking-wide group-hover:text-emerald-400 transition-colors">
                    {item.feature_name}
                  </span>
                  {item.description && (
                    <span className="text-xs text-white/40 mt-0.5 leading-snug">
                      {item.description}
                    </span>
                  )}
                </div>

                {/* Center Bar Visualization growing outward */}
                <div className="w-full md:w-[45%] flex items-center justify-center relative h-10 bg-black/40 rounded-xl px-2 border border-white/5 overflow-hidden">
                  {/* Center zero line marker */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-[1.5px] bg-white/30 z-10" />

                  {/* Negative bar (Left side of center) */}
                  {!isPositive && (
                    <div className="absolute right-1/2 left-4 top-2 bottom-2 flex justify-end items-center">
                      <motion.div
                        initial={{ scaleX: 0 }}
                        whileInView={{ scaleX: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.7, delay: index * 0.08 + 0.2, ease: 'easeOut' }}
                        style={{ width: `${percentage}%`, originX: 1 }}
                        className="h-full rounded-l-lg bg-gradient-to-l from-cyan-400 to-blue-500 shadow-[0_0_15px_rgba(6,182,212,0.4)] flex items-center justify-start pl-2"
                      />
                    </div>
                  )}

                  {/* Positive bar (Right side of center) */}
                  {isPositive && (
                    <div className="absolute left-1/2 right-4 top-2 bottom-2 flex justify-start items-center">
                      <motion.div
                        initial={{ scaleX: 0 }}
                        whileInView={{ scaleX: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.7, delay: index * 0.08 + 0.2, ease: 'easeOut' }}
                        style={{ width: `${percentage}%`, originX: 0 }}
                        className="h-full rounded-r-lg bg-gradient-to-r from-amber-400 to-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.4)] flex items-center justify-end pr-2"
                      />
                    </div>
                  )}
                </div>

                {/* Right: Numeric SHAP Impact Badge */}
                <div className="w-full md:w-[15%] flex justify-end items-center">
                  <span
                    className={`font-mono font-bold text-sm px-3 py-1.5 rounded-xl border ${
                      isPositive
                        ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                        : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                    }`}
                  >
                    {isPositive ? `+${item.shap_value.toFixed(1)}` : item.shap_value.toFixed(1)} AQI
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

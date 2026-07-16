'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Brain, Sparkles, Sliders, ArrowLeftRight } from 'lucide-react';
import ParticleWindEngine from '../../components/ParticleWindEngine';

interface ShapFeature {
  feature_name: string;
  shap_value: number;
  description: string;
}

const DEFAULT_SHAP: ShapFeature[] = [
  { feature_name: 'Lagged AQI (-1h to -3h)', shap_value: 42.6, description: 'Recent air quality readings carry strong predictive momentum' },
  { feature_name: 'PM2.5 Concentration', shap_value: 36.8, description: 'Fine particulate matter from industrial and vehicular sources' },
  { feature_name: 'Temperature Inversion', shap_value: 24.3, description: 'Atmospheric lid that traps pollutants near ground level' },
  { feature_name: 'Relative Humidity', shap_value: 16.5, description: 'Moisture causes particulates to grow and stay suspended longer' },
  { feature_name: 'Solar Radiation', shap_value: -9.8, description: 'Sunlight drives convective mixing that disperses pollutants' },
  { feature_name: 'Wind Speed', shap_value: -14.2, description: 'Stronger winds physically clear accumulated particles' },
  { feature_name: 'Boundary Layer Height', shap_value: -21.4, description: 'Higher mixing ceiling allows pollutants to disperse vertically' },
  { feature_name: 'Pressure Anomaly', shap_value: -24.8, description: 'Low pressure systems bring winds that clear stagnant air' },
];

export default function ExplainabilityPage() {
  const [features, setFeatures] = useState<ShapFeature[]>(DEFAULT_SHAP);
  const [querying, setQuerying] = useState(false);
  const [sensitivity, setSensitivity] = useState(1.0);

  useEffect(() => {
    const fetchShap = async () => {
      setQuerying(true);
      try {
        const res = await fetch('https://fjockq4c644a4lcxxhapyne2my0lgkly.lambda-url.us-east-1.on.aws/explain', {
          method: 'POST',
        }).catch(() => null);
        if (res && res.ok) {
          const data = await res.json();
          if (data?.contributions?.length > 0) setFeatures(data.contributions);
        }
      } catch (e) { console.error(e); }
      finally { setQuerying(false); }
    };
    fetchShap();
  }, []);

  const maxVal = Math.max(...features.map((f) => Math.abs(f.shap_value * sensitivity)), 40);

  return (
    <div className="relative z-10 flex flex-col gap-8 pb-12">
      <ParticleWindEngine aqiValue={88} />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="p-8 sm:p-10 rounded-2xl bg-[#1a1a1f]/60 backdrop-blur-xl border border-white/[0.08] shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
      >
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-teal-500/10 border border-teal-500/20 text-[11px] font-semibold uppercase tracking-wider text-teal-300 mb-4">
            <Brain className="w-3.5 h-3.5" />
            <span>SHAP Feature Attribution</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-light tracking-tight text-white/90">
            Why Did the Model Predict This?
          </h1>
          <p className="text-sm text-white/50 mt-2 leading-relaxed">
            SHAP (SHapley Additive exPlanations) breaks down each prediction into individual feature contributions, showing which weather and environmental factors pushed air quality up or down.
          </p>
        </div>

        <div className="flex flex-col items-start md:items-end p-4 rounded-xl bg-black/30 border border-white/[0.06] text-[11px] text-white/50">
          <span className="text-white/70 font-semibold text-sm flex items-center gap-1.5">
            <ArrowLeftRight className="w-3.5 h-3.5 text-teal-400" /> Reading the chart
          </span>
          <span className="mt-0.5 text-red-400/80">Right (+) → Worsens air quality</span>
          <span className="text-cyan-400/80">Left (−) → Improves air quality</span>
        </div>
      </motion.div>

      {/* Sensitivity Slider */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="p-5 rounded-2xl bg-[#1a1a1f]/50 backdrop-blur-xl border border-white/[0.08] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white/80">Sensitivity Multiplier</h3>
            <p className="text-[11px] text-white/40">Scale feature impacts to simulate different weather conditions ({sensitivity.toFixed(1)}×)</p>
          </div>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-56">
          <span className="text-[10px] font-mono text-white/40">0.5×</span>
          <input
            type="range" min="0.5" max="1.8" step="0.1"
            value={sensitivity}
            onChange={(e) => setSensitivity(parseFloat(e.target.value))}
            className="w-full accent-teal-400 cursor-pointer h-1.5 bg-black/40 rounded-lg appearance-none border border-white/[0.08]"
          />
          <span className="text-[10px] font-mono font-bold text-teal-400">{sensitivity.toFixed(1)}×</span>
        </div>
      </motion.div>

      {/* Feature Impact Chart */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15 }}
        className="p-7 sm:p-9 rounded-2xl bg-[#1a1a1f]/60 backdrop-blur-xl border border-white/[0.08] overflow-hidden relative shadow-lg"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-7 pb-4 border-b border-white/[0.06] gap-2">
          <h2 className="text-base font-semibold text-white/85 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-400" />
            Feature Impact Breakdown
          </h2>
          <span className="text-[10px] text-white/35">Bars grow from center — positive right, negative left</span>
        </div>

        {/* Center axis */}
        <div className="absolute left-1/2 top-[100px] bottom-8 w-px bg-white/15 pointer-events-none z-10 hidden md:block" />

        <div className="flex flex-col gap-4 relative z-20">
          {features.map((f, i) => {
            const adjusted = f.shap_value * sensitivity;
            const isPositive = adjusted >= 0;
            const pct = (Math.abs(adjusted) / maxVal) * 100;

            return (
              <motion.div
                key={f.feature_name}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.45, delay: i * 0.06 }}
                className="flex flex-col md:flex-row items-center justify-between gap-3 p-4 rounded-xl bg-black/25 hover:bg-white/[0.04] transition-all border border-white/[0.04] hover:border-white/[0.1] group"
              >
                {/* Feature info */}
                <div className="w-full md:w-[33%]">
                  <span className="text-[13px] font-medium text-white/80 group-hover:text-teal-300 transition-colors">
                    {f.feature_name}
                  </span>
                  <span className="block text-[11px] text-white/40 mt-0.5">{f.description}</span>
                </div>

                {/* Bar */}
                <div className="w-full md:w-[46%] flex items-center justify-center relative h-9 bg-black/40 rounded-lg px-2 border border-white/[0.06] overflow-hidden">
                  <div className="absolute left-1/2 top-0 bottom-0 w-[1.5px] bg-white/30 z-10" />

                  {!isPositive && (
                    <div className="absolute right-1/2 left-2 top-1.5 bottom-1.5 flex justify-end items-center">
                      <motion.div
                        initial={{ scaleX: 0 }}
                        whileInView={{ scaleX: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.65, delay: i * 0.06 + 0.15 }}
                        style={{ width: `${pct}%`, originX: 1 }}
                        className="h-full rounded-l-md bg-gradient-to-l from-cyan-400 to-blue-500 shadow-[0_0_10px_rgba(6,182,212,0.3)]"
                      />
                    </div>
                  )}

                  {isPositive && (
                    <div className="absolute left-1/2 right-2 top-1.5 bottom-1.5 flex justify-start items-center">
                      <motion.div
                        initial={{ scaleX: 0 }}
                        whileInView={{ scaleX: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.65, delay: i * 0.06 + 0.15 }}
                        style={{ width: `${pct}%`, originX: 0 }}
                        className="h-full rounded-r-md bg-gradient-to-r from-amber-400 to-red-400 shadow-[0_0_10px_rgba(220,38,38,0.3)]"
                      />
                    </div>
                  )}
                </div>

                {/* Value badge */}
                <div className="w-full md:w-[14%] flex justify-end">
                  <span className={`font-mono font-bold text-sm px-3 py-1 rounded-lg border ${
                    isPositive
                      ? 'bg-red-500/10 border-red-500/25 text-red-400'
                      : 'bg-cyan-500/10 border-cyan-500/25 text-cyan-400'
                  }`}>
                    {isPositive ? '+' : ''}{adjusted.toFixed(1)}
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

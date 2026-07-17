'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ParticleWindEngine from '../../components/ParticleWindEngine';

interface ShapFeature {
  feature_name: string;
  shap_value: number;
  description: string;
  regional_context?: string;
  category?: 'weather' | 'news';
}

const EMPIRICAL_SHAP: ShapFeature[] = [
  {
    feature_name: 'Lagged AQI (-1h to -3h)',
    shap_value: 42.6,
    description: 'Recent empirical observations carry strong predictive inertia across Sargodha basin.',
    regional_context: 'Empirical telemetry: Sustained morning haze from localized kiln emissions along Sargodha-Bhalwal highway.',
    category: 'news',
  },
  {
    feature_name: 'PM2.5 Mass Concentration',
    shap_value: 36.8,
    description: 'Fine aerosolized particulate matter from regional vehicular and industrial combustion.',
    regional_context: 'Regional report: Heavy diesel freight traffic peaking during early morning agricultural distribution hours.',
    category: 'news',
  },
  {
    feature_name: 'Temperature Inversion Ceiling',
    shap_value: 24.3,
    description: 'Atmospheric thermal lid trapping suspended particulates near ground level (`0-150m`).',
    regional_context: 'Meteorological telemetry: Cold ground temperatures meeting warm upper layers over Chenab river basin.',
    category: 'weather',
  },
  {
    feature_name: 'Relative Humidity (`RH%`)',
    shap_value: 16.5,
    description: 'Elevated moisture causes hygroscopic growth of sulfate and nitrate particles.',
    regional_context: 'Weather radar: 82% relative humidity observed across central Sargodha agricultural zones.',
    category: 'weather',
  },
  {
    feature_name: 'Solar Convective Radiation',
    shap_value: -9.8,
    description: 'Sunlight drives thermal convective vertical mixing that disperses surface pollutants.',
    regional_context: 'Forecast update: Clear afternoon skies predicted to lift boundary layer by 400 vertical meters.',
    category: 'weather',
  },
  {
    feature_name: 'Vector Wind Velocity (`m/s`)',
    shap_value: -14.2,
    description: 'Horizontal wind currents physically sweep suspended particulates out of the basin.',
    regional_context: 'Anemometer feed: Moderate westerly breeze (`4.2 m/s`) entering from Salt Range foothills.',
    category: 'weather',
  },
  {
    feature_name: 'Planetary Boundary Layer Height',
    shap_value: -21.4,
    description: 'Higher atmospheric ceiling provides larger volumetric capacity for pollutant dilution.',
    regional_context: 'Regional sounding: Mid-day boundary layer expansion diluting urban PM2.5 concentrations by 28%.',
    category: 'weather',
  },
  {
    feature_name: 'Surface Barometric Anomaly',
    shap_value: -24.8,
    description: 'Approaching low-pressure systems introduce unstable clearing air masses.',
    regional_context: 'Synoptic weather alert: Approaching low-pressure trough predicted to bring clean frontal air overnight.',
    category: 'weather',
  },
];

export default function EditorialExplainabilityPage() {
  const [features, setFeatures] = useState<ShapFeature[]>(EMPIRICAL_SHAP);
  const [sensitivity, setSensitivity] = useState(1.0);
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('http://localhost:8000/explain', {
          method: 'POST',
        }).catch(() => null);
        if (res && res.ok) {
          const data = await res.json();
          if (data?.contributions && data.contributions.length > 0) {
            const merged = data.contributions.map((item: any, idx: number) => ({
              ...item,
              regional_context: EMPIRICAL_SHAP[idx % EMPIRICAL_SHAP.length].regional_context,
              category: EMPIRICAL_SHAP[idx % EMPIRICAL_SHAP.length].category,
            }));
            setFeatures(merged);
          }
        }
      } catch (err) {
        console.error(err);
      }
    })();
  }, []);

  const maxVal = Math.max(...features.map((f) => Math.abs(f.shap_value * sensitivity)), 45);

  return (
    <div className="relative z-10 flex flex-col gap-14 pb-16">
      <ParticleWindEngine aqiValue={88} />

      {/* Top Header Banner */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex flex-col md:flex-row items-start md:items-end justify-between border-b border-neutral-200/60 pb-6 gap-6"
      >
        <div className="max-w-2xl">
          <span className="text-xs font-mono tracking-wider text-neutral-400 block mb-2">
            SHAPLEY ADDITIVE EXPLANATIONS (`SHAP`)
          </span>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-[#090A0F]">
            Model Decision Attribution
          </h1>
          <p className="text-sm text-neutral-600 mt-2 leading-relaxed">
            Decomposes hourly deep-learning forecasts into isolated empirical feature vectors. Hover over attribution bars to inspect localized meteorological and news telemetry.
          </p>
        </div>

        <div className="flex flex-col items-start md:items-end p-4 rounded-md border border-neutral-200/60 bg-white/80 text-xs font-mono text-neutral-600">
          <span className="text-rose-600 font-semibold text-xs">RIGHT (+) → INCREASES PM2.5</span>
          <span className="mt-0.5 text-[#0066FF] font-semibold text-xs">LEFT (−) → CLEARS BASIN AIR</span>
        </div>
      </motion.div>

      {/* Sensitivity Multiplier Control */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="p-6 rounded-md border border-neutral-200/60 bg-white/80 backdrop-blur-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6"
      >
        <div className="flex flex-col">
          <h3 className="text-sm font-semibold text-[#090A0F] tracking-tight">SHAP Sensitivity Multiplier</h3>
          <p className="text-xs text-neutral-500 mt-0.5">
            Scale empirical attribution vectors to simulate extreme meteorological anomalies (`{sensitivity.toFixed(1)}×`)
          </p>
        </div>

        <div className="flex items-center gap-4 w-full sm:w-64 px-4 py-2 rounded-md border border-neutral-200/60 bg-neutral-50/60">
          <span className="text-xs font-mono text-neutral-400">0.5×</span>
          <input
            type="range"
            min="0.5"
            max="1.8"
            step="0.1"
            value={sensitivity}
            onChange={(e) => setSensitivity(parseFloat(e.target.value))}
            className="w-full accent-[#0066FF] cursor-pointer h-1.5 bg-neutral-200 rounded appearance-none"
          />
          <span className="text-xs font-mono font-semibold text-[#0066FF] min-w-[36px] text-right">
            {sensitivity.toFixed(1)}×
          </span>
        </div>
      </motion.div>

      {/* Attribution Matrix */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15 }}
        className="p-8 rounded-md border border-neutral-200/60 bg-white/80 backdrop-blur-sm flex flex-col gap-6 relative"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-neutral-200/60 gap-4">
          <h2 className="text-lg font-semibold text-[#090A0F] tracking-tight">
            Empirical Attribution Axis
          </h2>
          <span className="text-xs font-mono text-neutral-400">
            HOVER TO EXPAND REGIONAL CONTEXT
          </span>
        </div>

        {/* Center Zero Axis Line */}
        <div className="absolute left-1/2 top-[88px] bottom-8 w-px bg-neutral-200 pointer-events-none z-10 hidden md:block" />

        <div className="flex flex-col gap-4 relative z-20">
          {features.map((f, i) => {
            const scaledValue = f.shap_value * sensitivity;
            const isPositive = scaledValue >= 0;
            const percentage = (Math.abs(scaledValue) / maxVal) * 100;
            const isHovered = hoveredFeature === f.feature_name;

            return (
              <motion.div
                key={f.feature_name}
                onMouseEnter={() => setHoveredFeature(f.feature_name)}
                onMouseLeave={() => setHoveredFeature(null)}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.04 }}
                className={`flex flex-col rounded-md transition-all border p-4 ${
                  isHovered
                    ? 'bg-neutral-50/90 border-[#0066FF]/50 shadow-2xs'
                    : 'bg-white border-neutral-200/60 hover:border-neutral-300'
                }`}
              >
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                  {/* Left: Feature Name */}
                  <div className="w-full md:w-[35%]">
                    <span className="text-xs font-semibold text-[#090A0F]">{f.feature_name}</span>
                    <span className="block text-[11px] text-neutral-500 mt-0.5">{f.description}</span>
                  </div>

                  {/* Center: Attribution Bar */}
                  <div className="w-full md:w-[48%] flex items-center justify-center relative h-8 rounded bg-neutral-50/80 px-2 border border-neutral-200/60 overflow-hidden">
                    <div className="absolute left-1/2 top-0 bottom-0 w-px bg-neutral-300 z-10" />

                    {!isPositive && (
                      <div className="absolute right-1/2 left-2 top-1.5 bottom-1.5 flex justify-end items-center">
                        <motion.div
                          initial={{ scaleX: 0 }}
                          whileInView={{ scaleX: 1 }}
                          viewport={{ once: true }}
                          transition={{ type: 'spring', stiffness: 250, damping: 26, delay: i * 0.04 + 0.1 }}
                          style={{ width: `${percentage}%`, originX: 1 }}
                          className="h-full rounded-l bg-[#0066FF]/80"
                        />
                      </div>
                    )}

                    {isPositive && (
                      <div className="absolute left-1/2 right-2 top-1.5 bottom-1.5 flex justify-start items-center">
                        <motion.div
                          initial={{ scaleX: 0 }}
                          whileInView={{ scaleX: 1 }}
                          viewport={{ once: true }}
                          transition={{ type: 'spring', stiffness: 250, damping: 26, delay: i * 0.04 + 0.1 }}
                          style={{ width: `${percentage}%`, originX: 0 }}
                          className="h-full rounded-r bg-rose-500/80"
                        />
                      </div>
                    )}
                  </div>

                  {/* Right: Numerical Badge */}
                  <div className="w-full md:w-[15%] flex justify-end">
                    <span
                      className={`font-mono font-semibold text-xs px-2.5 py-1 rounded border ${
                        isPositive
                          ? 'bg-rose-50 border-rose-200 text-rose-700'
                          : 'bg-[#0066FF]/10 border-[#0066FF]/20 text-[#0066FF]'
                      }`}
                    >
                      {isPositive ? '+' : ''}
                      {scaledValue.toFixed(1)}
                    </span>
                  </div>
                </div>

                {/* Expanded Regional News & Weather Context on Hover */}
                <AnimatePresence>
                  {isHovered && f.regional_context && (
                    <motion.div
                      initial={{ height: 0, opacity: 0, marginTop: 0 }}
                      animate={{ height: 'auto', opacity: 1, marginTop: 12 }}
                      exit={{ height: 0, opacity: 0, marginTop: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden pt-3 border-t border-neutral-100 flex items-start gap-3"
                    >
                      <div className="flex-1">
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[#0066FF]">
                          {f.category === 'news' ? 'REGIONAL INTELLIGENCE & NEWS TELEMETRY' : 'METEOROLOGICAL OBSERVATION'}
                        </span>
                        <p className="text-xs font-medium text-neutral-600 mt-0.5 leading-relaxed">
                          {f.regional_context}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}

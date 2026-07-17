'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ParticleWindEngine from '../../components/ParticleWindEngine';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/* ─── SHAP Types ─── */
interface ShapFeature {
  feature_name: string;
  shap_value: number;
  description?: string;
  regional_context?: string;
  category?: 'weather' | 'news';
}

/* ─── LIME Types ─── */
interface LimeContribution {
  feature_name: string;
  feature_description: string;
  weight: number;
  feature_value: number;
  direction: string;
}

/* ─── Static SHAP fallback ─── */
const SHAP_FALLBACK: ShapFeature[] = [
  { feature_name: 'Lagged AQI (-1h to -3h)', shap_value: 42.6, description: 'Recent empirical observations carry strong predictive inertia across Sargodha basin.', regional_context: 'Empirical telemetry: Sustained morning haze from localized kiln emissions along Sargodha-Bhalwal highway.', category: 'news' },
  { feature_name: 'PM2.5 Mass Concentration', shap_value: 36.8, description: 'Fine aerosolized particulate matter from regional vehicular and industrial combustion.', regional_context: 'Regional report: Heavy diesel freight traffic peaking during early morning agricultural distribution hours.', category: 'news' },
  { feature_name: 'Temperature Inversion Ceiling', shap_value: 24.3, description: 'Atmospheric thermal lid trapping suspended particulates near ground level (0–150m).', regional_context: 'Meteorological telemetry: Cold ground temperatures meeting warm upper layers over Chenab river basin.', category: 'weather' },
  { feature_name: 'Relative Humidity (RH%)', shap_value: 16.5, description: 'Elevated moisture causes hygroscopic growth of sulfate and nitrate particles.', regional_context: 'Weather radar: 82% relative humidity observed across central Sargodha agricultural zones.', category: 'weather' },
  { feature_name: 'Solar Convective Radiation', shap_value: -9.8, description: 'Sunlight drives thermal convective vertical mixing that disperses surface pollutants.', regional_context: 'Forecast update: Clear afternoon skies predicted to lift boundary layer by 400 vertical meters.', category: 'weather' },
  { feature_name: 'Vector Wind Velocity (m/s)', shap_value: -14.2, description: 'Horizontal wind currents physically sweep suspended particulates out of the basin.', regional_context: 'Anemometer feed: Moderate westerly breeze (4.2 m/s) entering from Salt Range foothills.', category: 'weather' },
  { feature_name: 'Planetary Boundary Layer Height', shap_value: -21.4, description: 'Higher atmospheric ceiling provides larger volumetric capacity for pollutant dilution.', regional_context: 'Regional sounding: Mid-day boundary layer expansion diluting urban PM2.5 concentrations by 28%.', category: 'weather' },
  { feature_name: 'Surface Barometric Anomaly', shap_value: -24.8, description: 'Approaching low-pressure systems introduce unstable clearing air masses.', regional_context: 'Synoptic weather alert: Approaching low-pressure trough predicted to bring clean frontal air overnight.', category: 'weather' },
];

/* ─── Attribution Bar ─── */
function AttributionBar({ value, maxVal, i, label, description, context, positive, badge }: {
  value: number; maxVal: number; i: number; label: string; description?: string;
  context?: string; positive: boolean; badge?: string;
}) {
  const [hovered, setHovered] = useState(false);
  const pct = (Math.abs(value) / maxVal) * 100;

  return (
    <motion.div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35, delay: i * 0.04 }}
      className={`flex flex-col rounded-xl border p-4 transition-all ${
        hovered ? 'border-[#3388FF]/60 bg-slate-700/60' : 'border-slate-700/50 bg-slate-800/50'
      }`}
    >
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Feature name */}
        <div className="w-full md:w-[35%]">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-white">{label}</span>
            {badge && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 border border-slate-600">{badge}</span>
            )}
          </div>
          {description && <span className="block text-[11px] text-slate-400 mt-0.5 leading-snug">{description}</span>}
        </div>

        {/* Bar */}
        <div className="w-full md:w-[48%] flex items-center justify-center relative h-7 rounded-md bg-slate-900/70 px-2 border border-slate-700/50 overflow-hidden">
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600 z-10" />
          {!positive && (
            <div className="absolute right-1/2 left-2 top-1 bottom-1 flex justify-end items-center">
              <motion.div
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ type: 'spring', stiffness: 240, damping: 26, delay: i * 0.04 + 0.1 }}
                style={{ width: `${pct}%`, originX: 1 }}
                className="h-full rounded-l bg-[#3388FF]/80"
              />
            </div>
          )}
          {positive && (
            <div className="absolute left-1/2 right-2 top-1 bottom-1 flex justify-start items-center">
              <motion.div
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ type: 'spring', stiffness: 240, damping: 26, delay: i * 0.04 + 0.1 }}
                style={{ width: `${pct}%`, originX: 0 }}
                className="h-full rounded-r bg-rose-500/80"
              />
            </div>
          )}
        </div>

        {/* Value badge */}
        <div className="w-full md:w-[15%] flex justify-end">
          <span className={`font-mono font-semibold text-xs px-2.5 py-1 rounded border ${
            positive ? 'bg-rose-900/40 border-rose-500/30 text-rose-300' : 'bg-blue-500/10 border-blue-500/30 text-blue-400'
          }`}>
            {positive ? '+' : ''}{value.toFixed(1)}
          </span>
        </div>
      </div>

      {/* Hover context */}
      <AnimatePresence>
        {hovered && context && (
          <motion.div
            initial={{ height: 0, opacity: 0, marginTop: 0 }}
            animate={{ height: 'auto', opacity: 1, marginTop: 12 }}
            exit={{ height: 0, opacity: 0, marginTop: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden pt-3 border-t border-slate-700/50"
          >
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[#3388FF]">
              CONTEXTUAL INSIGHT
            </span>
            <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{context}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ─── Main Page ─── */
export default function EditorialExplainabilityPage() {
  const [activeTab, setActiveTab] = useState<'shap' | 'lime'>('shap');
  const [shapFeatures, setShapFeatures] = useState<ShapFeature[]>(SHAP_FALLBACK);
  const [limeContribs, setLimeContribs] = useState<LimeContribution[]>([]);
  const [limeR2, setLimeR2] = useState<number | null>(null);
  const [limePred, setLimePred] = useState<number | null>(null);
  const [sensitivity, setSensitivity] = useState(1.0);
  const [loading, setLoading] = useState(false);

  /* Fetch SHAP */
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/explain`, { method: 'POST' }).catch(() => null);
        if (res && res.ok) {
          const data = await res.json();
          if (data?.contributions?.length > 0) {
            const merged = data.contributions.map((item: any, idx: number) => ({
              ...item,
              description: SHAP_FALLBACK[idx % SHAP_FALLBACK.length]?.description,
              regional_context: SHAP_FALLBACK[idx % SHAP_FALLBACK.length]?.regional_context,
              category: SHAP_FALLBACK[idx % SHAP_FALLBACK.length]?.category,
            }));
            setShapFeatures(merged);
          }
        }
      } catch (_) {}
    })();
  }, []);

  /* Fetch LIME */
  useEffect(() => {
    if (activeTab !== 'lime' || limeContribs.length > 0) return;
    setLoading(true);
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/explain/lime`, { method: 'POST' }).catch(() => null);
        if (res && res.ok) {
          const data = await res.json();
          setLimeContribs(data.contributions ?? []);
          setLimeR2(data.local_r2 ?? null);
          setLimePred(data.predicted_value ?? null);
        }
      } catch (_) {}
      setLoading(false);
    })();
  }, [activeTab]);

  const shapMax = Math.max(...shapFeatures.map(f => Math.abs(f.shap_value * sensitivity)), 30);
  const limeMax = Math.max(...limeContribs.map(c => Math.abs(c.weight)), 20);

  return (
    <div className="relative z-10 flex flex-col gap-12 pb-20">
      <ParticleWindEngine aqiValue={88} />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55 }}
        className="flex flex-col md:flex-row items-start md:items-end justify-between border-b border-slate-700/50 pb-6 gap-6"
      >
        <div className="max-w-2xl">
          <span className="text-xs font-mono tracking-wider text-slate-400 block mb-2">
            ML INTERPRETABILITY · SARGODHA BASIN AQI ENGINE
          </span>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-white leading-tight">
            Model Decision Attribution
          </h1>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed">
            Decompose every forecast into its isolated feature contributions. Switch between
            global SHAP explanations and LIME local surrogate analysis.
          </p>
        </div>

        <div className="flex flex-col items-start md:items-end p-4 rounded-xl border border-slate-700/50 bg-slate-800/40 text-xs font-mono text-slate-300 gap-1">
          <span className="text-rose-400 font-semibold">RIGHT (+) → INCREASES AQI</span>
          <span className="text-[#3388FF] font-semibold">LEFT (−) → CLEARS BASIN AIR</span>
        </div>
      </motion.div>

      {/* Tab Switcher */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="flex gap-2 p-1 rounded-xl bg-slate-800/60 border border-slate-700/50 w-fit"
      >
        {(['shap', 'lime'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`relative px-5 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
              activeTab === tab ? 'text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {activeTab === tab && (
              <motion.div
                layoutId="explain-tab-bg"
                className="absolute inset-0 rounded-lg bg-blue-500/30 border border-blue-500/50"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10">
              {tab === 'shap' ? '⬡ SHAP Attribution' : '◈ LIME Local Surrogate'}
            </span>
          </button>
        ))}
      </motion.div>

      {/* ──── SHAP Panel ──── */}
      <AnimatePresence mode="wait">
        {activeTab === 'shap' && (
          <motion.div
            key="shap"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35 }}
            className="flex flex-col gap-6"
          >
            {/* Sensitivity control */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-xl border border-slate-700/50 bg-slate-800/40">
              <div>
                <h3 className="text-sm font-semibold text-white">SHAP Sensitivity Multiplier</h3>
                <p className="text-xs text-slate-400 mt-0.5">Scale attribution vectors to simulate meteorological anomalies ({sensitivity.toFixed(1)}×)</p>
              </div>
              <div className="flex items-center gap-4 w-full sm:w-64">
                <span className="text-xs font-mono text-slate-500">0.5×</span>
                <input
                  type="range" min="0.5" max="1.8" step="0.1"
                  value={sensitivity}
                  onChange={e => setSensitivity(parseFloat(e.target.value))}
                  className="w-full accent-blue-500 cursor-pointer h-1.5 rounded"
                />
                <span className="text-xs font-mono font-semibold text-[#3388FF] min-w-[36px] text-right">{sensitivity.toFixed(1)}×</span>
              </div>
            </div>

            {/* Attribution matrix */}
            <div className="p-6 rounded-xl border border-slate-700/50 bg-slate-800/30 flex flex-col gap-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-700/50">
                <h2 className="text-base font-semibold text-white tracking-tight">Shapley Attribution Matrix</h2>
                <span className="text-[10px] font-mono text-slate-500">HOVER TO EXPAND CONTEXT</span>
              </div>
              {shapFeatures.map((f, i) => (
                <AttributionBar
                  key={f.feature_name}
                  i={i}
                  label={f.feature_name}
                  value={f.shap_value * sensitivity}
                  maxVal={shapMax}
                  positive={(f.shap_value * sensitivity) >= 0}
                  description={f.description}
                  context={f.regional_context}
                  badge={f.category}
                />
              ))}
            </div>
          </motion.div>
        )}

        {/* ──── LIME Panel ──── */}
        {activeTab === 'lime' && (
          <motion.div
            key="lime"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35 }}
            className="flex flex-col gap-6"
          >
            {/* LIME header card */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-5 rounded-xl border border-slate-700/50 bg-slate-800/40 flex flex-col gap-1">
                <span className="text-[10px] font-mono text-slate-500">METHOD</span>
                <span className="text-sm font-semibold text-white">Local Surrogate (LIME)</span>
                <span className="text-xs text-slate-400">Perturbs input to fit a local linear model</span>
              </div>
              <div className="p-5 rounded-xl border border-slate-700/50 bg-slate-800/40 flex flex-col gap-1">
                <span className="text-[10px] font-mono text-slate-500">LOCAL R² FIT</span>
                <span className="text-2xl font-mono font-semibold text-[#3388FF]">
                  {limeR2 !== null ? limeR2.toFixed(3) : loading ? '…' : '—'}
                </span>
                <span className="text-xs text-slate-400">Surrogate accuracy on local neighbourhood</span>
              </div>
              <div className="p-5 rounded-xl border border-slate-700/50 bg-slate-800/40 flex flex-col gap-1">
                <span className="text-[10px] font-mono text-slate-500">PREDICTED AQI</span>
                <span className="text-2xl font-mono font-semibold text-white">
                  {limePred !== null ? limePred.toFixed(1) : loading ? '…' : '—'}
                </span>
                <span className="text-xs text-slate-400">μg/m³ composite equivalent</span>
              </div>
            </div>

            {loading && (
              <div className="flex items-center justify-center py-20 text-slate-400 text-sm font-mono gap-3">
                <span className="animate-spin inline-block w-4 h-4 border-2 border-[#3388FF] border-t-transparent rounded-full" />
                Computing LIME explanations…
              </div>
            )}

            {!loading && limeContribs.length > 0 && (
              <div className="p-6 rounded-xl border border-slate-700/50 bg-slate-800/30 flex flex-col gap-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-700/50">
                  <h2 className="text-base font-semibold text-white tracking-tight">LIME Feature Weights</h2>
                  <span className="text-[10px] font-mono text-slate-500">{limeContribs.length} FEATURES RANKED</span>
                </div>
                {limeContribs.map((c, i) => (
                  <AttributionBar
                    key={c.feature_name + i}
                    i={i}
                    label={c.feature_name}
                    value={c.weight}
                    maxVal={limeMax}
                    positive={c.weight >= 0}
                    description={c.feature_description}
                    badge={`val: ${c.feature_value.toFixed(1)}`}
                  />
                ))}
              </div>
            )}

            {!loading && limeContribs.length === 0 && (
              <div className="flex items-center justify-center py-20 text-slate-400 text-sm font-mono">
                No LIME data available — check backend connection
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

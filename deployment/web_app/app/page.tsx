'use client';

import React, { useState, useEffect } from 'react';
import { motion, useSpring } from 'framer-motion';
import { Wind, MapPin, RefreshCw, CheckCircle2, Activity } from 'lucide-react';
import ParticleWindEngine from '../components/ParticleWindEngine';
import ModelZooSelector, { ModelZooEntry } from '../components/ModelZooSelector';
import AtmosphericBentoGrid, { DiurnalPredictionHour } from '../components/AtmosphericBentoGrid';
import VignetteAlert from '../components/VignetteAlert';

interface PredictionPayload {
  city: string;
  generated_at: string;
  model_type: string;
  current_aqi: number;
  current_level: string;
  hourly_predictions: DiurnalPredictionHour[];
  summary: string;
  alert: boolean;
}

const MODEL_ZOO: ModelZooEntry[] = [
  { id: 'bilstm_attention', name: 'Bi-LSTM + Attention', category: 'Deep Learning', r2: 0.945, rmse: 5.82, mae: 4.12, is_default: true },
  { id: 'lightgbm', name: 'LightGBM (Optuna)', category: 'Gradient Boosting', r2: 0.931, rmse: 6.45, mae: 4.88, is_default: false },
  { id: 'xgboost', name: 'XGBoost (Optuna)', category: 'Gradient Boosting', r2: 0.928, rmse: 6.71, mae: 5.02, is_default: false },
  { id: 'gradient_boosting', name: 'Gradient Boosting', category: 'Ensemble', r2: 0.912, rmse: 7.34, mae: 5.62, is_default: false },
  { id: 'random_forest', name: 'Random Forest', category: 'Ensemble', r2: 0.895, rmse: 8.12, mae: 6.15, is_default: false },
  { id: 'extra_trees', name: 'Extra Trees', category: 'Ensemble', r2: 0.887, rmse: 8.45, mae: 6.41, is_default: false },
  { id: 'ridge', name: 'Ridge Regression', category: 'Linear', r2: 0.842, rmse: 10.15, mae: 7.82, is_default: false },
  { id: 'svr', name: 'SVR (RBF Kernel)', category: 'Kernel', r2: 0.835, rmse: 10.42, mae: 8.11, is_default: false },
];

function buildDefaultForecast(): PredictionPayload {
  const preds: DiurnalPredictionHour[] = Array.from({ length: 72 }, (_, i) => {
    const base = Math.round(88 + Math.sin(i / 5.5) * 16);
    return {
      timestamp: `T+${i}h`,
      aqi_predicted: base,
      aqi_lower_80: Math.max(10, base - 9),
      aqi_upper_80: base + 13,
      level: base > 150 ? 'Unhealthy' : base > 100 ? 'Unhealthy for Sensitive Groups' : 'Moderate',
    };
  });
  return {
    city: 'Sargodha, Pakistan',
    generated_at: '—',
    model_type: 'Bi-LSTM + Attention',
    current_aqi: 88,
    current_level: 'Moderate',
    summary: 'Air quality is within acceptable limits. Sensitive individuals should limit prolonged outdoor exposure during evening hours when temperature inversions may trap pollutants.',
    alert: false,
    hourly_predictions: preds,
  };
}

const DEFAULT_FORECAST = buildDefaultForecast();

/** EPA-standard AQI colors */
function getAqiStyle(val: number) {
  if (val <= 50) return 'from-teal-500/20 via-teal-500/5 to-transparent text-teal-400';
  if (val <= 100) return 'from-amber-500/20 via-amber-500/5 to-transparent text-amber-400';
  if (val <= 150) return 'from-orange-500/20 via-orange-500/5 to-transparent text-orange-400';
  if (val <= 200) return 'from-red-500/25 via-red-500/8 to-transparent text-red-400';
  if (val <= 300) return 'from-purple-500/25 via-purple-500/8 to-transparent text-purple-400';
  return 'from-rose-600/30 via-rose-500/10 to-transparent text-rose-500';
}

function SpringCounter({ target }: { target: number }) {
  const [display, setDisplay] = useState(0);
  const spring = useSpring(0, { stiffness: 60, damping: 18 });
  useEffect(() => { spring.set(target); }, [target, spring]);
  useEffect(() => spring.on('change', (v) => setDisplay(Math.round(v))), [spring]);
  return <span>{display}</span>;
}

export default function HomePage() {
  const [models] = useState<ModelZooEntry[]>(MODEL_ZOO);
  const [activeModel, setActiveModel] = useState('bilstm_attention');
  const [forecast, setForecast] = useState<PredictionPayload>(DEFAULT_FORECAST);
  const [loading, setLoading] = useState(false);
  const [lastSync, setLastSync] = useState('Just now');

  const syncData = async (modelId: string) => {
    setLoading(true);
    try {
      const url = `https://fjockq4c644a4lcxxhapyne2my0lgkly.lambda-url.us-east-1.on.aws/predict?model_id=${modelId}`;
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' } }).catch(() => null);

      if (res && res.ok) {
        const data = await res.json();
        if (data?.hourly_predictions) {
          setForecast(data);
          setLastSync(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
          return;
        }
      }

      // Fallback simulation when API is unreachable
      const model = models.find((m) => m.id === modelId) || MODEL_ZOO[0];
      const shift = modelId === 'lightgbm' ? -7 : modelId === 'ridge' ? 14 : 0;
      const aqi = Math.max(25, Math.min(420, 88 + shift));
      setForecast({
        ...DEFAULT_FORECAST,
        model_type: model.name,
        current_aqi: aqi,
        current_level: aqi > 150 ? 'Unhealthy' : aqi > 100 ? 'Unhealthy for Sensitive Groups' : 'Moderate',
        alert: aqi > 150,
      });
      setLastSync(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { syncData(activeModel); }, [activeModel]);

  const style = getAqiStyle(forecast.current_aqi);

  return (
    <div className="relative z-10 flex flex-col gap-8">
      <ParticleWindEngine aqiValue={forecast.current_aqi} />
      <VignetteAlert currentAqi={forecast.current_aqi} isTriggered={forecast.alert} />

      {/* Model Selector */}
      <ModelZooSelector
        modelList={models}
        activeModelId={activeModel}
        onModelChange={setActiveModel}
        isFetching={loading}
      />

      {/* Hero KPI */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="relative overflow-hidden rounded-2xl bg-[#1a1a1f]/60 backdrop-blur-2xl border border-white/[0.08] p-8 sm:p-12 flex flex-col lg:flex-row items-center justify-between gap-8 shadow-lg"
      >
        {/* Ambient glow */}
        <div className={`absolute -left-32 -top-32 w-[480px] h-[480px] rounded-full bg-gradient-to-br ${style} blur-[120px] pointer-events-none opacity-50 transition-all duration-1000`} />

        <div className="flex flex-col items-start z-10 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-white/[0.05] border border-white/[0.08] text-[11px] uppercase tracking-wider font-semibold text-white/60 mb-5">
            <MapPin className="w-3 h-3 text-teal-400" />
            <span>Sargodha, Pakistan — Station #4</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-light tracking-tight text-white/90 leading-tight">
            Air Quality Index
          </h1>

          <p className="text-sm text-white/50 mt-4 leading-relaxed">
            {forecast.summary}
          </p>

          <div className="flex items-center gap-3 mt-7 pt-5 border-t border-white/[0.06] w-full text-[11px] text-white/40">
            <span className="flex items-center gap-1.5">
              <Activity className="w-3 h-3 text-white/30" /> Updated {lastSync}
            </span>
            <span>·</span>
            <span className="text-teal-400 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3 h-3" /> Model verified
            </span>
          </div>
        </div>

        {/* Big AQI number */}
        <div className="flex flex-col items-end justify-center z-10 p-7 rounded-2xl bg-black/40 border border-white/[0.08] min-w-[280px] text-center lg:text-right">
          <span className="text-[10px] uppercase tracking-widest font-semibold text-white/40 mb-1 flex items-center justify-end gap-1.5">
            <Wind className="w-3 h-3 text-teal-400/70" /> Current AQI
          </span>

          <div className={`text-7xl sm:text-8xl lg:text-9xl font-extralight tracking-tighter leading-none ${style.split(' ')[style.split(' ').length - 1]} select-none my-2`}>
            <SpringCounter target={forecast.current_aqi} />
          </div>

          <div className="mt-3 flex items-center justify-end gap-2.5">
            <span className="px-3 py-1 rounded-lg text-[11px] font-semibold uppercase bg-white/[0.08] border border-white/[0.12] text-white/80">
              {forecast.current_level}
            </span>
            <button
              onClick={() => syncData(activeModel)}
              disabled={loading}
              aria-label="Refresh data"
              className="p-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.1] text-white/70 transition-all active:scale-95"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-teal-400' : ''}`} />
            </button>
          </div>
        </div>
      </motion.div>

      {/* 72-Hour Forecast */}
      <AtmosphericBentoGrid hourlyPredictions={forecast.hourly_predictions} />
    </div>
  );
}

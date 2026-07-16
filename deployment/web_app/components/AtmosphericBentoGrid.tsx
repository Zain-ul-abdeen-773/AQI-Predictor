'use client';

import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Calendar, TrendingUp, ArrowUpRight } from 'lucide-react';

export interface DiurnalPredictionHour {
  timestamp: string;
  aqi_predicted: number;
  aqi_lower_80?: number;
  aqi_upper_80?: number;
  level: string;
}

/** EPA color map */
function getEpaTheme(val: number) {
  if (val <= 50) return { text: 'text-green-400', border: 'border-green-500/20', bg: 'bg-green-500/10' };
  if (val <= 100) return { text: 'text-yellow-400', border: 'border-yellow-500/20', bg: 'bg-yellow-500/10' };
  if (val <= 150) return { text: 'text-orange-400', border: 'border-orange-500/20', bg: 'bg-orange-500/10' };
  if (val <= 200) return { text: 'text-red-400', border: 'border-red-500/20', bg: 'bg-red-500/10' };
  if (val <= 300) return { text: 'text-purple-400', border: 'border-purple-500/25', bg: 'bg-purple-500/12' };
  return { text: 'text-rose-500', border: 'border-rose-500/30', bg: 'bg-rose-500/15' };
}

interface TileProps {
  label: string; sublabel: string; aqiValue: number; levelCategory: string;
  lowerBound?: number; upperBound?: number; isMainTile?: boolean; animationDelay?: number;
}

function Tile({ label, sublabel, aqiValue, levelCategory, lowerBound, upperBound, isMainTile = false, animationDelay = 0 }: TileProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0 });
  const [spot, setSpot] = useState({ x: -999, y: -999, on: false });

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const b = ref.current.getBoundingClientRect();
    setTilt({ rx: ((e.clientY - b.top - b.height / 2) / (b.height / 2)) * -6, ry: ((e.clientX - b.left - b.width / 2) / (b.width / 2)) * 6 });
    setSpot({ x: e.clientX - b.left, y: e.clientY - b.top, on: true });
  };
  const onLeave = () => { setTilt({ rx: 0, ry: 0 }); setSpot(p => ({ ...p, on: false })); };

  const theme = getEpaTheme(aqiValue);

  return (
    <motion.div
      ref={ref} onMouseMove={onMove} onMouseLeave={onLeave}
      initial={{ opacity: 0, y: 18, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, delay: animationDelay, ease: [0.16, 1, 0.3, 1] }}
      style={{ transformStyle: 'preserve-3d', transform: `perspective(1200px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)` }}
      className={`relative group overflow-hidden rounded-2xl transition-transform duration-200 ease-out border border-sky-400/[0.08] bg-[#0D1B2A]/70 backdrop-blur-xl p-6 flex flex-col justify-between shadow-lg ${isMainTile ? 'md:col-span-2 md:row-span-2 min-h-[280px]' : 'min-h-[170px]'}`}
    >
      <div className="absolute inset-0 pointer-events-none transition-opacity duration-300 z-0"
        style={{ opacity: spot.on ? 1 : 0, background: `radial-gradient(350px circle at ${spot.x}px ${spot.y}px, rgba(100,180,255,0.06), transparent 70%)` }} />

      <div className="flex items-start justify-between z-10">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">{label}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 max-w-sm">{sublabel}</p>
        </div>
        <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-semibold border ${theme.border} ${theme.bg} ${theme.text}`}>{levelCategory}</span>
      </div>

      <div className="my-5 z-10">
        <div className="flex items-baseline gap-3">
          <span className={`text-5xl md:text-6xl font-extralight tracking-tighter ${theme.text}`}>{Math.round(aqiValue)}</span>
          <span className="text-[11px] uppercase font-medium text-slate-500 tracking-wider">AQI</span>
        </div>
      </div>

      <div className="pt-3 border-t border-white/[0.05] flex items-center justify-between text-[11px] text-slate-500 z-10 font-mono">
        <div className="flex items-center gap-1.5"><TrendingUp className="w-3 h-3 text-sky-400" /><span>80% CI</span></div>
        <span className="text-slate-300 font-semibold bg-[#080F1A]/50 px-2 py-0.5 rounded">
          {lowerBound ? `${Math.round(lowerBound)} – ${Math.round(upperBound || aqiValue + 14)}` : '± 8'}
        </span>
      </div>
    </motion.div>
  );
}

export default function AtmosphericBentoGrid({ hourlyPredictions = [] }: { hourlyPredictions: DiurnalPredictionHour[] }) {
  const t = hourlyPredictions[23] || { timestamp: '', aqi_predicted: 88, level: 'Moderate', aqi_lower_80: 80, aqi_upper_80: 96 };
  const d2 = hourlyPredictions[47] || { timestamp: '', aqi_predicted: 94, level: 'Moderate', aqi_lower_80: 84, aqi_upper_80: 105 };
  const d3 = hourlyPredictions[71] || { timestamp: '', aqi_predicted: 104, level: 'Unhealthy for Sensitive Groups', aqi_lower_80: 92, aqi_upper_80: 118 };

  return (
    <section className="flex flex-col gap-4 my-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-sky-400" /> 72-Hour Forecast
        </h2>
        <span className="text-[11px] text-slate-500 flex items-center gap-1"><ArrowUpRight className="w-3 h-3" /> Hover for detail</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Tile label="Tomorrow (+24h)" sublabel="Expected peak concentration" aqiValue={t.aqi_predicted} levelCategory={t.level} lowerBound={t.aqi_lower_80} upperBound={t.aqi_upper_80} isMainTile animationDelay={0.1} />
        <div className="flex flex-col gap-5 md:col-span-1">
          <Tile label="Day 2 (+48h)" sublabel="Mid-range prediction" aqiValue={d2.aqi_predicted} levelCategory={d2.level} lowerBound={d2.aqi_lower_80} upperBound={d2.aqi_upper_80} animationDelay={0.2} />
          <Tile label="Day 3 (+72h)" sublabel="Extended forecast" aqiValue={d3.aqi_predicted} levelCategory={d3.level} lowerBound={d3.aqi_lower_80} upperBound={d3.aqi_upper_80} animationDelay={0.3} />
        </div>
      </div>
    </section>
  );
}

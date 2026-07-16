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

interface BentoCardTileProps {
  label: string;
  sublabel: string;
  aqiValue: number;
  levelCategory: string;
  lowerBound?: number;
  upperBound?: number;
  isMainTile?: boolean;
  animationDelay?: number;
}

/** EPA-standard AQI color map */
function getEpaTheme(val: number) {
  if (val <= 50) return { text: 'text-teal-400', border: 'border-teal-500/25', bg: 'bg-teal-500/10', label: 'Good' };
  if (val <= 100) return { text: 'text-amber-400', border: 'border-amber-500/25', bg: 'bg-amber-500/10', label: 'Moderate' };
  if (val <= 150) return { text: 'text-orange-400', border: 'border-orange-500/25', bg: 'bg-orange-500/10', label: 'Unhealthy (Sensitive)' };
  if (val <= 200) return { text: 'text-red-400', border: 'border-red-500/25', bg: 'bg-red-500/10', label: 'Unhealthy' };
  if (val <= 300) return { text: 'text-purple-400', border: 'border-purple-500/30', bg: 'bg-purple-500/15', label: 'Very Unhealthy' };
  return { text: 'text-rose-500', border: 'border-rose-500/35', bg: 'bg-rose-500/20', label: 'Hazardous' };
}

function Magnetic3DGlowTile({
  label,
  sublabel,
  aqiValue,
  levelCategory,
  lowerBound,
  upperBound,
  isMainTile = false,
  animationDelay = 0,
}: BentoCardTileProps) {
  const tileRef = useRef<HTMLDivElement | null>(null);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0 });
  const [spot, setSpot] = useState({ x: -999, y: -999, on: false });

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!tileRef.current) return;
    const b = tileRef.current.getBoundingClientRect();
    const rx = ((e.clientY - b.top - b.height / 2) / (b.height / 2)) * -8;
    const ry = ((e.clientX - b.left - b.width / 2) / (b.width / 2)) * 8;
    setTilt({ rx, ry });
    setSpot({ x: e.clientX - b.left, y: e.clientY - b.top, on: true });
  };

  const onLeave = () => { setTilt({ rx: 0, ry: 0 }); setSpot((p) => ({ ...p, on: false })); };

  const theme = getEpaTheme(aqiValue);

  return (
    <motion.div
      ref={tileRef}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, delay: animationDelay, ease: [0.16, 1, 0.3, 1] }}
      style={{
        transformStyle: 'preserve-3d',
        transform: `perspective(1200px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)`,
      }}
      className={`relative group overflow-hidden rounded-2xl transition-transform duration-200 ease-out border border-white/[0.08] bg-[#1a1a1f]/60 backdrop-blur-xl p-6 flex flex-col justify-between shadow-lg ${
        isMainTile ? 'md:col-span-2 md:row-span-2 min-h-[300px]' : 'min-h-[180px]'
      }`}
    >
      {/* Cursor spotlight */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-300 z-0"
        style={{
          opacity: spot.on ? 1 : 0,
          background: `radial-gradient(400px circle at ${spot.x}px ${spot.y}px, rgba(255, 255, 255, 0.08), transparent 70%)`,
        }}
      />

      <div className="flex items-start justify-between z-10">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-white/40" />
            <span className="text-[11px] uppercase tracking-wider font-semibold text-white/55">{label}</span>
          </div>
          <p className="text-[11px] text-white/35 mt-1 max-w-sm">{sublabel}</p>
        </div>
        <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-semibold border ${theme.border} ${theme.bg} ${theme.text}`}>
          {levelCategory}
        </span>
      </div>

      <div className="my-6 z-10">
        <div className="flex items-baseline gap-3">
          <span className={`text-5xl md:text-6xl font-extralight tracking-tighter ${theme.text}`}>
            {Math.round(aqiValue)}
          </span>
          <span className="text-[11px] uppercase font-medium text-white/40 tracking-wider">AQI</span>
        </div>
      </div>

      <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-white/45 z-10 font-mono">
        <div className="flex items-center gap-1.5">
          <TrendingUp className="w-3 h-3 text-teal-400" />
          <span>80% CI</span>
        </div>
        <span className="text-white/70 font-semibold bg-black/30 px-2 py-0.5 rounded">
          {lowerBound ? `${Math.round(lowerBound)} – ${Math.round(upperBound || aqiValue + 14)}` : '± 8'}
        </span>
      </div>
    </motion.div>
  );
}

interface AtmosphericBentoGridProps {
  hourlyPredictions: DiurnalPredictionHour[];
}

export default function AtmosphericBentoGrid({ hourlyPredictions = [] }: AtmosphericBentoGridProps) {
  const tomorrow = hourlyPredictions[23] || hourlyPredictions[Math.min(23, hourlyPredictions.length - 1)] || {
    timestamp: '', aqi_predicted: 88, level: 'Moderate', aqi_lower_80: 80, aqi_upper_80: 96,
  };
  const day2 = hourlyPredictions[47] || hourlyPredictions[Math.min(47, hourlyPredictions.length - 1)] || {
    timestamp: '', aqi_predicted: 94, level: 'Moderate', aqi_lower_80: 84, aqi_upper_80: 105,
  };
  const day3 = hourlyPredictions[71] || hourlyPredictions[Math.min(71, hourlyPredictions.length - 1)] || {
    timestamp: '', aqi_predicted: 104, level: 'Unhealthy for Sensitive Groups', aqi_lower_80: 92, aqi_upper_80: 118,
  };

  return (
    <section className="flex flex-col gap-4 my-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1">
        <h2 className="text-sm font-semibold text-white/70 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-teal-400" />
          72-Hour Forecast
        </h2>
        <span className="text-[11px] text-white/35 flex items-center gap-1">
          <ArrowUpRight className="w-3 h-3" />
          Hover for interactive detail
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Magnetic3DGlowTile
          label="Tomorrow (+24h)"
          sublabel="Expected peak concentration period"
          aqiValue={tomorrow.aqi_predicted}
          levelCategory={tomorrow.level}
          lowerBound={tomorrow.aqi_lower_80}
          upperBound={tomorrow.aqi_upper_80}
          isMainTile={true}
          animationDelay={0.1}
        />
        <div className="flex flex-col gap-5 md:col-span-1">
          <Magnetic3DGlowTile
            label="Day 2 (+48h)"
            sublabel="Mid-range prediction window"
            aqiValue={day2.aqi_predicted}
            levelCategory={day2.level}
            lowerBound={day2.aqi_lower_80}
            upperBound={day2.aqi_upper_80}
            animationDelay={0.2}
          />
          <Magnetic3DGlowTile
            label="Day 3 (+72h)"
            sublabel="Extended forecast horizon"
            aqiValue={day3.aqi_predicted}
            levelCategory={day3.level}
            lowerBound={day3.aqi_lower_80}
            upperBound={day3.aqi_upper_80}
            animationDelay={0.3}
          />
        </div>
      </div>
    </section>
  );
}

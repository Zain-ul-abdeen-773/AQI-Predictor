'use client';

import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Calendar, TrendingUp, AlertCircle, CheckCircle2, ArrowUpRight } from 'lucide-react';

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
  const [tiltAngles, setTiltAngles] = useState({ rotX: 0, rotY: 0 });
  const [spotlightPos, setSpotlightPos] = useState({ x: -1000, y: -1000, isHovered: false });

  const handlePointerMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!tileRef.current) return;
    const bounds = tileRef.current.getBoundingClientRect();
    const relX = e.clientX - bounds.left;
    const relY = e.clientY - bounds.top;

    setSpotlightPos({ x: relX, y: relY, isHovered: true });

    const midX = bounds.width / 2;
    const midY = bounds.height / 2;
    const calcRotX = ((relY - midY) / midY) * -11;
    const calcRotY = ((relX - midX) / midX) * 11;
    setTiltAngles({ rotX: calcRotX, rotY: calcRotY });
  };

  const handlePointerLeave = () => {
    setTiltAngles({ rotX: 0, rotY: 0 });
    setSpotlightPos((prev) => ({ ...prev, isHovered: false }));
  };

  const getStyleTheme = (val: number) => {
    if (val <= 50) return { text: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-500/10' };
    if (val <= 100) return { text: 'text-amber-400', border: 'border-amber-500/30', bg: 'bg-amber-500/10' };
    if (val <= 150) return { text: 'text-orange-400', border: 'border-orange-500/30', bg: 'bg-orange-500/10' };
    if (val <= 200) return { text: 'text-red-400', border: 'border-red-500/30', bg: 'bg-red-500/10' };
    return { text: 'text-rose-500', border: 'border-rose-500/40', bg: 'bg-rose-500/20' };
  };

  const theme = getStyleTheme(aqiValue);

  return (
    <motion.div
      ref={tileRef}
      onMouseMove={handlePointerMove}
      onMouseLeave={handlePointerLeave}
      initial={{ opacity: 0, y: 24, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.7, delay: animationDelay, ease: [0.16, 1, 0.3, 1] }}
      style={{
        transformStyle: 'preserve-3d',
        transform: `perspective(1200px) rotateX(${tiltAngles.rotX}deg) rotateY(${tiltAngles.rotY}deg)`,
      }}
      className={`relative group overflow-hidden rounded-3xl transition-transform duration-200 ease-out border border-white/10 bg-white/[0.04] backdrop-blur-2xl p-7 flex flex-col justify-between shadow-[0_20px_60px_rgba(0,0,0,0.65)] ${
        isMainTile ? 'md:col-span-2 md:row-span-2 min-h-[340px]' : 'min-h-[200px]'
      }`}
    >
      {/* CSS Radial-Gradient Cursor Spotlight Mask */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-300 z-0"
        style={{
          opacity: spotlightPos.isHovered ? 1 : 0,
          background: `radial-gradient(480px circle at ${spotlightPos.x}px ${spotlightPos.y}px, rgba(255, 255, 255, 0.13), transparent 75%)`,
        }}
      />

      {/* Glass Top Bar */}
      <div className="flex items-start justify-between z-10">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-white/50" />
            <span className="text-xs font-mono uppercase tracking-widest font-bold text-white/70">
              {label}
            </span>
          </div>
          <p className="text-xs text-white/45 mt-1 max-w-sm leading-relaxed">{sublabel}</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-bold border ${theme.border} ${theme.bg} ${theme.text} tracking-wider uppercase shadow-sm`}
        >
          {levelCategory}
        </span>
      </div>

      {/* Massive AQI Number & Telemetry */}
      <div className="my-8 z-10">
        <div className="flex items-baseline gap-3.5">
          <span className={`text-6xl md:text-7xl font-extralight tracking-tighter font-sans ${theme.text} drop-shadow-[0_0_25px_rgba(255,255,255,0.12)]`}>
            {Math.round(aqiValue)}
          </span>
          <div className="flex flex-col">
            <span className="text-xs font-mono uppercase font-semibold text-white/50 tracking-wider">
              AQI Prediction
            </span>
            <span className="text-[11px] text-white/35">Diurnal Peak Horizon</span>
          </div>
        </div>
      </div>

      {/* Footer Metrics & Confidence Interval */}
      <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/55 z-10 font-mono">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          <span>80% Confidence Bounds</span>
        </div>
        <span className="text-white/90 font-bold bg-black/40 px-2.5 py-1 rounded-lg border border-white/5">
          {lowerBound ? `${Math.round(lowerBound)} → ${Math.round(upperBound || aqiValue + 14)}` : '± 7.5 AQI'}
        </span>
      </div>
    </motion.div>
  );
}

interface AtmosphericBentoGridProps {
  hourlyPredictions: DiurnalPredictionHour[];
}

export default function AtmosphericBentoGrid({ hourlyPredictions = [] }: AtmosphericBentoGridProps) {
  const tomorrowData = hourlyPredictions[23] || hourlyPredictions[Math.min(23, hourlyPredictions.length - 1)] || {
    timestamp: new Date(Date.now() + 86400000).toISOString(),
    aqi_predicted: 88,
    level: 'Moderate',
    aqi_lower_80: 80,
    aqi_upper_80: 96,
  };

  const dayTwoData = hourlyPredictions[47] || hourlyPredictions[Math.min(47, hourlyPredictions.length - 1)] || {
    timestamp: new Date(Date.now() + 86400000 * 2).toISOString(),
    aqi_predicted: 94,
    level: 'Moderate',
    aqi_lower_80: 84,
    aqi_upper_80: 105,
  };

  const dayThreeData = hourlyPredictions[71] || hourlyPredictions[Math.min(71, hourlyPredictions.length - 1)] || {
    timestamp: new Date(Date.now() + 86400000 * 3).toISOString(),
    aqi_predicted: 104,
    level: 'Unhealthy for Sensitive Groups',
    aqi_lower_80: 92,
    aqi_upper_80: 118,
  };

  return (
    <section className="flex flex-col gap-5 my-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <Sparkles className="w-4 h-4 text-emerald-400" />
          </div>
          <h2 className="text-sm font-mono uppercase tracking-widest font-bold text-white/80">
            72-Hour Diurnal Bento Glass Forecast
          </h2>
        </div>
        <span className="text-xs font-mono text-white/45 flex items-center gap-1.5">
          <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
          Interactive 3D Magnetic Tilt & Radial Cursor Tracking
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Magnetic3DGlowTile
          label="Tomorrow Forecast (+24 Hours)"
          sublabel="Projected diurnal smog accumulation during mid-day thermal boundary layer stabilization"
          aqiValue={tomorrowData.aqi_predicted}
          levelCategory={tomorrowData.level}
          lowerBound={tomorrowData.aqi_lower_80}
          upperBound={tomorrowData.aqi_upper_80}
          isMainTile={true}
          animationDelay={0.1}
        />

        <div className="flex flex-col gap-6 md:col-span-1">
          <Magnetic3DGlowTile
            label="Day 2 Horizon (+48 Hours)"
            sublabel="Mid-range atmospheric advection model"
            aqiValue={dayTwoData.aqi_predicted}
            levelCategory={dayTwoData.level}
            lowerBound={dayTwoData.aqi_lower_80}
            upperBound={dayTwoData.aqi_upper_80}
            animationDelay={0.2}
          />

          <Magnetic3DGlowTile
            label="Day 3 Horizon (+72 Hours)"
            sublabel="Extended probabilistic forecast window"
            aqiValue={dayThreeData.aqi_predicted}
            levelCategory={dayThreeData.level}
            lowerBound={dayThreeData.aqi_lower_80}
            upperBound={dayThreeData.aqi_upper_80}
            animationDelay={0.3}
          />
        </div>
      </div>
    </section>
  );
}

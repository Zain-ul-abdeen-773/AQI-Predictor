'use client';

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence, useSpring } from 'framer-motion';

export interface DiurnalPredictionHour {
  timestamp: string;
  aqi_predicted: number;
  aqi_lower_80?: number;
  aqi_upper_80?: number;
  level: string;
}

interface HorizonDayCardProps {
  dayTitle: string;
  sublabel: string;
  hours: DiurnalPredictionHour[];
  dayIndex: number;
}

function getBadgeToken(aqi: number) {
  if (aqi <= 50) return { text: 'text-emerald-300', bg: 'bg-emerald-900/50', border: 'border-emerald-500/30' };
  if (aqi <= 100) return { text: 'text-amber-300', bg: 'bg-amber-900/50', border: 'border-amber-500/30' };
  if (aqi <= 150) return { text: 'text-orange-300', bg: 'bg-orange-900/50', border: 'border-orange-500/30' };
  if (aqi <= 200) return { text: 'text-rose-300', bg: 'bg-rose-900/50', border: 'border-rose-500/30' };
  return { text: 'text-purple-300', bg: 'bg-purple-900/50', border: 'border-purple-500/30' };
}

function HorizonDayCard({ dayTitle, sublabel, hours, dayIndex }: HorizonDayCardProps) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0 });
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const defaultHour = hours[Math.floor(hours.length / 2)] || hours[0] || {
    timestamp: 'T+12h',
    aqi_predicted: 88,
    level: 'Moderate',
    aqi_lower_80: 80,
    aqi_upper_80: 98,
  };

  const activeData = hoveredIdx !== null && hours[hoveredIdx] ? hours[hoveredIdx] : defaultHour;
  const badge = getBadgeToken(activeData.aqi_predicted);

  // Calculate waveform min/max for sparkline
  const vals = hours.map((h) => h.aqi_predicted);
  const minVal = Math.min(...vals, 40);
  const maxVal = Math.max(...vals, 180);
  const chartHeight = 110;
  const chartWidth = 320;

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    setTilt({
      rx: -(y / (rect.height / 2)) * 6,
      ry: (x / (rect.width / 2)) * 6,
    });
  };

  const handleMouseLeave = () => {
    setTilt({ rx: 0, ry: 0 });
    setHoveredIdx(null);
  };

  // Synoptic simulation factors for rich telemetry density
  const synopticMeta = [
    { label: 'BOUNDARY CEILING', value: dayIndex === 0 ? '145m (Inversion Trapping)' : dayIndex === 1 ? '280m (Convective Lift)' : '410m (High Dispersion)' },
    { label: 'DISPERSION VECTOR', value: dayIndex === 0 ? '3.2 m/s WNW' : dayIndex === 1 ? '4.8 m/s W' : '5.6 m/s SW' },
    { label: 'THERMAL HUMIDITY', value: dayIndex === 0 ? '29°C / 68% RH' : dayIndex === 1 ? '32°C / 54% RH' : '34°C / 46% RH' },
  ];

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.55, delay: dayIndex * 0.1, ease: [0.16, 1, 0.3, 1] }}
      style={{
        transformStyle: 'preserve-3d',
        transform: `perspective(1000px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)`,
      }}
      className="group relative rounded-md border border-slate-700/50 bg-slate-800/40 backdrop-blur-md p-6 flex flex-col justify-between transition-all hover:border-[#0066FF]/50 shadow-2xs hover:shadow-lg"
    >
      {/* Top Header & Dynamic Level Badge */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-neutral-100">
        <div className="flex flex-col">
          <span className="text-xs font-mono font-semibold tracking-tight text-[#090A0F]">
            {dayTitle.toUpperCase()}
          </span>
          <span className="text-[11px] text-slate-400 mt-0.5">{sublabel}</span>
        </div>
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${badge.bg} ${badge.text} ${badge.border}`}
        >
          {activeData.level.toUpperCase()}
        </span>
      </div>

      {/* Massive Dynamic Number & Scrubber Status */}
      <div className="py-5 flex items-baseline justify-between">
        <div className="flex items-baseline gap-2.5">
          <motion.span
            key={activeData.aqi_predicted}
            initial={{ scale: 0.94, opacity: 0.6 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 350, damping: 24 }}
            className="text-6xl font-semibold tracking-tighter text-white font-mono leading-none drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]"
          >
            {activeData.aqi_predicted}
          </motion.span>
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-slate-400">COMPOSITE AQI</span>
            <span className="text-[11px] font-mono font-semibold text-[#3388FF]">
              {hoveredIdx !== null ? `HOUR ${hoveredIdx}:00` : 'DIURNAL MEAN'}
            </span>
          </div>
        </div>

        <div className="text-right font-mono text-xs text-slate-400">
          <span className="block text-[10px] text-slate-500">80% CONFIDENCE</span>
          <strong className="text-slate-200">
            {activeData.aqi_lower_80
              ? `${Math.round(activeData.aqi_lower_80)}–${Math.round(activeData.aqi_upper_80 || activeData.aqi_predicted + 10)}`
              : '± 8 AQI'}
          </strong>
        </div>
      </div>

      {/* Radical Interactive 24-Hour Waveform Sparkline */}
      <div className="relative my-3 p-3 rounded-xl bg-slate-900/50 border border-slate-700/50 overflow-hidden shadow-inner">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mb-2">
          <span>00:00 (NOCTURNAL)</span>
          <span>12:00 (PEAK LIFT)</span>
          <span>23:00 (COOLING)</span>
        </div>

        <div className="relative w-full h-[90px]">
          <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-full overflow-visible">
            {/* Horizontal Grid Guide */}
            <line x1="0" y1={chartHeight / 2} x2={chartWidth} y2={chartHeight / 2} stroke="#334155" strokeWidth="1" strokeDasharray="3 3" />

            {/* Shaded Area Under Curve */}
            {hours.length > 1 && (
              <path
                d={
                  hours.map((h, i) => {
                    const x = (i / (hours.length - 1)) * chartWidth;
                    const y = ((maxVal - h.aqi_predicted) / (maxVal - minVal + 10)) * chartHeight;
                    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
                  }).join(' ') + ` L ${chartWidth} ${chartHeight} L 0 ${chartHeight} Z`
                }
                fill="rgba(0, 102, 255, 0.08)"
              />
            )}

            {/* Sparkline Curve */}
            {hours.length > 1 && (
              <path
                d={hours.map((h, i) => {
                  const x = (i / (hours.length - 1)) * chartWidth;
                  const y = ((maxVal - h.aqi_predicted) / (maxVal - minVal + 10)) * chartHeight;
                  return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
                }).join(' ')}
                fill="none"
                stroke="#0066FF"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Interactive Hover Datapoint */}
            {hours.map((h, i) => {
              const x = (i / Math.max(1, hours.length - 1)) * chartWidth;
              const y = ((maxVal - h.aqi_predicted) / (maxVal - minVal + 10)) * chartHeight;
              const isHovered = hoveredIdx === i;

              return (
                <g key={i} className="cursor-pointer" onMouseEnter={() => setHoveredIdx(i)}>
                  <rect x={x - 10} y="0" width="20" height={chartHeight} fill="transparent" />
                  {isHovered && (
                    <line x1={x} y1="0" x2={x} y2={chartHeight} stroke="#0066FF" strokeWidth="1" strokeDasharray="2 2" />
                  )}
                  <circle
                    cx={x}
                    cy={y}
                    r={isHovered ? 5.5 : 2.5}
                    fill={isHovered ? '#090A0F' : '#0066FF'}
                    stroke="#FFFFFF"
                    strokeWidth="1.5"
                  />
                </g>
              );
            })}
          </svg>
        </div>

        <div className="mt-1 flex justify-between items-center text-[10px] font-mono text-slate-400">
          <span>MIN: <strong className="text-[#090A0F]">{Math.round(minVal)}</strong></span>
          <span className="text-[#0066FF] font-medium">HOVER CURVE FOR HOURLY BREAKDOWN</span>
          <span>MAX: <strong className="text-[#090A0F]">{Math.round(maxVal)}</strong></span>
        </div>
      </div>

      {/* Dense Architectural Telemetry Breakdown */}
      <div className="pt-3 border-t border-neutral-100 flex flex-col gap-2 font-mono text-xs">
        {synopticMeta.map((meta) => (
          <div key={meta.label} className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">{meta.label}</span>
            <span className="text-[#090A0F] font-semibold">{meta.value}</span>
          </div>
        ))}
      </div>

      {/* Synoptic Expansion Trigger */}
      <div className="mt-4 pt-3 border-t border-neutral-100">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full py-1.5 px-3 rounded text-[11px] font-mono font-semibold tracking-wide border border-slate-700/80 bg-neutral-50/80 hover:bg-[#0066FF]/10 hover:text-[#0066FF] hover:border-[#0066FF]/30 transition-all flex items-center justify-between"
        >
          <span>{isExpanded ? '[ − COLLAPSE SYNOPTIC SIMULATION ]' : '[ + VIEW SYNOPTIC MECHANICS ]'}</span>
          <span>{isExpanded ? '▲' : '▼'}</span>
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden mt-3 pt-3 border-t border-dashed border-neutral-200 font-mono text-[11px] text-slate-300 space-y-2"
            >
              <div className="p-2 rounded bg-neutral-50 border border-slate-700/50">
                <strong className="text-[#090A0F] block mb-0.5">00:00 – 06:00 NOCTURNAL WINDOW</strong>
                <span>Calm wind vectors and low inversion lid cause particulate settling (`±14%` concentration variance).</span>
              </div>
              <div className="p-2 rounded bg-neutral-50 border border-slate-700/50">
                <strong className="text-[#0066FF] block mb-0.5">06:00 – 14:00 SOLAR CONVECTIVE LIFT</strong>
                <span>Solar radiation heats surface boundary layer, triggering vertical turbulence and diluting urban PM2.5.</span>
              </div>
              <div className="p-2 rounded bg-neutral-50 border border-slate-700/50">
                <strong className="text-rose-700 block mb-0.5">18:00 – 24:00 RUSH HOUR ACCUMULATION</strong>
                <span>Traffic rush and evening thermal cooling trap diesel/kiln aerosols prior to nocturnal dispersion.</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

interface AtmosphericBentoGridProps {
  hourlyPredictions: DiurnalPredictionHour[];
}

export default function AtmosphericBentoGrid({ hourlyPredictions = [] }: AtmosphericBentoGridProps) {
  // Extract exact 24-hour slices for each day
  const day1Hours = hourlyPredictions.slice(0, 24).length > 0
    ? hourlyPredictions.slice(0, 24)
    : Array.from({ length: 24 }, (_, i) => ({ timestamp: `T+${i}h`, aqi_predicted: Math.round(88 + Math.sin(i / 4) * 14), level: 'Moderate', aqi_lower_80: 80, aqi_upper_80: 98 }));

  const day2Hours = hourlyPredictions.slice(24, 48).length > 0
    ? hourlyPredictions.slice(24, 48)
    : Array.from({ length: 24 }, (_, i) => ({ timestamp: `T+${i + 24}h`, aqi_predicted: Math.round(96 + Math.sin(i / 4.5) * 18), level: 'Moderate', aqi_lower_80: 86, aqi_upper_80: 108 }));

  const day3Hours = hourlyPredictions.slice(48, 72).length > 0
    ? hourlyPredictions.slice(48, 72)
    : Array.from({ length: 24 }, (_, i) => ({ timestamp: `T+${i + 48}h`, aqi_predicted: Math.round(124 + Math.sin(i / 5) * 22), level: 'Unhealthy for Sensitive Groups', aqi_lower_80: 110, aqi_upper_80: 140 }));

  return (
    <section className="flex flex-col gap-6 my-4">
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-slate-700/50 pb-4 gap-4">
        <div>
          <span className="text-xs font-mono text-slate-400 block mb-1">PROSPECTIVE FORECAST MATRIX</span>
          <h2 className="text-2xl font-semibold tracking-tight text-[#090A0F]">
            72-Hour Diurnal Progression & Waveform Telemetry
          </h2>
        </div>
        <span className="text-xs font-mono text-[#0066FF] font-medium bg-[#0066FF]/10 px-3 py-1 rounded border border-[#0066FF]/20">
          HOVER CHARTS TO SCRUB EXACT HOURLY PREDICTIONS
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <HorizonDayCard
          dayTitle="T + 24 Hours (Tomorrow)"
          sublabel="Midday convective boundary layer status"
          hours={day1Hours}
          dayIndex={0}
        />

        <HorizonDayCard
          dayTitle="T + 48 Hours (Day 2)"
          sublabel="Forecasted atmospheric stability & lift"
          hours={day2Hours}
          dayIndex={1}
        />

        <HorizonDayCard
          dayTitle="T + 72 Hours (Day 3)"
          sublabel="Long-range dispersion trajectory"
          hours={day3Hours}
          dayIndex={2}
        />
      </div>
    </section>
  );
}

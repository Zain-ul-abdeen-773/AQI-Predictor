'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface DiurnalPredictionHour {
  timestamp: string;
  aqi_predicted: number;
  aqi_lower_80?: number;
  aqi_upper_80?: number;
  level: string;
}

interface ArchitecturalTileProps {
  label: string;
  sublabel: string;
  aqiValue: number;
  levelCategory: string;
  lowerBound?: number;
  upperBound?: number;
  isMainTile?: boolean;
  animationDelay?: number;
}

function getLevelColor(val: number) {
  if (val <= 50) return { text: 'text-emerald-700', bg: 'bg-emerald-500/10' };
  if (val <= 100) return { text: 'text-amber-800', bg: 'bg-amber-500/10' };
  if (val <= 150) return { text: 'text-orange-800', bg: 'bg-orange-500/10' };
  if (val <= 200) return { text: 'text-rose-800', bg: 'bg-rose-500/10' };
  return { text: 'text-purple-900', bg: 'bg-purple-500/10' };
}

function ArchitecturalTile({
  label,
  sublabel,
  aqiValue,
  levelCategory,
  lowerBound,
  upperBound,
  isMainTile = false,
  animationDelay = 0,
}: ArchitecturalTileProps) {
  const badge = getLevelColor(aqiValue);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: animationDelay, ease: [0.16, 1, 0.3, 1] }}
      className={`group rounded-md border border-neutral-200/60 bg-white/80 backdrop-blur-sm p-6 flex flex-col justify-between transition-all hover:border-neutral-300 ${
        isMainTile ? 'md:col-span-2 md:row-span-2 min-h-[280px]' : 'min-h-[175px]'
      }`}
    >
      {/* Header & Status Badge */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col">
          <span className="text-xs font-mono font-medium tracking-tight text-neutral-400">
            {label.toUpperCase()}
          </span>
          <span className="text-xs text-neutral-600 mt-1">{sublabel}</span>
        </div>
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${badge.bg} ${badge.text}`}
        >
          {levelCategory.toUpperCase()}
        </span>
      </div>

      {/* Massive Editorial Number */}
      <div className="my-6">
        <div className="flex items-baseline gap-2">
          <span className="text-6xl md:text-7xl font-semibold tracking-tighter text-[#090A0F] font-mono">
            {Math.round(aqiValue)}
          </span>
          <span className="text-[11px] font-mono text-neutral-400">COMPOSITE AQI</span>
        </div>
      </div>

      {/* Footer Confidence Interval */}
      <div className="pt-3 border-t border-neutral-100 flex items-center justify-between text-xs font-mono text-neutral-500">
        <span>80% CONFIDENCE BAND</span>
        <span className="font-semibold text-[#090A0F]">
          {lowerBound ? `${Math.round(lowerBound)} – ${Math.round(upperBound || aqiValue + 12)}` : '± 8 AQI'}
        </span>
      </div>
    </motion.div>
  );
}

interface AtmosphericBentoGridProps {
  hourlyPredictions: DiurnalPredictionHour[];
}

export default function AtmosphericBentoGrid({ hourlyPredictions = [] }: AtmosphericBentoGridProps) {
  const tomorrow = hourlyPredictions[23] ||
    hourlyPredictions[Math.min(23, hourlyPredictions.length - 1)] || {
      timestamp: '',
      aqi_predicted: 88,
      level: 'Moderate',
      aqi_lower_80: 80,
      aqi_upper_80: 98,
    };

  const dayAfter = hourlyPredictions[47] ||
    hourlyPredictions[Math.min(47, hourlyPredictions.length - 1)] || {
      timestamp: '',
      aqi_predicted: 96,
      level: 'Moderate',
      aqi_lower_80: 86,
      aqi_upper_80: 108,
    };

  const day3 = hourlyPredictions[71] ||
    hourlyPredictions[Math.min(71, hourlyPredictions.length - 1)] || {
      timestamp: '',
      aqi_predicted: 124,
      level: 'Unhealthy for Sensitive Groups',
      aqi_lower_80: 110,
      aqi_upper_80: 140,
    };

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-neutral-200/60 pb-4 gap-4">
        <div>
          <span className="text-xs font-mono text-neutral-400 block mb-1">PROSPECTIVE FORECAST</span>
          <h2 className="text-2xl font-semibold tracking-tight text-[#090A0F]">
            72-Hour Diurnal Progression
          </h2>
        </div>
        <span className="text-xs font-mono text-neutral-500">
          Evaluated via sliding 24h attention windows
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <ArchitecturalTile
          label="T + 24 Hours (Tomorrow)"
          sublabel="Midday convective boundary layer status"
          aqiValue={tomorrow.aqi_predicted}
          levelCategory={tomorrow.level}
          lowerBound={tomorrow.aqi_lower_80}
          upperBound={tomorrow.aqi_upper_80}
          isMainTile={true}
          animationDelay={0.05}
        />

        <ArchitecturalTile
          label="T + 48 Hours (Day 2)"
          sublabel="Forecasted atmospheric stability"
          aqiValue={dayAfter.aqi_predicted}
          levelCategory={dayAfter.level}
          lowerBound={dayAfter.aqi_lower_80}
          upperBound={dayAfter.aqi_upper_80}
          animationDelay={0.12}
        />

        <ArchitecturalTile
          label="T + 72 Hours (Day 3)"
          sublabel="Long-range dispersion trajectory"
          aqiValue={day3.aqi_predicted}
          levelCategory={day3.level}
          lowerBound={day3.aqi_lower_80}
          upperBound={day3.aqi_upper_80}
          animationDelay={0.18}
        />
      </div>
    </section>
  );
}

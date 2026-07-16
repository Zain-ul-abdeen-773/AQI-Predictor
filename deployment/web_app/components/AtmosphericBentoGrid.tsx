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

interface NeumorphicTileProps {
  label: string;
  sublabel: string;
  aqiValue: number;
  levelCategory: string;
  lowerBound?: number;
  upperBound?: number;
  isMainTile?: boolean;
  animationDelay?: number;
}

/** Tailored EPA Light Theme badges */
function getEpaBadgeStyle(val: number) {
  if (val <= 50) return { text: 'text-emerald-700', border: 'border-emerald-300', bg: 'bg-emerald-100/80', dot: 'bg-emerald-500' };
  if (val <= 100) return { text: 'text-amber-800', border: 'border-amber-300', bg: 'bg-amber-100/80', dot: 'bg-amber-500' };
  if (val <= 150) return { text: 'text-orange-800', border: 'border-orange-300', bg: 'bg-orange-100/80', dot: 'bg-orange-500' };
  if (val <= 200) return { text: 'text-rose-800', border: 'border-rose-300', bg: 'bg-rose-100/80', dot: 'bg-rose-600' };
  return { text: 'text-purple-900', border: 'border-purple-300', bg: 'bg-purple-100/80', dot: 'bg-purple-600' };
}

function MagneticNeumorphicTile({
  label,
  sublabel,
  aqiValue,
  levelCategory,
  lowerBound,
  upperBound,
  isMainTile = false,
  animationDelay = 0,
}: NeumorphicTileProps) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0 });
  const [shadowOffset, setShadowOffset] = useState({ sx: -8, sy: -8, bx: 8, by: 8 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const deltaX = e.clientX - centerX;
    const deltaY = e.clientY - centerY;

    // Calculate 3D tilt
    const rx = (deltaY / (rect.height / 2)) * -9;
    const ry = (deltaX / (rect.width / 2)) * 9;
    setTilt({ rx, ry });

    // Calculate virtual light source dynamic Neumorphic shadow shift
    // If cursor is at top-left, stark white shadow moves away opposite (`+X, +Y`), gray shadow shifts towards (`-X, -Y`)
    const shiftFactorX = (deltaX / rect.width) * 16;
    const shiftFactorY = (deltaY / rect.height) * 16;

    setShadowOffset({
      sx: -8 - shiftFactorX,
      sy: -8 - shiftFactorY,
      bx: 8 - shiftFactorX,
      by: 8 - shiftFactorY,
    });
  };

  const handleMouseLeave = () => {
    setTilt({ rx: 0, ry: 0 });
    setShadowOffset({ sx: -8, sy: -8, bx: 8, by: 8 });
  };

  const badge = getEpaBadgeStyle(aqiValue);

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      initial={{ opacity: 0, y: 24, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.65, delay: animationDelay, ease: [0.16, 1, 0.3, 1] }}
      style={{
        transformStyle: 'preserve-3d',
        transform: `perspective(1200px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)`,
        boxShadow: `${shadowOffset.sx}px ${shadowOffset.sy}px 20px rgba(255, 255, 255, 0.95), ${shadowOffset.bx}px ${shadowOffset.by}px 20px rgba(209, 217, 230, 0.82)`,
      }}
      className={`relative group rounded-3xl bg-[#F2F4F8] border border-white p-7 flex flex-col justify-between transition-transform duration-150 ease-out ${
        isMainTile ? 'md:col-span-2 md:row-span-2 min-h-[310px]' : 'min-h-[185px]'
      }`}
    >
      {/* Top Header */}
      <div className="flex items-start justify-between z-10">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#64748B]" />
            <span className="text-xs uppercase tracking-wider font-bold text-[#475569]">{label}</span>
          </div>
          <p className="text-xs font-medium text-[#64748B] mt-1 max-w-sm">{sublabel}</p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold border ${badge.border} ${badge.bg} ${badge.text} shadow-sm`}
        >
          <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
          {levelCategory}
        </span>
      </div>

      {/* Massive Central AQI Typography */}
      <div className="my-7 z-10">
        <div className="flex items-baseline gap-3">
          <span className="text-6xl md:text-7xl font-extrabold tracking-tighter text-[#2D3748]">
            {Math.round(aqiValue)}
          </span>
          <span className="text-xs uppercase font-extrabold text-[#64748B] tracking-wider">AQI Score</span>
        </div>
      </div>

      {/* Footer Confidence Interval */}
      <div className="pt-4 border-t border-[#D1D9E6]/60 flex items-center justify-between text-xs text-[#64748B] z-10 font-mono">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-[#0284C7]" />
          <span className="font-semibold">80% Confidence Band</span>
        </div>
        <span className="text-[#2D3748] font-bold bg-[#F2F4F8] shadow-neumorphic-inset-sm px-3 py-1 rounded-xl border border-white">
          {lowerBound ? `${Math.round(lowerBound)} – ${Math.round(upperBound || aqiValue + 12)}` : '± 8'}
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
      aqi_upper_80: 96,
    };
  const day2 = hourlyPredictions[47] ||
    hourlyPredictions[Math.min(47, hourlyPredictions.length - 1)] || {
      timestamp: '',
      aqi_predicted: 94,
      level: 'Moderate',
      aqi_lower_80: 84,
      aqi_upper_80: 105,
    };
  const day3 = hourlyPredictions[71] ||
    hourlyPredictions[Math.min(71, hourlyPredictions.length - 1)] || {
      timestamp: '',
      aqi_predicted: 104,
      level: 'Unhealthy for Sensitive Groups',
      aqi_lower_80: 92,
      aqi_upper_80: 118,
    };

  return (
    <section className="flex flex-col gap-5 my-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-2">
        <h2 className="text-base font-extrabold text-[#2D3748] flex items-center gap-2.5">
          <Sparkles className="w-5 h-5 text-[#0284C7]" />
          Tactile 3-Day Bento Box Forecast
        </h2>
        <span className="text-xs font-semibold text-[#64748B] flex items-center gap-1.5">
          <ArrowUpRight className="w-4 h-4 text-[#0284C7]" />
          Hover cards for magnetic 3D tilt & virtual light source shift
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MagneticNeumorphicTile
          label="Tomorrow (+24h)"
          sublabel="Peak diurnal concentration during morning inversion"
          aqiValue={tomorrow.aqi_predicted}
          levelCategory={tomorrow.level}
          lowerBound={tomorrow.aqi_lower_80}
          upperBound={tomorrow.aqi_upper_80}
          isMainTile={true}
          animationDelay={0.1}
        />
        <div className="flex flex-col gap-6 md:col-span-1">
          <MagneticNeumorphicTile
            label="Day 2 (+48h)"
            sublabel="Mid-range atmospheric dispersion horizon"
            aqiValue={day2.aqi_predicted}
            levelCategory={day2.level}
            lowerBound={day2.aqi_lower_80}
            upperBound={day2.aqi_upper_80}
            animationDelay={0.2}
          />
          <MagneticNeumorphicTile
            label="Day 3 (+72h)"
            sublabel="Extended regional air quality projection"
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

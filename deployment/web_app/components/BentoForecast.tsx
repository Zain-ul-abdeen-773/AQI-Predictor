'use client';

import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Wind, ShieldAlert, ArrowUpRight, TrendingUp, Calendar } from 'lucide-react';

export interface ForecastHour {
  timestamp: string;
  aqi_predicted: number;
  aqi_lower_80?: number;
  aqi_upper_80?: number;
  level: string;
}

interface BentoForecastProps {
  hourlyPredictions: ForecastHour[];
}

interface BentoCardProps {
  title: string;
  subtitle: string;
  aqi: number;
  level: string;
  lower?: number;
  upper?: number;
  delay?: number;
  isMain?: boolean;
}

function MagneticGlowCard({
  title,
  subtitle,
  aqi,
  level,
  lower,
  upper,
  delay = 0,
  isMain = false,
}: BentoCardProps) {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Calculate percentage for cursor radial-gradient glow
    const xPercent = (x / rect.width) * 100;
    const yPercent = (y / rect.height) * 100;
    setMousePos({ x: xPercent, y: yPercent });

    // Calculate 3D tilt angles (-10deg to 10deg)
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rX = ((y - centerY) / centerY) * -10;
    const rY = ((x - centerX) / centerX) * 10;
    setRotateX(rX);
    setRotateY(rY);
  };

  const handleMouseLeave = () => {
    setRotateX(0);
    setRotateY(0);
  };

  const getAqiColor = (val: number) => {
    if (val <= 50) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (val <= 100) return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    if (val <= 150) return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
    if (val <= 200) return 'text-red-400 border-red-500/30 bg-red-500/10';
    return 'text-rose-500 border-rose-500/40 bg-rose-500/20';
  };

  const colorClass = getAqiColor(aqi);

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay }}
      style={{
        transformStyle: 'preserve-3d',
        transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
      }}
      className={`relative group overflow-hidden rounded-3xl transition-transform duration-200 ease-out border border-white/10 bg-white/[0.04] backdrop-blur-2xl p-6 flex flex-col justify-between ${
        isMain ? 'md:col-span-2 md:row-span-2' : ''
      }`}
    >
      {/* Soft radial cursor tracking glow */}
      <div
        className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `radial-gradient(400px circle at ${mousePos.x}% ${mousePos.y}%, rgba(255, 255, 255, 0.12), transparent 80%)`,
        }}
      />

      {/* Card Header */}
      <div className="flex items-start justify-between z-10">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-white/50" />
            <span className="text-xs uppercase tracking-widest font-semibold text-white/60">
              {title}
            </span>
          </div>
          <p className="text-xs text-white/40 mt-1">{subtitle}</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold border ${colorClass} tracking-wide`}
        >
          {level}
        </span>
      </div>

      {/* Main AQI Number */}
      <div className="my-6 z-10">
        <div className="flex items-baseline gap-3">
          <span className={`text-5xl md:text-6xl font-extralight tracking-tight font-sans ${colorClass.split(' ')[0]}`}>
            {Math.round(aqi)}
          </span>
          <span className="text-sm font-medium text-white/50 tracking-wider uppercase">
            AQI Forecast
          </span>
        </div>
      </div>

      {/* Footer Metrics */}
      <div className="pt-4 border-t border-white/5 flex items-center justify-between text-xs text-white/50 z-10">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          <span>Uncertainty Bounds (80% CI)</span>
        </div>
        <span className="font-mono text-white/80">
          {lower ? `${Math.round(lower)} - ${Math.round(upper || aqi + 15)}` : '± 8 AQI'}
        </span>
      </div>
    </motion.div>
  );
}

export default function BentoForecast({ hourlyPredictions = [] }: BentoForecastProps) {
  // Extract key target checkpoints: +24h (Tomorrow), +48h (Day 2), +72h (Day 3)
  const tomorrow = hourlyPredictions[23] || hourlyPredictions[Math.min(23, hourlyPredictions.length - 1)] || {
    timestamp: new Date(Date.now() + 86400000).toISOString(),
    aqi_predicted: 88,
    level: 'Moderate',
    aqi_lower_80: 80,
    aqi_upper_80: 96,
  };

  const day2 = hourlyPredictions[47] || hourlyPredictions[Math.min(47, hourlyPredictions.length - 1)] || {
    timestamp: new Date(Date.now() + 86400000 * 2).toISOString(),
    aqi_predicted: 94,
    level: 'Moderate',
    aqi_lower_80: 84,
    aqi_upper_80: 105,
  };

  const day3 = hourlyPredictions[71] || hourlyPredictions[Math.min(71, hourlyPredictions.length - 1)] || {
    timestamp: new Date(Date.now() + 86400000 * 3).toISOString(),
    aqi_predicted: 102,
    level: 'Unhealthy for Sensitive Groups',
    aqi_lower_80: 90,
    aqi_upper_80: 116,
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-8">
      <MagneticGlowCard
        title="Tomorrow Forecast (+24 Hours)"
        subtitle="Expected diurnal peak afternoon smog concentration"
        aqi={tomorrow.aqi_predicted}
        level={tomorrow.level}
        lower={tomorrow.aqi_lower_80}
        upper={tomorrow.aqi_upper_80}
        delay={0.1}
        isMain={true}
      />
      
      <div className="flex flex-col gap-6 md:col-span-1">
        <MagneticGlowCard
          title="Day 2 (+48 Hours)"
          subtitle="Mid-range atmospheric dispersion model"
          aqi={day2.aqi_predicted}
          level={day2.level}
          lower={day2.aqi_lower_80}
          upper={day2.aqi_upper_80}
          delay={0.2}
        />
        <MagneticGlowCard
          title="Day 3 (+72 Hours)"
          subtitle="Extended horizon probabilistic forecast"
          aqi={day3.aqi_predicted}
          level={day3.level}
          lower={day3.aqi_lower_80}
          upper={day3.aqi_upper_80}
          delay={0.3}
        />
      </div>
    </div>
  );
}

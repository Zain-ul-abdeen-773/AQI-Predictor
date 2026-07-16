'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Wind, Activity, BarChart2, ShieldCheck, Zap } from 'lucide-react';

export default function LiquidNavigation() {
  const currentPath = usePathname();

  const navItems = [
    { label: '3-Day Overview', route: '/', icon: Activity },
    { label: 'EDA & Model Telemetry', route: '/analytics', icon: BarChart2 },
    { label: 'SHAP Explainability', route: '/explainability', icon: ShieldCheck },
  ];

  return (
    <header className="sticky top-5 z-50 max-w-7xl mx-auto px-4 sm:px-6 mb-8">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-3.5 px-5 rounded-3xl bg-white/[0.045] backdrop-blur-3xl border border-white/10 shadow-[0_16px_50px_rgba(0,0,0,0.7)] hover:border-white/20 transition-all duration-300">
        {/* Brand & Atmospheric Station Badge */}
        <Link href="/" className="flex items-center gap-3.5 group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/10 border border-emerald-500/30 group-hover:border-emerald-400/60 transition-all shadow-[0_0_20px_rgba(16,185,129,0.25)]">
            <Wind className="w-5 h-5 text-emerald-400 group-hover:rotate-180 transition-transform duration-700 ease-in-out" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-white group-hover:text-emerald-300 transition-colors">
                Pearls AQI Engine
              </span>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono uppercase font-bold tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Sargodha #4
              </span>
            </div>
            <span className="text-[11px] text-white/50 tracking-wide">
              Atmospheric Obsidian • Spatial Hyper-Minimalism
            </span>
          </div>
        </Link>

        {/* Liquid Multi-Page Route Tabs */}
        <nav className="flex items-center gap-1.5 p-1.5 rounded-2xl bg-black/40 border border-white/5">
          {navItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = currentPath === item.route;

            return (
              <Link
                key={item.route}
                href={item.route}
                className={`relative px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-colors flex items-center gap-2 z-10 ${
                  isActive ? 'text-white' : 'text-white/60 hover:text-white'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="liquid-nav-tab"
                    className="absolute inset-0 bg-white/[0.12] rounded-xl border border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.1)] z-[-1]"
                    transition={{ type: 'spring', stiffness: 420, damping: 32 }}
                  />
                )}
                <IconComponent className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-white/40'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Live Engine Status Indicator */}
        <div className="hidden xl:flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/10 text-xs font-mono text-white/70">
          <div className="relative flex items-center justify-center w-2 h-2">
            <span className="absolute inline-flex w-full h-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
            <span className="relative inline-flex w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <span>60 FPS Particle Stream</span>
          <Zap className="w-3.5 h-3.5 text-amber-400" />
        </div>
      </div>
    </header>
  );
}

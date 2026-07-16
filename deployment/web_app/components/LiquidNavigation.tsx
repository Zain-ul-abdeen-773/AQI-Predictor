'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Wind, Activity, BarChart2, ShieldCheck } from 'lucide-react';

export default function LiquidNavigation() {
  const currentPath = usePathname();

  const navItems = [
    { label: 'Overview', route: '/', icon: Activity },
    { label: 'Model Comparison', route: '/analytics', icon: BarChart2 },
    { label: 'Explainability', route: '/explainability', icon: ShieldCheck },
  ];

  return (
    <header className="sticky top-4 z-50 max-w-7xl mx-auto px-4 sm:px-6 mb-8">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-3 px-5 rounded-2xl bg-[#1a1a1f]/80 backdrop-blur-2xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.5)] transition-all duration-300">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500/25 to-sky-500/15 border border-teal-500/25 group-hover:border-teal-400/50 transition-all">
            <Wind className="w-[18px] h-[18px] text-teal-400 group-hover:rotate-90 transition-transform duration-500" />
          </div>
          <div className="flex flex-col">
            <span className="text-[15px] font-semibold tracking-tight text-white/90 group-hover:text-white transition-colors">
              Pearls AQI
            </span>
            <span className="text-[10px] text-white/40 tracking-wide">
              Sargodha Region • Air Quality Intelligence
            </span>
          </div>
        </Link>

        {/* Nav Tabs */}
        <nav className="flex items-center gap-1 p-1 rounded-xl bg-white/[0.04] border border-white/[0.05]">
          {navItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = currentPath === item.route;

            return (
              <Link
                key={item.route}
                href={item.route}
                className={`relative px-4 py-2 rounded-lg text-[13px] font-medium transition-colors flex items-center gap-2 z-10 ${
                  isActive ? 'text-white' : 'text-white/50 hover:text-white/80'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="active-tab"
                    className="absolute inset-0 bg-white/[0.1] rounded-lg border border-white/[0.12] z-[-1]"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <IconComponent className={`w-3.5 h-3.5 ${isActive ? 'text-teal-400' : 'text-white/35'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Status Dot — subtle, no jargon */}
        <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-[11px] text-white/50">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-60" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal-500" />
          </span>
          <span>Live</span>
        </div>
      </div>
    </header>
  );
}

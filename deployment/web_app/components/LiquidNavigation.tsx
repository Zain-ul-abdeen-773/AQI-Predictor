'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Wind, Activity, BarChart2, ShieldCheck, Sun } from 'lucide-react';

export default function LiquidNavigation() {
  const currentPath = usePathname();

  const navItems = [
    { label: 'Overview', route: '/', icon: Activity },
    { label: 'Model Comparison', route: '/analytics', icon: BarChart2 },
    { label: 'Explainability', route: '/explainability', icon: ShieldCheck },
  ];

  return (
    <header className="sticky top-4 z-50 max-w-7xl mx-auto px-4 sm:px-6 mb-8">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-3.5 px-6 rounded-3xl bg-[#F2F4F8]/85 backdrop-blur-xl border border-white/60 shadow-neumorphic transition-all duration-300">
        {/* Brand Logo & Station Badge */}
        <Link href="/" className="flex items-center gap-3.5 group">
          <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-sm group-hover:scale-105 transition-transform duration-300 border border-white">
            <Wind className="w-5 h-5 text-[#0284C7] group-hover:rotate-90 transition-transform duration-500" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-bold tracking-tight text-[#2D3748]">
              Pearls AQI
            </span>
            <span className="text-[11px] font-medium text-[#64748B] tracking-wide">
              Sargodha Region • Soft UI Engine
            </span>
          </div>
        </Link>

        {/* Liquid Nav Tabs */}
        <nav className="flex items-center gap-1.5 p-1.5 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-inset border border-white/80">
          {navItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = currentPath === item.route;

            return (
              <Link
                key={item.route}
                href={item.route}
                className={`relative px-4 py-2 rounded-xl text-[13px] font-semibold transition-colors flex items-center gap-2 z-10 ${
                  isActive ? 'text-[#0284C7]' : 'text-[#64748B] hover:text-[#2D3748]'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="liquid-nav-pill"
                    className="absolute inset-0 bg-[#F2F4F8] rounded-xl shadow-neumorphic-sm border border-white z-[-1]"
                    transition={{ type: 'spring', stiffness: 350, damping: 28 }}
                  />
                )}
                <IconComponent className={`w-4 h-4 ${isActive ? 'text-[#0284C7]' : 'text-[#94A3B8]'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Status Indicator */}
        <div className="hidden xl:flex items-center gap-2.5 px-4 py-2 rounded-2xl bg-[#F2F4F8] shadow-neumorphic-sm border border-white text-xs font-semibold text-[#475569]">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 shadow-sm" />
          </span>
          <span>Station Active</span>
        </div>
      </div>
    </header>
  );
}

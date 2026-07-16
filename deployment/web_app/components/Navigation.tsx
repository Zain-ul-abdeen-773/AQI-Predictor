'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Wind, BarChart3, HelpCircle, Activity, Globe } from 'lucide-react';

export default function Navigation() {
  const pathname = usePathname();

  const links = [
    { name: '3-Day Overview', href: '/', icon: Activity },
    { name: 'EDA & Trends', href: '/analytics', icon: BarChart3 },
    { name: 'SHAP Explainability', href: '/explainability', icon: HelpCircle },
  ];

  return (
    <header className="sticky top-4 z-40 max-w-7xl mx-auto px-4 md:px-6 mb-6">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-3.5 rounded-2xl bg-black/50 backdrop-blur-2xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="p-2.5 rounded-xl bg-white/[0.07] border border-white/10 group-hover:border-emerald-500/40 transition-colors">
            <Wind className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white font-sans">
                Pearls AQI
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Sargodha
              </span>
            </div>
            <span className="text-[11px] text-white/50 block font-light">
              Atmospheric Obsidian Intelligence
            </span>
          </div>
        </Link>

        {/* Liquid Nav Links */}
        <nav className="flex items-center gap-1 bg-white/[0.04] p-1.5 rounded-xl border border-white/5">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative px-4 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2 z-10 ${
                  isActive ? 'text-white' : 'text-white/60 hover:text-white'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="liquid-active-tab"
                    className="absolute inset-0 bg-white/10 rounded-lg border border-white/15 z-[-1]"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : ''}`} />
                <span>{link.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Live Status Badge */}
        <div className="hidden lg:flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>60 FPS Particle Engine Active</span>
        </div>
      </div>
    </header>
  );
}

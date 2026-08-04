'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Wind } from 'lucide-react';

export default function LiquidNavigation() {
  const currentPath = usePathname();

  const navItems = [
    { label: 'Overview', route: '/' },
    { label: 'Model Comparison', route: '/analytics' },
    { label: 'Explainability', route: '/explainability' },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.06] bg-[#0B0F19]/70 backdrop-blur-2xl mb-10 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-6">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <motion.div
              whileHover={{ rotateY: 180, scale: 1.1 }}
              transition={{ type: 'spring', stiffness: 260, damping: 20 }}
              className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-lg shadow-blue-500/25"
              style={{ transformStyle: 'preserve-3d' }}
            >
              <Wind className="w-4 h-4" />
            </motion.div>
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-bold tracking-tight text-white">
                Pearls AQI
              </span>
              <span className="text-[11px] font-mono font-medium text-slate-400 hidden sm:inline-block">
                SARGODHA BASIN
              </span>
            </div>
          </Link>

          <span className="h-5 w-px bg-white/10 hidden md:block" />

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = currentPath === item.route;
              return (
                <Link
                  key={item.route}
                  href={item.route}
                  className={`relative px-4 py-2 rounded-lg text-xs font-medium transition-all duration-300 ${
                    isActive
                      ? 'text-white font-semibold'
                      : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-glow"
                      className="absolute inset-0 rounded-lg bg-white/[0.06] border border-white/[0.08] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute -bottom-[9px] left-4 right-4 h-[2px] bg-gradient-to-r from-blue-500 via-cyan-400 to-blue-500 rounded-full shadow-[0_0_8px_rgba(56,189,248,0.5)]"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Status */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-full border border-white/[0.06] bg-white/[0.03] text-[11px] font-mono text-slate-300 shadow-inner">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]" />
            </span>
            <span>LIVE</span>
          </div>
        </motion.div>
      </div>
    </header>
  );
}

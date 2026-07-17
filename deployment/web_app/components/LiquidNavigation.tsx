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
    <header className="sticky top-0 z-50 w-full border-b border-neutral-200/60 bg-[#FAFAFC]/85 backdrop-blur-md mb-10 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-6">
        {/* Brand Architecture Identity */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex items-center justify-center w-7 h-7 rounded-md bg-neutral-900 text-white transition-transform duration-200 group-hover:scale-105">
              <Wind className="w-4 h-4 text-[#0066FF]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-semibold tracking-tight text-[#090A0F]">
                Pearls AQI
              </span>
              <span className="text-[11px] font-mono font-medium text-neutral-400 hidden sm:inline-block">
                SARGODHA BASIN
              </span>
            </div>
          </Link>

          {/* Architectural Top Divider */}
          <span className="h-4 w-px bg-neutral-200/60 hidden md:block" />

          {/* Clean Editorial Navigation Links */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = currentPath === item.route;
              return (
                <Link
                  key={item.route}
                  href={item.route}
                  className={`relative px-3.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'text-[#0066FF] font-semibold'
                      : 'text-neutral-500 hover:text-[#090A0F] hover:bg-neutral-100/60'
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <motion.div
                      layoutId="editorial-nav-indicator"
                      className="absolute bottom-0 left-3.5 right-3.5 h-[2px] bg-[#0066FF] rounded-full"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Status Indicator & System Telemetry */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-md border border-neutral-200/60 bg-white/50 text-[11px] font-mono text-neutral-600">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
            </span>
            <span>TELEMETRY LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
}

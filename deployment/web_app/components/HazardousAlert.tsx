'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

interface HazardousAlertProps {
  aqi?: number;
  alert?: boolean;
}

export default function HazardousAlert({ aqi = 0, alert = false }: HazardousAlertProps) {
  const isHazardous = alert || aqi > 150;

  return (
    <AnimatePresence>
      {isHazardous && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8 }}
          className="fixed inset-0 pointer-events-none z-50 overflow-hidden"
        >
          {/* Breathing Screen-Wide Red Vignette Mask */}
          <motion.div
            animate={{
              opacity: [0.3, 0.7, 0.3],
              scale: [1, 1.02, 1],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{
              background: 'radial-gradient(circle at center, transparent 60%, rgba(225, 29, 72, 0.45) 100%)',
            }}
            className="absolute inset-0 w-full h-full"
          />

          {/* Top Advisory Floating Banner */}
          <motion.div
            initial={{ y: -60, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -60, opacity: 0 }}
            transition={{ type: 'spring', damping: 20, stiffness: 200 }}
            className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-auto max-w-xl w-full px-4"
          >
            <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-rose-950/90 border border-rose-500/40 backdrop-blur-2xl shadow-[0_0_30px_rgba(225,29,72,0.4)] text-rose-200">
              <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400">
                <AlertTriangle className="w-5 h-5 animate-pulse" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-bold tracking-wider text-rose-400">
                    Environmental Danger Warning
                  </span>
                  <span className="text-xs font-mono font-semibold bg-rose-500/30 px-2 py-0.5 rounded text-white">
                    AQI {Math.round(aqi)}
                  </span>
                </div>
                <p className="text-xs text-rose-200/90 mt-0.5">
                  Atmospheric particulate levels exceed safe exposure thresholds. Keep windows sealed and run N95 / HEPA filtration.
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

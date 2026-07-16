'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

interface VignetteAlertProps {
  currentAqi?: number;
  isTriggered?: boolean;
}

export default function VignetteAlert({ currentAqi = 0, isTriggered = false }: VignetteAlertProps) {
  const active = isTriggered || currentAqi > 150;

  return (
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.0 }}
          className="fixed inset-0 pointer-events-none z-40 overflow-hidden"
        >
          {/* Subtle warm amber breathing border glow around edges */}
          <motion.div
            animate={{
              opacity: [0.3, 0.65, 0.3],
              boxShadow: [
                'inset 0 0 60px rgba(245, 158, 11, 0.25)',
                'inset 0 0 110px rgba(245, 158, 11, 0.45)',
                'inset 0 0 60px rgba(245, 158, 11, 0.25)',
              ],
            }}
            transition={{ duration: 3.8, repeat: Infinity, ease: 'easeInOut' }}
            className="absolute inset-0 w-full h-full rounded-3xl border-4 border-amber-400/30"
          />

          {/* Frosted Warm Amber Advisory Banner at Top */}
          <motion.div
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -50, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 220 }}
            className="absolute top-6 left-1/2 -translate-x-1/2 pointer-events-auto max-w-xl w-full px-4"
          >
            <div className="flex items-start gap-4 p-5 rounded-3xl bg-[#F2F4F8]/95 shadow-neumorphic-lg border border-amber-300 backdrop-blur-2xl text-[#2D3748]">
              <div className="p-3 rounded-2xl bg-amber-100 border border-amber-300 text-amber-700 shadow-neumorphic-inset-sm">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-extrabold tracking-wider text-amber-800 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-amber-600" /> Soft Advisory • Elevated Concentration
                  </span>
                  <span className="text-xs font-mono font-bold bg-amber-200/80 text-amber-900 px-2.5 py-1 rounded-xl border border-amber-300">
                    AQI {Math.round(currentAqi)}
                  </span>
                </div>
                <p className="text-xs font-medium text-[#475569] mt-1.5 leading-relaxed">
                  Atmospheric particulate accumulation has exceeded regional thresholds (`150 AQI`). We recommend sensitive demographics limit strenuous physical outdoor activities.
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

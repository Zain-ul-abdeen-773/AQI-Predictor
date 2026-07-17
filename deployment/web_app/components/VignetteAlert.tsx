'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';

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
          transition={{ duration: 0.8 }}
          className="fixed inset-0 pointer-events-none z-40 overflow-hidden"
        >
          {/* Subtle amber perimeter pulse */}
          <motion.div
            animate={{
              opacity: [0.2, 0.45, 0.2],
            }}
            transition={{ duration: 4.0, repeat: Infinity, ease: 'easeInOut' }}
            className="absolute inset-0 w-full h-full border-2 border-amber-500/40"
          />

          {/* Editorial Advisory Header Bar */}
          <motion.div
            initial={{ y: -40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -40, opacity: 0 }}
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            className="absolute top-16 left-1/2 -translate-x-1/2 pointer-events-auto max-w-xl w-full px-4"
          >
            <div className="flex items-start gap-4 p-4 rounded-md bg-slate-800/80 border border-amber-300/80 shadow-2xs backdrop-blur-md text-[#090A0F]">
              <div className="p-2 rounded bg-amber-50 text-amber-700 border border-amber-200">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-900">
                    REGIONAL ADVISORY • ELEVATED PARTICULATE LOAD
                  </span>
                  <span className="text-xs font-mono font-semibold bg-amber-100 text-amber-900 px-2 py-0.5 rounded border border-amber-200">
                    AQI {Math.round(currentAqi)}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  Atmospheric particulate accumulation has crossed benchmark limits (`150 AQI`). Sensitive demographics are advised to reduce outdoor physical exertion.
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, ShieldAlert, XCircle } from 'lucide-react';

interface VignetteAlertProps {
  currentAqi?: number;
  isTriggered?: boolean;
}

export default function VignetteAlert({ currentAqi = 0, isTriggered = false }: VignetteAlertProps) {
  const activeWarning = isTriggered || currentAqi > 150;

  return (
    <AnimatePresence>
      {activeWarning && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.9 }}
          className="fixed inset-0 pointer-events-none z-40 overflow-hidden"
        >
          {/* Breathing Screen-Wide Red Vignette Mask at Edges of Screen */}
          <motion.div
            animate={{
              opacity: [0.35, 0.75, 0.35],
              scale: [1, 1.015, 1],
            }}
            transition={{
              duration: 3.2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{
              background: 'radial-gradient(circle at center, transparent 58%, rgba(225, 29, 72, 0.52) 100%)',
            }}
            className="absolute inset-0 w-full h-full pointer-events-none"
          />

          {/* Emergency Floating Environmental Advisory Modal */}
          <motion.div
            initial={{ y: -70, opacity: 0, scale: 0.95 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: -70, opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 22, stiffness: 220 }}
            className="absolute top-6 left-1/2 -translate-x-1/2 pointer-events-auto max-w-xl w-full px-4"
          >
            <div className="flex items-start gap-3.5 p-4 rounded-3xl bg-rose-950/95 border border-rose-500/50 backdrop-blur-3xl shadow-[0_12px_45px_rgba(225,29,72,0.5)] text-rose-100">
              <div className="p-2.5 rounded-2xl bg-rose-500/25 text-rose-400 border border-rose-500/40">
                <AlertTriangle className="w-6 h-6 animate-pulse" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase font-extrabold tracking-widest text-rose-400 flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5" /> Environmental Hazard Advisory
                  </span>
                  <span className="text-xs font-mono font-bold bg-rose-500/35 px-2.5 py-1 rounded-lg border border-rose-500/40 text-white shadow-sm">
                    AQI {Math.round(currentAqi)} (Severe)
                  </span>
                </div>
                <p className="text-xs text-rose-200/90 mt-1 leading-relaxed">
                  Diurnal atmospheric stagnation has concentrated particulate matter above safe biological exposure thresholds. Keep facility ventilation sealed and activate HEPA filtration loops immediately.
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

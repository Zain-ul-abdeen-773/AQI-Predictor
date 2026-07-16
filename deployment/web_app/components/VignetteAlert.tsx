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
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }}
          className="fixed inset-0 pointer-events-none z-40 overflow-hidden">
          <motion.div
            animate={{ opacity: [0.3, 0.6, 0.3], scale: [1, 1.01, 1] }}
            transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
            style={{ background: 'radial-gradient(circle at center, transparent 60%, rgba(180, 50, 50, 0.4) 100%)' }}
            className="absolute inset-0 w-full h-full" />

          <motion.div
            initial={{ y: -60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -60, opacity: 0 }}
            transition={{ type: 'spring', damping: 22, stiffness: 200 }}
            className="absolute top-5 left-1/2 -translate-x-1/2 pointer-events-auto max-w-lg w-full px-4">
            <div className="flex items-start gap-3 p-4 rounded-2xl bg-red-950/90 border border-red-500/40 backdrop-blur-2xl shadow-[0_8px_30px_rgba(180,50,50,0.3)] text-red-100">
              <div className="p-2 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] uppercase font-bold tracking-wider text-red-400 flex items-center gap-1">
                    <ShieldAlert className="w-3 h-3" /> Air Quality Warning
                  </span>
                  <span className="text-[11px] font-mono font-bold bg-red-500/30 px-2 py-0.5 rounded text-white">
                    AQI {Math.round(currentAqi)}
                  </span>
                </div>
                <p className="text-[12px] text-red-200/80 mt-1 leading-relaxed">
                  Air quality has exceeded safe levels. Limit outdoor activity and keep windows closed. Consider using air purification.
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

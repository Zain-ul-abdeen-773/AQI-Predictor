'use client';

import React from 'react';
import { motion } from 'framer-motion';

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28, scale: 0.95, filter: 'blur(8px)' }}
      animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
      exit={{ opacity: 0, y: -20, scale: 0.95, filter: 'blur(8px)' }}
      transition={{
        type: 'spring',
        stiffness: 280,
        damping: 32,
        mass: 0.9,
      }}
      className="w-full"
    >
      {children}
    </motion.div>
  );
}

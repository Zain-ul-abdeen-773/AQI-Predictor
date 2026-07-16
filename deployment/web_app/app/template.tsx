'use client';

import React from 'react';
import { motion } from 'framer-motion';

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, filter: 'blur(10px)' }}
      animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
      exit={{ opacity: 0, scale: 0.96, filter: 'blur(10px)' }}
      transition={{
        type: 'spring',
        stiffness: 280,
        damping: 28,
        duration: 0.65,
      }}
      className="w-full"
    >
      {children}
    </motion.div>
  );
}

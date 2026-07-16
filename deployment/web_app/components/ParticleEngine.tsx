'use client';

import React, { useEffect, useRef } from 'react';

interface ParticleEngineProps {
  aqi?: number;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  alpha: number;
  maxAlpha: number;
  life: number;
  maxLife: number;
}

export default function ParticleEngine({ aqi = 85 }: ParticleEngineProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Determine particle behavior & color based on AQI level
    const isHazardous = aqi > 150;
    const isModerate = aqi > 100 && aqi <= 150;
    
    // Particle count: denser for high smog
    const particleCount = isHazardous ? 1200 : isModerate ? 800 : 600;
    
    // Velocity multiplier
    const baseSpeed = isHazardous ? 3.5 : isModerate ? 2.0 : 1.2;
    const turbulence = isHazardous ? 1.8 : isModerate ? 0.8 : 0.3;

    // Color gradients
    const getParticleColor = (alpha: number) => {
      if (isHazardous) {
        // Toxic Ochre / Crimson Smog (#e11d48 / #d97706)
        return `rgba(225, 29, 72, ${alpha})`;
      } else if (isModerate) {
        // Amber / Ochre (#f59e0b)
        return `rgba(245, 158, 11, ${alpha})`;
      } else {
        // Calm Emerald / Cyan (#10b981 / #06b6d4)
        return `rgba(16, 185, 129, ${alpha})`;
      }
    };

    const particles: Particle[] = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.2) * baseSpeed,
        vy: (Math.random() - 0.5) * (baseSpeed * 0.4),
        radius: Math.random() * 2.2 + 0.6,
        alpha: Math.random() * 0.6 + 0.1,
        maxAlpha: Math.random() * 0.7 + 0.2,
        life: Math.random() * 100,
        maxLife: Math.random() * 200 + 100,
      });
    }

    let time = 0;
    const render = () => {
      time += 0.015;
      
      // Clear with slight trail effect for fluid wind feel
      ctx.fillStyle = 'rgba(10, 10, 10, 0.25)';
      ctx.fillRect(0, 0, width, height);

      particles.forEach((p) => {
        p.life += 1;
        if (p.life >= p.maxLife) {
          p.x = -10;
          p.y = Math.random() * height;
          p.life = 0;
          p.vx = (Math.random() * 0.8 + 0.4) * baseSpeed;
        }

        // Simulating perlin-like wind wave currents using sine/cosine
        const windWave = Math.sin(time + p.y * 0.005) * turbulence;
        const verticalWave = Math.cos(time * 0.8 + p.x * 0.005) * (turbulence * 0.5);

        p.x += p.vx + windWave;
        p.y += p.vy + verticalWave;

        // Screen wrap
        if (p.x > width + 20) p.x = -20;
        if (p.x < -20) p.x = width + 20;
        if (p.y > height + 20) p.y = -20;
        if (p.y < -20) p.y = height + 20;

        // Smooth alpha fade in/out during life cycle
        const progress = p.life / p.maxLife;
        let currentAlpha = p.maxAlpha;
        if (progress < 0.2) {
          currentAlpha = (progress / 0.2) * p.maxAlpha;
        } else if (progress > 0.8) {
          currentAlpha = ((1 - progress) / 0.2) * p.maxAlpha;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = getParticleColor(currentAlpha);
        ctx.shadowBlur = isHazardous ? 12 : 8;
        ctx.shadowColor = getParticleColor(currentAlpha * 0.8);
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [aqi]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[-1] w-full h-full bg-[#0A0A0A]"
    />
  );
}

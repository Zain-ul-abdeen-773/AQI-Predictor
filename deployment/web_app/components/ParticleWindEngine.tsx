'use client';

import React, { useEffect, useRef } from 'react';

interface ParticleWindEngineProps {
  aqiValue?: number;
}

interface WindParticle {
  x: number;
  y: number;
  speedX: number;
  speedY: number;
  radius: number;
  opacity: number;
  maxOpacity: number;
  age: number;
  lifespan: number;
  angleOffset: number;
}

export default function ParticleWindEngine({ aqiValue = 85 }: ParticleWindEngineProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<{ x: number; y: number; active: boolean }>({ x: -1000, y: -1000, active: false });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY, active: true };
    };
    const handleMouseLeave = () => {
      mouseRef.current.active = false;
    };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const onResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', onResize);

    // Compute dynamic atmospheric parameters
    const isDanger = aqiValue > 150;
    const isModerate = aqiValue > 100 && aqiValue <= 150;

    const totalParticles = isDanger ? 1400 : isModerate ? 1000 : 750;
    const velocityScale = isDanger ? 4.6 : isModerate ? 2.4 : 1.4;
    const turbulenceStrength = isDanger ? 2.2 : isModerate ? 1.1 : 0.45;

    // Color definitions
    const getParticleRgba = (alpha: number, index: number) => {
      if (isDanger) {
        // Toxic Ochre / Crimson Smog (#E11D48 / #D97706 / #F43F5E)
        const colors = [
          `rgba(225, 29, 72, ${alpha})`,
          `rgba(217, 119, 6, ${alpha})`,
          `rgba(244, 63, 94, ${alpha})`,
          `rgba(180, 83, 9, ${alpha})`
        ];
        return colors[index % colors.length];
      } else if (isModerate) {
        // Warm Amber / Ochre (#F59E0B / #D97706 / #FBBF24)
        const colors = [
          `rgba(245, 158, 11, ${alpha})`,
          `rgba(217, 119, 6, ${alpha})`,
          `rgba(251, 191, 36, ${alpha})`
        ];
        return colors[index % colors.length];
      } else {
        // Calm Emerald / Cyan (#10B981 / #06B6D4 / #34D399)
        const colors = [
          `rgba(16, 185, 129, ${alpha})`,
          `rgba(6, 182, 212, ${alpha})`,
          `rgba(52, 211, 153, ${alpha})`,
          `rgba(14, 165, 233, ${alpha})`
        ];
        return colors[index % colors.length];
      }
    };

    const particles: WindParticle[] = Array.from({ length: totalParticles }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      speedX: (Math.random() * 0.9 + 0.3) * velocityScale,
      speedY: (Math.random() - 0.5) * velocityScale * 0.35,
      radius: Math.random() * 2.4 + 0.7,
      opacity: 0,
      maxOpacity: Math.random() * 0.65 + 0.25,
      age: Math.random() * 120,
      lifespan: Math.random() * 180 + 120,
      angleOffset: Math.random() * Math.PI * 2,
    }));

    let tick = 0;

    const renderLoop = () => {
      tick += 0.018;

      // Obsidian background with motion blur / wind trail persistence
      ctx.fillStyle = 'rgba(10, 10, 10, 0.22)';
      ctx.fillRect(0, 0, width, height);

      const { x: mx, y: my, active: mActive } = mouseRef.current;

      particles.forEach((p, idx) => {
        p.age += 1;
        if (p.age >= p.lifespan) {
          p.x = -15;
          p.y = Math.random() * height;
          p.age = 0;
          p.speedX = (Math.random() * 0.8 + 0.4) * velocityScale;
        }

        // Perlin-like wind current equations
        const waveY = Math.sin(tick + p.x * 0.004 + p.angleOffset) * turbulenceStrength;
        const waveX = Math.cos(tick * 0.9 + p.y * 0.004) * (turbulenceStrength * 0.4);

        p.x += p.speedX + waveX;
        p.y += p.speedY + waveY;

        // Interactive mouse cursor wind deflection
        if (mActive) {
          const dx = p.x - mx;
          const dy = p.y - my;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 180 && dist > 0) {
            const force = (1 - dist / 180) * 3.5;
            p.x += (dx / dist) * force;
            p.y += (dy / dist) * force;
          }
        }

        // Screen boundary wraparound
        if (p.x > width + 25) p.x = -25;
        if (p.x < -25) p.x = width + 25;
        if (p.y > height + 25) p.y = -25;
        if (p.y < -25) p.y = height + 25;

        // Smooth fade-in / fade-out lifecycle
        const lifeRatio = p.age / p.lifespan;
        let curOpacity = p.maxOpacity;
        if (lifeRatio < 0.18) {
          curOpacity = (lifeRatio / 0.18) * p.maxOpacity;
        } else if (lifeRatio > 0.82) {
          curOpacity = ((1 - lifeRatio) / 0.18) * p.maxOpacity;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = getParticleRgba(curOpacity, idx);
        ctx.shadowBlur = isDanger ? 14 : 9;
        ctx.shadowColor = getParticleRgba(curOpacity * 0.9, idx);
        ctx.fill();
      });

      animId = requestAnimationFrame(renderLoop);
    };

    renderLoop();

    return () => {
      window.removeEventListener('resize', onResize);
      cancelAnimationFrame(animId);
    };
  }, [aqiValue]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 z-[-1] w-full h-full pointer-events-none bg-[#0A0A0A]"
    />
  );
}

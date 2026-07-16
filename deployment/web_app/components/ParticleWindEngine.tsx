'use client';

import React, { useEffect, useRef } from 'react';

interface ParticleWindEngineProps {
  aqiValue?: number;
}

interface WindMote {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  opacity: number;
  peakOpacity: number;
  age: number;
  lifespan: number;
  phase: number;
}

/**
 * Uses EPA-standard AQI color ranges:
 *   Good (0-50)       → Soft teal/green
 *   Moderate (51-100) → Warm gold/amber
 *   USG (101-150)     → Burnt orange
 *   Unhealthy (151+)  → Deep red/maroon
 */
export default function ParticleWindEngine({ aqiValue = 85 }: ParticleWindEngineProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<{ x: number; y: number; on: boolean }>({ x: -999, y: -999, on: false });

  useEffect(() => {
    const onMove = (e: MouseEvent) => { mouseRef.current = { x: e.clientX, y: e.clientY, on: true }; };
    const onLeave = () => { mouseRef.current.on = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseleave', onLeave);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseleave', onLeave); };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    let raf: number;
    let w = (canvas.width = window.innerWidth);
    let h = (canvas.height = window.innerHeight);
    const onResize = () => { if (!canvas) return; w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight; };
    window.addEventListener('resize', onResize);

    // EPA-based behavior tiers
    const isHazardous = aqiValue > 150;
    const isUSG = aqiValue > 100 && aqiValue <= 150;
    const isModerate = aqiValue > 50 && aqiValue <= 100;

    const count = isHazardous ? 1100 : isUSG ? 850 : isModerate ? 650 : 500;
    const speed = isHazardous ? 3.8 : isUSG ? 2.2 : isModerate ? 1.3 : 0.9;
    const turb = isHazardous ? 2.0 : isUSG ? 1.0 : isModerate ? 0.5 : 0.3;

    // EPA-realistic color palette
    const getColor = (alpha: number, i: number) => {
      if (isHazardous) {
        // Deep reds & maroons — like real smog/wildfire haze
        const c = [
          `rgba(190, 50, 50, ${alpha})`,   // deep red
          `rgba(160, 40, 60, ${alpha})`,    // maroon
          `rgba(200, 80, 40, ${alpha})`,    // burnt sienna
          `rgba(140, 30, 50, ${alpha})`,    // dark crimson
        ];
        return c[i % c.length];
      } else if (isUSG) {
        // Burnt oranges — hazy afternoon sun
        const c = [
          `rgba(210, 120, 40, ${alpha})`,   // burnt orange
          `rgba(190, 100, 35, ${alpha})`,   // dark amber
          `rgba(220, 140, 50, ${alpha})`,   // warm orange
        ];
        return c[i % c.length];
      } else if (isModerate) {
        // Warm golds — like a dusty sunset
        const c = [
          `rgba(200, 170, 80, ${alpha})`,   // warm gold
          `rgba(180, 155, 70, ${alpha})`,   // muted amber
          `rgba(190, 165, 90, ${alpha})`,   // sandy gold
        ];
        return c[i % c.length];
      } else {
        // Soft teals & greens — clean, fresh air
        const c = [
          `rgba(80, 180, 160, ${alpha})`,   // soft teal
          `rgba(70, 165, 150, ${alpha})`,   // muted cyan
          `rgba(90, 190, 170, ${alpha})`,   // seafoam
          `rgba(75, 170, 180, ${alpha})`,   // sky teal
        ];
        return c[i % c.length];
      }
    };

    const motes: WindMote[] = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() * 0.8 + 0.25) * speed,
      vy: (Math.random() - 0.5) * speed * 0.3,
      r: Math.random() * 2.0 + 0.5,
      opacity: 0,
      peakOpacity: Math.random() * 0.5 + 0.15,
      age: Math.random() * 120,
      lifespan: Math.random() * 200 + 100,
      phase: Math.random() * Math.PI * 2,
    }));

    let t = 0;
    const draw = () => {
      t += 0.016;
      // Soft trail fade for atmospheric persistence
      ctx.fillStyle = 'rgba(17, 17, 20, 0.2)';
      ctx.fillRect(0, 0, w, h);

      const { x: mx, y: my, on } = mouseRef.current;

      motes.forEach((p, i) => {
        p.age++;
        if (p.age >= p.lifespan) {
          p.x = -12;
          p.y = Math.random() * h;
          p.age = 0;
          p.vx = (Math.random() * 0.7 + 0.3) * speed;
        }

        // Natural wind sway
        const wx = Math.cos(t * 0.85 + p.y * 0.003) * turb * 0.4;
        const wy = Math.sin(t + p.x * 0.004 + p.phase) * turb;

        p.x += p.vx + wx;
        p.y += p.vy + wy;

        // Mouse interaction — gentle deflection
        if (on) {
          const dx = p.x - mx;
          const dy = p.y - my;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 150 && dist > 0) {
            const f = (1 - dist / 150) * 2.5;
            p.x += (dx / dist) * f;
            p.y += (dy / dist) * f;
          }
        }

        // Wrap
        if (p.x > w + 20) p.x = -20;
        if (p.x < -20) p.x = w + 20;
        if (p.y > h + 20) p.y = -20;
        if (p.y < -20) p.y = h + 20;

        // Smooth lifecycle fade
        const life = p.age / p.lifespan;
        let a = p.peakOpacity;
        if (life < 0.15) a = (life / 0.15) * p.peakOpacity;
        else if (life > 0.85) a = ((1 - life) / 0.15) * p.peakOpacity;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = getColor(a, i);
        ctx.shadowBlur = isHazardous ? 10 : 6;
        ctx.shadowColor = getColor(a * 0.7, i);
        ctx.fill();
      });

      raf = requestAnimationFrame(draw);
    };

    draw();
    return () => { window.removeEventListener('resize', onResize); cancelAnimationFrame(raf); };
  }, [aqiValue]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 z-[-1] w-full h-full pointer-events-none"
      style={{ background: '#111114' }}
    />
  );
}

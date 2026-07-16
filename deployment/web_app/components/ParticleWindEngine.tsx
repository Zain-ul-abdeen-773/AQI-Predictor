'use client';

import React, { useEffect, useRef } from 'react';

interface ParticleWindEngineProps {
  aqiValue?: number;
}

interface DustParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  maxAlpha: number;
  angle: number;
  angleSpeed: number;
}

export default function ParticleWindEngine({ aqiValue = 88 }: ParticleWindEngineProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const pointerRef = useRef({ x: -999, y: -999, active: false });

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      pointerRef.current = { x: e.clientX, y: e.clientY, active: true };
    };
    const handleLeave = () => {
      pointerRef.current.active = false;
    };
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseleave', handleLeave);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseleave', handleLeave);
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let rafId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Determine atmospheric state based on exact AQI
    const isHazardous = aqiValue > 150;
    const isUSG = aqiValue > 100 && aqiValue <= 150;
    const isModerate = aqiValue > 50 && aqiValue <= 100;

    // Particle density and turbulence physics
    const particleCount = isHazardous ? 950 : isUSG ? 700 : isModerate ? 500 : 380;
    const baseSpeed = isHazardous ? 3.4 : isUSG ? 2.1 : isModerate ? 1.3 : 0.85;
    const rayDiffusion = isHazardous ? 65 : isUSG ? 40 : 15;

    // Color tones tailored for Ethereal Luminous (#F2F4F8 base)
    const baseTint = isHazardous
      ? 'rgba(254, 243, 199, 0.45)' // warning amber (#FEF3C7)
      : isUSG
      ? 'rgba(254, 237, 213, 0.35)' // soft orange haze
      : isModerate
      ? 'rgba(242, 244, 248, 0.3)'  // neutral ethereal
      : 'rgba(224, 242, 254, 0.45)'; // fresh morning blue (#E0F2FE)

    const particleColors = isHazardous
      ? ['#D97706', '#B45309', '#92400E', '#F59E0B']
      : isUSG
      ? ['#EA580C', '#C2410C', '#FB923C', '#D97706']
      : isModerate
      ? ['#64748B', '#475569', '#94A3B8', '#CBD5E1']
      : ['#0284C7', '#0369A1', '#38BDF8', '#7DD3FC'];

    const particles: DustParticle[] = Array.from({ length: particleCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() * 0.8 + 0.3) * baseSpeed,
      vy: (Math.random() - 0.5) * baseSpeed * 0.35,
      size: Math.random() * 2.6 + 0.6,
      alpha: Math.random() * 0.5 + 0.15,
      maxAlpha: Math.random() * 0.6 + 0.2,
      angle: Math.random() * Math.PI * 2,
      angleSpeed: (Math.random() - 0.5) * 0.03,
    }));

    let time = 0;

    const animate = () => {
      time += 0.016;
      ctx.clearRect(0, 0, width, height);

      // 1. Render base atmospheric wash
      ctx.fillStyle = baseTint;
      ctx.fillRect(0, 0, width, height);

      // 2. Render Volumetric Sun Rays casting diagonally from top-left
      ctx.save();
      const numRays = isHazardous ? 8 : 5;
      const rayOriginX = width * 0.15;
      const rayOriginY = -100;

      for (let i = 0; i < numRays; i++) {
        const spreadAngle = (i - numRays / 2) * 0.18 + Math.sin(time * 0.5 + i) * 0.04;
        const rayLength = Math.max(width, height) * 1.4;
        const endX = rayOriginX + Math.cos(Math.PI / 3 + spreadAngle) * rayLength;
        const endY = rayOriginY + Math.sin(Math.PI / 3 + spreadAngle) * rayLength;

        const rayGrad = ctx.createLinearGradient(rayOriginX, rayOriginY, endX, endY);
        if (isHazardous) {
          rayGrad.addColorStop(0, 'rgba(251, 191, 36, 0.22)');
          rayGrad.addColorStop(0.5, 'rgba(217, 119, 6, 0.08)');
          rayGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        } else {
          rayGrad.addColorStop(0, 'rgba(255, 255, 255, 0.65)');
          rayGrad.addColorStop(0.4, 'rgba(224, 242, 254, 0.25)');
          rayGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        }

        ctx.beginPath();
        ctx.moveTo(rayOriginX, rayOriginY);
        ctx.lineTo(endX - 120, endY);
        ctx.lineTo(endX + 120, endY);
        ctx.closePath();
        ctx.fillStyle = rayGrad;
        if (isHazardous) {
          ctx.filter = `blur(${rayDiffusion}px)`;
        } else {
          ctx.filter = `blur(${rayDiffusion}px)`;
        }
        ctx.fill();
      }
      ctx.restore();

      // 3. Render Microscopic Wind/Dust Particles
      const { x: px, y: py, active } = pointerRef.current;

      particles.forEach((p, idx) => {
        p.angle += p.angleSpeed;
        const windX = Math.cos(time * 0.9 + p.y * 0.004) * 0.45;
        const windY = Math.sin(time * 1.1 + p.x * 0.003) * 0.35;

        p.x += p.vx + windX;
        p.y += p.vy + windY;

        // Tactile cursor interaction
        if (active) {
          const dx = p.x - px;
          const dy = p.y - py;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 140 && dist > 0) {
            const force = (1 - dist / 140) * 3.2;
            p.x += (dx / dist) * force;
            p.y += (dy / dist) * force;
          }
        }

        // Screen wrap
        if (p.x > width + 20) p.x = -20;
        if (p.x < -20) p.x = width + 20;
        if (p.y > height + 20) p.y = -20;
        if (p.y < -20) p.y = height + 20;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = particleColors[idx % particleColors.length];
        ctx.globalAlpha = p.alpha;
        ctx.shadowBlur = isHazardous ? 6 : 3;
        ctx.shadowColor = particleColors[idx % particleColors.length];
        ctx.fill();
      });

      ctx.globalAlpha = 1.0;
      rafId = requestAnimationFrame(animate);
    };

    animate();
    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(rafId);
    };
  }, [aqiValue]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 z-[-1] w-full h-full pointer-events-none"
      style={{ backgroundColor: '#F2F4F8' }}
    />
  );
}

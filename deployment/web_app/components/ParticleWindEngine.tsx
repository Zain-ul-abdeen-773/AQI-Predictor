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

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const isHazardous = aqiValue > 150;
    const isUSG = aqiValue > 100 && aqiValue <= 150;
    const isModerate = aqiValue > 50 && aqiValue <= 100;

    const particleCount = isHazardous ? 700 : isUSG ? 550 : isModerate ? 420 : 320;
    const baseSpeed = isHazardous ? 2.8 : isUSG ? 1.8 : isModerate ? 1.1 : 0.75;
    const rayDiffusion = isHazardous ? 50 : 25;

    // Color tones tailored for dark theme background
    const baseTint = isHazardous
      ? 'rgba(127, 29, 29, 0.12)'
      : isUSG
      ? 'rgba(120, 53, 15, 0.10)'
      : isModerate
      ? 'rgba(15, 23, 42, 0.15)'
      : 'rgba(15, 23, 42, 0.10)';

    const particleColors = isHazardous
      ? ['#E11D48', '#BE123C', '#F43F5E', '#FB7185']
      : isUSG
      ? ['#D97706', '#B45309', '#F59E0B', '#FBBF24']
      : isModerate
      ? ['#64748B', '#475569', '#94A3B8', '#CBD5E1']
      : ['#0066FF', '#0284C7', '#38BDF8', '#60A5FA'];

    const particles: DustParticle[] = Array.from({ length: particleCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() * 0.8 + 0.3) * baseSpeed,
      vy: (Math.random() - 0.5) * baseSpeed * 0.35,
      size: Math.random() * 2.2 + 0.6,
      alpha: Math.random() * 0.45 + 0.1,
      maxAlpha: Math.random() * 0.5 + 0.15,
      angle: Math.random() * Math.PI * 2,
      angleSpeed: (Math.random() - 0.5) * 0.03,
    }));

    let time = 0;

    const animate = () => {
      time += 0.016;
      ctx.clearRect(0, 0, width, height);

      ctx.fillStyle = baseTint;
      ctx.fillRect(0, 0, width, height);

      // Volumetric architectural lighting rays
      ctx.save();
      const numRays = isHazardous ? 6 : 4;
      const rayOriginX = width * 0.2;
      const rayOriginY = -120;

      for (let i = 0; i < numRays; i++) {
        const spreadAngle = (i - numRays / 2) * 0.18 + Math.sin(time * 0.5 + i) * 0.04;
        const rayLength = Math.max(width, height) * 1.4;
        const endX = rayOriginX + Math.cos(Math.PI / 3 + spreadAngle) * rayLength;
        const endY = rayOriginY + Math.sin(Math.PI / 3 + spreadAngle) * rayLength;

        const rayGrad = ctx.createLinearGradient(rayOriginX, rayOriginY, endX, endY);
        if (isHazardous) {
          rayGrad.addColorStop(0, 'rgba(244, 63, 94, 0.15)');
          rayGrad.addColorStop(0.5, 'rgba(225, 29, 72, 0.05)');
          rayGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        } else {
          rayGrad.addColorStop(0, 'rgba(59, 130, 246, 0.12)');
          rayGrad.addColorStop(0.4, 'rgba(59, 130, 246, 0.04)');
          rayGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        }

        ctx.beginPath();
        ctx.moveTo(rayOriginX, rayOriginY);
        ctx.lineTo(endX - 100, endY);
        ctx.lineTo(endX + 100, endY);
        ctx.closePath();
        ctx.fillStyle = rayGrad;
        ctx.filter = `blur(${rayDiffusion}px)`;
        ctx.fill();
      }
      ctx.restore();

      const { x: px, y: py, active } = pointerRef.current;

      particles.forEach((p, idx) => {
        p.angle += p.angleSpeed;
        const windX = Math.cos(time * 0.9 + p.y * 0.004) * 0.45;
        const windY = Math.sin(time * 1.1 + p.x * 0.003) * 0.35;

        p.x += p.vx + windX;
        p.y += p.vy + windY;

        if (active) {
          const dx = p.x - px;
          const dy = p.y - py;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 140 && dist > 0) {
            const force = (140 - dist) / 140;
            p.x += (dx / dist) * force * 5;
            p.y += (dy / dist) * force * 5;
          }
        }

        if (p.x > width + 20) p.x = -20;
        if (p.x < -20) p.x = width + 20;
        if (p.y > height + 20) p.y = -20;
        if (p.y < -20) p.y = height + 20;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = particleColors[idx % particleColors.length];
        ctx.globalAlpha = p.alpha;
        ctx.fill();
        ctx.globalAlpha = 1.0;
      });

      requestAnimationFrame(animate);
    };

    const animId = requestAnimationFrame(animate);
    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animId);
    };
  }, [aqiValue]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none z-0 w-full h-full"
    />
  );
}

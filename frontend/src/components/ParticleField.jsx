/**
 * ParticleField – Cursor-reactive particle animation
 * =====================================================
 * An HTML Canvas + JS physics particle field inspired by
 * Google Antigravity IDE's interactive background.
 *
 * Particles drift slowly on their own.  When the mouse moves
 * they are attracted or repelled inside a circular force-field,
 * creating the spiralling / vortex motion.
 *
 * Props:
 *  - particleCount  (number)  default 120
 *  - colors         (string[]) palette
 *  - maxRadius      (number)  force-field radius
 *  - style          (object)  extra CSS for the wrapper
 */

import React, { useRef, useEffect, useCallback } from 'react';

// ── defaults ────────────────────────────────────────────────
const DEFAULTS = {
  particleCount: 130,
  colors: [
    'rgba(99,102,241,0.6)',   // indigo
    'rgba(139,92,246,0.5)',   // violet
    'rgba(6,182,212,0.5)',    // cyan
    'rgba(245,158,11,0.35)',  // amber
    'rgba(255,255,255,0.25)', // white-ish
  ],
  maxRadius: 200, // px – cursor influence radius
};

export default function ParticleField({
  particleCount = DEFAULTS.particleCount,
  colors = DEFAULTS.colors,
  maxRadius = DEFAULTS.maxRadius,
  style = {},
}) {
  const canvasRef = useRef(null);
  const mouse = useRef({ x: -9999, y: -9999 }); // offscreen initially
  const particles = useRef([]);
  const raf = useRef(null);
  const dims = useRef({ w: 0, h: 0 });

  // ── Particle factory ──────────────────────────────────────
  const createParticle = useCallback(
    (w, h) => {
      const size = Math.random() * 3 + 1;
      return {
        x: Math.random() * w,
        y: Math.random() * h,
        // base velocity – slow drift
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        // original position for gentle homing
        ox: 0,
        oy: 0,
        size,
        color: colors[Math.floor(Math.random() * colors.length)],
        // each particle has its own force multiplier (variety)
        forceMul: 0.6 + Math.random() * 0.8,
        // tangential direction: +1 clockwise, -1 counter-clockwise
        tangentDir: Math.random() > 0.5 ? 1 : -1,
        opacity: 0.3 + Math.random() * 0.5,
        pulseSpeed: 0.005 + Math.random() * 0.01,
        pulsePhase: Math.random() * Math.PI * 2,
      };
    },
    [colors],
  );

  // ── Resize handler ────────────────────────────────────────
  const handleResize = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    const w = parent.clientWidth;
    const h = parent.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    dims.current = { w, h, dpr };

    // Re-seed particles on significant resize
    if (particles.current.length === 0) {
      const arr = [];
      for (let i = 0; i < particleCount; i++) {
        const p = createParticle(w, h);
        p.ox = p.x;
        p.oy = p.y;
        arr.push(p);
      }
      particles.current = arr;
    }
  }, [particleCount, createParticle]);

  // ── Mouse tracker ─────────────────────────────────────────
  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    mouse.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }, []);

  const handleMouseLeave = useCallback(() => {
    mouse.current = { x: -9999, y: -9999 };
  }, []);

  // ── Main render loop ──────────────────────────────────────
  const tick = useCallback(
    (time) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const { w, h, dpr } = dims.current;

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, w, h);

      const mx = mouse.current.x;
      const my = mouse.current.y;
      const mouseActive = mx > -999 && my > -999;

      const pts = particles.current;
      const len = pts.length;

      for (let i = 0; i < len; i++) {
        const p = pts[i];

        // ── cursor force ────────────────────────────────
        if (mouseActive) {
          const dx = p.x - mx;
          const dy = p.y - my;
          const distSq = dx * dx + dy * dy;
          const dist = Math.sqrt(distSq);

          if (dist < maxRadius && dist > 1) {
            // Normalised direction away from cursor
            const nx = dx / dist;
            const ny = dy / dist;

            // Force falls off with distance (inverse-square softened)
            const strength = ((maxRadius - dist) / maxRadius) * 2.5 * p.forceMul;

            // Radial component – repel outward
            const radial = strength * 0.45;
            // Tangential component – spiral motion (perpendicular to radial)
            const tangent = strength * 0.55 * p.tangentDir;

            // tangent direction: rotate normal 90°
            const tx = -ny;
            const ty = nx;

            p.vx += nx * radial + tx * tangent;
            p.vy += ny * radial + ty * tangent;
          }
        }

        // ── gentle homing back to original zone ─────────
        const homeForce = 0.002;
        p.vx += (p.ox - p.x) * homeForce;
        p.vy += (p.oy - p.y) * homeForce;

        // ── damping (friction) ──────────────────────────
        p.vx *= 0.96;
        p.vy *= 0.96;

        // ── integrate ───────────────────────────────────
        p.x += p.vx;
        p.y += p.vy;

        // ── wrap around edges ───────────────────────────
        if (p.x < -20) { p.x = w + 20; p.ox = p.x; }
        else if (p.x > w + 20) { p.x = -20; p.ox = p.x; }
        if (p.y < -20) { p.y = h + 20; p.oy = p.y; }
        else if (p.y > h + 20) { p.y = -20; p.oy = p.y; }

        // ── pulsing opacity ─────────────────────────────
        const pulse = Math.sin(time * p.pulseSpeed + p.pulsePhase) * 0.15 + 0.85;
        const alpha = p.opacity * pulse;

        // ── draw ────────────────────────────────────────
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color.replace(/[\d.]+\)$/, `${alpha})`);
        ctx.fill();
      }

      // ── draw subtle connecting lines between nearby particles ──
      ctx.lineWidth = 0.4;
      const linkDist = 100;
      const linkDistSq = linkDist * linkDist;
      for (let i = 0; i < len; i++) {
        for (let j = i + 1; j < len; j++) {
          const dx = pts[i].x - pts[j].x;
          const dy = pts[i].y - pts[j].y;
          const dSq = dx * dx + dy * dy;
          if (dSq < linkDistSq) {
            const a = (1 - dSq / linkDistSq) * 0.12;
            ctx.beginPath();
            ctx.moveTo(pts[i].x, pts[i].y);
            ctx.lineTo(pts[j].x, pts[j].y);
            ctx.strokeStyle = `rgba(255,255,255,${a})`;
            ctx.stroke();
          }
        }
      }

      ctx.restore();

      raf.current = requestAnimationFrame(tick);
    },
    [maxRadius],
  );

  // ── Lifecycle ─────────────────────────────────────────────
  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('mousemove', handleMouseMove);
      canvas.addEventListener('mouseleave', handleMouseLeave);
    }
    raf.current = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (canvas) {
        canvas.removeEventListener('mousemove', handleMouseMove);
        canvas.removeEventListener('mouseleave', handleMouseLeave);
      }
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [handleResize, handleMouseMove, handleMouseLeave, tick]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'auto',   // we NEED mouse events on the canvas
        zIndex: 0,
        ...style,
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
        }}
      />
    </div>
  );
}

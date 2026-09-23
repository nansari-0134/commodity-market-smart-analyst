/**
 * Commodity Market Intelligence Platform - Ambient Financial Canvas
 * Renders an interactive, performant market constellation layer with glowing nodes,
 * connecting ticker vectors, and subtle particle physics.
 */
(function() {
    'use strict';

    const canvas = document.getElementById('marketCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    let animationId = null;
    let isVisible = true;

    const PARTICLE_COUNT = Math.min(36, Math.floor((window.innerWidth * window.innerHeight) / 35000));
    const CONNECT_DIST = 140;
    const COLORS = [
        '#00f2fe', // Electric Cyan
        '#8b5cf6', // Cyber Violet
        '#10b981', // Neon Emerald
        '#f59e0b', // Solar Amber
        '#ec4899', // Radiant Magenta
        '#3b82f6'  // Ultra Blue
    ];

    const mouse = {
        x: null,
        y: null,
        radius: 160
    };

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }

    class Particle {
        constructor() {
            this.reset(true);
        }

        reset(initial) {
            this.x = initial ? Math.random() * width : (Math.random() > 0.5 ? 0 : width);
            this.y = initial ? Math.random() * height : Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.45;
            this.vy = (Math.random() - 0.5) * 0.45;
            this.size = Math.random() * 2 + 1.2;
            this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
            this.alpha = Math.random() * 0.5 + 0.3;
            this.pulseSpeed = Math.random() * 0.02 + 0.01;
            this.pulse = Math.random() * Math.PI;
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;

            // Soft pulse
            this.pulse += this.pulseSpeed;
            this.currentAlpha = this.alpha + Math.sin(this.pulse) * 0.2;

            // Bounce on borders
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;

            // Mouse interaction
            if (mouse.x !== null && mouse.y !== null) {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < mouse.radius) {
                    const force = (mouse.radius - dist) / mouse.radius;
                    this.x += dx * force * 0.02;
                    this.y += dy * force * 0.02;
                }
            }
        }

        draw() {
            ctx.save();
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.globalAlpha = Math.max(0.1, Math.min(1, this.currentAlpha));
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 8;
            ctx.fill();
            ctx.restore();
        }
    }

    function init() {
        resize();
        particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push(new Particle());
        }
    }

    function drawConnections() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const p1 = particles[i];
                const p2 = particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < CONNECT_DIST) {
                    const alpha = (1 - dist / CONNECT_DIST) * 0.22;
                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = p1.color;
                    ctx.globalAlpha = alpha;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                    ctx.restore();
                }
            }

            // Mouse connection
            if (mouse.x !== null && mouse.y !== null) {
                const p = particles[i];
                const dx = mouse.x - p.x;
                const dy = mouse.y - p.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < mouse.radius) {
                    const alpha = (1 - dist / mouse.radius) * 0.35;
                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = p.color;
                    ctx.globalAlpha = alpha;
                    ctx.lineWidth = 1;
                    ctx.shadowColor = p.color;
                    ctx.shadowBlur = 6;
                    ctx.stroke();
                    ctx.restore();
                }
            }
        }
    }

    function animate() {
        if (!isVisible) return;

        ctx.clearRect(0, 0, width, height);

        particles.forEach(p => {
            p.update();
            p.draw();
        });

        drawConnections();
        animationId = requestAnimationFrame(animate);
    }

    // Event listeners
    window.addEventListener('resize', () => {
        resize();
    });

    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    window.addEventListener('mouseleave', () => {
        mouse.x = null;
        mouse.y = null;
    });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            isVisible = false;
            if (animationId) cancelAnimationFrame(animationId);
        } else {
            isVisible = true;
            animate();
        }
    });

    init();
    animate();
})();

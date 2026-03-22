/**
 * MEMORIES_CORE.JS
 * - "Freeze & Focus" Entry Animation
 * - 2D Scan Animation (Canvas Sketch)
 * - Soft Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    // initFreezeFocus(); // Removed by user request
    initPaperInteractions();
    initSketchScan();
});

/* --- 1. FREEZE & FOCUS ANIMATION (REMOVED) --- */
function initFreezeFocus() {
    // Removed
}

/* --- 2. PAPER INTERACTIONS (Hover/Click) --- */
function initPaperInteractions() {
    const cards = document.querySelectorAll('.paper-card');

    cards.forEach(card => {
        // Subtle tilt on mouse move
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Very subtle rotation
            const rotateX = ((y - rect.height / 2) / rect.height) * -2;
            const rotateY = ((x - rect.width / 2) / rect.width) * 2;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    });
}

/* --- 3. 2D SKETCH SCAN ANIMATION --- */
function initSketchScan() {
    const scanCanvas = document.getElementById('scan-canvas');
    if (!scanCanvas) return;

    const ctx = scanCanvas.getContext('2d');
    const width = scanCanvas.width = scanCanvas.parentElement.offsetWidth;
    const height = scanCanvas.height = 300;

    let scanLineY = 0;
    let particles = [];

    // Simple Sketchy Line Particle
    class SketchParticle {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.size = Math.random() * 3;
            this.life = 100;
            this.color = `rgba(84, 160, 255, ${Math.random()})`;
        }
        update() {
            this.life -= 2;
            this.y -= Math.random() * 2;
        }
        draw() {
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        // Draw Scan Line (Hand-drawn style)
        ctx.beginPath();
        ctx.moveTo(0, scanLineY);
        ctx.bezierCurveTo(width / 3, scanLineY + 5, width * 2 / 3, scanLineY - 5, width, scanLineY);
        ctx.strokeStyle = '#54a0ff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Particles
        if (Math.random() > 0.8) {
            particles.push(new SketchParticle(Math.random() * width, scanLineY));
        }

        particles.forEach((p, i) => {
            p.update();
            p.draw();
            if (p.life <= 0) particles.splice(i, 1);
        });

        // Move line
        scanLineY += 2;
        if (scanLineY > height) scanLineY = 0;

        requestAnimationFrame(animate);
    }
    animate();
}

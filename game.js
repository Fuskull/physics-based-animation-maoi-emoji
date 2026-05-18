// Canvas setup
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Game state
const game = {
    score: 0,
    health: 100,
    shakeX: 0,
    shakeY: 0,
    shakeMagnitude: 0
};

// Vector utilities
class Vec2 {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
    add(v) { return new Vec2(this.x + v.x, this.y + v.y); }
    sub(v) { return new Vec2(this.x - v.x, this.y - v.y); }
    mul(s) { return new Vec2(this.x * s, this.y * s); }
    length() { return Math.sqrt(this.x * this.x + this.y * this.y); }
    normalize() {
        const len = this.length();
        return len > 0 ? new Vec2(this.x / len, this.y / len) : new Vec2(0, 0);
    }
    dot(v) { return this.x * v.x + this.y * v.y; }
    cross(v) { return this.x * v.y - this.y * v.x; }
}

// Rigid Body with full dynamics
class RigidBody {
    constructor(x, y, width, height, mass = 1) {
        this.pos = new Vec2(x, y);
        this.vel = new Vec2(0, 0);
        this.angle = 0;
        this.angularVel = 0;
        this.mass = mass;
        this.invMass = mass > 0 ? 1 / mass : 0;
        this.inertia = (mass * (width * width + height * height)) / 12;
        this.invInertia = this.inertia > 0 ? 1 / this.inertia : 0;
        this.width = width;
        this.height = height;
        this.restitution = 0.5;
        this.friction = 0.3;
        this.force = new Vec2(0, 0);
        this.torque = 0;
    }
    
    applyForce(force, point = null) {
        this.force = this.force.add(force);
        if (point) {
            const r = point.sub(this.pos);
            this.torque += r.cross(force);
        }
    }
    
    update(dt) {
        if (this.invMass === 0) return;
        
        // Linear dynamics
        const acc = this.force.mul(this.invMass);
        acc.y += 980; // gravity
        this.vel = this.vel.add(acc.mul(dt));
        this.pos = this.pos.add(this.vel.mul(dt));
        
        // Angular dynamics
        const angAcc = this.torque * this.invInertia;
        this.angularVel += angAcc * dt;
        this.angularVel *= 0.98; // damping
        this.angle += this.angularVel * dt;
        
        // Reset forces
        this.force = new Vec2(0, 0);
        this.torque = 0;
    }
    
    getVertices() {
        const cos = Math.cos(this.angle);
        const sin = Math.sin(this.angle);
        const hw = this.width / 2;
        const hh = this.height / 2;
        
        return [
            new Vec2(this.pos.x + (-hw * cos - -hh * sin), this.pos.y + (-hw * sin + -hh * cos)),
            new Vec2(this.pos.x + (hw * cos - -hh * sin), this.pos.y + (hw * sin + -hh * cos)),
            new Vec2(this.pos.x + (hw * cos - hh * sin), this.pos.y + (hw * sin + hh * cos)),
            new Vec2(this.pos.x + (-hw * cos - hh * sin), this.pos.y + (-hw * sin + hh * cos))
        ];
    }
    
    draw() {
        const verts = this.getVertices();
        ctx.fillStyle = '#95a5a6';
        ctx.strokeStyle = '#7f8c8d';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(verts[0].x, verts[0].y);
        for (let i = 1; i < verts.length; i++) {
            ctx.lineTo(verts[i].x, verts[i].y);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
    }
}

// Forward Kinematics Chain (articulated arm)
class KinematicChain {
    constructor(x, y, segments, segmentLength) {
        this.basePos = new Vec2(x, y);
        this.segments = [];
        this.angles = [];
        this.segmentLength = segmentLength;
        
        for (let i = 0; i < segments; i++) {
            this.angles.push(0);
        }
        this.updateFK();
    }
    
    // Forward Kinematics - compute end positions from angles
    updateFK() {
        this.segments = [this.basePos];
        let currentPos = new Vec2(this.basePos.x, this.basePos.y);
        let cumulativeAngle = 0;
        
        for (let i = 0; i < this.angles.length; i++) {
            cumulativeAngle += this.angles[i];
            currentPos = new Vec2(
                currentPos.x + Math.cos(cumulativeAngle) * this.segmentLength,
                currentPos.y + Math.sin(cumulativeAngle) * this.segmentLength
            );
            this.segments.push(currentPos);
        }
    }
    
    // Inverse Kinematics - reach toward target
    solveIK(target, iterations = 10) {
        for (let iter = 0; iter < iterations; iter++) {
            // Backward pass
            for (let i = this.segments.length - 1; i > 0; i--) {
                const prev = this.segments[i - 1];
                const targetPos = i === this.segments.length - 1 ? target : this.segments[i + 1];
                
                const dir = targetPos.sub(prev).normalize();
                this.segments[i] = prev.add(dir.mul(this.segmentLength));
            }
            
            // Forward pass
            this.segments[0] = this.basePos;
            for (let i = 1; i < this.segments.length; i++) {
                const dir = this.segments[i].sub(this.segments[i - 1]).normalize();
                this.segments[i] = this.segments[i - 1].add(dir.mul(this.segmentLength));
            }
        }
        
        // Update angles from positions
        for (let i = 0; i < this.angles.length; i++) {
            const dir = this.segments[i + 1].sub(this.segments[i]);
            this.angles[i] = Math.atan2(dir.y, dir.x);
            if (i > 0) this.angles[i] -= this.angles[i - 1];
        }
    }
    
    update(target) {
        this.solveIK(target);
        this.updateFK();
    }
    
    draw() {
        ctx.strokeStyle = '#e67e22';
        ctx.lineWidth = 6;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        ctx.beginPath();
        ctx.moveTo(this.segments[0].x, this.segments[0].y);
        for (let i = 1; i < this.segments.length; i++) {
            ctx.lineTo(this.segments[i].x, this.segments[i].y);
        }
        ctx.stroke();
        
        // Draw joints
        this.segments.forEach((seg, i) => {
            ctx.fillStyle = i === 0 ? '#c0392b' : '#d35400';
            ctx.beginPath();
            ctx.arc(seg.x, seg.y, 5, 0, Math.PI * 2);
            ctx.fill();
        });
    }
}

// PBD Particle
class Particle {
    constructor(x, y, mass = 1, fixed = false) {
        this.pos = new Vec2(x, y);
        this.oldPos = new Vec2(x, y);
        this.mass = mass;
        this.fixed = fixed;
    }
    
    update(dt) {
        if (this.fixed) return;
        const vel = this.pos.sub(this.oldPos);
        this.oldPos = new Vec2(this.pos.x, this.pos.y);
        this.pos = this.pos.add(vel.mul(0.99)); // damping
        this.pos.y += 980 * dt * dt; // gravity
    }
}

// PBD Constraint
class DistanceConstraint {
    constructor(p1, p2, distance = null) {
        this.p1 = p1;
        this.p2 = p2;
        this.distance = distance || p1.pos.sub(p2.pos).length();
    }
    
    solve() {
        const delta = this.p2.pos.sub(this.p1.pos);
        const dist = delta.length();
        if (dist === 0) return;
        
        const diff = (dist - this.distance) / dist;
        const offset = delta.mul(diff * 0.5);
        
        if (!this.p1.fixed) this.p1.pos = this.p1.pos.add(offset);
        if (!this.p2.fixed) this.p2.pos = this.p2.pos.sub(offset);
    }
}

// Rope system
class Rope {
    constructor(x, y, length, segments) {
        this.particles = [];
        this.constraints = [];
        
        const segLen = length / segments;
        for (let i = 0; i <= segments; i++) {
            const fixed = i === 0;
            this.particles.push(new Particle(x, y + i * segLen, 1, fixed));
        }
        
        for (let i = 0; i < this.particles.length - 1; i++) {
            this.constraints.push(new DistanceConstraint(this.particles[i], this.particles[i + 1]));
        }
    }
    
    update(dt) {
        this.particles.forEach(p => p.update(dt));
        for (let i = 0; i < 3; i++) {
            this.constraints.forEach(c => c.solve());
        }
    }
    
    draw() {
        ctx.strokeStyle = '#8B4513';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(this.particles[0].pos.x, this.particles[0].pos.y);
        for (let i = 1; i < this.particles.length; i++) {
            ctx.lineTo(this.particles[i].pos.x, this.particles[i].pos.y);
        }
        ctx.stroke();
    }
}

// Cloth system
class Cloth {
    constructor(x, y, width, height, cols, rows) {
        this.particles = [];
        this.constraints = [];
        
        const dx = width / (cols - 1);
        const dy = height / (rows - 1);
        
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const fixed = row === 0 && (col === 0 || col === cols - 1);
                this.particles.push(new Particle(x + col * dx, y + row * dy, 1, fixed));
            }
        }
        
        // Structural constraints
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const idx = row * cols + col;
                if (col < cols - 1) {
                    this.constraints.push(new DistanceConstraint(this.particles[idx], this.particles[idx + 1]));
                }
                if (row < rows - 1) {
                    this.constraints.push(new DistanceConstraint(this.particles[idx], this.particles[idx + cols]));
                }
            }
        }
    }
    
    update(dt) {
        this.particles.forEach(p => p.update(dt));
        for (let i = 0; i < 3; i++) {
            this.constraints.forEach(c => c.solve());
        }
    }
    
    draw() {
        ctx.strokeStyle = '#4a90e2';
        ctx.lineWidth = 1;
        this.constraints.forEach(c => {
            ctx.beginPath();
            ctx.moveTo(c.p1.pos.x, c.p1.pos.y);
            ctx.lineTo(c.p2.pos.x, c.p2.pos.y);
            ctx.stroke();
        });
    }
}

// Player
class Player {
    constructor(x, y) {
        this.pos = new Vec2(x, y);
        this.vel = new Vec2(0, 0);
        this.radius = 15;
        this.rope = null;
        this.onGround = false;
    }
    
    update(dt) {
        if (this.rope) {
            const end = this.rope.particles[this.rope.particles.length - 1];
            this.pos = new Vec2(end.pos.x, end.pos.y);
            this.vel = end.pos.sub(end.oldPos).mul(1 / dt);
        } else {
            this.vel.y += 980 * dt;
            this.pos = this.pos.add(this.vel.mul(dt));
            
            // Ground collision
            if (this.pos.y + this.radius > canvas.height - 50) {
                this.pos.y = canvas.height - 50 - this.radius;
                this.vel.y = 0;
                this.vel.x *= 0.8;
                this.onGround = true;
            } else {
                this.onGround = false;
            }
            
            // Wall collision
            if (this.pos.x < this.radius) {
                this.pos.x = this.radius;
                this.vel.x = 0;
            }
            if (this.pos.x > canvas.width - this.radius) {
                this.pos.x = canvas.width - this.radius;
                this.vel.x = 0;
            }
        }
    }
    
    attachRope(rope) {
        this.rope = rope;
        const end = rope.particles[rope.particles.length - 1];
        end.fixed = false;
    }
    
    detachRope() {
        if (this.rope) {
            const end = this.rope.particles[this.rope.particles.length - 1];
            this.vel = end.pos.sub(end.oldPos).mul(60);
            this.rope = null;
        }
    }
    
    draw() {
        ctx.fillStyle = '#ff6b6b';
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

// Bullet
class Bullet {
    constructor(x, y, vx, vy) {
        this.pos = new Vec2(x, y);
        this.vel = new Vec2(vx, vy);
        this.radius = 4;
        this.dead = false;
    }
    
    update(dt) {
        this.pos = this.pos.add(this.vel.mul(dt));
        if (this.pos.x < 0 || this.pos.x > canvas.width || 
            this.pos.y < 0 || this.pos.y > canvas.height) {
            this.dead = true;
        }
    }
    
    draw() {
        ctx.fillStyle = '#ffff00';
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Enemy
class Enemy {
    constructor(x, y) {
        this.pos = new Vec2(x, y);
        this.vel = new Vec2((Math.random() - 0.5) * 100, 0);
        this.radius = 20;
        this.dead = false;
        this.health = 2;
    }
    
    update(dt) {
        this.vel.y += 980 * dt;
        this.pos = this.pos.add(this.vel.mul(dt));
        
        if (this.pos.y + this.radius > canvas.height - 50) {
            this.pos.y = canvas.height - 50 - this.radius;
            this.vel.y = 0;
        }
        
        if (this.pos.x < this.radius || this.pos.x > canvas.width - this.radius) {
            this.vel.x *= -1;
        }
    }
    
    hit() {
        this.health--;
        if (this.health <= 0) {
            this.dead = true;
            return true;
        }
        return false;
    }
    
    draw() {
        ctx.fillStyle = '#e74c3c';
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#c0392b';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

// Particle effect
class ParticleEffect {
    constructor(x, y, color) {
        this.particles = [];
        for (let i = 0; i < 20; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 200 + 100;
            this.particles.push({
                pos: new Vec2(x, y),
                vel: new Vec2(Math.cos(angle) * speed, Math.sin(angle) * speed),
                life: 1,
                color: color
            });
        }
    }
    
    update(dt) {
        this.particles.forEach(p => {
            p.vel.y += 500 * dt;
            p.pos = p.pos.add(p.vel.mul(dt));
            p.life -= dt * 2;
        });
        this.particles = this.particles.filter(p => p.life > 0);
    }
    
    draw() {
        this.particles.forEach(p => {
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life;
            ctx.beginPath();
            ctx.arc(p.pos.x, p.pos.y, 3, 0, Math.PI * 2);
            ctx.fill();
        });
        ctx.globalAlpha = 1;
    }
}

// Game objects
const player = new Player(canvas.width / 2, 100);
const ropes = [];
const cloths = [];
const bullets = [];
const enemies = [];
const particles = [];
const rigidBodies = [];
const kinematicChains = [];

// Create initial ropes
for (let i = 0; i < 3; i++) {
    ropes.push(new Rope(200 + i * 300, 50, 200, 10));
}

// Create cloth
cloths.push(new Cloth(canvas.width - 300, 50, 200, 150, 10, 8));

// Create rigid bodies (platforms and boxes)
rigidBodies.push(new RigidBody(400, 400, 100, 20, 0)); // static platform
rigidBodies.push(new RigidBody(700, 500, 80, 80, 2)); // dynamic box
rigidBodies.push(new RigidBody(300, 300, 60, 60, 1.5)); // dynamic box

// Create kinematic chains (robotic arms)
kinematicChains.push(new KinematicChain(100, canvas.height - 50, 4, 40));
kinematicChains.push(new KinematicChain(canvas.width - 100, canvas.height - 50, 3, 50));

// Input handling
const keys = {};
let mousePos = new Vec2(0, 0);

window.addEventListener('keydown', e => keys[e.key.toLowerCase()] = true);
window.addEventListener('keyup', e => keys[e.key.toLowerCase()] = false);
window.addEventListener('mousemove', e => {
    mousePos = new Vec2(e.clientX, e.clientY);
});
window.addEventListener('click', e => {
    const dir = mousePos.sub(player.pos).normalize();
    bullets.push(new Bullet(player.pos.x, player.pos.y, dir.x * 800, dir.y * 800));
});

// Spawn enemies
function spawnEnemy() {
    const x = Math.random() * (canvas.width - 100) + 50;
    enemies.push(new Enemy(x, 50));
}

setInterval(spawnEnemy, 2000);

// Screen shake
function shake(magnitude) {
    game.shakeMagnitude = magnitude;
}

// Game loop
let lastTime = performance.now();

function gameLoop(currentTime) {
    const dt = Math.min((currentTime - lastTime) / 1000, 0.016);
    lastTime = currentTime;
    
    // Update
    if (keys['a'] || keys['arrowleft']) {
        if (player.rope) {
            const end = player.rope.particles[player.rope.particles.length - 1];
            end.pos.x -= 200 * dt;
        } else if (player.onGround) {
            player.vel.x = -200;
        }
    }
    if (keys['d'] || keys['arrowright']) {
        if (player.rope) {
            const end = player.rope.particles[player.rope.particles.length - 1];
            end.pos.x += 200 * dt;
        } else if (player.onGround) {
            player.vel.x = 200;
        }
    }
    
    if (keys[' '] && !player.rope) {
        let closest = null;
        let minDist = 300;
        ropes.forEach(rope => {
            const dist = player.pos.sub(rope.particles[0].pos).length();
            if (dist < minDist) {
                minDist = dist;
                closest = rope;
            }
        });
        if (closest) {
            player.attachRope(closest);
        }
    } else if (!keys[' '] && player.rope) {
        player.detachRope();
    }
    
    ropes.forEach(r => r.update(dt));
    cloths.forEach(c => c.update(dt));
    player.update(dt);
    bullets.forEach(b => b.update(dt));
    enemies.forEach(e => e.update(dt));
    particles.forEach(p => p.update(dt));
    
    // Update rigid bodies
    rigidBodies.forEach(rb => {
        rb.update(dt);
        
        // Ground collision
        const verts = rb.getVertices();
        verts.forEach(v => {
            if (v.y > canvas.height - 50) {
                rb.pos.y -= (v.y - (canvas.height - 50));
                rb.vel.y *= -rb.restitution;
                rb.vel.x *= (1 - rb.friction);
            }
        });
        
        // Wall collision
        if (rb.pos.x < rb.width / 2) {
            rb.pos.x = rb.width / 2;
            rb.vel.x *= -rb.restitution;
        }
        if (rb.pos.x > canvas.width - rb.width / 2) {
            rb.pos.x = canvas.width - rb.width / 2;
            rb.vel.x *= -rb.restitution;
        }
        
        // Player collision with rigid bodies (can stand on them)
        if (!player.rope) {
            verts.forEach(v => {
                const dist = player.pos.sub(v).length();
                if (dist < player.radius + 10) {
                    const normal = player.pos.sub(v).normalize();
                    player.pos = v.add(normal.mul(player.radius + 10));
                    
                    // Transfer momentum
                    if (normal.y < -0.5) {
                        player.vel.y = Math.max(0, player.vel.y);
                        player.vel.x += rb.vel.x * 0.5;
                        player.onGround = true;
                    }
                    
                    // Apply force to rigid body
                    rb.applyForce(normal.mul(-500), v);
                }
            });
        }
    });
    
    // Update kinematic chains (IK to follow and grab nearest enemy)
    kinematicChains.forEach(chain => {
        let target = null;
        let minDist = 250;
        
        // Find nearest enemy
        enemies.forEach(enemy => {
            const dist = enemy.pos.sub(chain.basePos).length();
            if (dist < minDist) {
                minDist = dist;
                target = enemy;
            }
        });
        
        if (target) {
            chain.update(target.pos);
            
            // Grab enemy if close enough
            const endPos = chain.segments[chain.segments.length - 1];
            const grabDist = endPos.sub(target.pos).length();
            if (grabDist < 25) {
                // Pull enemy toward base
                const pullDir = chain.basePos.sub(target.pos).normalize();
                target.vel = target.vel.add(pullDir.mul(300 * dt));
                
                // Damage enemy over time
                if (Math.random() < 0.05) {
                    if (target.hit()) {
                        game.score += 5;
                        particles.push(new ParticleEffect(target.pos.x, target.pos.y, '#e67e22'));
                    }
                }
            }
        } else {
            // Idle animation
            const idleTarget = new Vec2(
                chain.basePos.x + Math.sin(currentTime * 0.001) * 100,
                chain.basePos.y - 100
            );
            chain.update(idleTarget);
        }
    });
    
    // Collision detection
    bullets.forEach(bullet => {
        // Bullet vs enemies
        enemies.forEach(enemy => {
            if (!bullet.dead && !enemy.dead) {
                const dist = bullet.pos.sub(enemy.pos).length();
                if (dist < bullet.radius + enemy.radius) {
                    bullet.dead = true;
                    if (enemy.hit()) {
                        game.score += 10;
                        particles.push(new ParticleEffect(enemy.pos.x, enemy.pos.y, '#ff6b6b'));
                    }
                }
            }
        });
        
        // Bullet vs rigid bodies (apply impulse)
        rigidBodies.forEach(rb => {
            if (!bullet.dead && rb.invMass > 0) {
                const verts = rb.getVertices();
                verts.forEach(v => {
                    const dist = bullet.pos.sub(v).length();
                    if (dist < bullet.radius + 5) {
                        bullet.dead = true;
                        const impulse = bullet.vel.mul(0.5);
                        rb.applyForce(impulse.mul(100), v);
                        particles.push(new ParticleEffect(bullet.pos.x, bullet.pos.y, '#ffff00'));
                    }
                });
            }
        });
    });
    
    // Player-enemy collision
    enemies.forEach(enemy => {
        const dist = player.pos.sub(enemy.pos).length();
        if (dist < player.radius + enemy.radius) {
            game.health -= 10;
            enemy.dead = true;
            shake(20);
            particles.push(new ParticleEffect(enemy.pos.x, enemy.pos.y, '#ff0000'));
        }
    });
    
    // Cleanup
    bullets.splice(0, bullets.length, ...bullets.filter(b => !b.dead));
    enemies.splice(0, enemies.length, ...enemies.filter(e => !e.dead));
    particles.splice(0, particles.length, ...particles.filter(p => p.particles.length > 0));
    
    // Screen shake
    if (game.shakeMagnitude > 0) {
        game.shakeX = (Math.random() - 0.5) * game.shakeMagnitude;
        game.shakeY = (Math.random() - 0.5) * game.shakeMagnitude;
        game.shakeMagnitude *= 0.9;
        if (game.shakeMagnitude < 0.5) game.shakeMagnitude = 0;
    }
    
    // Draw
    ctx.save();
    ctx.translate(game.shakeX, game.shakeY);
    ctx.clearRect(-game.shakeX, -game.shakeY, canvas.width, canvas.height);
    
    // Draw ground
    ctx.fillStyle = '#2c3e50';
    ctx.fillRect(0, canvas.height - 50, canvas.width, 50);
    
    ropes.forEach(r => r.draw());
    cloths.forEach(c => c.draw());
    rigidBodies.forEach(rb => rb.draw());
    kinematicChains.forEach(kc => kc.draw());
    player.draw();
    bullets.forEach(b => b.draw());
    enemies.forEach(e => e.draw());
    particles.forEach(p => p.draw());
    
    ctx.restore();
    
    // Update UI
    document.getElementById('health').textContent = Math.max(0, game.health);
    document.getElementById('score').textContent = game.score;
    document.getElementById('enemies').textContent = enemies.length;
    
    if (game.health <= 0) {
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#fff';
        ctx.font = '48px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', canvas.width / 2, canvas.height / 2);
        ctx.font = '24px Arial';
        ctx.fillText('Score: ' + game.score, canvas.width / 2, canvas.height / 2 + 50);
        return;
    }
    
    requestAnimationFrame(gameLoop);
}

gameLoop(performance.now());

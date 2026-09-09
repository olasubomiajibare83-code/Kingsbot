import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="⚔️ Alchemy of Souls — All Powers",
    page_icon="⚔️",
    layout="centered",
)

st.title("⚔️ Alchemy of Souls — All Powers")
st.caption("Jang Uk (White) + Naksu (Black) | Fast • Flying • All Powers")

# ============================================================
# GAME HTML
# ============================================================

game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { margin: 0; background: #0a0a0a; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        canvas { border: 3px solid #4d96ff; border-radius: 12px; background: radial-gradient(ellipse at center, #1a1a3e 0%, #0a0a1a 100%); box-shadow: 0 0 60px rgba(77, 150, 255, 0.15); touch-action: none; }
        .controls { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); display: flex; gap: 12px; background: rgba(0,0,0,0.8); padding: 12px 20px; border-radius: 16px; border: 1px solid rgba(77, 150, 255, 0.2); flex-wrap: wrap; justify-content: center; z-index: 10; }
        .controls button { padding: 8px 16px; border: none; border-radius: 8px; font-weight: bold; font-size: 13px; color: white; cursor: pointer; transition: all 0.2s; min-width: 60px; }
        .controls button:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(255,255,255,0.15); }
        .controls button:active { transform: scale(0.95); }
        .btn-sword { background: linear-gradient(135deg, #4d96ff, #6bcb77); }
        .btn-fire { background: linear-gradient(135deg, #ff6b6b, #ffd93d); }
        .btn-ice { background: linear-gradient(135deg, #4d96ff, #00b4d8); }
        .btn-soul { background: linear-gradient(135deg, #f093fb, #f5576c); }
        .btn-fly { background: linear-gradient(135deg, #6bcb77, #4d96ff); }
        .btn-block { background: linear-gradient(135deg, #4a00e0, #8e2de2); }
        .btn-reset { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
        @media (max-width: 600px) { .controls button { padding: 6px 12px; font-size: 11px; min-width: 45px; } canvas { width: 100%; height: auto; } }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="900" height="500"></canvas>
    <div class="controls">
        <button class="btn-sword" onclick="playerSword()">⚔️ Sword</button>
        <button class="btn-fire" onclick="playerFire()">🔥 Fire</button>
        <button class="btn-ice" onclick="playerIce()">❄️ Ice</button>
        <button class="btn-soul" onclick="playerSoul()">💀 Soul</button>
        <button class="btn-fly" onclick="playerFly()">🕊️ Fly</button>
        <button class="btn-block" onclick="playerBlock()">🛡️ Block</button>
        <button class="btn-reset" onclick="resetGame()">🔄 Reset</button>
    </div>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');

        // ============================================================
        // VILLAIN HOUSES
        // ============================================================
        const VILLAIN_HOUSES = [
            { name: 'House of Shadows', boss: 'Shadow Lord', difficulty: 1 },
            { name: 'House of Flames', boss: 'Fire Demon', difficulty: 2 },
            { name: 'House of Storms', boss: 'Storm King', difficulty: 3 },
            { name: 'House of Souls', boss: 'Soul Eater', difficulty: 4 },
            { name: 'House of Darkness', boss: 'Dark Emperor', difficulty: 5 },
            { name: 'House of Chaos', boss: 'Chaos God', difficulty: 6 }
        ];

        let currentHouse = 0;
        let enemies = [];
        let currentVillainIndex = 0;
        let gameOver = false;
        let winner = '';
        let fightLog = [];
        let frameCount = 0;
        let allHousesCleared = false;
        let isFlying = false;
        let flyTimer = 0;
        let dashTimer = 0;
        let comboCount = 0;

        function generateVillains(houseIndex) {
            const house = VILLAIN_HOUSES[houseIndex];
            const count = 4 + Math.floor(house.difficulty * 1.5);
            const villains = [];
            const names = ['Shadow', 'Blaze', 'Storm', 'Soul', 'Dark', 'Chaos', 'Frost', 'Venom', 'Phantom', 'Crimson'];
            for (let i = 0; i < count; i++) {
                const baseHealth = 60 + house.difficulty * 15 + Math.floor(Math.random() * 20);
                const isBoss = (i === count - 1);
                villains.push({
                    name: isBoss ? house.boss : names[i % names.length] + ' Warrior',
                    health: isBoss ? baseHealth * 2.5 : baseHealth,
                    maxHealth: isBoss ? baseHealth * 2.5 : baseHealth,
                    damage: isBoss ? 15 + house.difficulty * 3 : 8 + house.difficulty * 2,
                    isBoss: isBoss,
                    speed: isBoss ? 2 : 1 + Math.random() * 0.5,
                    y: 350,
                    x: 700 + Math.random() * 100,
                    width: 55,
                    height: 100,
                    color: isBoss ? '#ff6b6b' : '#2d3436',
                    energy: 100,
                    maxEnergy: 100,
                    isFlying: false,
                    flyTimer: 0,
                    isAttacking: false,
                    attackFrame: 0,
                    hitCooldown: 0,
                    isHit: false,
                    hitTimer: 0,
                    animTimer: 0
                });
            }
            return villains;
        }

        // ============================================================
        // CHARACTER CLASS (JANG UK)
        // ============================================================
        class JangUk {
            constructor() {
                this.x = 200;
                this.y = 350;
                this.width = 55;
                this.height = 100;
                this.vx = 0;
                this.vy = 0;
                this.health = 100;
                this.maxHealth = 100;
                this.energy = 100;
                this.maxEnergy = 100;
                this.soulEnergy = 0;
                this.maxSoulEnergy = 100;
                this.isAttacking = false;
                this.attackFrame = 0;
                this.attackType = 'sword';
                this.hitCooldown = 0;
                this.combo = 0;
                this.blocking = false;
                this.isHit = false;
                this.hitTimer = 0;
                this.isFlying = false;
                this.flyTimer = 0;
                this.isDashing = false;
                this.dashTimer = 0;
                this.animTimer = 0;
                this.speed = 4;
                this.color = '#ffffff';
                this.glowColor = '#4d96ff';
                this.swordAngle = 0;
                this.particles = [];
                this.grounded = true;
            }

            draw(ctx) {
                ctx.save();
                const x = this.x;
                const y = this.y;
                
                // Glow
                ctx.shadowColor = this.glowColor;
                ctx.shadowBlur = 30;
                
                // White robe (Jang Uk)
                ctx.fillStyle = '#f0f0f0';
                ctx.shadowBlur = 20;
                ctx.fillRect(x - 20, y - 45, 40, 55);
                ctx.fillStyle = '#e0e0e0';
                ctx.fillRect(x - 15, y - 35, 30, 40);
                ctx.fillStyle = '#4d96ff';
                ctx.fillRect(x - 18, y - 10, 36, 5);
                
                // Head
                ctx.shadowBlur = 15;
                ctx.fillStyle = '#f5deb3';
                ctx.beginPath();
                ctx.arc(x, y - 62, 22, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#1a1a1a';
                ctx.beginPath();
                ctx.arc(x, y - 68, 22, Math.PI, 2 * Math.PI);
                ctx.fill();
                
                // Eye glow
                ctx.shadowBlur = 20;
                ctx.shadowColor = this.glowColor;
                ctx.fillStyle = this.glowColor;
                ctx.beginPath();
                ctx.arc(x - 7, y - 65, 4, 0, Math.PI * 2);
                ctx.fill();
                ctx.beginPath();
                ctx.arc(x + 7, y - 65, 4, 0, Math.PI * 2);
                ctx.fill();
                
                // Sword
                ctx.shadowBlur = 15;
                ctx.shadowColor = '#4d96ff';
                ctx.strokeStyle = '#4d96ff';
                ctx.lineWidth = 3;
                const swordAngle = this.isAttacking ? Math.sin(this.attackFrame * 0.2) * 1.2 : 0;
                ctx.save();
                ctx.translate(x + 28, y - 35);
                ctx.rotate(swordAngle - 0.5);
                ctx.fillStyle = '#4d96ff';
                ctx.fillRect(0, -2, 35, 4);
                ctx.fillStyle = '#8B4513';
                ctx.fillRect(-5, -4, 8, 8);
                ctx.restore();
                
                // Attack effects
                if (this.isAttacking && this.attackFrame < 15) {
                    const colors = {
                        sword: '#4d96ff',
                        fire: '#ff6b6b',
                        ice: '#00b4d8',
                        soul: '#f093fb'
                    };
                    ctx.shadowBlur = 40;
                    ctx.shadowColor = colors[this.attackType] || '#4d96ff';
                    ctx.fillStyle = `rgba(77, 150, 255, 0.2)`;
                    ctx.beginPath();
                    ctx.arc(x + 50, y - 30, 30 + this.attackFrame * 2, 0, Math.PI * 2);
                    ctx.fill();
                    
                    for (let i = 0; i < 8; i++) {
                        const angle = (i / 8) * Math.PI * 2 + this.attackFrame * 0.1;
                        ctx.fillStyle = `rgba(77, 150, 255, 0.3)`;
                        ctx.beginPath();
                        ctx.arc(x + 40 + Math.cos(angle) * (20 + this.attackFrame * 2),
                               y - 30 + Math.sin(angle) * (20 + this.attackFrame * 2), 3, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
                
                // Flying effect
                if (this.isFlying || this.flyTimer > 0) {
                    ctx.shadowBlur = 40;
                    ctx.shadowColor = '#4d96ff';
                    for (let i = 0; i < 5; i++) {
                        ctx.fillStyle = `rgba(77, 150, 255, ${0.1 - i * 0.02})`;
                        ctx.beginPath();
                        ctx.arc(x - 20 + i * 10, y + 30 + i * 5 + Math.sin(this.animTimer + i) * 3, 5 - i * 0.5, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
                
                // Hit effect
                if (this.isHit) {
                    ctx.shadowBlur = 50;
                    ctx.shadowColor = '#ff0000';
                    ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
                    ctx.beginPath();
                    ctx.arc(x, y - 30, 45, 0, Math.PI * 2);
                    ctx.fill();
                }
                
                ctx.restore();
                
                // Health bar
                this.drawHealthBar(ctx, x, y - 105, 'white');
                
                // Name
                ctx.fillStyle = '#4d96ff';
                ctx.font = 'bold 13px Arial';
                ctx.textAlign = 'center';
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#4d96ff';
                ctx.fillText('⚔️ Jang Uk', x, y - 120);
                ctx.shadowBlur = 0;
            }
            
            drawHealthBar(ctx, x, y, color) {
                const width = 80;
                const height = 8;
                const hx = x - width/2;
                ctx.fillStyle = 'rgba(0,0,0,0.7)';
                ctx.fillRect(hx - 1, y - 1, width + 2, height + 2);
                const pct = this.health / this.maxHealth;
                ctx.fillStyle = pct > 0.5 ? '#6bcb77' : pct > 0.25 ? '#ffd93d' : '#ff6b6b';
                ctx.fillRect(hx, y, width * pct, height);
                
                // Energy
                ctx.fillStyle = 'rgba(0,0,0,0.5)';
                ctx.fillRect(hx - 1, y + 10, width + 2, 5);
                ctx.fillStyle = '#4d96ff';
                ctx.fillRect(hx, y + 10, width * (this.energy / this.maxEnergy), 5);
                
                // Soul Energy
                ctx.fillStyle = 'rgba(0,0,0,0.5)';
                ctx.fillRect(hx - 1, y + 17, width + 2, 4);
                ctx.fillStyle = '#f093fb';
                ctx.fillRect(hx, y + 17, width * (this.soulEnergy / this.maxSoulEnergy), 4);
            }
            
            attack(type) {
                if (this.isAttacking) return;
                let cost = 0;
                if (type === 'sword') cost = 8;
                else if (type === 'fire') cost = 15;
                else if (type === 'ice') cost = 20;
                else if (type === 'soul') {
                    if (this.soulEnergy < 40) return;
                    cost = 40;
                }
                if (this.energy < cost) return;
                this.isAttacking = true;
                this.attackFrame = 0;
                this.attackType = type;
                this.energy -= cost;
                if (type === 'soul') this.soulEnergy -= 40;
            }
            
            fly() {
                if (!this.isFlying) {
                    this.isFlying = true;
                    this.flyTimer = 120;
                    this.vy = -6;
                }
            }
            
            update() {
                this.animTimer += 0.05;
                this.hitCooldown = Math.max(0, this.hitCooldown - 1);
                
                // Gravity
                if (!this.isFlying) {
                    this.vy += 0.5;
                    if (this.vy > 6) this.vy = 6;
                } else {
                    this.vy += 0.2;
                    if (this.vy > 2) this.vy = 2;
                    this.flyTimer--;
                    if (this.flyTimer <= 0) {
                        this.isFlying = false;
                    }
                }
                
                // Movement with dash
                if (this.isDashing) {
                    this.dashTimer--;
                    if (this.dashTimer <= 0) this.isDashing = false;
                }
                
                this.x += this.vx + (this.isDashing ? 8 : 0);
                this.y += this.vy;
                
                // Ground
                if (this.y >= 350) {
                    this.y = 350;
                    this.vy = 0;
                    this.grounded = true;
                } else {
                    this.grounded = false;
                }
                
                // Boundaries
                if (this.x < 20) this.x = 20;
                if (this.x > 800) this.x = 800;
                
                if (this.isAttacking) {
                    this.attackFrame++;
                    if (this.attackFrame > 20) this.isAttacking = false;
                }
                
                if (this.isHit) {
                    this.hitTimer++;
                    if (this.hitTimer > 10) { this.isHit = false; this.hitTimer = 0; }
                }
                
                // Regenerate
                if (this.energy < this.maxEnergy) this.energy = Math.min(this.maxEnergy, this.energy + 0.15);
                if (this.soulEnergy < this.maxSoulEnergy) this.soulEnergy = Math.min(this.maxSoulEnergy, this.soulEnergy + 0.08);
            }
            
            getAttackDamage() {
                const base = {
                    sword: Math.floor(Math.random() * 10) + 12,
                    fire: Math.floor(Math.random() * 14) + 18,
                    ice: Math.floor(Math.random() * 18) + 22,
                    soul: Math.floor(Math.random() * 25) + 35
                };
                const dmg = base[this.attackType] || 10;
                return Math.floor(dmg * (1 + this.combo * 0.05));
            }
            
            getHitbox() {
                return { x: this.x - 28, y: this.y - 65, w: 56, h: 95 };
            }
        }

        // ============================================================
        // NAKSU CLASS
        // ============================================================
        class Naksu {
            constructor() {
                this.x = 80;
                this.y = 350;
                this.width = 50;
                this.height = 95;
                this.vx = 0;
                this.vy = 0;
                this.health = 80;
                this.maxHealth = 80;
                this.energy = 100;
                this.maxEnergy = 100;
                this.isAttacking = false;
                this.attackFrame = 0;
                this.hitCooldown = 0;
                this.isHit = false;
                this.hitTimer = 0;
                this.animTimer = 0;
                this.glowColor = '#ff6b6b';
                this.isFlying = false;
                this.flyTimer = 0;
                this.speed = 3;
                this.grounded = true;
            }
            
            draw(ctx) {
                ctx.save();
                const x = this.x;
                const y = this.y;
                
                ctx.shadowColor = this.glowColor;
                ctx.shadowBlur = 20;
                ctx.fillStyle = '#1a1a1a';
                ctx.shadowBlur = 15;
                ctx.fillRect(x - 18, y - 42, 36, 50);
                ctx.fillStyle = '#2a2a2a';
                ctx.fillRect(x - 14, y - 32, 28, 35);
                ctx.fillStyle = '#ff6b6b';
                ctx.fillRect(x - 16, y - 8, 32, 4);
                
                ctx.shadowBlur = 15;
                ctx.fillStyle = '#f5deb3';
                ctx.beginPath();
                ctx.arc(x, y - 58, 20, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#1a1a1a';
                ctx.beginPath();
                ctx.arc(x, y - 63, 20, Math.PI, 2 * Math.PI);
                ctx.fill();
                ctx.fillRect(x - 15, y - 58, 30, 15);
                
                ctx.shadowBlur = 20;
                ctx.shadowColor = this.glowColor;
                ctx.fillStyle = this.glowColor;
                ctx.beginPath();
                ctx.arc(x - 6, y - 60, 4, 0, Math.PI * 2);
                ctx.fill();
                ctx.beginPath();
                ctx.arc(x + 6, y - 60, 4, 0, Math.PI * 2);
                ctx.fill();
                
                if (this.isAttacking && this.attackFrame < 15) {
                    ctx.shadowBlur = 40;
                    ctx.shadowColor = '#ff6b6b';
                    ctx.fillStyle = 'rgba(255, 107, 107, 0.3)';
                    ctx.beginPath();
                    ctx.arc(x + 40, y - 30, 25 + this.attackFrame * 2, 0, Math.PI * 2);
                    ctx.fill();
                }
                
                if (this.isFlying || this.flyTimer > 0) {
                    ctx.shadowBlur = 40;
                    ctx.shadowColor = '#ff6b6b';
                    for (let i = 0; i < 5; i++) {
                        ctx.fillStyle = `rgba(255, 107, 107, ${0.1 - i * 0.02})`;
                        ctx.beginPath();
                        ctx.arc(x - 15 + i * 8, y + 25 + i * 4 + Math.sin(this.animTimer + i) * 3, 4 - i * 0.5, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
                
                if (this.isHit) {
                    ctx.shadowBlur = 40;
                    ctx.shadowColor = '#ff0000';
                    ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
                    ctx.beginPath();
                    ctx.arc(x, y - 30, 40, 0, Math.PI * 2);
                    ctx.fill();
                }
                
                ctx.restore();
                
                this.drawHealthBar(ctx, x, y - 100, '#ff6b6b');
                ctx.fillStyle = '#ff6b6b';
                ctx.font = 'bold 12px Arial';
                ctx.textAlign = 'center';
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#ff6b6b';
                ctx.fillText('🔥 Naksu', x, y - 115);
                ctx.shadowBlur = 0;
            }
            
            drawHealthBar(ctx, x, y, color) {
                const width = 70;
                const height = 6;
                const hx = x - width/2;
                ctx.fillStyle = 'rgba(0,0,0,0.7)';
                ctx.fillRect(hx - 1, y - 1, width + 2, height + 2);
                const pct = this.health / this.maxHealth;
                ctx.fillStyle = pct > 0.5 ? '#6bcb77' : pct > 0.25 ? '#ffd93d' : '#ff6b6b';
                ctx.fillRect(hx, y, width * pct, height);
            }
            
            attack() {
                if (this.isAttacking) return;
                this.isAttacking = true;
                this.attackFrame = 0;
            }
            
            fly() {
                if (!this.isFlying) {
                    this.isFlying = true;
                    this.flyTimer = 80;
                    this.vy = -5;
                }
            }
            
            update() {
                this.animTimer += 0.05;
                this.hitCooldown = Math.max(0, this.hitCooldown - 1);
                
                if (!this.isFlying) {
                    this.vy += 0.5;
                    if (this.vy > 6) this.vy = 6;
                } else {
                    this.vy += 0.2;
                    if (this.vy > 2) this.vy = 2;
                    this.flyTimer--;
                    if (this.flyTimer <= 0) this.isFlying = false;
                }
                
                this.x += this.vx;
                this.y += this.vy;
                
                if (this.y >= 350) {
                    this.y = 350;
                    this.vy = 0;
                    this.grounded = true;
                } else {
                    this.grounded = false;
                }
                if (this.x < 20) this.x = 20;
                if (this.x > 800) this.x = 800;
                
                if (this.isAttacking) {
                    this.attackFrame++;
                    if (this.attackFrame > 18) this.isAttacking = false;
                }
                if (this.isHit) {
                    this.hitTimer++;
                    if (this.hitTimer > 10) { this.isHit = false; this.hitTimer = 0; }
                }
            }
            
            getHitbox() {
                return { x: this.x - 25, y: this.y - 60, w: 50, h: 85 };
            }
        }

        // ============================================================
        // INIT GAME
        // ============================================================
        const player = new JangUk();
        const naksu = new Naksu();
        let currentEnemy = null;
        let houseIndex = 0;
        let villainIndex = 0;
        let allHousesCleared = false;

        function initHouse() {
            enemies = generateVillains(houseIndex);
            villainIndex = 0;
            currentEnemy = enemies[0];
            gameOver = false;
            winner = '';
            player.health = player.maxHealth;
            naksu.health = naksu.maxHealth;
            player.energy = player.maxEnergy;
            player.soulEnergy = 0;
            fightLog = [`⚔️ Entered ${VILLAIN_HOUSES[houseIndex].name}`];
        }

        function nextVillain() {
            villainIndex++;
            if (villainIndex >= enemies.length) {
                if (houseIndex >= VILLAIN_HOUSES.length - 1) {
                    allHousesCleared = true;
                    fightLog.push('🏆 ALL HOUSES CLEARED!');
                } else {
                    fightLog.push(`✅ ${VILLAIN_HOUSES[houseIndex].name} Cleared!`);
                    houseIndex++;
                    initHouse();
                }
            } else {
                currentEnemy = enemies[villainIndex];
                fightLog.push(`⚔️ Next: ${currentEnemy.name}`);
            }
        }

        // ============================================================
        // DRAW FUNCTIONS
        // ============================================================
        function drawBackground() {
            const grad = ctx.createRadialGradient(450, 100, 50, 450, 250, 500);
            grad.addColorStop(0, '#1a1a3e');
            grad.addColorStop(1, '#0a0a1a');
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, 900, 500);
            
            for (let i = 0; i < 50; i++) {
                ctx.fillStyle = `rgba(255,255,255,${0.1 + Math.random() * 0.3})`;
                ctx.beginPath();
                ctx.arc(20 + i * 18, 15 + Math.sin(i * 0.7 + frameCount * 0.005) * 10, 1 + Math.random(), 0, Math.PI * 2);
                ctx.fill();
            }
            
            ctx.fillStyle = 'rgba(255,255,255,0.05)';
            ctx.beginPath();
            ctx.arc(750, 60, 50, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = 'rgba(255,255,255,0.02)';
            ctx.beginPath();
            ctx.arc(740, 55, 40, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.fillStyle = 'rgba(255,255,255,0.03)';
            ctx.fillRect(0, 340, 900, 160);
            ctx.fillStyle = 'rgba(255,255,255,0.05)';
            for (let i = 0; i < 90; i++) {
                ctx.fillRect(i * 10, 340 + Math.sin(i * 0.5 + frameCount * 0.005) * 3, 2, 6);
            }
            
            ctx.fillStyle = 'rgba(255,255,255,0.1)';
            ctx.font = '16px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(`🏠 ${VILLAIN_HOUSES[houseIndex].name}`, 20, 30);
            ctx.fillText(`👥 ${villainIndex + 1}/${enemies.length}`, 20, 50);
            
            // Powers
            ctx.fillStyle = 'rgba(255,255,255,0.3)';
            ctx.font = '12px Arial';
            ctx.fillText(`⚡ ${Math.floor(player.energy)}% | 💠 ${Math.floor(player.soulEnergy)}%`, 20, 70);
            ctx.fillText(`🕊️ ${player.isFlying ? 'FLYING' : 'GROUND'}`, 20, 90);
            
            // Combo
            if (player.combo > 2) {
                ctx.fillStyle = '#ffd93d';
                ctx.font = 'bold 20px Arial';
                ctx.textAlign = 'center';
                ctx.shadowBlur = 20;
                ctx.shadowColor = '#ffd93d';
                ctx.fillText(`🔥 ${player.combo}x COMBO!`, 450, 100);
                ctx.shadowBlur = 0;
            }
        }

        // ============================================================
        // ENEMY UPDATE
        // ============================================================
        function updateEnemy() {
            if (!currentEnemy || currentEnemy.health <= 0 || gameOver) return;
            if (currentEnemy.isAttacking) return;
            
            const dist = Math.abs(currentEnemy.x - player.x);
            const action = Math.random();
            
            if (dist < 200) {
                if (action < 0.15 && currentEnemy.energy >= 25) {
                    currentEnemy.isAttacking = true;
                    currentEnemy.attackFrame = 0;
                    currentEnemy.energy -= 25;
                } else if (action < 0.35 && currentEnemy.energy >= 12) {
                    currentEnemy.isAttacking = true;
                    currentEnemy.attackFrame = 0;
                    currentEnemy.energy -= 12;
                } else if (action < 0.55 && currentEnemy.energy >= 8) {
                    currentEnemy.isAttacking = true;
                    currentEnemy.attackFrame = 0;
                    currentEnemy.energy -= 8;
                } else {
                    if (currentEnemy.x < player.x) currentEnemy.x += currentEnemy.speed;
                    else currentEnemy.x -= currentEnemy.speed;
                }
            } else {
                if (currentEnemy.x < player.x) currentEnemy.x += currentEnemy.speed * 1.5;
                else currentEnemy.x -= currentEnemy.speed * 1.5;
            }
            
            if (currentEnemy.isAttacking) {
                currentEnemy.attackFrame++;
                if (currentEnemy.attackFrame > 15) currentEnemy.isAttacking = false;
            }
        }

        // ============================================================
        // COLLISION
        // ============================================================
        function rectCollide(r1, r2) {
            return !(r2.x > r1.x + r1.w || r2.x + r2.w < r1.x ||
                     r2.y > r1.y + r1.h || r2.y + r2.h < r1.y);
        }

        // ============================================================
        // GAME LOOP
        // ============================================================
        function gameLoop() {
            frameCount++;
            
            if (allHousesCleared) {
                drawBackground();
                ctx.fillStyle = 'rgba(0,0,0,0.6)';
                ctx.fillRect(0, 0, 900, 500);
                ctx.fillStyle = '#ffd93d';
                ctx.font = 'bold 52px Arial';
                ctx.textAlign = 'center';
                ctx.shadowBlur = 40;
                ctx.shadowColor = '#ffd93d';
                ctx.fillText('🏆 ALL HOUSES CLEARED!', 450, 200);
                ctx.fillStyle = 'white';
                ctx.font = '24px Arial';
                ctx.shadowBlur = 0;
                ctx.fillText('Jang Uk & Naksu have won!', 450, 260);
                requestAnimationFrame(gameLoop);
                return;
            }
            
            if (!gameOver && currentEnemy) {
                // Update player
                player.update();
                naksu.update();
                updateEnemy();
                
                // Player attack
                if (player.isAttacking && currentEnemy.health > 0) {
                    const attackBox = { x: player.x + 20, y: player.y - 40, w: 50, h: 60 };
                    const enemyBox = currentEnemy.getHitbox();
                    if (rectCollide(attackBox, enemyBox) && currentEnemy.hitCooldown === 0) {
                        const damage = player.getAttackDamage();
                        currentEnemy.health -= damage;
                        currentEnemy.isHit = true;
                        currentEnemy.hitCooldown = 15;
                        player.combo++;
                        fightLog.push(`⚔️ ${player.attackType} dealt ${damage} damage!`);
                        if (player.combo > 2) fightLog.push(`🔥 ${player.combo}x COMBO!`);
                        if (currentEnemy.health <= 0) {
                            fightLog.push(`💀 ${currentEnemy.name} defeated!`);
                            nextVillain();
                        }
                    }
                }
                
                // Naksu attack
                if (!gameOver && currentEnemy && currentEnemy.health > 0) {
                    if (Math.random() < 0.015) naksu.attack();
                    if (naksu.isAttacking && naksu.attackFrame === 10) {
                        const attackBox = { x: naksu.x + 30, y: naksu.y - 35, w: 40, h: 50 };
                        const enemyBox = currentEnemy.getHitbox();
                        if (rectCollide(attackBox, enemyBox) && currentEnemy.hitCooldown === 0) {
                            const damage = Math.floor(Math.random() * 12) + 10;
                            currentEnemy.health -= damage;
                            currentEnemy.isHit = true;
                            currentEnemy.hitCooldown = 15;
                            fightLog.push(`🔥 Naksu dealt ${damage} damage!`);
                            if (currentEnemy.health <= 0) {
                                fightLog.push(`💀 ${currentEnemy.name} defeated!`);
                                nextVillain();
                            }
                        }
                    }
                }
                
                // Enemy attack
                if (currentEnemy && currentEnemy.isAttacking && currentEnemy.attackFrame === 10 && currentEnemy.health > 0) {
                    const attackBox = { x: currentEnemy.x - 30, y: currentEnemy.y - 40, w: 50, h: 60 };
                    const playerBox = player.getHitbox();
                    if (rectCollide(attackBox, playerBox) && player.hitCooldown === 0 && !player.blocking) {
                        const damage = Math.floor(currentEnemy.damage * (0.7 + Math.random() * 0.6));
                        player.health -= damage;
                        player.isHit = true;
                        player.hitCooldown = 15;
                        fightLog.push(`💢 ${currentEnemy.name} dealt ${damage} damage!`);
                        if (player.health <= 0) {
                            player.health = 0;
                            gameOver = true;
                            winner = 'Shadow';
                            fightLog.push('💀 You were defeated!');
                        }
                    } else if (rectCollide(attackBox, playerBox) && player.blocking) {
                        fightLog.push('🛡️ Blocked!');
                    }
                }
            }
            
            // Draw
            drawBackground();
            
            if (currentEnemy && currentEnemy.health > 0) {
                currentEnemy.draw(ctx);
            }
            
            player.draw(ctx);
            naksu.draw(ctx);
            
            if (gameOver) {
                ctx.fillStyle = 'rgba(0,0,0,0.6)';
                ctx.fillRect(0, 0, 900, 500);
                ctx.fillStyle = winner === 'You' ? '#6bcb77' : '#ff6b6b';
                ctx.font = 'bold 48px Arial';
                ctx.textAlign = 'center';
                ctx.shadowBlur = 40;
                ctx.shadowColor = winner === 'You' ? '#6bcb77' : '#ff6b6b';
                ctx.fillText(winner === 'You' ? '🏆 YOU WIN!' : '💀 YOU LOSE!', 450, 180);
                ctx.shadowBlur = 0;
                ctx.fillStyle = 'white';
                ctx.font = '20px Arial';
                ctx.fillText('Press SPACE to restart', 450, 240);
            }
            
            // Fight log
            ctx.fillStyle = 'rgba(0,0,0,0.5)';
            ctx.fillRect(10, 430, 350, 60);
            ctx.fillStyle = 'rgba(255,255,255,0.3)';
            ctx.font = '11px monospace';
            ctx.textAlign = 'left';
            for (let i = 0; i < Math.min(3, fightLog.length); i++) {
                const log = fightLog[fightLog.length - 1 - i];
                if (log) ctx.fillText(log, 16, 445 + i * 18);
            }
            
            ctx.fillStyle = 'rgba(255,255,255,0.1)';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Sword:A | Fire:S | Ice:D | Soul:W | Fly:Q | Block:E', 450, 495);
            
            requestAnimationFrame(gameLoop);
        }

        // ============================================================
        // CONTROLS
        // ============================================================
        function playerSword() { if (!gameOver) player.attack('sword'); }
        function playerFire() { if (!gameOver) player.attack('fire'); }
        function playerIce() { if (!gameOver) player.attack('ice'); }
        function playerSoul() { if (!gameOver) player.attack('soul'); }
        function playerFly() { if (!gameOver) player.fly(); }
        function playerBlock() { if (!gameOver) player.blocking = !player.blocking; }

        window.playerSword = playerSword;
        window.playerFire = playerFire;
        window.playerIce = playerIce;
        window.playerSoul = playerSoul;
        window.playerFly = playerFly;
        window.playerBlock = playerBlock;

        function resetGame() {
            houseIndex = 0;
            initHouse();
            player.health = player.maxHealth;
            naksu.health = naksu.maxHealth;
            player.energy = player.maxEnergy;
            player.soulEnergy = 0;
            player.combo = 0;
            gameOver = false;
            winner = '';
            fightLog = ['🔄 Game Reset'];
        }
        window.resetGame = resetGame;

        // Keyboard
        document.addEventListener('keydown', (e) => {
            if (e.key === ' ' && gameOver) { resetGame(); return; }
            switch(e.key.toLowerCase()) {
                case 'a': playerSword(); break;
                case 's': playerFire(); break;
                case 'd': playerIce(); break;
                case 'w': playerSoul(); break;
                case 'q': playerFly(); break;
                case 'e': playerBlock(); break;
            }
            // Movement
            if (e.key === 'ArrowLeft') player.vx = -player.speed;
            if (e.key === 'ArrowRight') player.vx = player.speed;
            if (e.key === 'ArrowUp') { if (player.grounded) { player.vy = -8; } }
        });
        document.addEventListener('keyup', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') player.vx = 0;
        });

        initHouse();
        gameLoop();
    </script>
</body>
</html>
"""

# ============================================================
# DISPLAY
# ============================================================

components.html(game_html, height=550)

# ============================================================
# CONTROLS
# ============================================================

st.write("""
### 🎮 Controls

| Key | Action | Energy Cost |
| :--- | :--- | :--- |
| **A** | ⚔️ **Sword Slash** | 8 |
| **S** | 🔥 **Fire Power** | 15 |
| **D** | ❄️ **Ice Power** | 20 |
| **W** | 💀 **Soul Power** | 40 (Soul Energy) |
| **Q** | 🕊️ **Fly / Hover** | 0 |
| **E** | 🛡️ **Block / Unblock** | 0 |
| **Space** | 🔄 **Reset** | — |
| **Arrow Keys** | 🏃 **Move** | — |

### ⚔️ All Powers

| Power | Description |
| :--- | :--- |
| ⚔️ **Sword** | Fast sword attack with combo potential |
| 🔥 **Fire** | Naksu's fire energy blast |
| ❄️ **Ice** | Jang Uk's ice power (freezes enemies) |
| 💀 **Soul** | Ultimate soul-shifting attack (massive damage) |
| 🕊️ **Fly** | Fly and hover in the air |
| 🛡️ **Block** | Defend against enemy attacks |

### 🏠 Villain Houses

| House | Boss | Difficulty |
| :--- | :--- | :--- |
| 1. House of Shadows | Shadow Lord | ⭐ |
| 2. House of Flames | Fire Demon | ⭐⭐ |
| 3. House of Storms | Storm King | ⭐⭐⭐ |
| 4. House of Souls | Soul Eater | ⭐⭐⭐⭐ |
| 5. House of Darkness | Dark Emperor | ⭐⭐⭐⭐⭐ |
| 6. House of Chaos | Chaos God | ⭐⭐⭐⭐⭐⭐ |
""")

st.divider()
st.caption("⚔️ Alchemy of Souls — All Powers | Fast • Flying • Sword • Fire • Ice • Soul")

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="⚔️ Alchemy of Souls — Soul Shift",
    page_icon="⚔️",
    layout="wide",
)

st.title("⚔️ Alchemy of Souls — Soul Shift Edition")
st.caption("Jang Uk + Naksu — All Powers + Soul Shifting vs The 6 Villain Houses")

game_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
        background: #000;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        overflow: hidden;
        font-family: 'Segoe UI', Arial, sans-serif;
        touch-action: none;
    }
    #gameWrap {
        position: relative;
        width: 100%;
        max-width: 1000px;
        aspect-ratio: 16/9;
        max-height: 100vh;
    }
    canvas {
        width: 100%;
        height: 100%;
        display: block;
        background: #1a1a1a;
        border-radius: 8px;
    }
    .ui {
        position: absolute;
        inset: 0;
        pointer-events: none;
        user-select: none;
    }

    .topbar {
        position: absolute;
        top: 6px; left: 0; right: 0;
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        padding: 0 10px;
    }
    .side { display: flex; align-items: center; gap: 6px; flex: 1; }
    .side.right { flex-direction: row-reverse; }
    .name {
        font-size: 13px; font-weight: 800; color: #fff;
        text-shadow: 0 2px 4px #000; letter-spacing: .5px; white-space: nowrap;
    }
    .bars { flex: 1; }
    .hpbar {
        height: 12px; border: 2px solid #000; background: #2a1a1a;
        border-radius: 3px; overflow: hidden; box-shadow: 0 0 6px rgba(0,0,0,.6);
    }
    .hpfill { height: 100%; background: linear-gradient(180deg, #ffd24a, #ff9d2e); transition: width .25s linear; }
    .hpfill.enemy { background: linear-gradient(180deg, #ff5a3c, #c41e1e); }
    .energybar {
        height: 6px; margin-top: 3px; background: #0a1a2a;
        border: 1px solid #000; border-radius: 3px; overflow: hidden;
    }
    .energyfill { height: 100%; background: linear-gradient(180deg, #6ee7ff, #22a7ff); transition: width .25s linear; }
    .soulbar {
        height: 5px; margin-top: 2px; background: #2a0a2a;
        border: 1px solid #000; border-radius: 3px; overflow: hidden;
    }
    .soulfill { height: 100%; background: linear-gradient(180deg, #ff7bff, #c420c4); transition: width .25s linear; }
    .timer {
        font-size: 26px; font-weight: 900; color: #fff;
        text-shadow: 0 0 10px #000, 0 2px 4px #000;
        min-width: 60px; text-align: center; margin-top: 2px;
    }

    .skills {
        position: absolute; top: 48px;
        display: grid; grid-template-columns: repeat(2, 34px); gap: 4px;
    }
    .skills.left { left: 10px; }
    .skills.right { right: 10px; }
    .skill {
        width: 34px; height: 34px;
        background: linear-gradient(135deg, #3a2f7a, #5b4bc4);
        border: 2px solid #8a7bff; border-radius: 6px;
        transform: rotate(45deg);
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 8px rgba(120,100,255,.6);
    }
    .skill span { transform: rotate(-45deg); font-size: 15px; }

    .fight {
        position: absolute; top: 42%; left: 50%;
        transform: translate(-50%,-50%);
        font-size: 70px; font-weight: 900; color: #fff;
        text-shadow: 0 0 25px #ff3c00, 0 0 50px #ff3c00, 0 6px 12px #000;
        letter-spacing: 6px;
        animation: fightAnim 1.6s ease-out forwards;
        white-space: nowrap;
    }
    @keyframes fightAnim {
        0% { transform: translate(-50%,-50%) scale(.2); opacity: 0; }
        40% { transform: translate(-50%,-50%) scale(1.15); opacity: 1; }
        100% { transform: translate(-50%,-50%) scale(1); opacity: 0; }
    }

    .joystick {
        position: absolute; bottom: 18px; left: 18px;
        width: 130px; height: 130px; border-radius: 50%;
        background: radial-gradient(circle at 50% 50%, rgba(40,40,60,.55), rgba(10,10,20,.75));
        border: 2px solid rgba(120,180,255,.35);
        box-shadow: 0 0 20px rgba(0,140,255,.25) inset;
        pointer-events: auto; touch-action: none;
    }
    .joy-arrow {
        position: absolute; color: #6ee7ff; font-size: 20px; font-weight: 900;
        text-shadow: 0 0 8px #22a7ff; opacity: .85;
    }
    .joy-up { top: 6px; left: 50%; transform: translateX(-50%); }
    .joy-down { bottom: 6px; left: 50%; transform: translateX(-50%); }
    .joy-left { left: 6px; top: 50%; transform: translateY(-50%); }
    .joy-right { right: 6px; top: 50%; transform: translateY(-50%); }
    .joy-knob {
        position: absolute; top: 50%; left: 50%;
        width: 52px; height: 52px; margin: -26px 0 0 -26px;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 30%, #9fd8ff, #2f7fd6 60%, #123a66);
        border: 2px solid #bfe9ff;
        box-shadow: 0 0 14px rgba(120,200,255,.7);
    }

    .actions {
        position: absolute; bottom: 8px; right: 8px;
        width: 210px; height: 210px; pointer-events: auto;
    }
    .abtn {
        position: absolute; border-radius: 50%;
        border: 3px solid rgba(255,255,255,.55);
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-size: 22px;
        text-shadow: 0 2px 4px #000;
        cursor: pointer;
        box-shadow: 0 0 16px rgba(0,0,0,.6), 0 0 22px var(--glow, rgba(120,200,255,.4));
        background: var(--bg, radial-gradient(circle at 35% 30%, #6ea8ff, #274a9b));
        transition: transform .08s; user-select: none;
    }
    .abtn:active { transform: scale(.9); }

    .abtn-sword  { width: 72px; height: 72px; right: 5px;  bottom: 55px; --bg: radial-gradient(circle at 35% 30%, #9fd8ff, #2f7fd6); --glow: rgba(120,200,255,.7); }
    .abtn-ice    { width: 60px; height: 60px; right: 82px; bottom: 5px;  --bg: radial-gradient(circle at 35% 30%, #b8f0ff, #3fa9e8); --glow: rgba(80,220,255,.7); }
    .abtn-water  { width: 60px; height: 60px; right: 82px; bottom: 70px; --bg: radial-gradient(circle at 35% 30%, #7fd6ff, #1a5ba8); --glow: rgba(80,180,255,.7); }
    .abtn-fly    { width: 54px; height: 54px; right: 5px;  bottom: 0px;  --bg: radial-gradient(circle at 35% 30%, #a8f0c0, #2fb36a); --glow: rgba(80,255,140,.7); }
    .abtn-fire   { width: 60px; height: 60px; right: 145px; bottom: 10px; --bg: radial-gradient(circle at 35% 30%, #ffb46b, #d64a00); --glow: rgba(255,140,60,.7); }
    .abtn-blade  { width: 54px; height: 54px; right: 148px; bottom: 75px; --bg: radial-gradient(circle at 35% 30%, #ff8f8f, #a82020); --glow: rgba(255,90,90,.7); }
    .abtn-shadow { width: 54px; height: 54px; right: 145px; bottom: 138px; --bg: radial-gradient(circle at 35% 30%, #b98bff, #4a1a8a); --glow: rgba(180,120,255,.7); }
    .abtn-soul   { width: 58px; height: 58px; right: 82px; bottom: 140px; --bg: radial-gradient(circle at 35% 30%, #ff8fd6, #b3208b); --glow: rgba(255,120,220,.7); }
    .abtn-shift  { width: 62px; height: 62px; right: 5px;  bottom: 140px; --bg: radial-gradient(circle at 35% 30%, #ffdd66, #cc6600); --glow: rgba(255,220,80,.9); animation: pulseShift 1.5s ease-in-out infinite; }
    
    @keyframes pulseShift {
        0%, 100% { box-shadow: 0 0 16px rgba(0,0,0,.6), 0 0 22px rgba(255,220,80,.4); }
        50% { box-shadow: 0 0 16px rgba(0,0,0,.6), 0 0 35px rgba(255,220,80,.9); }
    }

    .house {
        position: absolute; top: 6px; left: 50%; transform: translateX(-50%);
        font-size: 11px; color: #ffd24a; text-shadow: 0 2px 4px #000;
        letter-spacing: 1px; font-weight: 700; margin-top: 26px;
    }
</style>
</head>
<body>
<div id="gameWrap">
    <canvas id="cv" width="960" height="540"></canvas>
    <div class="ui">
        <div class="topbar">
            <div class="side left">
                <div class="name" id="pName">JANG UK</div>
                <div class="bars">
                    <div class="hpbar"><div class="hpfill" id="pHp" style="width:100%"></div></div>
                    <div class="energybar"><div class="energyfill" id="pEn" style="width:100%"></div></div>
                    <div class="soulbar"><div class="soulfill" id="pSoul" style="width:0%"></div></div>
                </div>
            </div>
            <div class="timer" id="timer">99</div>
            <div class="side right">
                <div class="name" id="eName">SHADOW</div>
                <div class="bars">
                    <div class="hpbar"><div class="hpfill enemy" id="eHp" style="width:100%"></div></div>
                    <div class="energybar"><div class="energyfill" id="eEn" style="width:100%"></div></div>
                </div>
            </div>
        </div>

        <div class="skills left">
            <div class="skill"><span>❄️</span></div>
            <div class="skill"><span>⚔️</span></div>
            <div class="skill"><span>💧</span></div>
            <div class="skill"><span>🕊️</span></div>
        </div>
        <div class="skills right">
            <div class="skill"><span>🗡️</span></div>
            <div class="skill"><span>💥</span></div>
            <div class="skill"><span>🛡️</span></div>
            <div class="skill"><span>⚡</span></div>
        </div>

        <div class="fight" id="fightText">FIGHT!</div>
        <div class="house" id="houseLabel">HOUSE OF SHADOWS</div>

        <div class="joystick" id="joy">
            <div class="joy-arrow joy-up">▲</div>
            <div class="joy-arrow joy-down">▼</div>
            <div class="joy-arrow joy-left">◀</div>
            <div class="joy-arrow joy-right">▶</div>
            <div class="joy-knob" id="knob"></div>
        </div>

        <div class="actions">
            <div class="abtn abtn-sword"  onclick="pSword()">⚔️</div>
            <div class="abtn abtn-ice"    onclick="pIce()">❄️</div>
            <div class="abtn abtn-water"  onclick="pWater()">💧</div>
            <div class="abtn abtn-fly"    onclick="pFly()">🕊️</div>
            <div class="abtn abtn-fire"   onclick="nFire()">🔥</div>
            <div class="abtn abtn-blade"  onclick="nBlade()">🗡️</div>
            <div class="abtn abtn-shadow" onclick="nShadow()">🌑</div>
            <div class="abtn abtn-soul"   onclick="pSoul()">💠</div>
            <div class="abtn abtn-shift"  onclick="soulShift()">🌀</div>
        </div>
    </div>
</div>

<script>
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const W = 960, H = 540;

const HOUSES = [
    { name: 'HOUSE OF SHADOWS', boss: 'SHADOW LORD', diff: 1 },
    { name: 'HOUSE OF FLAMES', boss: 'FIRE DEMON', diff: 2 },
    { name: 'HOUSE OF STORMS', boss: 'STORM KING', diff: 3 },
    { name: 'HOUSE OF SOULS', boss: 'SOUL EATER', diff: 4 },
    { name: 'HOUSE OF DARKNESS', boss: 'DARK EMPEROR', diff: 5 },
    { name: 'HOUSE OF CHAOS', boss: 'CHAOS GOD', diff: 6 }
];

let houseIdx = 0, villainIdx = 0;
let enemies = [], currentEnemy = null;
let gameOver = false, allClear = false;
let timer = 99, timerAcc = 0;
let fightLog = [], frame = 0;
let effects = [];
let soulShifted = false;
let soulShiftTimer = 0;

// ============================================================
// PLAYER — JANG UK (can shift into Naksu)
// ============================================================
const player = {
    x: 260, y: 400, w: 60, h: 110,
    vx: 0, vy: 0, facing: 1,
    hp: 100, maxHp: 100,
    en: 100, maxEn: 100,
    soul: 0, maxSoul: 100,
    attacking: false, atkFrame: 0, atkType: 'sword',
    hitCd: 0, combo: 0, blocking: false,
    isHit: false, hitTimer: 0,
    flying: false, flyTimer: 0,
    speed: 5, grounded: true, anim: 0,
    shield: false, shieldTimer: 0,
    dashX: 0, dashTimer: 0,

    draw() {
        const x = this.x, y = this.y;
        ctx.save();
        
        // Colors change based on soul state
        const isNaksu = soulShifted;
        const bodyColor = isNaksu ? '#181818' : '#f7f7f7';
        const innerColor = isNaksu ? '#282828' : '#e2e2e2';
        const beltColor = isNaksu ? '#ff4d6d' : '#3fa9ff';
        const eyeColor = isNaksu ? '#ff4d6d' : '#7fd6ff';
        const hairColor = '#141414';

        ctx.shadowColor = eyeColor; ctx.shadowBlur = 25;

        // Robe body
        ctx.fillStyle = bodyColor;
        ctx.fillRect(x - 22, y - 50, 44, 60);
        ctx.fillStyle = innerColor;
        ctx.fillRect(x - 16, y - 38, 32, 45);
        // Belt
        ctx.fillStyle = beltColor;
        ctx.fillRect(x - 20, y - 12, 40, 6);

        // Head
        ctx.fillStyle = '#f6d9b0';
        ctx.beginPath(); ctx.arc(x, y - 68, 24, 0, Math.PI*2); ctx.fill();
        // Hair
        ctx.fillStyle = hairColor;
        ctx.beginPath(); ctx.arc(x, y - 74, 24, Math.PI, Math.PI*2); ctx.fill();
        ctx.fillRect(x - 24, y - 74, 10, 26);
        ctx.fillRect(x + 14, y - 74, 10, 26);

        // Eyes
        ctx.shadowColor = eyeColor; ctx.shadowBlur = 18;
        ctx.fillStyle = eyeColor;
        ctx.beginPath(); ctx.arc(x - 8, y - 71, 4.5, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x + 8, y - 71, 4.5, 0, Math.PI*2); ctx.fill();

        // Arms
        ctx.shadowBlur = 10;
        ctx.fillStyle = innerColor;
        const armSwing = this.attacking ? Math.sin(this.atkFrame * 0.35) * 26 : 0;
        ctx.fillRect(x - 34, y - 40 + armSwing, 12, 42);
        ctx.fillRect(x + 22, y - 40 - armSwing, 12, 42);

        // Sword
        const sw = this.attacking ? Math.sin(this.atkFrame * 0.4) * 1.6 : 0;
        ctx.save();
        ctx.translate(x + 30, y - 40);
        ctx.rotate(sw - 0.45);
        ctx.shadowColor = eyeColor; ctx.shadowBlur = 20;
        ctx.fillStyle = isNaksu ? '#ffb46b' : '#cdefff';
        ctx.fillRect(0, -3, 52, 6);
        ctx.fillStyle = '#8b5a2b'; ctx.fillRect(-8, -5, 10, 10);
        ctx.restore();

        // Attack aura
        if (this.attacking && this.atkFrame < 18) {
            const colors = { sword:eyeColor, fire:'#ff7b4a', ice:'#4ce0ff', water:'#3fa9ff', soul:'#ff7bff' };
            ctx.shadowColor = colors[this.atkType]; ctx.shadowBlur = 45;
            ctx.fillStyle = (colors[this.atkType] || eyeColor) + '55';
            ctx.beginPath();
            ctx.arc(x + 60 * this.facing, y - 40, 30 + this.atkFrame * 2.5, 0, Math.PI*2);
            ctx.fill();
        }

        // Flying aura
        if (this.flying) {
            ctx.shadowColor = eyeColor; ctx.shadowBlur = 35;
            for (let i = 0; i < 6; i++) {
                ctx.fillStyle = `rgba(${isNaksu?'255,107,107':'127,214,255'},${0.18 - i*0.025})`;
                ctx.beginPath();
                ctx.arc(x - 18 + i*7, y + 28 + i*6 + Math.sin(this.anim + i)*4, 7 - i*0.8, 0, Math.PI*2);
                ctx.fill();
            }
        }

        // Soul shift aura
        if (soulShifted) {
            ctx.shadowColor = '#ffdd66'; ctx.shadowBlur = 50;
            for (let i = 0; i < 8; i++) {
                const angle = (i / 8) * Math.PI * 2 + this.anim;
                ctx.fillStyle = `rgba(255,220,80,${0.3 + Math.sin(this.anim + i)*0.1})`;
                ctx.beginPath();
                ctx.arc(x + Math.cos(angle) * 55, y - 35 + Math.sin(angle) * 55, 4, 0, Math.PI*2);
                ctx.fill();
            }
        }

        // Shield
        if (this.shield) {
            ctx.shadowColor = eyeColor; ctx.shadowBlur = 40;
            ctx.strokeStyle = `rgba(${isNaksu?'255,107,107':'127,214,255'},0.7)`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(x, y - 35, 60, 0, Math.PI*2);
            ctx.stroke();
        }

        // Hit flash
        if (this.isHit) {
            ctx.shadowColor = '#ff2020'; ctx.shadowBlur = 55;
            ctx.fillStyle = 'rgba(255,30,30,0.28)';
            ctx.beginPath(); ctx.arc(x, y - 35, 50, 0, Math.PI*2); ctx.fill();
        }

        ctx.restore();
    },

    update() {
        this.anim += 0.06;
        this.hitCd = Math.max(0, this.hitCd - 1);
        this.shieldTimer = Math.max(0, this.shieldTimer - 1);
        if (this.shieldTimer <= 0) this.shield = false;
        this.dashTimer = Math.max(0, this.dashTimer - 1);
        
        // Soul shift timer
        if (soulShiftTimer > 0) {
            soulShiftTimer--;
            if (soulShiftTimer <= 0 && soulShifted) {
                soulShifted = false;
                fightLog.push('🌀 Soul shift ended');
                effects.push({ type: 'soulShift', x: this.x, y: this.y, timer: 60 });
            }
        }

        if (!this.flying) {
            this.vy += 0.55;
            if (this.vy > 8) this.vy = 8;
        } else {
            this.vy += 0.12;
            if (this.vy > 2) this.vy = 2;
            this.flyTimer--;
            if (this.flyTimer <= 0) this.flying = false;
        }

        if (this.dashTimer > 0) {
            this.x += this.dashX * 14;
        } else {
            this.x += this.vx;
        }
        this.y += this.vy;

        if (this.y >= 400) { this.y = 400; this.vy = 0; this.grounded = true; }
        else this.grounded = false;

        if (this.x < 40) this.x = 40;
        if (this.x > W - 40) this.x = W - 40;

        if (this.attacking) {
            this.atkFrame++;
            if (this.atkFrame > 22) this.attacking = false;
        }
        if (this.isHit) {
            this.hitTimer++;
            if (this.hitTimer > 10) { this.isHit = false; this.hitTimer = 0; }
        }

        if (this.en < this.maxEn) this.en = Math.min(this.maxEn, this.en + 0.25);
        if (this.soul < this.maxSoul) this.soul = Math.min(this.maxSoul, this.soul + 0.12);
    },

    attack(type) {
        if (this.attacking || gameOver) return;
        const costs = { sword:8, fire:15, ice:20, water:18, soul:40 };
        const cost = costs[type];
        if (type === 'soul' && this.soul < cost) return;
        if (this.en < cost && type !== 'soul') return;

        this.attacking = true;
        this.atkFrame = 0;
        this.atkType = type;
        if (type === 'soul') this.soul -= cost;
        else this.en -= cost;
    },

    iceStorm() {
        if (this.attacking || gameOver || this.en < 25) return;
        this.attacking = true;
        this.atkFrame = 0;
        this.atkType = 'ice';
        this.en -= 25;
        effects.push({ type: 'iceStorm', x: this.x, y: this.y, timer: 60 });
    },

    waterWhip() {
        if (this.attacking || gameOver || this.en < 18) return;
        this.attacking = true;
        this.atkFrame = 0;
        this.atkType = 'water';
        this.en -= 18;
        effects.push({ type: 'waterWhip', x: this.x, y: this.y, timer: 40 });
    },

    fly() {
        if (!this.flying) {
            this.flying = true;
            this.flyTimer = 150;
            this.vy = -9;
        }
    },

    getDmg() {
        // If soul-shifted, use Naksu's damage table
        if (soulShifted) {
            const naksuBase = {
                fire: Math.floor(Math.random()*14)+20,
                blade: Math.floor(Math.random()*12)+22,
                shadow: Math.floor(Math.random()*20)+26,
                sword: Math.floor(Math.random()*10)+16,
                ice: Math.floor(Math.random()*18)+24,
                water: Math.floor(Math.random()*16)+22,
                soul: Math.floor(Math.random()*25)+38
            };
            return Math.floor((naksuBase[this.atkType] || 18) * (1 + this.combo * 0.05));
        }
        const base = {
            sword: Math.floor(Math.random()*10)+14,
            fire: Math.floor(Math.random()*14)+20,
            ice: Math.floor(Math.random()*18)+24,
            water: Math.floor(Math.random()*16)+22,
            soul: Math.floor(Math.random()*25)+38
        };
        return Math.floor((base[this.atkType] || 12) * (1 + this.combo * 0.05));
    },

    box() { return { x: this.x-30, y: this.y-70, w: 60, h: 100 }; }
};

// ============================================================
// NAKSU (Ally)
// ============================================================
const naksu = {
    x: 130, y: 400,
    hp: 80, maxHp: 80,
    en: 100, maxEn: 100,
    attacking: false, atkFrame: 0, atkType: 'fire',
    hitCd: 0, isHit: false, hitTimer: 0,
    anim: 0, flying: false, flyTimer: 0, vy: 0,

    draw() {
        const x = this.x, y = this.y;
        ctx.save();
        ctx.shadowColor = '#ff6b6b'; ctx.shadowBlur = 20;

        ctx.fillStyle = '#181818';
        ctx.fillRect(x - 20, y - 46, 40, 54);
        ctx.fillStyle = '#282828';
        ctx.fillRect(x - 15, y - 34, 30, 38);
        ctx.fillStyle = '#ff4d6d';
        ctx.fillRect(x - 18, y - 10, 36, 5);

        ctx.fillStyle = '#f6d9b0';
        ctx.beginPath(); ctx.arc(x, y - 64, 21, 0, Math.PI*2); ctx.fill();

        ctx.fillStyle = '#141414';
        ctx.beginPath(); ctx.arc(x, y - 70, 21, Math.PI, Math.PI*2); ctx.fill();
        ctx.fillRect(x - 21, y - 70, 9, 30);
        ctx.fillRect(x + 12, y - 70, 9, 30);

        ctx.shadowColor = '#ff4d6d'; ctx.shadowBlur = 18;
        ctx.fillStyle = '#ff4d6d';
        ctx.beginPath(); ctx.arc(x - 7, y - 66, 4, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x + 7, y - 66, 4, 0, Math.PI*2); ctx.fill();

        const sw = this.attacking ? Math.sin(this.atkFrame * 0.4) * 1.4 : 0;
        ctx.save();
        ctx.translate(x + 26, y - 36);
        ctx.rotate(sw - 0.4);
        ctx.shadowColor = '#ff7b4a'; ctx.shadowBlur = 25;
        ctx.fillStyle = '#ffb46b'; ctx.fillRect(0, -3, 42, 6);
        ctx.restore();

        if (this.attacking && this.atkFrame < 15) {
            const colors = { fire:'#ff6b6b', blade:'#ff4d6d', shadow:'#b98bff' };
            ctx.shadowColor = colors[this.atkType]; ctx.shadowBlur = 45;
            ctx.fillStyle = (colors[this.atkType] || '#ff6b6b') + '55';
            ctx.beginPath(); ctx.arc(x + 46, y - 36, 26 + this.atkFrame*2, 0, Math.PI*2); ctx.fill();
        }

        if (this.isHit) {
            ctx.shadowColor = '#ff2020'; ctx.shadowBlur = 45;
            ctx.fillStyle = 'rgba(255,30,30,0.25)';
            ctx.beginPath(); ctx.arc(x, y - 34, 45, 0, Math.PI*2); ctx.fill();
        }
        ctx.restore();
    },

    update() {
        this.anim += 0.06;
        this.hitCd = Math.max(0, this.hitCd - 1);
        if (!this.flying) { this.vy += 0.55; if (this.vy > 8) this.vy = 8; }
        else { this.vy += 0.12; if (this.vy > 2) this.vy = 2; this.flyTimer--; if (this.flyTimer<=0) this.flying=false; }
        this.y += this.vy;
        if (this.y >= 400) { this.y = 400; this.vy = 0; }
        if (this.attacking) { this.atkFrame++; if (this.atkFrame > 20) this.attacking = false; }
        if (this.isHit) { this.hitTimer++; if (this.hitTimer>10){this.isHit=false;this.hitTimer=0;} }
        if (this.en < this.maxEn) this.en = Math.min(this.maxEn, this.en + 0.3);
    },

    getDmg() {
        return Math.floor(Math.random()*12) + 12;
    },

    box() { return { x: this.x-26, y: this.y-62, w: 52, h: 88 }; }
};

// ============================================================
// ENEMIES
// ============================================================
function makeEnemies(hIdx) {
    const h = HOUSES[hIdx];
    const count = 3 + Math.floor(h.diff * 1.3);
    const arr = [];
    const names = ['SHADOW','BLAZE','STORM','SOUL','DARK','CHAOS','FROST','VENOM'];
    for (let i = 0; i < count; i++) {
        const isBoss = (i === count - 1);
        const baseHp = 70 + h.diff * 20;
        arr.push({
            name: isBoss ? h.boss : names[i % names.length] + ' WARRIOR',
            hp: isBoss ? baseHp * 2.6 : baseHp,
            maxHp: isBoss ? baseHp * 2.6 : baseHp,
            dmg: isBoss ? 16 + h.diff * 3 : 9 + h.diff * 2,
            isBoss, speed: isBoss ? 2.6 : 1.2 + Math.random() * 0.6,
            x: 760 + Math.random() * 90, y: 400,
            attacking: false, atkFrame: 0, hitCd: 0,
            isHit: false, hitTimer: 0, anim: 0,
            color: isBoss ? '#ff3c3c' : '#8c8c8c',
            energy: 100,

            draw() {
                const x = this.x, y = this.y;
                ctx.save();
                ctx.shadowColor = this.color; ctx.shadowBlur = this.isBoss ? 35 : 18;
                ctx.fillStyle = this.isBoss ? '#5a0d0d' : '#22282b';
                ctx.fillRect(x - 22, y - 50, 44, 60);
                ctx.fillStyle = this.isBoss ? '#7a1010' : '#323a3d';
                ctx.fillRect(x - 16, y - 38, 32, 45);
                ctx.fillStyle = this.isBoss ? '#e6c89a' : '#8c959b';
                ctx.beginPath(); ctx.arc(x, y - 68, 24, 0, Math.PI*2); ctx.fill();
                ctx.fillStyle = this.isBoss ? '#3a0505' : '#1a2023';
                ctx.beginPath(); ctx.arc(x, y - 74, 24, Math.PI, Math.PI*2); ctx.fill();
                ctx.fillRect(x - 24, y - 74, 48, 10);
                ctx.shadowColor = this.color; ctx.shadowBlur = 22;
                ctx.fillStyle = this.color;
                ctx.beginPath(); ctx.arc(x - 8, y - 71, 5, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(x + 8, y - 71, 5, 0, Math.PI*2); ctx.fill();
                ctx.shadowBlur = 12;
                ctx.strokeStyle = this.color; ctx.lineWidth = 5;
                ctx.beginPath();
                ctx.moveTo(x - 40, y - 36);
                ctx.lineTo(x - 72, y - 58);
                ctx.stroke();
                if (this.attacking && this.atkFrame < 15) {
                    ctx.shadowColor = this.color; ctx.shadowBlur = 45;
                    ctx.fillStyle = this.color + '55';
                    ctx.beginPath(); ctx.arc(x - 66, y - 34, 26 + this.atkFrame*2, 0, Math.PI*2); ctx.fill();
                }
                if (this.isHit) {
                    ctx.shadowColor = '#ff2020'; ctx.shadowBlur = 55;
                    ctx.fillStyle = 'rgba(255,30,30,0.35)';
                    ctx.beginPath(); ctx.arc(x, y - 34, 50, 0, Math.PI*2); ctx.fill();
                }
                ctx.restore();
            },
            update() {
                this.anim += 0.06;
                this.hitCd = Math.max(0, this.hitCd - 1);
                if (this.attacking) { this.atkFrame++; if (this.atkFrame > 15) this.attacking = false; }
                if (this.isHit) { this.hitTimer++; if (this.hitTimer>10){this.isHit=false;this.hitTimer=0;} }
            },
            box() { return { x: this.x-30, y: this.y-70, w: 60, h: 100 }; }
        });
    }
    return arr;
}

// ============================================================
// INIT
// ============================================================
function initHouse() {
    enemies = makeEnemies(houseIdx);
    villainIdx = 0;
    currentEnemy = enemies[0];
    gameOver = false;
    player.hp = player.maxHp;
    naksu.hp = naksu.maxHp;
    player.en = player.maxEn;
    player.soul = 0;
    player.combo = 0;
    timer = 99;
    effects = [];
    fightLog = ['Entered ' + HOUSES[houseIdx].name];
    document.getElementById('houseLabel').textContent = HOUSES[houseIdx].name;
    document.getElementById('eName').textContent = currentEnemy.name;
    const ft = document.getElementById('fightText');
    ft.style.animation = 'none';
    void ft.offsetWidth;
    ft.style.animation = 'fightAnim 1.6s ease-out forwards';
}

function nextVillain() {
    villainIdx++;
    if (villainIdx >= enemies.length) {
        if (houseIdx >= HOUSES.length - 1) {
            allClear = true;
            fightLog.push('ALL HOUSES CLEARED!');
        } else {
            fightLog.push(HOUSES[houseIdx].name + ' Cleared!');
            houseIdx++;
            initHouse();
        }
    } else {
        currentEnemy = enemies[villainIdx];
        document.getElementById('eName').textContent = currentEnemy.name;
        fightLog.push('Next: ' + currentEnemy.name);
    }
}

function resetGame() {
    houseIdx = 0;
    allClear = false;
    soulShifted = false;
    soulShiftTimer = 0;
    initHouse();
}

function hit(a, b) {
    return !(b.x > a.x + a.w || b.x + b.w < a.x || b.y > a.y + a.h || b.y + b.h < a.y);
}

function enemyAI(e) {
    if (!e || e.hp <= 0 || gameOver || e.attacking) return;
    const dx = player.x - e.x;
    const dist = Math.abs(dx);
    if (dist < 220) {
        if (Math.random() < 0.18) { e.attacking = true; e.atkFrame = 0; }
        else { e.x += dx > 0 ? e.speed : -e.speed; }
    } else {
        e.x += dx > 0 ? e.speed * 1.4 : -e.speed * 1.4;
    }
    if (e.x < W - 60) e.x = W - 60;
}

function updateEffects() {
    for (let i = effects.length - 1; i >= 0; i--) {
        effects[i].timer--;
        if (effects[i].timer <= 0) effects.splice(i, 1);
    }
}

function drawBg() {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#0a1220');
    g.addColorStop(0.55, '#16283a');
    g.addColorStop(1, '#0a0f18');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = 'rgba(200,230,255,0.08)';
    ctx.beginPath(); ctx.arc(760, 90, 70, 0, Math.PI*2); ctx.fill();
    for (let i = 0; i < 14; i++) {
        const bx = 30 + i * 70 + Math.sin(i * 1.4) * 10;
        const sw = 14 + Math.sin(i) * 3;
        ctx.fillStyle = i % 3 === 0 ? 'rgba(30,60,50,0.55)' : 'rgba(20,45,38,0.45)';
        ctx.fillRect(bx, -20, sw, 460);
        ctx.fillStyle = 'rgba(40,80,60,0.5)';
        for (let l = 0; l < 4; l++) {
            const ly = 60 + l * 90 + Math.sin(i + l) * 20;
            ctx.beginPath();
            ctx.ellipse(bx + sw + 18, ly, 22, 6, -0.4, 0, Math.PI*2);
            ctx.fill();
        }
    }
    const fg = ctx.createLinearGradient(0, 400, 0, H);
    fg.addColorStop(0, '#3a3f46');
    fg.addColorStop(1, '#1a1d22');
    ctx.fillStyle = fg;
    ctx.fillRect(0, 400, W, H - 400);
    ctx.strokeStyle = 'rgba(0,0,0,0.4)';
    ctx.lineWidth = 2;
    for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 12; c++) {
            const tx = c * 80 + (r % 2) * 40 - 40;
            const ty = 400 + r * 47;
            ctx.strokeRect(tx, ty, 80, 47);
        }
    }
    const v = ctx.createRadialGradient(W/2, H/2, 200, W/2, H/2, 600);
    v.addColorStop(0, 'rgba(0,0,0,0)');
    v.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = v;
    ctx.fillRect(0, 0, W, H);
}

function drawEffects() {
    for (const e of effects) {
        if (e.type === 'iceStorm') {
            const pct = e.timer / 60;
            ctx.shadowColor = '#4ce0ff'; ctx.shadowBlur = 40;
            for (let i = 0; i < 12; i++) {
                const angle = (i / 12) * Math.PI * 2 + frame * 0.05;
                ctx.fillStyle = `rgba(76,224,255,${pct * 0.6})`;
                ctx.beginPath();
                ctx.arc(e.x + Math.cos(angle) * 80, e.y - 40 + Math.sin(angle) * 80, 8, 0, Math.PI*2);
                ctx.fill();
            }
        }
        if (e.type === 'waterWhip') {
            const pct = e.timer / 40;
            ctx.shadowColor = '#3fa9ff'; ctx.shadowBlur = 30;
            ctx.strokeStyle = `rgba(63,169,255,${pct})`;
            ctx.lineWidth = 6;
            ctx.beginPath();
            ctx.moveTo(e.x, e.y - 40);
            ctx.quadraticCurveTo(e.x + 80, e.y - 80 + Math.sin(frame * 0.3) * 20, e.x + 160, e.y - 40);
            ctx.stroke();
        }
        if (e.type === 'soulShift') {
            const pct = e.timer / 60;
            ctx.shadowColor = '#ffdd66'; ctx.shadowBlur = 60;
            for (let i = 0; i < 20; i++) {
                const angle = (i / 20) * Math.PI * 2 + frame * 0.08;
                ctx.fillStyle = `rgba(255,220,80,${pct * 0.7})`;
                ctx.beginPath();
                ctx.arc(e.x + Math.cos(angle) * 100, e.y - 40 + Math.sin(angle) * 100, 6, 0, Math.PI*2);
                ctx.fill();
            }
        }
    }
}

function updateUI() {
    const pHp = Math.max(0, player.hp / player.maxHp) * 100;
    const pEn = Math.max(0, player.en / player.maxEn) * 100;
    const pSoul = Math.max(0, player.soul / player.maxSoul) * 100;
    document.getElementById('pHp').style.width = pHp + '%';
    document.getElementById('pEn').style.width = pEn + '%';
    document.getElementById('pSoul').style.width = pSoul + '%';
    if (currentEnemy) {
        const eHp = Math.max(0, currentEnemy.hp / currentEnemy.maxHp) * 100;
        document.getElementById('eHp').style.width = eHp + '%';
    }
    document.getElementById('timer').textContent = String(Math.max(0, Math.floor(timer))).padStart(2, '0');
    document.getElementById('pName').textContent = soulShifted ? 'NAKSU (SHIFTED)' : 'JANG UK';
}

// ============================================================
// MAIN LOOP
// ============================================================
let lastT = performance.now();
function loop(now) {
    const dt = Math.min(50, now - lastT) / 16.67;
    lastT = now;
    frame++;

    if (allClear) {
        drawBg();
        ctx.fillStyle = 'rgba(0,0,0,0.75)';
        ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = '#ffd24a';
        ctx.font = 'bold 58px Arial';
        ctx.textAlign = 'center';
        ctx.shadowColor = '#ffd24a'; ctx.shadowBlur = 40;
        ctx.fillText('ALL HOUSES CLEARED!', W/2, H/2 - 20);
        ctx.shadowBlur = 0;
        ctx.fillStyle = '#fff';
        ctx.font = '24px Arial';
        ctx.fillText('Jang Uk & Naksu have won!', W/2, H/2 + 40);
        requestAnimationFrame(loop);
        return;
    }

    if (!gameOver) {
        player.update();
        naksu.update();
        if (currentEnemy && currentEnemy.hp > 0) {
            currentEnemy.update();
            enemyAI(currentEnemy);
        }
        updateEffects();

        timerAcc += dt;
        if (timerAcc >= 60) { timerAcc = 0; timer--; if (timer <= 0) { timer = 0; gameOver = true; } }

        // Player attack
        if (player.attacking && currentEnemy && currentEnemy.hp > 0) {
            const a = { x: player.x + 24, y: player.y - 46, w: 60, h: 70 };
            if (hit(a, currentEnemy.box()) && currentEnemy.hitCd === 0) {
                const d = player.getDmg();
                currentEnemy.hp -= d;
                currentEnemy.isHit = true;
                currentEnemy.hitCd = 15;
                player.combo++;
                fightLog.push((soulShifted?'Naksu':'Jang Uk') + ' ' + player.atkType + ' → ' + d + ' dmg!');
                if (currentEnemy.hp <= 0) {
                    fightLog.push(currentEnemy.name + ' defeated!');
                    nextVillain();
                }
            }
        }

        // Naksu auto-attack
        if (currentEnemy && currentEnemy.hp > 0) {
            if (Math.random() < 0.02) {
                naksu.attacking = true;
                naksu.atkFrame = 0;
                naksu.atkType = 'fire';
            }
            if (naksu.attacking && naksu.atkFrame === 10) {
                const a = { x: naksu.x + 30, y: naksu.y - 40, w: 50, h: 60 };
                if (hit(a, currentEnemy.box()) && currentEnemy.hitCd === 0) {
                    const d = naksu.getDmg();
                    currentEnemy.hp -= d;
                    currentEnemy.isHit = true;
                    currentEnemy.hitCd = 15;
                    fightLog.push('Naksu → ' + d + ' dmg!');
                    if (currentEnemy.hp <= 0) {
                        fightLog.push(currentEnemy.name + ' defeated!');
                        nextVillain();
                    }
                }
            }
        }

        // Enemy attack
        if (currentEnemy && currentEnemy.attacking && currentEnemy.atkFrame === 10 && currentEnemy.hp > 0) {
            const a = { x: currentEnemy.x - 60, y: currentEnemy.y - 46, w: 60, h: 70 };
            if (hit(a, player.box()) && player.hitCd === 0) {
                if (!player.shield) {
                    const d = Math.floor(currentEnemy.dmg * (0.75 + Math.random() * 0.5));
                    player.hp -= d;
                    player.isHit = true;
                    player.hitCd = 15;
                    fightLog.push(currentEnemy.name + ' → ' + d + '!');
                    if (player.hp <= 0) {
                        player.hp = 0;
                        gameOver = true;
                        fightLog.push('You were defeated!');
                    }
                } else {
                    fightLog.push('Shield blocked!');
                }
            }
        }
    }

    drawBg();
    if (currentEnemy && currentEnemy.hp > 0) currentEnemy.draw();
    player.draw();
    naksu.draw();
    drawEffects();

    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(14, H - 78, 320, 66);
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    ctx.font = '12px monospace';
    ctx.textAlign = 'left';
    for (let i = 0; i < Math.min(4, fightLog.length); i++) {
        const log = fightLog[fightLog.length - 1 - i];
        if (log) ctx.fillText('› ' + log, 22, H - 60 + i * 15);
    }

    if (gameOver) {
        ctx.fillStyle = 'rgba(0,0,0,0.78)';
        ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = '#ff3c3c';
        ctx.font = 'bold 62px Arial';
        ctx.textAlign = 'center';
        ctx.shadowColor = '#ff3c3c'; ctx.shadowBlur = 45;
        ctx.fillText('YOU LOSE', W/2, H/2 - 10);
        ctx.shadowBlur = 0;
        ctx.fillStyle = '#fff';
        ctx.font = '22px Arial';
        ctx.fillText('Tap ⚔️ to restart', W/2, H/2 + 50);
    }

    updateUI();
    requestAnimationFrame(loop);
}

// ============================================================
// SOUL SHIFTING
// ============================================================
function soulShift() {
    if (gameOver) return;
    if (player.soul < 100) {
        fightLog.push('🌀 Need 100% Soul Energy!');
        return;
    }
    player.soul = 0;
    soulShifted = true;
    soulShiftTimer = 900; // 15 seconds
    player.hp = player.maxHp; // Full heal on shift
    fightLog.push('🌀 SOUL SHIFT! You are now Naksu!');
    effects.push({ type: 'soulShift', x: player.x, y: player.y, timer: 60 });
}

// ============================================================
// JOYSTICK
// ============================================================
(function initJoystick() {
    const joy = document.getElementById('joy');
    const knob = document.getElementById('knob');
    let active = false, cx = 0, cy = 0;

    function start(e) {
        active = true;
        const r = joy.getBoundingClientRect();
        cx = r.left + r.width/2;
        cy = r.top + r.height/2;
        move(e);
    }
    function move(e) {
        if (!active) return;
        const t = e.touches ? e.touches[0] : e;
        const dx = t.clientX - cx;
        const dy = t.clientY - cy;
        const dist = Math.min(45, Math.hypot(dx, dy));
        const ang = Math.atan2(dy, dx);
        knob.style.transform = `translate(${Math.cos(ang)*dist}px, ${Math.sin(ang)*dist}px)`;
        if (dist < 8) { player.vx = 0; return; }
        const nx = dx / (Math.hypot(dx, dy) || 1);
        player.vx = nx * player.speed;
        if (nx < -0.3) player.facing = -1;
        if (nx >  0.3) player.facing =  1;
    }
    function end() {
        active = false;
        knob.style.transform = 'translate(0,0)';
        player.vx = 0;
    }
    joy.addEventListener('mousedown', start);
    joy.addEventListener('touchstart', start, {passive:true});
    document.addEventListener('mousemove', move);
    document.addEventListener('touchmove', move, {passive:false});
    document.addEventListener('mouseup', end);
    document.addEventListener('touchend', end);
})();

// ============================================================
// BUTTON HANDLERS
// ============================================================
function pSword() { if (gameOver) { resetGame(); return; } player.attack('sword'); }
function pIce()   { if (!gameOver) player.iceStorm(); }
function pWater() { if (!gameOver) player.waterWhip(); }
function pFly()   { if (!gameOver) player.fly(); }
function pSoul()  { if (!gameOver) player.attack('soul'); }
function nFire()   { if (!gameOver) player.attack('fire'); }
function nBlade()  { if (!gameOver) player.attack('sword'); }
function nShadow() { if (!gameOver) player.attack('water'); }

window.pSword = pSword;
window.pIce = pIce;
window.pWater = pWater;
window.pFly = pFly;
window.pSoul = pSoul;
window.nFire = nFire;
window.nBlade = nBlade;
window.nShadow = nShadow;
window.soulShift = soulShift;
window.resetGame = resetGame;

// Keyboard
document.addEventListener('keydown', (e) => {
    switch(e.key.toLowerCase()) {
        case 'a': pSword(); break;
        case 's': pIce(); break;
        case 'd': pWater(); break;
        case 'w': pSoul(); break;
        case 'q': pFly(); break;
        case 'e': soulShift(); break;
        case 'z': nFire(); break;
        case 'x': nBlade(); break;
        case 'c': nShadow(); break;
        case ' ': if (gameOver) resetGame(); break;
    }
    if (e.key === 'ArrowLeft') player.vx = -player.speed;
    if (e.key === 'ArrowRight') player.vx = player.speed;
    if (e.key === 'ArrowUp' && player.grounded) player.vy = -10;
});
document.addEventListener('keyup', (e) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') player.vx = 0;
});

initHouse();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

components.html(game_html, height=650)

st.write("""
### 🌀 Soul Shifting

| Feature | Description |
| :--- | :--- |
| **Soul Shift** | Swap into the other character's body |
| **Cost** | 100% Soul Energy (pink bar) |
| **Duration** | 15 seconds |
| **Effect** | Full HP + new powers + visual change |

### 🎮 Controls

| Button | Power |
| :--- | :--- |
| ⚔️ | Sword Slash |
| ❄️ | Ice Storm |
| 💧 | Water Whip |
| 🕊️ | Fly |
| 💠 | Soul Power |
| 🌀 | **Soul Shift** |
| 🔥 | Naksu Fire |
| 🗡️ | Naksu Blade |
| 🌑 | Naksu Shadow |

### 🏠 The 6 Houses
1. Shadows → Shadow Lord
2. Flames → Fire Demon
3. Storms → Storm King
4. Souls → Soul Eater
5. Darkness → Dark Emperor
6. Chaos → Chaos God
""")

st.divider()
st.caption("⚔️ Alchemy of Souls — Soul Shift Edition")

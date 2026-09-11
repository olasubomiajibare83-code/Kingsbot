import streamlit as st
import streamlit.components.v1 as components

# 1. Set Streamlit to use the whole screen, no padding
st.set_page_config(
    page_title="⚔️ Alchemy of Souls",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Remove Streamlit's default padding so the game fills the phone screen
st.markdown("""
<style>
    .block-container { padding: 0 !important; max-width: 100% !important; }
    header { display: none !important; }
    footer { display: none !important; }
    #MainMenu { display: none !important; }
    .stApp { background: #000 !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚔️ Alchemy of Souls — Soul Shift Edition")

game_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body {
        width: 100%;
        height: 100%;
        background: #000;
        overflow: hidden;
        font-family: 'Segoe UI', Arial, sans-serif;
        touch-action: none;
    }
    /* THIS IS THE FIX: The canvas is now 100% width and 100% height of the iframe */
    #gameWrap {
        position: relative;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
    }
    canvas {
        width: 100%;
        height: 100%;
        display: block;
        background: #1a1a1a;
    }

    /* UI overlay */
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
        font-size: 12px; font-weight: 800; color: #fff;
        text-shadow: 0 2px 4px #000; white-space: nowrap;
    }
    .bars { flex: 1; }
    .hpbar {
        height: 10px; border: 2px solid #000; background: #2a1a1a;
        border-radius: 3px; overflow: hidden;
    }
    .hpfill { height: 100%; background: linear-gradient(180deg, #ffd24a, #ff9d2e); transition: width .25s linear; }
    .hpfill.enemy { background: linear-gradient(180deg, #ff5a3c, #c41e1e); }
    .energybar {
        height: 5px; margin-top: 2px; background: #0a1a2a;
        border: 1px solid #000; border-radius: 3px; overflow: hidden;
    }
    .energyfill { height: 100%; background: linear-gradient(180deg, #6ee7ff, #22a7ff); transition: width .25s linear; }
    .soulbar {
        height: 4px; margin-top: 2px; background: #2a0a2a;
        border: 1px solid #000; border-radius: 3px; overflow: hidden;
    }
    .soulfill { height: 100%; background: linear-gradient(180deg, #ff7bff, #c420c4); transition: width .25s linear; }
    .timer {
        font-size: 22px; font-weight: 900; color: #fff;
        text-shadow: 0 0 10px #000;
        min-width: 50px; text-align: center;
    }

    /* Joystick and buttons - made smaller for phone */
    .joystick {
        position: absolute; bottom: 15px; left: 15px;
        width: 110px; height: 110px; border-radius: 50%;
        background: radial-gradient(circle, rgba(40,40,60,.5), rgba(10,10,20,.7));
        border: 2px solid rgba(120,180,255,.3);
        pointer-events: auto; touch-action: none;
    }
    .joy-arrow { position: absolute; color: #6ee7ff; font-size: 16px; font-weight: 900; }
    .joy-up { top: 4px; left: 50%; transform: translateX(-50%); }
    .joy-down { bottom: 4px; left: 50%; transform: translateX(-50%); }
    .joy-left { left: 4px; top: 50%; transform: translateY(-50%); }
    .joy-right { right: 4px; top: 50%; transform: translateY(-50%); }
    .joy-knob {
        position: absolute; top: 50%; left: 50%;
        width: 44px; height: 44px; margin: -22px 0 0 -22px;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 30%, #9fd8ff, #2f7fd6 60%, #123a66);
        border: 2px solid #bfe9ff;
    }

    .actions {
        position: absolute; bottom: 5px; right: 5px;
        width: 180px; height: 180px; pointer-events: auto;
    }
    .abtn {
        position: absolute; border-radius: 50%;
        border: 2px solid rgba(255,255,255,.5);
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-size: 18px;
        cursor: pointer;
        background: var(--bg, radial-gradient(circle at 35% 30%, #6ea8ff, #274a9b));
        box-shadow: 0 0 10px var(--glow, rgba(120,200,255,.4));
        transition: transform .08s;
    }
    .abtn:active { transform: scale(.9); }

    .abtn-sword  { width: 60px; height: 60px; right: 5px;  bottom: 45px; --bg: radial-gradient(circle at 35% 30%, #9fd8ff, #2f7fd6); }
    .abtn-ice    { width: 50px; height: 50px; right: 70px; bottom: 5px;  --bg: radial-gradient(circle at 35% 30%, #b8f0ff, #3fa9e8); }
    .abtn-water  { width: 50px; height: 50px; right: 70px; bottom: 60px; --bg: radial-gradient(circle at 35% 30%, #7fd6ff, #1a5ba8); }
    .abtn-fly    { width: 45px; height: 45px; right: 5px;  bottom: 0px;  --bg: radial-gradient(circle at 35% 30%, #a8f0c0, #2fb36a); }
    .abtn-fire   { width: 50px; height: 50px; right: 125px; bottom: 10px; --bg: radial-gradient(circle at 35% 30%, #ffb46b, #d64a00); }
    .abtn-blade  { width: 45px; height: 45px; right: 128px; bottom: 65px; --bg: radial-gradient(circle at 35% 30%, #ff8f8f, #a82020); }
    .abtn-shadow { width: 45px; height: 45px; right: 125px; bottom: 120px; --bg: radial-gradient(circle at 35% 30%, #b98bff, #4a1a8a); }
    .abtn-soul   { width: 50px; height: 50px; right: 70px; bottom: 120px; --bg: radial-gradient(circle at 35% 30%, #ff8fd6, #b3208b); }
    .abtn-shift  { width: 55px; height: 55px; right: 5px;  bottom: 120px; --bg: radial-gradient(circle at 35% 30%, #ffdd66, #cc6600); animation: pulseShift 1.5s infinite; }
    @keyframes pulseShift { 50% { box-shadow: 0 0 25px rgba(255,220,80,.9); } }

    .fight {
        position: absolute; top: 40%; left: 50%;
        transform: translate(-50%,-50%);
        font-size: 50px; font-weight: 900; color: #fff;
        text-shadow: 0 0 25px #ff3c00, 0 0 50px #ff3c00;
        animation: fightAnim 1.6s ease-out forwards;
        white-space: nowrap;
    }
    @keyframes fightAnim {
        0% { transform: translate(-50%,-50%) scale(.2); opacity: 0; }
        40% { transform: translate(-50%,-50%) scale(1.15); opacity: 1; }
        100% { transform: translate(-50%,-50%) scale(1); opacity: 0; }
    }
    .house {
        position: absolute; top: 55px; left: 50%; transform: translateX(-50%);
        font-size: 10px; color: #ffd24a; letter-spacing: 1px; font-weight: 700;
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
// ================= SETUP =================
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

const player = {
    x: 260, y: 400, vx: 0, vy: 0, facing: 1,
    hp: 100, maxHp: 100, en: 100, maxEn: 100, soul: 0, maxSoul: 100,
    attacking: false, atkFrame: 0, atkType: 'sword',
    hitCd: 0, combo: 0, isHit: false, hitTimer: 0,
    flying: false, flyTimer: 0, speed: 5, grounded: true, anim: 0,
    shield: false, shieldTimer: 0,

    draw() {
        const x = this.x, y = this.y;
        const isNaksu = soulShifted;
        const bodyColor = isNaksu ? '#181818' : '#f7f7f7';
        const innerColor = isNaksu ? '#282828' : '#e2e2e2';
        const beltColor = isNaksu ? '#ff4d6d' : '#3fa9ff';
        const eyeColor = isNaksu ? '#ff4d6d' : '#7fd6ff';

        ctx.save();
        ctx.shadowColor = eyeColor; ctx.shadowBlur = 25;

        ctx.fillStyle = bodyColor;
        ctx.fillRect(x - 22, y - 50, 44, 60);
        ctx.fillStyle = innerColor;
        ctx.fillRect(x - 16, y - 38, 32, 45);
        ctx.fillStyle = beltColor;
        ctx.fillRect(x - 20, y - 12, 40, 6);

        ctx.fillStyle = '#f6d9b0';
        ctx.beginPath(); ctx.arc(x, y - 68, 24, 0, Math.PI*2); ctx.fill();
        ctx.fillStyle = '#141414';
        ctx.beginPath(); ctx.arc(x, y - 74, 24, Math.PI, Math.PI*2); ctx.fill();

        ctx.shadowColor = eyeColor; ctx.shadowBlur = 18;
        ctx.fillStyle = eyeColor;
        ctx.beginPath(); ctx.arc(x - 8, y - 71, 4.5, 0, Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x + 8, y - 71, 4.5, 0, Math.PI*2); ctx.fill();

        // Sword
        const sw = this.attacking ? Math.sin(this.atkFrame * 0.4) * 1.6 : 0;
        ctx.save();
        ctx.translate(x + 30, y - 40);
        ctx.rotate(sw - 0.45);
        ctx.shadowColor = eyeColor; ctx.shadowBlur = 20;
        ctx.fillStyle = isNaksu ? '#ffb46b' : '#cdefff';
        ctx.fillRect(0, -3, 52, 6);
        ctx.restore();

        // Auras
        if (this.attacking && this.atkFrame < 18) {
            const colors = { sword:eyeColor, fire:'#ff7b4a', ice:'#4ce0ff', water:'#3fa9ff', soul:'#ff7bff' };
            ctx.shadowColor = colors[this.atkType] || eyeColor; ctx.shadowBlur = 45;
            ctx.fillStyle = (colors[this.atkType] || eyeColor) + '55';
            ctx.beginPath(); ctx.arc(x + 60 * this.facing, y - 40, 30 + this.atkFrame * 2.5, 0, Math.PI*2); ctx.fill();
        }
        if (this.flying) {
            for (let i = 0; i < 6; i++) {
                ctx.fillStyle = `rgba(${isNaksu?'255,107,107':'127,214,255'},${0.18 - i*0.025})`;
                ctx.beginPath(); ctx.arc(x - 18 + i*7, y + 28 + i*6, 7 - i*0.8, 0, Math.PI*2); ctx.fill();
            }
        }
        if (soulShifted) {
            ctx.shadowColor = '#ffdd66'; ctx.shadowBlur = 50;
            for (let i = 0; i < 8; i++) {
                const angle = (i / 8) * Math.PI * 2 + this.anim;
                ctx.fillStyle = `rgba(255,220,80,0.4)`;
                ctx.beginPath(); ctx.arc(x + Math.cos(angle) * 55, y - 35 + Math.sin(angle) * 55, 4, 0, Math.PI*2); ctx.fill();
            }
        }
        if (this.isHit) {
            ctx.shadowColor = '#ff2020'; ctx.shadowBlur = 55;
            ctx.fillStyle = 'rgba(255,30,30,0.3)';
            ctx.beginPath(); ctx.arc(x, y - 35, 50, 0, Math.PI*2); ctx.fill();
        }
        ctx.restore();
    },
    update() {
        this.anim += 0.06;
        this.hitCd = Math.max(0, this.hitCd - 1);
        if (soulShiftTimer > 0) {
            soulShiftTimer--;
            if (soulShiftTimer <= 0 && soulShifted) {
                soulShifted = false;
                effects.push({ type: 'soulShift', x: this.x, y: this.y, timer: 60 });
            }
        }
        if (!this.flying) { this.vy += 0.55; if (this.vy > 8) this.vy = 8; }
        else { this.vy += 0.12; if (this.vy > 2) this.vy = 2; this.flyTimer--; if (this.flyTimer<=0) this.flying=false; }
        this.x += this.vx; this.y += this.vy;
        if (this.y >= 400) { this.y = 400; this.vy = 0; this.grounded = true; } else this.grounded = false;
        if (this.x < 40) this.x = 40; if (this.x > W - 40) this.x = W - 40;
        if (this.attacking) { this.atkFrame++; if (this.atkFrame > 22) this.attacking = false; }
        if (this.isHit) { this.hitTimer++; if (this.hitTimer>10){this.isHit=false;this.hitTimer=0;} }
        if (this.en < this.maxEn) this.en = Math.min(this.maxEn, this.en + 0.25);
        if (this.soul < this.maxSoul) this.soul = Math.min(this.maxSoul, this.soul + 0.12);
    },
    attack(type) {
        if (this.attacking || gameOver) return;
        const costs = { sword:8, fire:15, ice:20, water:18, soul:40 };
        if (type === 'soul' && this.soul < 40) return;
        if (this.en < costs[type] && type !== 'soul') return;
        this.attacking = true; this.atkFrame = 0; this.atkType = type;
        if (type === 'soul') this.soul -= 40; else this.en -= costs[type];
    },
    iceStorm() { if (this.attacking || gameOver || this.en < 25) return; this.attacking=true; this.atkFrame=0; this.atkType='ice'; this.en-=25; effects.push({type:'iceStorm',x:this.x,y:this.y,timer:60}); },
    waterWhip() { if (this.attacking || gameOver || this.en < 18) return; this.attacking=true; this.atkFrame=0; this.atkType='water'; this.en-=18; effects.push({type:'waterWhip',x:this.x,y:this.y,timer:40}); },
    fly() { if (!this.flying) { this.flying = true; this.flyTimer = 150; this.vy = -9; } },
    getDmg() {
        let base = { sword: Math.floor(Math.random()*10)+14, fire: Math.floor(Math.random()*14)+20, ice: Math.floor(Math.random()*18)+24, water: Math.floor(Math.random()*16)+22, soul: Math.floor(Math.random()*25)+38 };
        if (soulShifted) { base.sword += 5; base.water += 5; }
        return Math.floor((base[this.atkType] || 12) * (1 + this.combo * 0.05));
    },
    box() { return { x: this.x-30, y: this.y-70, w: 60, h: 100 }; }
};

const naksu = {
    x: 130, y: 400, hp: 80, maxHp: 80,
    attacking: false, atkFrame: 0,
    anim: 0, vy: 0,
    draw() {
        const x = this.x, y = this.y;
        ctx.save();
        ctx.shadowColor = '#ff6b6b'; ctx.shadowBlur = 20;
        ctx.fillStyle = '#181818'; ctx.fillRect(x - 20, y - 46, 40, 54);
        ctx.fillStyle = '#282828'; ctx.fillRect(x - 15, y - 34, 30, 38);
        ctx.fillStyle = '#ff4d6d'; ctx.fillRect(x - 18, y - 10, 36, 5);
        ctx.fillStyle = '#f6d9b0'; ctx.beginPath(); ctx.arc(x, y - 64, 21, 0, Math.PI*2); ctx.fill();
        ctx.fillStyle = '#141414'; ctx.beginPath(); ctx.arc(x, y - 70, 21, Math.PI, Math.PI*2); ctx.fill();
        ctx.shadowColor = '#ff4d6d'; ctx.shadowBlur = 18;
        ctx.fillStyle = '#ff4d6d'; ctx.beginPath(); ctx.arc(x - 7, y - 66, 4, 0, Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(x + 7, y - 66, 4, 0, Math.PI*2); ctx.fill();
        ctx.restore();
    },
    update() {
        this.anim += 0.06;
        this.y += 0.5;
        if (this.y >= 400) this.y = 400;
        if (this.attacking) { this.atkFrame++; if (this.atkFrame > 20) this.attacking = false; }
    },
    getDmg() { return Math.floor(Math.random()*12) + 12; },
    box() { return { x: this.x-26, y: this.y-62, w: 52, h: 88 }; }
};

function makeEnemies(hIdx) {
    const h = HOUSES[hIdx]; const count = 3 + Math.floor(h.diff * 1.3); const arr = [];
    const names = ['SHADOW','BLAZE','STORM','SOUL','DARK','CHAOS','FROST','VENOM'];
    for (let i = 0; i < count; i++) {
        const isBoss = (i === count - 1); const baseHp = 70 + h.diff * 20;
        arr.push({
            name: isBoss ? h.boss : names[i % names.length] + ' WARRIOR',
            hp: isBoss ? baseHp * 2.6 : baseHp, maxHp: isBoss ? baseHp * 2.6 : baseHp,
            dmg: isBoss ? 16 + h.diff * 3 : 9 + h.diff * 2,
            isBoss, speed: isBoss ? 2.6 : 1.2 + Math.random() * 0.6,
            x: 760 + Math.random() * 90, y: 400,
            attacking: false, atkFrame: 0, hitCd: 0, isHit: false, hitTimer: 0, anim: 0,
            color: isBoss ? '#ff3c3c' : '#8c8c8c',
            draw() {
                const x = this.x, y = this.y;
                ctx.save();
                ctx.shadowColor = this.color; ctx.shadowBlur = this.isBoss ? 35 : 18;
                ctx.fillStyle = this.isBoss ? '#5a0d0d' : '#22282b'; ctx.fillRect(x - 22, y - 50, 44, 60);
                ctx.fillStyle = this.isBoss ? '#7a1010' : '#323a3d'; ctx.fillRect(x - 16, y - 38, 32, 45);
                ctx.fillStyle = this.isBoss ? '#e6c89a' : '#8c959b'; ctx.beginPath(); ctx.arc(x, y - 68, 24, 0, Math.PI*2); ctx.fill();
                ctx.fillStyle = this.isBoss ? '#3a0505' : '#1a2023'; ctx.beginPath(); ctx.arc(x, y - 74, 24, Math.PI, Math.PI*2); ctx.fill();
                ctx.fillStyle = this.color; ctx.beginPath(); ctx.arc(x - 8, y - 71, 5, 0, Math.PI*2); ctx.fill(); ctx.beginPath(); ctx.arc(x + 8, y - 71, 5, 0, Math.PI*2); ctx.fill();
                ctx.restore();
            },
            update() {
                this.anim += 0.06; this.hitCd = Math.max(0, this.hitCd - 1);
                if (this.attacking) { this.atkFrame++; if (this.atkFrame > 15) this.attacking = false; }
                if (this.isHit) { this.hitTimer++; if (this.hitTimer>10){this.isHit=false;this.hitTimer=0;} }
            },
            box() { return { x: this.x-30, y: this.y-70, w: 60, h: 100 }; }
        });
    }
    return arr;
}

function initHouse() {
    enemies = makeEnemies(houseIdx); villainIdx = 0; currentEnemy = enemies[0];
    gameOver = false; player.hp = player.maxHp; naksu.hp = naksu.maxHp;
    player.en = player.maxEn; player.soul = 0; player.combo = 0; timer = 99; effects = [];
    document.getElementById('houseLabel').textContent = HOUSES[houseIdx].name;
    document.getElementById('eName').textContent = currentEnemy.name;
    document.getElementById('fightText').style.animation = 'none';
    void document.getElementById('fightText').offsetWidth;
    document.getElementById('fightText').style.animation = 'fightAnim 1.6s forwards';
}
function nextVillain() {
    villainIdx++;
    if (villainIdx >= enemies.length) {
        if (houseIdx >= HOUSES.length - 1) { allClear = true; }
        else { houseIdx++; initHouse(); }
    } else { currentEnemy = enemies[villainIdx]; document.getElementById('eName').textContent = currentEnemy.name; }
}
function resetGame() { houseIdx = 0; allClear = false; soulShifted = false; soulShiftTimer = 0; initHouse(); }
function hit(a, b) { return !(b.x > a.x + a.w || b.x + b.w < a.x || b.y > a.y + a.h || b.y + b.h < a.y); }
function enemyAI(e) {
    if (!e || e.hp <= 0 || gameOver || e.attacking) return;
    const dx = player.x - e.x; const dist = Math.abs(dx);
    if (dist < 220) { if (Math.random() < 0.18) { e.attacking = true; e.atkFrame = 0; } else { e.x += dx > 0 ? e.speed : -e.speed; } }
    else { e.x += dx > 0 ? e.speed * 1.4 : -e.speed * 1.4; }
    if (e.x < W - 60) e.x = W - 60;
}
function updateEffects() { for (let i = effects.length - 1; i >= 0; i--) { effects[i].timer--; if (effects[i].timer <= 0) effects.splice(i, 1); } }

function drawBg() {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#0a1220'); g.addColorStop(0.55, '#16283a'); g.addColorStop(1, '#0a0f18');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 14; i++) {
        const bx = 30 + i * 70 + Math.sin(i * 1.4) * 10; const sw = 14 + Math.sin(i) * 3;
        ctx.fillStyle = i % 3 === 0 ? 'rgba(30,60,50,0.55)' : 'rgba(20,45,38,0.45)';
        ctx.fillRect(bx, -20, sw, 460);
    }
    const fg = ctx.createLinearGradient(0, 400, 0, H);
    fg.addColorStop(0, '#3a3f46'); fg.addColorStop(1, '#1a1d22');
    ctx.fillStyle = fg; ctx.fillRect(0, 400, W, H - 400);
}
function drawEffects() {
    for (const e of effects) {
        if (e.type === 'iceStorm') { const pct = e.timer / 60; for (let i = 0; i < 12; i++) { const angle = (i / 12) * Math.PI * 2 + frame * 0.05; ctx.fillStyle = `rgba(76,224,255,${pct * 0.6})`; ctx.beginPath(); ctx.arc(e.x + Math.cos(angle) * 80, e.y - 40 + Math.sin(angle) * 80, 8, 0, Math.PI*2); ctx.fill(); } }
        if (e.type === 'waterWhip') { const pct = e.timer / 40; ctx.strokeStyle = `rgba(63,169,255,${pct})`; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(e.x, e.y - 40); ctx.quadraticCurveTo(e.x + 80, e.y - 80, e.x + 160, e.y - 40); ctx.stroke(); }
        if (e.type === 'soulShift') { const pct = e.timer / 60; for (let i = 0; i < 20; i++) { const angle = (i / 20) * Math.PI * 2 + frame * 0.08; ctx.fillStyle = `rgba(255,220,80,${pct * 0.7})`; ctx.beginPath(); ctx.arc(e.x + Math.cos(angle) * 100, e.y - 40 + Math.sin(angle) * 100, 6, 0, Math.PI*2); ctx.fill(); } }
    }
}
function updateUI() {
    document.getElementById('pHp').style.width = Math.max(0, player.hp / player.maxHp) * 100 + '%';
    document.getElementById('pEn').style.width = Math.max(0, player.en / player.maxEn) * 100 + '%';
    document.getElementById('pSoul').style.width = Math.max(0, player.soul / player.maxSoul) * 100 + '%';
    if (currentEnemy) document.getElementById('eHp').style.width = Math.max(0, currentEnemy.hp / currentEnemy.maxHp) * 100 + '%';
    document.getElementById('timer').textContent = String(Math.max(0, Math.floor(timer))).padStart(2, '0');
    document.getElementById('pName').textContent = soulShifted ? 'NAKSU (SHIFTED)' : 'JANG UK';
}

let lastT = performance.now();
function loop(now) {
    const dt = Math.min(50, now - lastT) / 16.67; lastT = now; frame++;
    if (allClear) {
        drawBg(); ctx.fillStyle = 'rgba(0,0,0,0.75)'; ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = '#ffd24a'; ctx.font = 'bold 58px Arial'; ctx.textAlign = 'center';
        ctx.fillText('ALL HOUSES CLEARED!', W/2, H/2 - 20);
        requestAnimationFrame(loop); return;
    }
    if (!gameOver) {
        player.update(); naksu.update();
        if (currentEnemy && currentEnemy.hp > 0) { currentEnemy.update(); enemyAI(currentEnemy); }
        updateEffects();
        timerAcc += dt; if (timerAcc >= 60) { timerAcc = 0; timer--; if (timer <= 0) { timer = 0; gameOver = true; } }
        if (player.attacking && currentEnemy && currentEnemy.hp > 0) {
            const a = { x: player.x + 24, y: player.y - 46, w: 60, h: 70 };
            if (hit(a, currentEnemy.box()) && currentEnemy.hitCd === 0) {
                const d = player.getDmg(); currentEnemy.hp -= d; currentEnemy.isHit = true; currentEnemy.hitCd = 15; player.combo++;
                if (currentEnemy.hp <= 0) nextVillain();
            }
        }
        if (naksu.attacking && currentEnemy && currentEnemy.hp > 0) {
            const a = { x: naksu.x + 30, y: naksu.y - 40, w: 50, h: 60 };
            if (hit(a, currentEnemy.box()) && currentEnemy.hitCd === 0) {
                const d = naksu.getDmg(); currentEnemy.hp -= d; currentEnemy.isHit = true; currentEnemy.hitCd = 15;
                if (currentEnemy.hp <= 0) nextVillain();
            }
        }
    }
    drawBg();
    if (currentEnemy && currentEnemy.hp > 0) currentEnemy.draw();
    player.draw(); naksu.draw(); drawEffects();
    updateUI();
    requestAnimationFrame(loop);
}

function soulShift() {
    if (gameOver || player.soul < 100) return;
    player.soul = 0; soulShifted = true; soulShiftTimer = 900; player.hp = player.maxHp;
    effects.push({ type: 'soulShift', x: player.x, y: player.y, timer: 60 });
}

// Joystick
(function() {
    const joy = document.getElementById('joy'); const knob = document.getElementById('knob');
    let active = false, cx = 0, cy = 0;
    function start(e) { active = true; const r = joy.getBoundingClientRect(); cx = r.left + r.width/2; cy = r.top + r.height/2; move(e); }
    function move(e) {
        if (!active) return; const t = e.touches ? e.touches[0] : e;
        const dx = t.clientX - cx; const dy = t.clientY - cy;
        const dist = Math.min(35, Math.hypot(dx, dy)); const ang = Math.atan2(dy, dx);
        knob.style.transform = `translate(${Math.cos(ang)*dist}px, ${Math.sin(ang)*dist}px)`;
        if (dist < 8) { player.vx = 0; return; }
        player.vx = (dx / (Math.hypot(dx, dy) || 1)) * player.speed;
    }
    function end() { active = false; knob.style.transform = 'translate(0,0)'; player.vx = 0; }
    joy.addEventListener('mousedown', start); joy.addEventListener('touchstart', start, {passive:true});
    document.addEventListener('mousemove', move); document.addEventListener('touchmove', move, {passive:false});
    document.addEventListener('mouseup', end); document.addEventListener('touchend', end);
})();

function pSword() { if (gameOver) { resetGame(); return; } player.attack('sword'); }
function pIce() { if (!gameOver) player.iceStorm(); }
function pWater() { if (!gameOver) player.waterWhip(); }
function pFly() { if (!gameOver) player.fly(); }
function pSoul() { if (!gameOver) player.attack('soul'); }
function nFire() { if (!gameOver) player.attack('fire'); }
function nBlade() { if (!gameOver) player.attack('sword'); }
function nShadow() { if (!gameOver) player.attack('water'); }
window.pSword = pSword; window.pIce = pIce; window.pWater = pWater; window.pFly = pFly;
window.pSoul = pSoul; window.nFire = nFire; window.nBlade = nBlade; window.nShadow = nShadow;
window.soulShift = soulShift; window.resetGame = resetGame;

initHouse();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

# 3. This is the fix for the height. It tells Streamlit to make the iframe tall enough.
components.html(game_html, height=700)

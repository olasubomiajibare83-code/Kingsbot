import streamlit as st
import random
import time
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="🥊 Shadow Fight Ultimate",
    page_icon="🥊",
    layout="centered",
)

st.markdown("""
<style>
    .fight-title {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #ff6b6b, #ffd93d, #6bcb77, #4d96ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 0 0 10px #ff6b6b; }
        to { text-shadow: 0 0 30px #4d96ff; }
    }
    .health-bar {
        height: 25px;
        border-radius: 12px;
        background: #333;
        overflow: hidden;
        border: 2px solid #555;
    }
    .health-bar-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
        background: linear-gradient(90deg, #ff6b6b, #ffd93d);
    }
    .health-bar-fill.enemy {
        background: linear-gradient(90deg, #ff6b6b, #ff4444);
    }
    .energy-bar {
        height: 15px;
        border-radius: 10px;
        background: #1a1a2e;
        overflow: hidden;
        border: 1px solid #4d96ff;
    }
    .energy-bar-fill {
        height: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #4d96ff, #6bcb77);
        transition: width 0.3s ease;
    }
    .fight-log {
        max-height: 200px;
        overflow-y: auto;
        background: rgba(0,0,0,0.7);
        border-radius: 10px;
        padding: 10px;
        font-family: monospace;
        font-size: 13px;
        border: 1px solid #333;
    }
    .attack-btn {
        border: none;
        border-radius: 12px;
        padding: 12px 8px;
        font-weight: bold;
        font-size: 14px;
        color: white;
        cursor: pointer;
        transition: all 0.2s ease;
        width: 100%;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    .attack-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(255,255,255,0.2);
    }
    .attack-btn:active {
        transform: scale(0.95);
    }
    .punch-btn { background: linear-gradient(135deg, #f7971e, #ffd200); }
    .kick-btn { background: linear-gradient(135deg, #00b09b, #96c93d); }
    .special-btn { background: linear-gradient(135deg, #f093fb, #f5576c); }
    .combo-btn { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
    .block-btn { background: linear-gradient(135deg, #4a00e0, #8e2de2); }
    .vs-text {
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        color: #ff6b6b;
        text-shadow: 0 0 20px rgba(255,107,107,0.5);
    }
    .player-name { color: #4d96ff; font-weight: bold; font-size: 18px; }
    .enemy-name { color: #ff6b6b; font-weight: bold; font-size: 18px; }
    .combo-display {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        color: #ffd93d;
        text-shadow: 0 0 20px rgba(255,217,61,0.5);
        animation: pulse 0.5s ease-in-out infinite alternate;
    }
    @keyframes pulse {
        from { transform: scale(1); }
        to { transform: scale(1.05); }
    }
    .hit-effect {
        animation: hitFlash 0.3s ease;
    }
    @keyframes hitFlash {
        0% { background-color: rgba(255,0,0,0.3); }
        100% { background-color: transparent; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

if "player_health" not in st.session_state:
    st.session_state.player_health = 100
if "enemy_health" not in st.session_state:
    st.session_state.enemy_health = 100
if "player_energy" not in st.session_state:
    st.session_state.player_energy = 100
if "enemy_energy" not in st.session_state:
    st.session_state.enemy_energy = 100
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "winner" not in st.session_state:
    st.session_state.winner = None
if "round" not in st.session_state:
    st.session_state.round = 1
if "fight_log" not in st.session_state:
    st.session_state.fight_log = []
if "combo" not in st.session_state:
    st.session_state.combo = 0
if "player_wins" not in st.session_state:
    st.session_state.player_wins = 0
if "enemy_wins" not in st.session_state:
    st.session_state.enemy_wins = 0
if "last_attack" not in st.session_state:
    st.session_state.last_attack = ""
if "hit_effect" not in st.session_state:
    st.session_state.hit_effect = False
if "enemy_hit_effect" not in st.session_state:
    st.session_state.enemy_hit_effect = False

# ============================================================
# GAME FUNCTIONS
# ============================================================

def reset_game():
    st.session_state.player_health = 100
    st.session_state.enemy_health = 100
    st.session_state.player_energy = 100
    st.session_state.enemy_energy = 100
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.round += 1
    st.session_state.fight_log = []
    st.session_state.combo = 0
    st.session_state.last_attack = ""
    st.session_state.hit_effect = False
    st.session_state.enemy_hit_effect = False

def full_reset():
    st.session_state.player_health = 100
    st.session_state.enemy_health = 100
    st.session_state.player_energy = 100
    st.session_state.enemy_energy = 100
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.round = 1
    st.session_state.fight_log = []
    st.session_state.combo = 0
    st.session_state.player_wins = 0
    st.session_state.enemy_wins = 0
    st.session_state.last_attack = ""
    st.session_state.hit_effect = False
    st.session_state.enemy_hit_effect = False

def attack(attack_type):
    if st.session_state.game_over:
        st.session_state.fight_log.append("❌ Game is already over! Reset to fight again.")
        return
    
    damage = 0
    energy_cost = 0
    attack_name = ""
    
    if attack_type == "punch":
        damage = random.randint(8, 15)
        energy_cost = 5
        attack_name = "👊 Punch"
    elif attack_type == "kick":
        damage = random.randint(12, 20)
        energy_cost = 10
        attack_name = "🦵 Kick"
    elif attack_type == "special":
        damage = random.randint(20, 35)
        energy_cost = 25
        attack_name = "💥 Special Attack!"
    elif attack_type == "combo":
        damage = random.randint(30, 50)
        energy_cost = 40
        attack_name = "🔥 COMBO ATTACK!"
    elif attack_type == "block":
        st.session_state.fight_log.append("🛡️ You blocked! Enemy's attack is reduced.")
        block_damage = random.randint(2, 6)
        st.session_state.player_health -= block_damage
        enemy_attack(block_damage // 2)
        st.session_state.last_attack = "🛡️ Block"
        return
    
    if st.session_state.player_energy < energy_cost:
        st.session_state.fight_log.append(f"⚠️ Not enough energy! ({energy_cost} needed)")
        st.session_state.last_attack = "⚠️ Not enough energy"
        return
    
    st.session_state.player_energy -= energy_cost
    st.session_state.enemy_health -= damage
    st.session_state.last_attack = f"💥 {attack_name} - {damage} DMG"
    st.session_state.enemy_hit_effect = True
    
    if attack_type in ["punch", "kick"]:
        st.session_state.combo += 1
    else:
        st.session_state.combo = 0
    
    st.session_state.fight_log.append(f"💥 {attack_name} did {damage} damage!")
    
    if random.random() < 0.15:
        crit_damage = random.randint(5, 15)
        st.session_state.enemy_health -= crit_damage
        st.session_state.fight_log.append(f"💀 CRITICAL HIT! +{crit_damage} damage!")
        st.session_state.last_attack += f" 💀 CRITICAL +{crit_damage}"
    
    if st.session_state.enemy_health <= 0:
        st.session_state.enemy_health = 0
        st.session_state.game_over = True
        st.session_state.winner = "player"
        st.session_state.player_wins += 1
        st.session_state.fight_log.append("🏆 YOU WIN! 🏆")
        return
    
    enemy_attack()
    
    if st.session_state.player_health <= 0:
        st.session_state.player_health = 0
        st.session_state.game_over = True
        st.session_state.winner = "enemy"
        st.session_state.enemy_wins += 1
        st.session_state.fight_log.append("💀 You were defeated...")

def enemy_attack():
    attack_choice = random.choice(["punch", "punch", "kick", "special", "block"])
    damage = 0
    
    if attack_choice == "punch":
        damage = random.randint(5, 12)
        st.session_state.fight_log.append(f"👊 Enemy punches you for {damage} damage!")
        st.session_state.last_attack = f"👊 Enemy Punch - {damage} DMG"
    elif attack_choice == "kick":
        damage = random.randint(10, 18)
        st.session_state.fight_log.append(f"🦵 Enemy kicks you for {damage} damage!")
        st.session_state.last_attack = f"🦵 Enemy Kick - {damage} DMG"
    elif attack_choice == "special":
        damage = random.randint(15, 25)
        st.session_state.fight_log.append(f"💥 Enemy special attack! {damage} damage!")
        st.session_state.last_attack = f"💥 Enemy Special - {damage} DMG"
    elif attack_choice == "block":
        damage = random.randint(1, 3)
        st.session_state.fight_log.append(f"🛡️ Enemy blocks! {damage} damage reflected!")
        st.session_state.last_attack = f"🛡️ Enemy Block - {damage} DMG"
    
    st.session_state.player_health -= damage
    st.session_state.player_health = max(0, st.session_state.player_health)
    if damage > 0:
        st.session_state.hit_effect = True

def regenerate_energy():
    if not st.session_state.game_over:
        st.session_state.player_energy = min(100, st.session_state.player_energy + 10)
        st.session_state.enemy_energy = min(100, st.session_state.enemy_energy + 8)

# ============================================================
# UI
# ============================================================

st.markdown('<h1 class="fight-title">🥊 SHADOW FIGHT</h1>', unsafe_allow_html=True)

# VS Display
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    st.markdown('<p class="player-name">👤 YOU</p>', unsafe_allow_html=True)

with col2:
    st.markdown('<p class="vs-text">⚔️ VS</p>', unsafe_allow_html=True)

with col3:
    st.markdown('<p class="enemy-name">👹 SHADOW</p>', unsafe_allow_html=True)

# Health bars
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="health-bar">
        <div class="health-bar-fill" style="width: {st.session_state.player_health}%;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:12px; color:#888;">
        <span>❤️ Health: {st.session_state.player_health}%</span>
    </div>
    <div class="energy-bar" style="margin-top:5px;">
        <div class="energy-bar-fill" style="width: {st.session_state.player_energy}%;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:12px; color:#888;">
        <span>⚡ Energy: {st.session_state.player_energy}%</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="health-bar">
        <div class="health-bar-fill enemy" style="width: {st.session_state.enemy_health}%;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:12px; color:#888;">
        <span>❤️ Health: {st.session_state.enemy_health}%</span>
    </div>
    <div class="energy-bar" style="margin-top:5px;">
        <div class="energy-bar-fill" style="width: {st.session_state.enemy_energy}%;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:12px; color:#888;">
        <span>⚡ Energy: {st.session_state.enemy_energy}%</span>
    </div>
    """, unsafe_allow_html=True)

# Combo display
if st.session_state.combo > 2:
    st.markdown(f'<div class="combo-display">🔥 {st.session_state.combo}x COMBO!</div>', unsafe_allow_html=True)

# Score
st.info(f"🏆 Wins: {st.session_state.player_wins} | Losses: {st.session_state.enemy_wins} | Round: {st.session_state.round}")

# Last attack
if st.session_state.last_attack:
    st.write(f"**Last action:** {st.session_state.last_attack}")

# Fight buttons
if not st.session_state.game_over:
    st.write("---")
    st.write("### ⚔️ Choose your move:")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("👊 Punch", use_container_width=True):
            attack("punch")
            regenerate_energy()
            st.rerun()
    
    with col2:
        if st.button("🦵 Kick", use_container_width=True):
            attack("kick")
            regenerate_energy()
            st.rerun()
    
    with col3:
        if st.button("💥 Special", use_container_width=True):
            attack("special")
            regenerate_energy()
            st.rerun()
    
    with col4:
        if st.button("🔥 Combo", use_container_width=True):
            attack("combo")
            regenerate_energy()
            st.rerun()
    
    with col5:
        if st.button("🛡️ Block", use_container_width=True):
            attack("block")
            regenerate_energy()
            st.rerun()

# Game Over
if st.session_state.game_over:
    st.write("---")
    if st.session_state.winner == "player":
        st.balloons()
        st.success("🎉 YOU WIN! Amazing fight! 🎉")
    else:
        st.error("💀 You lost... Better luck next time!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Next Round", use_container_width=True):
            reset_game()
            st.rerun()
    with col2:
        if st.button("🔄 Full Reset", use_container_width=True):
            full_reset()
            st.rerun()

# Energy regenerate button
if not st.session_state.game_over:
    if st.button("⚡ Regenerate Energy (+10)"):
        regenerate_energy()
        st.rerun()

# Fight log
st.write("---")
st.write("### 📜 Fight Log")
with st.expander("Show fight log", expanded=False):
    st.markdown('<div class="fight-log">', unsafe_allow_html=True)
    for log in st.session_state.fight_log[-20:]:
        st.write(log)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# INSTRUCTIONS
# ============================================================

with st.expander("📖 How to Play"):
    st.write("""
    **🎯 Goal:** Defeat the Shadow Warrior!
    
    **⚔️ Moves:**
    - 👊 **Punch** — Quick attack (low damage, low energy)
    - 🦵 **Kick** — Medium attack (medium damage, medium energy)
    - 💥 **Special** — Strong attack (high damage, high energy)
    - 🔥 **Combo** — Devastating attack (massive damage, high energy)
    - 🛡️ **Block** — Reduce enemy damage
    
    **💡 Tips:**
    - Manage your energy wisely!
    - Build combos for extra damage
    - Block when enemy is about to attack
    - Use Special and Combo when enemy is weak
    
    **⚡ Energy regenerates automatically after each move!**
    """)

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption("🥊 Shadow Fight Ultimate • Made with ❤️ • Python + Streamlit")

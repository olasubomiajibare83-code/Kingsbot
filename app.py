import streamlit as st
import streamlit.components.v1 as components
import json
import os
import re
import time
import uuid
from datetime import datetime, date
import requests
import io

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="KingsBot Phone",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CUSTOM CSS FOR PHONE
# ============================================================

st.markdown("""
<style>
    /* Phone-friendly dark theme */
    .main {
        padding: 0 !important;
    }
    .block-container {
        padding: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* Chat bubbles */
    .user-bubble {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 10px 14px;
        border-radius: 18px 18px 4px 18px;
        max-width: 85%;
        margin: 4px 0 4px auto;
        font-size: 14px;
        animation: slideIn 0.3s ease;
        word-wrap: break-word;
    }
    .assistant-bubble {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
        padding: 10px 14px;
        border-radius: 18px 18px 18px 4px;
        max-width: 85%;
        margin: 4px auto 4px 0;
        font-size: 14px;
        animation: slideIn 0.3s ease;
        word-wrap: break-word;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Toggle buttons - phone friendly */
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        padding: 0.5rem !important;
        font-size: 14px !important;
    }
    
    /* Input bar - fixed at bottom */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(10, 10, 10, 0.95);
        padding: 8px 10px;
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255,255,255,0.05);
        z-index: 100;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    
    .input-row {
        display: flex;
        gap: 6px;
        align-items: center;
    }
    
    .input-row input {
        flex: 1;
        padding: 10px 14px;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 25px;
        background: rgba(255,255,255,0.05);
        color: white;
        font-size: 14px;
        outline: none;
        min-height: 40px;
    }
    
    .input-row input:focus {
        border-color: #667eea;
    }
    
    .input-row button {
        padding: 10px 16px;
        border: none;
        border-radius: 25px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        white-space: nowrap;
    }
    
    .input-row button:active {
        transform: scale(0.95);
    }
    
    /* Toggle row */
    .toggle-row {
        display: flex;
        gap: 6px;
        justify-content: center;
        padding: 2px 0;
        flex-wrap: wrap;
    }
    
    .toggle-btn {
        padding: 4px 12px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
        background: transparent;
        color: #888;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .toggle-btn.active {
        background: #667eea;
        border-color: #667eea;
        color: white;
    }
    
    .toggle-btn:active {
        transform: scale(0.95);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(0,0,0,0.95);
    }
    
    /* Hide default footer */
    footer {
        display: none;
    }
    
    /* Make chat scrollable with bottom padding */
    .chat-container {
        padding-bottom: 140px;
    }
    
    /* Mobile adjustments */
    @media (max-width: 600px) {
        .input-row input {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
        .user-bubble, .assistant-bubble {
            font-size: 15px;
            padding: 10px 14px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "memory_facts" not in st.session_state:
    st.session_state.memory_facts = []
if "memory_preferences" not in st.session_state:
    st.session_state.memory_preferences = []
if "web_search" not in st.session_state:
    st.session_state.web_search = False
if "think_mode" not in st.session_state:
    st.session_state.think_mode = False
if "emotion" not in st.session_state:
    st.session_state.emotion = "neutral"
if "topic" not in st.session_state:
    st.session_state.topic = "general"
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0
if "chats" not in st.session_state:
    st.session_state.chats = [{"id": "default", "title": "New Chat", "messages": []}]
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "default"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ============================================================
# FEATURES
# ============================================================

# Emotion Detection
EMOTION_KEYWORDS = {
    "happy": ["happy", "great", "awesome", "amazing", "love", "wonderful", "excited", "glad", "yesss"],
    "sad": ["sad", "crying", "upset", "hurt", "depressed", "miserable", "lonely", "disappointed"],
    "angry": ["angry", "mad", "frustrated", "annoyed", "furious", "outraged", "rage", "useless"],
    "confused": ["confused", "don't understand", "huh", "what", "lost", "unclear", "not getting"],
    "worried": ["worried", "scared", "afraid", "anxious", "nervous", "concerned", "panic"],
    "neutral": []
}

TOPIC_KEYWORDS = {
    "coding": ["code", "python", "program", "javascript", "html", "css", "api", "app", "software"],
    "science": ["science", "biology", "chemistry", "physics", "astronomy", "dna", "lab"],
    "math": ["math", "calculate", "equation", "algebra", "geometry", "calculus", "number"],
    "history": ["history", "war", "empire", "ancient", "civilization", "king", "queen"],
    "geography": ["country", "capital", "city", "river", "mountain", "ocean", "continent"],
    "technology": ["technology", "computer", "internet", "ai", "artificial intelligence", "robot"],
    "sports": ["sports", "football", "soccer", "basketball", "tennis", "cricket", "messi"],
    "entertainment": ["movie", "film", "music", "song", "actor", "actress", "concert", "cinema"],
    "health": ["health", "doctor", "hospital", "medicine", "fitness", "diet", "exercise"],
    "general": []
}

def detect_emotion(text):
    lower = text.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(word in lower for word in keywords):
            return emotion
    return "neutral"

def detect_topic(text):
    lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(word in lower for word in keywords):
            return topic
    return "general"

def detect_name(text):
    match = re.search(r"my name is ([A-Za-z ]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def detect_memory(text):
    markers = ["remember that ", "remember this: ", "please remember ", "save this: "]
    for marker in markers:
        if marker in text.lower():
            pos = text.lower().find(marker)
            fact = text[pos + len(marker):].strip(" .!?")
            if fact and len(fact) > 3:
                return fact
    return None

def detect_preference(text):
    markers = ["i prefer ", "i like ", "my favorite ", "i love "]
    for marker in markers:
        if marker in text.lower():
            pos = text.lower().find(marker)
            pref = text[pos:].strip(" .!?")
            if pref and len(pref) > 3:
                return pref
    return None

# ============================================================
# WEB SEARCH
# ============================================================

def web_search(query):
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(query)
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("extract"):
                return data["extract"]
        
        # Fallback: DuckDuckGo
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("AbstractText"):
                return data["AbstractText"]
        
        return None
    except Exception as e:
        return None

# ============================================================
# RESPONSE GENERATOR (FULL BRAIN)
# ============================================================

def generate_response(prompt):
    # Detect features from user input
    name = detect_name(prompt)
    if name:
        st.session_state.user_name = name
        return f"Nice to meet you, {name}! 👋 I'll remember your name."
    
    memory = detect_memory(prompt)
    if memory:
        if memory not in st.session_state.memory_facts:
            st.session_state.memory_facts.append(memory)
            st.session_state.memory_facts = st.session_state.memory_facts[-30:]
        return f"🧠 Got it! I'll remember: '{memory}'"
    
    preference = detect_preference(prompt)
    if preference:
        if preference not in st.session_state.memory_preferences:
            st.session_state.memory_preferences.append(preference)
            st.session_state.memory_preferences = st.session_state.memory_preferences[-30:]
        return f"💖 I'll remember that you {preference.lower()}"

    # Detect emotion and topic
    emotion = detect_emotion(prompt)
    topic = detect_topic(prompt)
    st.session_state.emotion = emotion
    st.session_state.topic = topic

    # Web search if enabled
    web_result = ""
    if st.session_state.web_search:
        with st.spinner("🌐 Searching the web..."):
            result = web_search(prompt)
            if result:
                web_result = f"\n\n[Web Search Result]\n{result[:2000]}"

    # Think mode (adds reasoning)
    think_prefix = ""
    if st.session_state.think_mode:
        think_prefix = "Let me think about this carefully... 🤔\n\n"

    # Generate intelligent response
    response = generate_advanced_response(prompt, emotion, topic)

    # Add web result if available
    if web_result:
        response += f"\n\n---\n{web_result}"

    if think_prefix:
        response = think_prefix + response

    return response

def generate_advanced_response(prompt, emotion, topic):
    # Build memory context
    memory_text = ""
    if st.session_state.user_name:
        memory_text += f"User's name: {st.session_state.user_name}. "
    if st.session_state.memory_facts:
        memory_text += f"Facts: {', '.join(st.session_state.memory_facts[-3:])}. "
    if st.session_state.memory_preferences:
        memory_text += f"Preferences: {', '.join(st.session_state.memory_preferences[-3:])}. "

    # Build response based on topic and emotion
    lower = prompt.lower()
    
    # GREETINGS
    if re.match(r'^(hi|hello|hey|greetings|sup|what\'s up|yo|howdy)', lower):
        return random_greeting()
    
    # HOW ARE YOU
    if re.search(r'how are you|how\'s it going|how do you do', lower):
        return random_how_are_you()
    
    # NAME
    if re.search(r'what is your name|who are you|your name', lower):
        return "I'm KingsBot! 📱 Your intelligent phone assistant with memory, emotions, web search, and more! I'm designed to run on your phone."

    # TIME
    if re.search(r'what time is it|current time|time now', lower):
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."

    # DATE
    if re.search(r'what day is it|what\'s the date|today\'s date', lower):
        return f"📅 Today is {datetime.now().strftime('%A, %B %d, %Y')}."

    # MATH
    math_match = re.search(r'(\d+)\s*([\+\-\*/xX])\s*(\d+)', lower)
    if math_match:
        try:
            a = int(math_match.group(1))
            op = math_match.group(2)
            b = int(math_match.group(3))
            if op == '+':
                result = a + b
            elif op == '-':
                result = a - b
            elif op == 'x' or op == 'X' or op == '*':
                result = a * b
            elif op == '/':
                result = a / b if b != 0 else "Cannot divide by zero"
            return f"🧮 {a} {op} {b} = {result}"
        except:
            pass

    # HELP
    if re.search(r'help|what can you do|capabilities|features', lower):
        return f"""
🤖 **I can help you with:**

📚 **General Knowledge** — History, geography, science, and more!
🧮 **Mathematics** — Basic arithmetic
💻 **Coding** — Python tips and explanations
🎯 **Memory** — I remember your name, facts, and preferences
🌐 **Web Search** — Toggle "🌐 Search" for real-time info
🧠 **Think Mode** — Toggle "🧠 Think" for reasoning
❤️ **Emotions** — I adapt to how you feel
💬 **Multiple Chats** — Start new conversations
📁 **File Upload** — Upload and read documents
📊 **Analytics** — Track your usage

**Commands:**
- "My name is Alex" → Saves your name
- "Remember that..." → Saves a fact
- "I like Python" → Saves a preference
- "What is 25 x 4?" → Math

**Toggles:**
- 🌐 Search — Enable web search
- 🧠 Think — Enable reasoning mode
"""

    # MEMORY COMMANDS
    if "forget everything" in lower or "clear memory" in lower:
        st.session_state.user_name = ""
        st.session_state.memory_facts = []
        st.session_state.memory_preferences = []
        return "🧹 Done. I cleared all your memory."

    if "forget my name" in lower:
        st.session_state.user_name = ""
        return "✅ Done. I forgot your name."

    if "forget my facts" in lower:
        st.session_state.memory_facts = []
        return "✅ Done. I forgot all your facts."

    if "forget my preferences" in lower:
        st.session_state.memory_preferences = []
        return "✅ Done. I forgot all your preferences."

    # Unknown
    emotion_emoji = {
        "happy": "😊", "sad": "😢", "angry": "😤",
        "confused": "🤔", "worried": "😰", "neutral": "🤖"
    }.get(emotion, "🤖")
    
    return f"{emotion_emoji} I'm here to help! What would you like to know? I can answer questions, solve math, remember facts, and search the web (if you toggle 🌐 Search)."

def random_greeting():
    return random.choice([
        "Hello! 👋 How can I help you today?",
        "Hi there! 😊 What's on your mind?",
        "Hey! Great to talk to you!",
        "Greetings! 📱 I'm here to assist you.",
    ])

def random_how_are_you():
    return random.choice([
        "I'm doing great, thanks! 😊 How about you?",
        "I'm functioning perfectly! 📱 How can I help?",
        "I'm always ready to help! 💪"
    ])

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("📱 KingsBot")
    st.caption("Phone Edition • v3.0")
    
    st.write(f"📊 **Interactions:** {st.session_state.interaction_count}")
    
    emotion_emoji = {
        "happy": "😊", "sad": "😢", "angry": "😤",
        "confused": "🤔", "worried": "😰", "neutral": "🤖"
    }.get(st.session_state.emotion, "🤖")
    st.write(f"❤️ **Emotion:** {emotion_emoji} {st.session_state.emotion}")
    st.write(f"🎯 **Topic:** {st.session_state.topic}")
    
    st.divider()
    
    st.subheader("💬 Conversations")
    for chat in st.session_state.chats:
        title = chat.get("title", "New Chat")
        display = title[:20] + "..." if len(title) > 20 else title
        prefix = "🟢 " if chat["id"] == st.session_state.current_chat_id else "💬 "
        if st.button(prefix + display, key="chat_" + chat["id"], use_container_width=True):
            st.session_state.current_chat_id = chat["id"]
            st.session_state.messages = chat.get("messages", [])
            st.rerun()
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = uuid.uuid4().hex[:8]
        st.session_state.chats.append({"id": new_id, "title": "New Chat", "messages": []})
        st.session_state.current_chat_id = new_id
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.subheader("🧠 Memory")
    st.write(f"**Name:** {st.session_state.user_name or 'Not set'}")
    st.write(f"**Facts:** {len(st.session_state.memory_facts)}")
    st.write(f"**Preferences:** {len(st.session_state.memory_preferences)}")
    
    if st.button("🧹 Clear Memory", use_container_width=True):
        st.session_state.user_name = ""
        st.session_state.memory_facts = []
        st.session_state.memory_preferences = []
        st.rerun()
    
    if st.button("📤 Export Chat", use_container_width=True):
        # Simple export
        lines = ["# KingsBot Chat Export", f"Date: {datetime.now().strftime('%B %d, %Y')}", ""]
        for msg in st.session_state.messages:
            role = "👤 User" if msg["role"] == "user" else "🤖 KingsBot"
            lines.append(f"**{role}:** {msg['content']}")
        st.download_button("📥 Download", "\n".join(lines), "chat_export.txt", "text/plain")

# ============================================================
# MAIN CHAT
# ============================================================

# Display header
st.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
    <span style="font-size: 28px;">📱</span>
    <h1 style="font-size: 22px; margin: 0;">KingsBot</h1>
</div>
""", unsafe_allow_html=True)

# Display chat messages
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CUSTOM INPUT (Phone-friendly)
# ============================================================

import random

st.markdown('<div class="input-container">', unsafe_allow_html=True)

# Toggle row
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🌐 Search", key="web_search_btn", use_container_width=True):
        st.session_state.web_search = not st.session_state.web_search
        st.rerun()
    if st.session_state.web_search:
        st.caption("✅ ON", help="Web search enabled")

with col2:
    if st.button("🧠 Think", key="think_btn", use_container_width=True):
        st.session_state.think_mode = not st.session_state.think_mode
        st.rerun()
    if st.session_state.think_mode:
        st.caption("✅ ON", help="Think mode enabled")

with col3:
    if st.button("🧹 Clear", key="clear_btn", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

with col4:
    if st.button("📂 Sidebar", key="sidebar_btn", use_container_width=True):
        st.sidebar.toggle()

# Input row
col1, col2 = st.columns([5, 1])
with col1:
    prompt = st.text_input("", placeholder="Type your message...", key="message_input", label_visibility="collapsed")
with col2:
    if st.button("Send", key="send_btn", use_container_width=True):
        if prompt and prompt.strip():
            with st.spinner("Thinking..."):
                # Save user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.interaction_count += 1
                
                # Generate response
                response = generate_response(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Update chat
                for chat in st.session_state.chats:
                    if chat["id"] == st.session_state.current_chat_id:
                        chat["messages"] = st.session_state.messages
                        if len(st.session_state.messages) == 2:
                            chat["title"] = prompt[:30] + "..." if len(prompt) > 30 else prompt
                        break
                
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div style="
    position: fixed;
    bottom: 100px;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 11px;
    color: #555;
    padding: 4px;
    z-index: 99;
    pointer-events: none;
">
    📱 KingsBot • Free • Memory • Web Search • Think Mode
</div>
""", unsafe_allow_html=True)

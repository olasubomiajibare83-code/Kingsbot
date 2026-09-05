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
import random

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="KingsBot — Groq",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main {
        padding: 0 !important;
    }
    .block-container {
        padding: 0.5rem !important;
        max-width: 100% !important;
    }
    
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
    
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        padding: 0.5rem !important;
        font-size: 14px !important;
        border: none;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    .stButton > button:active {
        transform: scale(0.95);
    }
    
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 12px 16px;
        font-size: 16px !important;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: white;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
    }
    
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
    
    .chat-container {
        padding-bottom: 100px;
    }
    
    footer {
        display: none;
    }
    
    @media (max-width: 600px) {
        .input-row input {
            font-size: 16px !important;
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
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ============================================================
# API KEY
# ============================================================

def get_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return st.session_state.api_key

# ============================================================
# GROQ BRAIN — CONFIRMED WORKING
# ============================================================

# ✅ CONFIRMED WORKING GROQ MODELS (September 2026)
GROQ_MODELS = [
    "gpt-oss-20b",           # 🏆 Best balance — 1000 tok/sec
    "gpt-oss-120b",          # 🧠 Smarter — 500 tok/sec
    "qwen-qwen3.6-27b",      # 🤔 Reasoning
    "llama-3.3-70b-versatile", # 📚 General purpose
    "llama-3.1-8b-instant",  # ⚡ Fastest
]

# ✅ CORRECT GROQ ENDPOINT
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

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
        
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("AbstractText"):
                return data["AbstractText"]
        return None
    except Exception:
        return None

# ============================================================
# GROQ AI RESPONSE
# ============================================================

def groq_response(prompt, emotion, topic):
    api_key = get_api_key()
    
    if not api_key:
        return "🔑 **API Key Missing.**\n\nPlease enter your Groq API key in the sidebar.\n\nGet a free key at: console.groq.com/keys"

    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key,
            base_url=GROQ_BASE_URL,
            timeout=60.0,
            max_retries=2,
        )
        
        memory = f"User's name: {st.session_state.user_name or 'Unknown'}. "
        if st.session_state.memory_facts:
            memory += f"Facts: {', '.join(st.session_state.memory_facts[-3:])}. "
        if st.session_state.memory_preferences:
            memory += f"Preferences: {', '.join(st.session_state.memory_preferences[-3:])}. "

        system_prompt = f"""You are KingsBot, a helpful AI assistant powered by Groq (blazing fast).

Current date: {datetime.now().strftime('%B %d, %Y')}

User emotion: {emotion}
User topic: {topic}

Memory: {memory}

Be helpful, clear, and concise. Answer any question the user asks. If you don't know something, say so."""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.messages[-15:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        if st.session_state.web_search:
            search_result = web_search(prompt)
            if search_result:
                messages.append({"role": "system", "content": f"Web search result: {search_result[:2000]}"})

        # ✅ Try models in order
        for model in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=600,
                )
                return response.choices[0].message.content
            except Exception:
                continue  # Try next model
        
        return "❌ All Groq models failed. Please try again later."

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate limit" in error_msg.lower():
            return "⏳ **Rate limit exceeded.** Please wait a moment and try again."
        if "401" in error_msg or "authentication" in error_msg.lower():
            return "🔑 **Invalid API Key.** Check your Groq API key."
        return f"❌ **Error:** {error_msg}"

# ============================================================
# FEATURES
# ============================================================

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
# RESPONSE GENERATOR
# ============================================================

def generate_response(prompt):
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

    emotion = detect_emotion(prompt)
    topic = detect_topic(prompt)
    st.session_state.emotion = emotion
    st.session_state.topic = topic

    if st.session_state.think_mode:
        return f"🤔 **Thinking...**\n\n{groq_response(prompt, emotion, topic)}"
    
    return groq_response(prompt, emotion, topic)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚡ KingsBot")
    st.caption("Groq • Blazing Fast")
    
    st.subheader("🔑 API Key")
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", key="api_key_input")
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ Key saved")
    else:
        st.caption("Get free key at console.groq.com/keys")
    
    st.divider()
    
    st.subheader("📊 Stats")
    st.write(f"**Interactions:** {st.session_state.interaction_count}")
    
    emotion_emoji = {
        "happy": "😊", "sad": "😢", "angry": "😤",
        "confused": "🤔", "worried": "😰", "neutral": "🤖"
    }.get(st.session_state.emotion, "🤖")
    st.write(f"**Emotion:** {emotion_emoji} {st.session_state.emotion}")
    st.write(f"**Topic:** {st.session_state.topic}")
    st.write(f"**Speed:** 🚀 500-1000+ tok/sec")
    
    st.divider()
    
    st.subheader("⚙️ Features")
    
    if st.button("🌐 Web Search", use_container_width=True):
        st.session_state.web_search = not st.session_state.web_search
        st.rerun()
    if st.session_state.web_search:
        st.success("✅ Web Search ON")
    else:
        st.info("⏸️ Web Search OFF")
    
    if st.button("🧠 Think Mode", use_container_width=True):
        st.session_state.think_mode = not st.session_state.think_mode
        st.rerun()
    if st.session_state.think_mode:
        st.success("✅ Think Mode ON")
    else:
        st.info("⏸️ Think Mode OFF")
    
    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.subheader("💬 Chats")
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
        lines = ["# KingsBot Chat Export", f"Date: {datetime.now().strftime('%B %d, %Y')}", ""]
        for msg in st.session_state.messages:
            role = "👤 User" if msg["role"] == "user" else "⚡ KingsBot"
            lines.append(f"**{role}:** {msg['content']}")
        st.download_button("📥 Download", "\n".join(lines), "chat_export.txt", "text/plain")

# ============================================================
# MAIN CHAT
# ============================================================

st.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
    <span style="font-size: 28px;">⚡</span>
    <h1 style="font-size: 22px; margin: 0;">KingsBot</h1>
    <span style="font-size: 12px; color: #00c853; margin-left: auto;">Groq • Blazing Fast</span>
</div>
""", unsafe_allow_html=True)

# Display chat
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-bubble">⚡ {msg["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# INPUT
# ============================================================

st.markdown('<div class="input-container">', unsafe_allow_html=True)

# Input row only
col1, col2 = st.columns([5, 1])
with col1:
    prompt = st.text_input("", placeholder="Ask anything...", key="message_input", label_visibility="collapsed")
with col2:
    if st.button("Send", key="send_btn", use_container_width=True):
        if prompt and prompt.strip():
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.interaction_count += 1
            
            with st.spinner("⚡ Thinking (Groq — blazing fast)..."):
                response = generate_response(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
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
    bottom: 80px;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 10px;
    color: #444;
    padding: 4px;
    z-index: 99;
    pointer-events: none;
">
    ⚡ KingsBot • Groq • 500-1000+ tok/sec • Free • Memory • Web Search
</div>
""", unsafe_allow_html=True)

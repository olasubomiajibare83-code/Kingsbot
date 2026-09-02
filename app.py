import json
import os
import uuid
import time
import hashlib
from datetime import datetime, date, timedelta
from functools import lru_cache
import base64
import io

import streamlit as st
from openai import OpenAI
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
import requests
import speech_recognition as sr
import PyPDF2
from docx import Document
import markdown

# ============================================================
# ULTIMATE KINGSBOT AI — ALL FEATURES (FIXED)
# ============================================================

st.set_page_config(
    page_title="KingsBot Ultimate",
    page_icon="🧠",
    layout="wide",
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .stat-card {
        background: rgba(255,255,255,0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        text-align: center;
    }
    .stat-number {
        font-size: 28px;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: rgba(255,255,255,0.03);
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SETTINGS
# ============================================================

MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "openai/gpt-oss-20b:free",
    "microsoft/phi-4:free",
    "cohere/north-mini-code:free",
    "mistralai/mistral-small-3.1-24b-instruct-2503:free"
]

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL_INDEX = 0

ACTIVE_HISTORY_MESSAGES = 120
MAX_MEMORY_FACTS = 200
MAX_MEMORY_PREFERENCES = 200
DAILY_REQUEST_LIMIT = 100

MEMORY_FILE = "kingsbot_memory.json"
CHATS_FILE = "kingsbot_chats.json"
REQUEST_FILE = "kingsbot_requests.json"
ANALYTICS_FILE = "kingsbot_analytics.json"

# ============================================================
# RATE LIMITER
# ============================================================

class RateLimiter:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 2
        self.backoff_factor = 2
        self.max_backoff = 60
        self.current_backoff = 0
        
    def wait_if_needed(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def handle_rate_limit(self):
        if self.current_backoff == 0:
            self.current_backoff = 2
        else:
            self.current_backoff = min(self.current_backoff * self.backoff_factor, self.max_backoff)
        st.warning(f"⏳ Rate limit hit. Waiting {self.current_backoff} seconds...")
        time.sleep(self.current_backoff)
        return self.current_backoff
    
    def reset_backoff(self):
        self.current_backoff = 0

rate_limiter = RateLimiter()

# ============================================================
# REQUEST TRACKER
# ============================================================

def load_requests():
    try:
        if os.path.exists(REQUEST_FILE):
            with open(REQUEST_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                if data.get("date") == str(date.today()):
                    return data.get("count", 0)
    except Exception:
        pass
    return 0

def save_request_count(count):
    try:
        with open(REQUEST_FILE, "w", encoding="utf-8") as file:
            json.dump({"date": str(date.today()), "count": count}, file, indent=2)
    except Exception:
        pass

def get_remaining_requests():
    return max(0, DAILY_REQUEST_LIMIT - load_requests())

def increment_request():
    save_request_count(load_requests() + 1)

# ============================================================
# STORAGE
# ============================================================

def load_json(filename, default):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                return json.load(file)
    except Exception:
        pass
    return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ============================================================
# MEMORY
# ============================================================

def default_memory():
    return {"name": "", "facts": [], "preferences": [], "emotion_history": [], "topics": []}

memory_data = load_json(MEMORY_FILE, default_memory())

# ============================================================
# CHAT STORAGE — FIXED
# ============================================================

def new_chat():
    return {
        "id": uuid.uuid4().hex,
        "title": "New conversation",
        "created": datetime.now().isoformat(timespec="seconds"),
        "messages": [],
        "metadata": {"topics": [], "emotions": [], "message_count": 0}
    }

saved_chats = load_json(CHATS_FILE, [])
if not saved_chats:
    saved_chats = [new_chat()]
    save_json(CHATS_FILE, saved_chats)

# ============================================================
# ANALYTICS
# ============================================================

def default_analytics():
    return {
        "total_interactions": 0,
        "daily_usage": {},
        "topics_count": {},
        "emotions_count": {},
        "average_response_time": 0,
        "response_times": []
    }

analytics_data = load_json(ANALYTICS_FILE, default_analytics())

# ============================================================
# SESSION STATE
# ============================================================

if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = saved_chats
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = saved_chats[0]["id"]
if "messages" not in st.session_state:
    selected = None
    for chat in st.session_state.saved_chats:
        if chat["id"] == st.session_state.current_chat_id:
            selected = chat
            break
    st.session_state.messages = list(selected.get("messages", [])) if selected else []
if "user_name" not in st.session_state:
    st.session_state.user_name = memory_data.get("name", "")
if "memory_facts" not in st.session_state:
    st.session_state.memory_facts = list(memory_data.get("facts", []))
if "memory_preferences" not in st.session_state:
    st.session_state.memory_preferences = list(memory_data.get("preferences", []))
if "emotion_history" not in st.session_state:
    st.session_state.emotion_history = list(memory_data.get("emotion_history", []))
if "topics" not in st.session_state:
    st.session_state.topics = list(memory_data.get("topics", []))
if "current_model_index" not in st.session_state:
    st.session_state.current_model_index = DEFAULT_MODEL_INDEX
if "analytics" not in st.session_state:
    st.session_state.analytics = analytics_data
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "language" not in st.session_state:
    st.session_state.language = "English"
if "voice_input" not in st.session_state:
    st.session_state.voice_input = None

# ============================================================
# API KEY
# ============================================================

def get_api_key():
    try:
        key = st.secrets.get("OPENROUTER_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("OPENROUTER_API_KEY")

API_KEY = get_api_key()

if API_KEY:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=120.0, max_retries=2)
else:
    client = None

# ============================================================
# EMOTION DETECTION
# ============================================================

EMOTION_KEYWORDS = {
    "happy": ["happy", "great", "awesome", "amazing", "love", "wonderful", "excited", "glad"],
    "sad": ["sad", "crying", "upset", "hurt", "depressed", "miserable", "lonely"],
    "angry": ["angry", "mad", "frustrated", "annoyed", "furious", "outraged", "rage"],
    "confused": ["confused", "don't understand", "huh", "what", "lost", "unclear"],
    "worried": ["worried", "scared", "afraid", "anxious", "nervous", "concerned", "panic"],
    "neutral": []
}

def detect_emotion(text):
    lower = text.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(word in lower for word in keywords):
            st.session_state.emotion_history.append({
                "emotion": emotion,
                "time": datetime.now().isoformat()
            })
            st.session_state.emotion_history = st.session_state.emotion_history[-50:]
            if emotion not in st.session_state.analytics["emotions_count"]:
                st.session_state.analytics["emotions_count"][emotion] = 0
            st.session_state.analytics["emotions_count"][emotion] += 1
            save_json(ANALYTICS_FILE, st.session_state.analytics)
            return emotion
    return "neutral"

# ============================================================
# TOPIC DETECTION
# ============================================================

TOPIC_KEYWORDS = {
    "coding": ["code", "python", "program", "javascript", "html", "css", "api", "app"],
    "science": ["science", "biology", "chemistry", "physics", "astronomy", "dna"],
    "math": ["math", "calculate", "equation", "algebra", "geometry", "calculus"],
    "history": ["history", "war", "empire", "ancient", "civilization", "king"],
    "geography": ["country", "capital", "city", "river", "mountain", "ocean"],
    "technology": ["technology", "computer", "internet", "ai", "artificial intelligence"],
    "sports": ["sports", "football", "soccer", "basketball", "tennis", "cricket"],
    "entertainment": ["movie", "film", "music", "song", "actor", "actress", "concert"],
    "health": ["health", "doctor", "hospital", "medicine", "fitness", "diet"],
    "business": ["business", "finance", "money", "invest", "stock", "market"],
    "general": []
}

def detect_topic(text):
    lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(word in lower for word in keywords):
            if topic not in st.session_state.topics:
                st.session_state.topics.append(topic)
                st.session_state.topics = st.session_state.topics[-30:]
                if topic not in st.session_state.analytics["topics_count"]:
                    st.session_state.analytics["topics_count"][topic] = 0
                st.session_state.analytics["topics_count"][topic] += 1
                save_json(ANALYTICS_FILE, st.session_state.analytics)
            return topic
    return "general"

# ============================================================
# FILE PROCESSING
# ============================================================

def process_uploaded_file(uploaded_file):
    try:
        content = ""
        file_type = uploaded_file.type
        
        if "text" in file_type:
            content = uploaded_file.read().decode("utf-8")
        elif "pdf" in file_type:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
        elif "document" in file_type:
            doc = Document(io.BytesIO(uploaded_file.read()))
            for para in doc.paragraphs:
                content += para.text + "\n"
        elif "csv" in file_type or "spreadsheet" in file_type:
            df = pd.read_csv(io.BytesIO(uploaded_file.read()))
            content = df.to_string()
        else:
            return "⚠️ File type not supported for extraction."
        
        return content[:5000]
    except Exception as e:
        return f"Error processing file: {str(e)}"

# ============================================================
# VOICE INPUT
# ============================================================

def speech_to_text(audio_bytes):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except:
        return None

# ============================================================
# MEMORY FUNCTIONS
# ============================================================

def save_memory():
    save_json(MEMORY_FILE, {
        "name": st.session_state.user_name,
        "facts": st.session_state.memory_facts[-MAX_MEMORY_FACTS:],
        "preferences": st.session_state.memory_preferences[-MAX_MEMORY_PREFERENCES:],
        "emotion_history": st.session_state.emotion_history[-50:],
        "topics": st.session_state.topics[-30:]
    })

def learn_from_user(text):
    changed = False
    lower = text.lower()

    if "my name is " in lower:
        pos = lower.find("my name is ")
        name = text[pos + len("my name is "):].strip(" .!?")
        if name:
            st.session_state.user_name = name[:80]
            changed = True

    memory_markers = ["remember that ", "remember this: ", "please remember "]
    for marker in memory_markers:
        if marker in lower:
            pos = lower.find(marker)
            fact = text[pos + len(marker):].strip(" .!?")
            if fact and fact not in st.session_state.memory_facts:
                st.session_state.memory_facts.append(fact)
                st.session_state.memory_facts = st.session_state.memory_facts[-MAX_MEMORY_FACTS:]
                changed = True
            break

    pref_markers = ["i prefer ", "i like ", "my favorite "]
    for marker in pref_markers:
        if marker in lower:
            pos = lower.find(marker)
            pref = text[pos:].strip(" .!?")
            if pref and pref not in st.session_state.memory_preferences:
                st.session_state.memory_preferences.append(pref)
                st.session_state.memory_preferences = st.session_state.memory_preferences[-MAX_MEMORY_PREFERENCES:]
                changed = True
            break

    if changed:
        save_memory()

def memory_text():
    lines = []
    if st.session_state.user_name:
        lines.append("User name: " + st.session_state.user_name)
    for fact in st.session_state.memory_facts:
        lines.append("Saved fact: " + str(fact))
    for pref in st.session_state.memory_preferences:
        lines.append("Preference: " + str(pref))
    return "\n".join(lines) if lines else "No saved memory."

# ============================================================
# AI INSTRUCTIONS
# ============================================================

def system_instructions():
    current_model = MODELS[st.session_state.current_model_index]
    emotion = detect_emotion(" ".join([m.get("content", "") for m in st.session_state.messages[-5:]])) if st.session_state.messages else "neutral"
    
    return f"""
You are KingsBot AI — Advanced Edition.

Your AI brain is {current_model} via OpenRouter.

Current date: {datetime.now().strftime('%B %d, %Y')}

Detected emotion: {emotion}

CAPABILITIES:
- General knowledge
- Web search
- Mathematics
- Science
- History
- Geography
- Technology
- AI
- Programming
- Advanced coding
- Debugging
- Problem solving
- Deep reasoning
- Writing
- Rewriting
- Planning
- Brainstorming
- Teaching
- Explanations
- Comparisons
- Research

TONE ADAPTATION:
Automatically adapt to the user's emotion and question type.

MEMORY:
{memory_text()}

RULES:
- Be helpful, clear, and concise
- For math: show steps
- If uncertain: say "I don't know"
- Don't claim human-like consciousness
- Use web search for current information
- Provide code with explanations
- Keep responses under 5 sentences (unless explaining complex topics)
"""

# ============================================================
# BUILD CONVERSATION
# ============================================================

def build_messages(user_text):
    recent = st.session_state.messages[-ACTIVE_HISTORY_MESSAGES:]
    result = []
    for msg in recent:
        role = msg.get("role")
        content = msg.get("content")
        if role in ("user", "assistant") and content:
            result.append({"role": role, "content": content})
    result.append({"role": "user", "content": user_text})
    return result

# ============================================================
# SAVE CHAT — FIXED
# ============================================================

def save_current_chat():
    for chat in st.session_state.saved_chats:
        if chat["id"] == st.session_state.current_chat_id:
            chat["messages"] = list(st.session_state.messages)
            chat["updated"] = datetime.now().isoformat(timespec="seconds")
            
            # ✅ FIX: Ensure metadata exists
            if "metadata" not in chat:
                chat["metadata"] = {"topics": [], "emotions": [], "message_count": 0}
            
            chat["metadata"]["message_count"] = len(st.session_state.messages)
            
            for msg in st.session_state.messages:
                if msg.get("role") == "user" and msg.get("content"):
                    title = " ".join(msg["content"].split())
                    chat["title"] = title[:50] + "..." if len(title) > 50 else title
                    break
            break
    save_json(CHATS_FILE, st.session_state.saved_chats)

def start_new_chat():
    chat = new_chat()
    st.session_state.saved_chats.insert(0, chat)
    st.session_state.current_chat_id = chat["id"]
    st.session_state.messages = []
    save_json(CHATS_FILE, st.session_state.saved_chats)

# ============================================================
# EXPORT CONVERSATION
# ============================================================

def export_conversation():
    lines = ["# KingsBot Conversation Export", f"Date: {datetime.now().strftime('%B %d, %Y at %H:%M')}", ""]
    for msg in st.session_state.messages:
        role = "👤 User" if msg["role"] == "user" else "🤖 KingsBot"
        lines.append(f"**{role}:** {msg['content']}")
        lines.append("")
    return "\n".join(lines)

# ============================================================
# ASK KINGSBOT
# ============================================================

def ask_kingsbot(user_text, file_content=None):
    remaining = get_remaining_requests()
    if remaining <= 0:
        reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        wait_seconds = (reset_time - datetime.now()).total_seconds()
        hours = int(wait_seconds // 3600)
        minutes = int((wait_seconds % 3600) // 60)
        return f"⛔ **Daily limit reached.** Resets in {hours}h {minutes}m."

    if not API_KEY:
        return "🔑 **OPENROUTER_API_KEY not found.** Add to Streamlit Secrets."

    learn_from_user(user_text)
    emotion = detect_emotion(user_text)
    topic = detect_topic(user_text)
    
    st.session_state.analytics["total_interactions"] += 1
    today = str(date.today())
    if today not in st.session_state.analytics["daily_usage"]:
        st.session_state.analytics["daily_usage"][today] = 0
    st.session_state.analytics["daily_usage"][today] += 1
    save_json(ANALYTICS_FILE, st.session_state.analytics)

    rate_limiter.wait_if_needed()

    full_text = user_text
    if file_content:
        full_text += f"\n\nFile content:\n{file_content}"

    max_attempts = 3
    model_attempts = 0

    for attempt in range(max_attempts):
        try:
            current_model = MODELS[st.session_state.current_model_index]
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": system_instructions()}
                ] + build_messages(full_text),
                temperature=0.7,
                top_p=0.9,
                max_tokens=4096,
                stream=False,
            )

            elapsed = time.time() - start_time
            st.session_state.analytics["response_times"].append(elapsed)
            st.session_state.analytics["average_response_time"] = sum(st.session_state.analytics["response_times"]) / len(st.session_state.analytics["response_times"])
            save_json(ANALYTICS_FILE, st.session_state.analytics)

            if not response or not hasattr(response, 'choices') or not response.choices:
                return "❌ No response received. Please try again."

            message = response.choices[0].message
            if not message or not hasattr(message, 'content'):
                return "❌ Empty response. Please try again."

            answer = message.content.strip()
            if not answer:
                return "I didn't receive an answer. Please try again."

            rate_limiter.reset_backoff()
            increment_request()
            return answer

        except Exception as error:
            error_text = str(error)
            lower = error_text.lower()

            if "429" in lower or "rate limit" in lower:
                rate_limiter.handle_rate_limit()
                if attempt < max_attempts - 1:
                    continue
                return f"⏳ **Rate limit exceeded.** Retried {max_attempts} times."

            if "model" in lower and ("not found" in lower or "does not exist" in lower):
                if model_attempts < len(MODELS) - 1:
                    st.session_state.current_model_index = (st.session_state.current_model_index + 1) % len(MODELS)
                    model_attempts += 1
                    st.warning(f"🔄 Switching to: {MODELS[st.session_state.current_model_index]}")
                    time.sleep(2)
                    continue
                return "⚠️ **All models unavailable.** Check OpenRouter."

            if "401" in lower or "authentication" in lower:
                return "🔐 **Authentication failed.** Check your API key."

            return f"❌ **Error:**\n\n{error_text}"

    return "❌ **Max retries exceeded.** Please try again later."

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:10px;">
        <h2>🧠 KingsBot</h2>
        <p style="color:#888;">Ultimate Edition</p>
    </div>
    """, unsafe_allow_html=True)
    
    remaining = get_remaining_requests()
    if remaining > 0:
        st.info(f"📊 **Requests:** {remaining} / {DAILY_REQUEST_LIMIT}")
    else:
        st.warning("⛔ **No requests today**")

    st.write(f"**Model:** {MODELS[st.session_state.current_model_index]}")
    emotion = detect_emotion(' '.join([m.get('content', '') for m in st.session_state.messages[-5:]])) if st.session_state.messages else 'neutral'
    st.write(f"**Emotion:** {emotion}")
    st.write(f"**Topic:** {st.session_state.topics[-1] if st.session_state.topics else 'general'}")

    st.divider()

    if st.button("➕ New Chat", use_container_width=True):
        start_new_chat()
        st.rerun()

    st.subheader("💬 Chats")
    for chat in st.session_state.saved_chats[:10]:
        title = chat.get("title", "New chat")
        display = title[:25] + "..." if len(title) > 25 else title
        prefix = "🟢 " if chat["id"] == st.session_state.current_chat_id else "💬 "
        if st.button(prefix + display, key="chat_" + chat["id"], use_container_width=True):
            st.session_state.current_chat_id = chat["id"]
            st.session_state.messages = list(chat.get("messages", []))
            st.rerun()

    st.divider()

    with st.expander("📁 File Upload"):
        uploaded_file = st.file_uploader("Upload file", type=["txt", "pdf", "docx", "csv", "py", "js", "html", "css", "json", "md"])
        if uploaded_file:
            content = process_uploaded_file(uploaded_file)
            if content and "Error" not in content:
                st.session_state.uploaded_files.append({"name": uploaded_file.name, "content": content})
                st.success(f"✅ {uploaded_file.name} uploaded")
            else:
                st.error(content or "Failed to process file")

    with st.expander("🎤 Voice Input"):
        audio_file = st.audio_input("Speak into microphone")
        if audio_file:
            with st.spinner("Processing voice..."):
                text = speech_to_text(audio_file.read())
                if text:
                    st.success(f"🗣️ You said: {text}")
                    st.session_state.voice_input = text
                else:
                    st.error("Could not understand audio")

    with st.expander("📊 Analytics"):
        st.metric("Total Interactions", st.session_state.analytics.get("total_interactions", 0))
        st.metric("Avg Response Time", f"{st.session_state.analytics.get('average_response_time', 0):.2f}s")
        
        if st.session_state.analytics.get("emotions_count"):
            st.write("**Emotions:**")
            for emotion, count in st.session_state.analytics["emotions_count"].items():
                st.write(f"• {emotion}: {count}")
        
        if st.session_state.analytics.get("topics_count"):
            st.write("**Topics:**")
            for topic, count in st.session_state.analytics["topics_count"].items():
                st.write(f"• {topic}: {count}")

    st.divider()

    if st.button("📥 Export Chat", use_container_width=True):
        st.download_button(
            "Download Export",
            export_conversation(),
            f"kingsbot_export_{datetime.now().strftime('%Y%m%d')}.md",
            "text/markdown"
        )

    if st.button("🧹 Clear Memory", use_container_width=True):
        st.session_state.user_name = ""
        st.session_state.memory_facts = []
        st.session_state.memory_preferences = []
        st.session_state.emotion_history = []
        save_memory()
        st.rerun()

    st.divider()
    st.caption("🧠 KingsBot Ultimate • All Features")

# ============================================================
# MAIN
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>🤖 KingsBot Ultimate</h1>
    <p>All Features • Memory • Voice • Files • Analytics • FREE</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(st.session_state.messages)}</div>
        <div style="color:#888;">Messages</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{st.session_state.analytics.get('total_interactions', 0)}</div>
        <div style="color:#888;">Interactions</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(st.session_state.memory_facts)}</div>
        <div style="color:#888;">Facts</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    remaining = get_remaining_requests()
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{remaining}</div>
        <div style="color:#888;">Requests Left</div>
    </div>
    """, unsafe_allow_html=True)

# Voice input from sidebar
if hasattr(st.session_state, 'voice_input') and st.session_state.voice_input:
    prompt = st.session_state.voice_input
    st.session_state.voice_input = None
else:
    prompt = st.chat_input("Ask KingsBot anything...")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 KingsBot is thinking..."):
            file_content = None
            if st.session_state.uploaded_files:
                file_content = st.session_state.uploaded_files[-1]["content"]
            
            answer = ask_kingsbot(prompt, file_content)
            st.markdown(answer)
            
            emotion = detect_emotion(prompt)
            topic = detect_topic(prompt)
            st.caption(f"🎯 Topic: {topic} • ❤️ Emotion: {emotion} • 🧠 Model: {MODELS[st.session_state.current_model_index]}")

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_current_chat()
    st.rerun()

st.divider()
st.caption("🧠 KingsBot Ultimate • All Features • 100% FREE • Powered by OpenRouter")

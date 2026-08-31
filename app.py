import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json
import re
import time
import random
from datetime import datetime
import speech_recognition as sr
import io

# ============================================================
# PAGE SETTINGS
# ============================================================
st.set_page_config(
    page_title="KingsBot — Groq AI",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 KingsBot — Groq Advanced AI")
st.caption("Ultra-Fast • Llama 4 • Web Search • Memory • Voice • 100% Free")

# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "goals" not in st.session_state:
    st.session_state.goals = []
if "reminders" not in st.session_state:
    st.session_state.reminders = []
if "personal_memory" not in st.session_state:
    st.session_state.personal_memory = []
if "preferences" not in st.session_state:
    st.session_state.preferences = []
if "favorite_quotes" not in st.session_state:
    st.session_state.favorite_quotes = []
if "emotion" not in st.session_state:
    st.session_state.emotion = "neutral"
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0
if "mood_history" not in st.session_state:
    st.session_state.mood_history = []
if "last_topic" not in st.session_state:
    st.session_state.last_topic = "general knowledge"
if "tone" not in st.session_state:
    st.session_state.tone = "Natural"
if "model" not in st.session_state:
    st.session_state.model = "mixtral-8x7b-32768"  # ✅ Confirmed working on free tier
if "response_time" not in st.session_state:
    st.session_state.response_time = 0
if "student_level" not in st.session_state:
    st.session_state.student_level = None

# ============================================================
# SIDEBAR — API KEY, MODEL, PROFILE
# ============================================================
with st.sidebar:
    st.header("⚙️ Groq Settings")
    
    api_key = st.text_input("Groq API Key", type="password", help="Get free key at console.groq.com")
    if api_key:
        st.session_state.api_key = api_key
    
    # ✅ Updated model list with confirmed free-tier models
    model = st.selectbox(
        "Select Model",
        [
            "mixtral-8x7b-32768",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "llama-3.2-3b-preview",
            "llama-3.2-1b-preview",
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview"
        ],
        index=0
    )
    st.session_state.model = model
    
    st.caption("Free tier models: Mixtral, Llama 3.1 70B, Gemma 2, etc.")
    st.caption("Free: 30 req/min, 14,400 req/day")
    st.divider()
    
    st.subheader("👤 Profile")
    st.write(f"**Name:** {st.session_state.user_name or 'Not set'}")
    st.write(f"**Education:** {st.session_state.student_level or 'Not set'}")
    st.write(f"**Interactions:** {st.session_state.interaction_count}")
    
    emotion_emoji = {
        "happy": "😊", "sad": "😢", "frustrated": "😤",
        "confused": "🤔", "worried": "😰", "neutral": "😐"
    }.get(st.session_state.emotion, "🤖")
    st.write(f"**Emotion:** {emotion_emoji} {st.session_state.emotion}")
    st.write(f"**Tone:** {st.session_state.tone}")
    st.write(f"**Topic:** {st.session_state.last_topic}")
    st.write(f"**⏱️ Response:** {st.session_state.response_time:.2f}s")
    
    st.divider()
    
    st.subheader("🎯 Goals")
    for g in st.session_state.goals:
        st.write(f"• {g}")
    if not st.session_state.goals:
        st.caption("Say 'my goal is...'")
    
    st.subheader("⏰ Reminders")
    for idx, r in enumerate(st.session_state.reminders):
        if not r["done"]:
            col1, col2 = st.columns([3, 1])
            col1.write(f"• {r['text']}")
            if col2.button("✅", key=f"rem_{idx}"):
                r["done"] = True
                st.rerun()
    
    st.subheader("💬 Favorite Quotes")
    for q in st.session_state.favorite_quotes:
        st.write(f"• \"{q}\"")
    
    st.subheader("❤️ Preferences")
    for p in st.session_state.preferences:
        st.write(f"• {p}")
    
    st.divider()
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🧹 Forget Everything"):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.goals = []
        st.session_state.reminders = []
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        st.session_state.favorite_quotes = []
        st.session_state.mood_history = []
        st.rerun()
    
    st.caption("🤖 KingsBot • Groq LPU • 500+ tokens/sec")

# ============================================================
# FEATURES — MEMORY, EMOTION, TONE, TOPIC
# ============================================================

# Emotion Detection
EMOTION_KEYWORDS = {
    "frustrated": ["angry", "mad", "annoyed", "frustrated", "wrong", "mistake", "useless"],
    "sad": ["sad", "crying", "upset", "hurt", "disappointed", "miserable"],
    "confused": ["confused", "don't understand", "huh", "what do you mean", "i don't get"],
    "worried": ["worried", "scared", "afraid", "nervous", "anxious", "concerned"],
    "happy": ["happy", "great", "awesome", "thanks", "love", "amazing", "wonderful"],
    "neutral": []
}

def detect_emotion(text):
    lower = text.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(word in lower for word in keywords):
            st.session_state.emotion = emotion
            st.session_state.mood_history.append({
                "emotion": emotion,
                "time": datetime.now().strftime("%H:%M")
            })
            st.session_state.mood_history = st.session_state.mood_history[-20:]
            return emotion
    st.session_state.emotion = "neutral"
    return "neutral"

def tone_for(emotion):
    tones = {
        "frustrated": ("😌 Calm", "Be calm, respectful, and direct."),
        "sad": ("💙 Warm", "Be kind, warm, and supportive."),
        "confused": ("🧩 Simple", "Explain step by step."),
        "worried": ("🤝 Reassuring", "Be reassuring and practical."),
        "happy": ("😊 Friendly", "Be friendly, positive, and energetic."),
        "neutral": ("🤖 Natural", "Be natural, friendly, and clear.")
    }
    return tones.get(emotion, tones["neutral"])

def recognize_topic(text):
    lower = text.lower()
    categories = {
        "coding": ["code", "python", "program", "app", "software"],
        "mathematics": ["math", "calculate", "equation", "algebra"],
        "science": ["science", "biology", "chemistry", "physics"],
        "sports": ["football", "soccer", "messi", "ronaldo"],
        "education": ["school", "class", "university", "teacher"],
        "history": ["history", "war", "empire", "ancient"],
        "geography": ["country", "capital", "continent", "river"],
        "technology": ["technology", "computer", "internet", "ai"],
        "general knowledge": ["who is", "what is", "where is", "tell me about"]
    }
    for category, words in categories.items():
        if any(word in lower for word in words):
            return category
    return "general knowledge"

def detect_name(text):
    patterns = [
        r"my name is ([A-Za-z ]+)",
        r"call me ([A-Za-z ]+)",
        r"i am ([A-Za-z ]+)",
        r"i'm ([A-Za-z ]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) >= 2:
                st.session_state.user_name = name
                return name
    return None

def detect_goal(text):
    match = re.search(r"my goal is ([^.!?]+)", text, re.IGNORECASE)
    if match:
        goal = match.group(1).strip()
        if goal and len(goal) > 5 and goal not in st.session_state.goals:
            st.session_state.goals.append(goal)
            st.session_state.goals = st.session_state.goals[-10:]
        return goal
    return None

def detect_reminder(text):
    match = re.search(r"remind me to ([^.!?]+)", text, re.IGNORECASE)
    if match:
        reminder = match.group(1).strip()
        if reminder and len(reminder) > 3:
            st.session_state.reminders.append({
                "text": reminder,
                "created": datetime.now().strftime("%H:%M"),
                "done": False
            })
            st.session_state.reminders = st.session_state.reminders[-10:]
        return reminder
    return None

def detect_quote(text):
    match = re.search(r'"(.*?)"', text)
    if match:
        quote = match.group(1).strip()
        if quote and len(quote) > 5 and quote not in st.session_state.favorite_quotes:
            st.session_state.favorite_quotes.append(quote)
            st.session_state.favorite_quotes = st.session_state.favorite_quotes[-10:]
        return quote
    return None

def detect_preference(text):
    patterns = [
        r"i like ([^.!?]+)",
        r"i love ([^.!?]+)",
        r"my favorite ([^.!?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            pref = match.group(1).strip()
            if pref and len(pref) > 3 and pref not in st.session_state.preferences:
                st.session_state.preferences.append(pref)
                st.session_state.preferences = st.session_state.preferences[-10:]
            return pref
    return None

def detect_education(text):
    levels = ["primary", "secondary", "high school", "university", "college", "jss", "sss", "grade"]
    for level in levels:
        if level in text.lower():
            st.session_state.student_level = level
            return level
    return None

def forget_information(text):
    lower = text.lower()
    
    if any(phrase in lower for phrase in ["forget everything", "clear memory", "erase everything", "reset memory"]):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.goals = []
        st.session_state.reminders = []
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        st.session_state.favorite_quotes = []
        st.session_state.mood_history = []
        return "✅ Done. I cleared everything."
    
    if "forget my name" in lower:
        st.session_state.user_name = None
        return "✅ Done. I forgot your name."
    
    if "forget my goals" in lower:
        st.session_state.goals = []
        return "✅ Done. I forgot your goals."
    
    if "forget my reminders" in lower:
        st.session_state.reminders = []
        return "✅ Done. I forgot your reminders."
    
    return None

# ============================================================
# VOICE INPUT (Speech-to-Text)
# ============================================================
def speech_to_text(audio_bytes):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None
    except Exception:
        return None

# ============================================================
# GENERATE RESPONSE — GROQ API
# ============================================================
def generate_response(prompt):
    if not st.session_state.api_key:
        return "⚠️ Please enter your Groq API key in the sidebar. Get one free at console.groq.com"
    
    # Run all memory/emotion detection
    detect_name(prompt)
    detect_goal(prompt)
    detect_reminder(prompt)
    detect_quote(prompt)
    detect_preference(prompt)
    detect_education(prompt)
    
    forgotten = forget_information(prompt)
    if forgotten:
        return forgotten
    
    emotion = detect_emotion(prompt)
    tone_name, tone_instruction = tone_for(emotion)
    st.session_state.tone = tone_name
    st.session_state.last_topic = recognize_topic(prompt)
    st.session_state.interaction_count += 1
    
    # Build memory context
    memory_text = ""
    if st.session_state.user_name:
        memory_text += f"User's name: {st.session_state.user_name}. "
    if st.session_state.student_level:
        memory_text += f"User's education level: {st.session_state.student_level}. "
    if st.session_state.goals:
        memory_text += f"User's goals: {', '.join(st.session_state.goals[-3:])}. "
    if st.session_state.personal_memory:
        memory_text += f"User facts: {', '.join(st.session_state.personal_memory[-3:])}. "
    if st.session_state.preferences:
        memory_text += f"User preferences: {', '.join(st.session_state.preferences[-3:])}. "
    if st.session_state.favorite_quotes:
        memory_text += f"User's favorite quotes: {', '.join(st.session_state.favorite_quotes[-2:])}. "
    
    # System prompt
    system_prompt = f"""
You are KingsBot, an intelligent, ultra-fast AI assistant powered by Groq.

Current date: {datetime.now().strftime('%B %d, %Y')}

User emotion: {emotion}
Tone: {tone_name}. {tone_instruction}

Memory:
{memory_text}

Be helpful, clear, and concise. Answer in a friendly way. Match your tone to the user's emotion.
If you don't know something, say so.
"""
    
    try:
        client = Groq(api_key=st.session_state.api_key)
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.messages[-15:])
        messages.append({"role": "user", "content": prompt})
        
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=st.session_state.model,
            messages=messages,
            temperature=0.7,
            max_tokens=600,
            top_p=0.9
        )
        
        elapsed = time.time() - start_time
        st.session_state.response_time = elapsed
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================================
# DISPLAY CONVERSATION
# ============================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ============================================================
# VOICE INPUT (STREAMLIT NATIVE)
# ============================================================
audio_file = st.audio_input("🎤 Press the microphone and speak")

if audio_file:
    with st.spinner("🎧 Processing your voice..."):
        audio_bytes = audio_file.read()
        voice_text = speech_to_text(audio_bytes)
        
        if voice_text:
            st.success(f"🗣️ You said: {voice_text}")
            # Process as if typed
            with st.chat_message("user"):
                st.write(voice_text)
            with st.chat_message("assistant"):
                with st.spinner("🧠 Thinking..."):
                    response = generate_response(voice_text)
                    st.write(response)
                    emotion_emoji = {
                        "happy": "😊", "sad": "😢", "frustrated": "😤",
                        "confused": "🤔", "worried": "😰", "neutral": "😐"
                    }.get(st.session_state.emotion, "🤖")
                    model_display = st.session_state.model
                    st.caption(f"⏱️ {st.session_state.response_time:.2f}s • {emotion_emoji} {st.session_state.emotion} • {model_display}")
            st.session_state.messages.append({"role": "user", "content": voice_text})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        else:
            st.error("❌ Could not understand the audio. Please try again.")

# ============================================================
# TEXT INPUT
# ============================================================
prompt = st.chat_input("Ask KingsBot anything...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner(f"🧠 Thinking with {st.session_state.model}..."):
            response = generate_response(prompt)
            st.write(response)
            emotion_emoji = {
                "happy": "😊", "sad": "😢", "frustrated": "😤",
                "confused": "🤔", "worried": "😰", "neutral": "😐"
            }.get(st.session_state.emotion, "🤖")
            model_display = st.session_state.model
            st.caption(f"⏱️ {st.session_state.response_time:.2f}s • {emotion_emoji} {st.session_state.emotion} • {model_display}")
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("🧠 KingsBot • Powered by Groq LPU • 500-1000+ tokens/sec • Free Tier Available")

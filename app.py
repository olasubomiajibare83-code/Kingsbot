import streamlit as st
import json
import re
import random
import time
from datetime import datetime
import base64
import io

# ============================================================
# PAGE SETTINGS
# ============================================================
st.set_page_config(
    page_title="KingsBot Ultimate",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .user-bubble {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 80%;
        margin: 8px 0 8px auto;
        animation: slideIn 0.3s ease;
    }
    .assistant-bubble {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        max-width: 80%;
        margin: 8px auto 8px 0;
        animation: slideIn 0.3s ease;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TITLE
# ============================================================
st.title("🧠 KingsBot Ultimate")
st.caption("Voice • Memory • Emotions • No API Key")

# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "personal_memory" not in st.session_state:
    st.session_state.personal_memory = []
if "goals" not in st.session_state:
    st.session_state.goals = []
if "reminders" not in st.session_state:
    st.session_state.reminders = []
if "emotion" not in st.session_state:
    st.session_state.emotion = "neutral"
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0
if "mood_history" not in st.session_state:
    st.session_state.mood_history = []
if "last_topic" not in st.session_state:
    st.session_state.last_topic = "general knowledge"
if "tone" not in st.session_state:
    st.session_state.tone = "Natural and friendly"
if "response_time" not in st.session_state:
    st.session_state.response_time = 0
if "favorite_quotes" not in st.session_state:
    st.session_state.favorite_quotes = []
if "preferences" not in st.session_state:
    st.session_state.preferences = []
if "topic_pattern" not in st.session_state:
    st.session_state.topic_pattern = []

# ============================================================
# EMOTION DETECTION
# ============================================================
EMOTION_KEYWORDS = {
    "frustrated": ["angry", "mad", "annoyed", "frustrated", "wrong", "mistake"],
    "sad": ["sad", "crying", "upset", "hurt", "disappointed"],
    "confused": ["confused", "don't understand", "huh", "what do you mean"],
    "worried": ["worried", "scared", "afraid", "nervous", "anxious"],
    "happy": ["happy", "great", "awesome", "thanks", "love", "amazing"],
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
            return emotion
    st.session_state.emotion = "neutral"
    return "neutral"

# ============================================================
# TONE ADAPTATION
# ============================================================
def tone_for(emotion):
    tones = {
        "frustrated": ("😌 Calm", "Be calm and direct."),
        "sad": ("💙 Warm", "Be kind and supportive."),
        "confused": ("🧩 Simple", "Explain step by step."),
        "worried": ("🤝 Reassuring", "Be reassuring."),
        "happy": ("😊 Friendly", "Be friendly and positive."),
        "neutral": ("🤖 Natural", "Be natural and clear.")
    }
    return tones.get(emotion, tones["neutral"])

# ============================================================
# TOPIC RECOGNITION
# ============================================================
def recognize_topic(text):
    lower = text.lower()
    categories = {
        "coding": ["code", "python", "program", "app", "software"],
        "mathematics": ["math", "calculate", "equation", "algebra"],
        "science": ["science", "biology", "chemistry", "physics"],
        "sports": ["football", "soccer", "messi", "ronaldo"],
        "education": ["school", "class", "university", "teacher"],
        "history": ["history", "war", "empire", "ancient"],
        "geography": ["country", "capital", "continent"],
        "technology": ["technology", "computer", "internet", "ai"],
        "general knowledge": ["who is", "what is", "where is", "tell me about"]
    }
    for category, words in categories.items():
        if any(word in lower for word in words):
            return category
    return "general knowledge"

# ============================================================
# DETECTION FUNCTIONS
# ============================================================
def detect_name(text):
    match = re.search(r"my name is ([A-Za-z ]+)", text, re.IGNORECASE)
    if match:
        st.session_state.user_name = match.group(1).strip()
        return match.group(1).strip()
    return None

def detect_goal(text):
    match = re.search(r"my goal is ([^.!?]+)", text, re.IGNORECASE)
    if match:
        goal = match.group(1).strip()
        if goal not in st.session_state.goals:
            st.session_state.goals.append(goal)
        return goal
    return None

def detect_reminder(text):
    match = re.search(r"remind me to ([^.!?]+)", text, re.IGNORECASE)
    if match:
        reminder = match.group(1).strip()
        st.session_state.reminders.append({"text": reminder, "done": False})
        return reminder
    return None

def detect_quote(text):
    match = re.search(r'"(.*?)"', text)
    if match:
        quote = match.group(1).strip()
        if quote not in st.session_state.favorite_quotes:
            st.session_state.favorite_quotes.append(quote)
        return quote
    return None

# ============================================================
# VERIFIED FACTS
# ============================================================
def verified_fact(question):
    lower = question.lower()
    if "messi" in lower and "world cup" in lower:
        return "🏆 Messi won the 2022 World Cup with Argentina."
    if "nigeria" in lower and "capital" in lower:
        return "🏙️ The capital of Nigeria is Abuja."
    if "what year is it" in lower or "current year" in lower:
        return f"📅 The current year is {datetime.now().year}."
    if "today's date" in lower:
        return f"📅 Today is {datetime.now().strftime('%B %d, %Y')}."
    if "what time" in lower:
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."
    return None

# ============================================================
# FORGET FUNCTION
# ============================================================
def forget_information(text):
    lower = text.lower()
    if "forget everything" in lower or "clear memory" in lower:
        st.session_state.user_name = None
        st.session_state.personal_memory = []
        st.session_state.goals = []
        st.session_state.reminders = []
        st.session_state.favorite_quotes = []
        return "✅ Done. I cleared everything."
    if "forget my name" in lower:
        st.session_state.user_name = None
        return "✅ Done. I forgot your name."
    return None

# ============================================================
# RESPONSE GENERATOR
# ============================================================
def generate_intelligent_response(text):
    lower = text.lower()
    
    if re.match(r'^(hi|hello|hey|greetings|sup|yo)', lower):
        return random.choice([
            "Hello! 👋 How can I help you?",
            "Hi there! 😊 What's on your mind?",
            "Hey! Great to talk to you!"
        ])
    
    if re.search(r'how are you', lower):
        return "I'm doing great, thanks! 😊 How are you?"
    
    if re.search(r'what is your name|who are you', lower):
        return "I'm KingsBot! 🤖 Your AI assistant with memory, emotions, and voice!"
    
    if re.search(r'what time is it', lower):
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."
    
    if re.search(r'what day is it', lower):
        return f"📅 Today is {datetime.now().strftime('%A, %B %d, %Y')}."
    
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
            elif op in ['x', 'X', '*']:
                result = a * b
            elif op == '/':
                result = a / b if b != 0 else "Cannot divide by zero"
            return f"🧮 {a} {op} {b} = {result}"
        except:
            pass
    
    if re.search(r'help|what can you do', lower):
        return """
🤖 **I can help with:**
- General Knowledge
- Mathematics
- Coding
- Goals & Reminders
- Memory

Try: "My name is Alex", "My goal is to learn Python", "Remind me to call mom"
"""
    
    return None

# ============================================================
# GENERATE RESPONSE
# ============================================================
def generate_response(user_message):
    start_time = time.time()
    
    detect_name(user_message)
    detect_goal(user_message)
    detect_reminder(user_message)
    detect_quote(user_message)
    
    forgotten = forget_information(user_message)
    if forgotten:
        return forgotten
    
    emotion = detect_emotion(user_message)
    tone_name, _ = tone_for(emotion)
    st.session_state.tone = tone_name
    st.session_state.last_topic = recognize_topic(user_message)
    st.session_state.interaction_count += 1
    
    fact = verified_fact(user_message)
    if fact:
        return fact
    
    response = generate_intelligent_response(user_message)
    if not response:
        response = "I'm here to help! What would you like to know?"
    
    st.session_state.response_time = time.time() - start_time
    return response

# ============================================================
# DISPLAY CONVERSATION
# ============================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# ============================================================
# VOICE INPUT (WORKS ON STREAMLIT CLOUD)
# ============================================================
audio_file = st.audio_input("🎤 Press the microphone and speak")

if audio_file:
    st.info("🎧 Voice recorded! (Speech-to-text is handled by your browser's built-in recognition)")
    st.caption("💡 On Streamlit Cloud, voice input is captured as audio. Type your message below for text input.")

# ============================================================
# TEXT INPUT
# ============================================================
prompt = st.chat_input("Type your message...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            response = generate_response(prompt)
            st.write(response)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("👤 Profile")
    st.write(f"**Name:** {st.session_state.user_name or 'Not set'}")
    st.write(f"**Interactions:** {st.session_state.interaction_count}")
    
    emotion_emoji = {
        "happy": "😊", "sad": "😢", "frustrated": "😤",
        "confused": "🤔", "worried": "😰", "neutral": "😐"
    }.get(st.session_state.emotion, "🤖")
    st.write(f"**Emotion:** {emotion_emoji} {st.session_state.emotion}")
    st.write(f"**Tone:** {st.session_state.tone}")
    st.write(f"**Topic:** {st.session_state.last_topic}")
    
    st.divider()
    
    st.subheader("🎯 Goals")
    for g in st.session_state.goals:
        st.write(f"• {g}")
    if not st.session_state.goals:
        st.caption("Say 'my goal is...'")
    
    st.subheader("⏰ Reminders")
    for r in st.session_state.reminders:
        if not r["done"]:
            col1, col2 = st.columns([3, 1])
            col1.write(f"• {r['text']}")
            if col2.button("✅", key=f"rem_{r['text'][:10]}"):
                r["done"] = True
                st.rerun()
    
    st.subheader("💬 Quotes")
    for q in st.session_state.favorite_quotes:
        st.write(f"• \"{q}\"")
    
    st.divider()
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🧹 Forget Everything"):
        st.session_state.user_name = None
        st.session_state.goals = []
        st.session_state.reminders = []
        st.session_state.favorite_quotes = []
        st.rerun()
    
    st.caption("🤖 KingsBot Ultimate • Voice + Memory")

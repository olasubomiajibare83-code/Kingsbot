import streamlit as st
import streamlit.components.v1 as components
import json
import re
import random
import time
from datetime import datetime
import speech_recognition as sr
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
    /* Chat Bubbles */
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
    .stat-card {
        background: rgba(255,255,255,0.05);
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton button {
        width: 100%;
        border-radius: 20px;
    }
    .css-1d391kg {
        background: rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TITLE
# ============================================================
st.title("🧠 KingsBot Ultimate")
st.caption("68+ Features • Voice • Memory • Emotions • No API Key")

# ============================================================
# SESSION STATE (MEMORY SYSTEM)
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
if "student_level" not in st.session_state:
    st.session_state.student_level = None

# ============================================================
# EMOTIONAL INTELLIGENCE (EMOTION DETECTION)
# ============================================================
EMOTION_KEYWORDS = {
    "frustrated": ["angry", "mad", "annoyed", "frustrated", "wrong", "mistake", "terrible", "useless"],
    "sad": ["sad", "crying", "upset", "hurt", "disappointed", "miserable"],
    "confused": ["confused", "don't understand", "huh", "what do you mean", "i don't get"],
    "worried": ["worried", "scared", "afraid", "nervous", "anxious", "concerned"],
    "happy": ["happy", "great", "awesome", "thanks", "love", "amazing", "perfect", "wonderful"],
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

# ============================================================
# TONE ADAPTATION
# ============================================================
def tone_for(emotion):
    tones = {
        "frustrated": ("😌 Calm", "Be calm, respectful, and direct."),
        "sad": ("💙 Warm", "Be kind, warm, and supportive."),
        "confused": ("🧩 Simple", "Use very simple language. Explain step by step."),
        "worried": ("🤝 Reassuring", "Be reassuring and practical."),
        "happy": ("😊 Friendly", "Be friendly, positive, and energetic."),
        "neutral": ("🤖 Natural", "Be natural, friendly, and clear.")
    }
    return tones.get(emotion, tones["neutral"])

# ============================================================
# TOPIC RECOGNITION
# ============================================================
def recognize_topic(text):
    lower = text.lower()
    categories = {
        "coding": ["code", "python", "program", "programming", "app", "software", "javascript", "html", "css"],
        "mathematics": ["math", "calculate", "equation", "algebra", "geometry", "calculus", "fraction", "decimal"],
        "science": ["science", "biology", "chemistry", "physics", "astronomy"],
        "sports": ["football", "soccer", "messi", "ronaldo", "world cup", "basketball"],
        "education": ["school", "class", "university", "teacher", "student", "exam"],
        "history": ["history", "war", "empire", "ancient", "civilization"],
        "geography": ["country", "capital", "continent", "river", "mountain", "ocean"],
        "technology": ["technology", "computer", "internet", "ai", "artificial intelligence", "robot"],
        "entertainment": ["movie", "film", "actor", "music", "song", "celebrity"],
        "health": ["health", "doctor", "hospital", "medicine", "fitness", "exercise"],
        "business": ["business", "company", "money", "invest", "stock", "market", "profit"],
        "philosophy": ["philosophy", "meaning", "purpose", "existence", "morality"],
        "general knowledge": ["who is", "what is", "where is", "when did", "why is", "how does", "tell me about", "meaning of"]
    }
    for category, words in categories.items():
        if any(word in lower for word in words):
            if category not in st.session_state.topic_pattern:
                st.session_state.topic_pattern.append(category)
                st.session_state.topic_pattern = st.session_state.topic_pattern[-10:]
            return category
    return "general knowledge"

# ============================================================
# DETECTION FUNCTIONS (MEMORY SYSTEM)
# ============================================================
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
    patterns = [
        r"my goal is ([^.!?]+)",
        r"i want to ([^.!?]+)",
        r"i aim to ([^.!?]+)",
        r"i dream of ([^.!?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            goal = match.group(1).strip()
            if goal and len(goal) > 5 and goal not in st.session_state.goals:
                st.session_state.goals.append(goal)
                st.session_state.goals = st.session_state.goals[-10:]
                return goal
    return None

def detect_reminder(text):
    patterns = [
        r"remind me to ([^.!?]+)",
        r"remember to ([^.!?]+)",
        r"don't forget to ([^.!?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
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

# ============================================================
# ETHICAL FORGETTING
# ============================================================
def forget_information(text):
    lower = text.lower()
    
    if any(phrase in lower for phrase in ["forget everything", "forget all my memory", "reset memory", "clear memory", "erase everything"]):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        st.session_state.goals = []
        st.session_state.reminders = []
        st.session_state.favorite_quotes = []
        st.session_state.mood_history = []
        return "✅ Done. I cleared all your saved memory."
    
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
# VERIFIED FACTS (KNOWLEDGE BASE)
# ============================================================
def verified_fact(question):
    lower = question.lower()
    
    # Sports
    if "messi" in lower and "world cup" in lower:
        return "🏆 Lionel Messi won the 2022 FIFA World Cup with Argentina."
    if "world cup" in lower and "winner" in lower:
        return "🏆 Argentina won the 2022 FIFA World Cup."
    if "ronaldo" in lower and "portugal" in lower:
        return "⚽ Cristiano Ronaldo is a Portuguese footballer. He has not won a World Cup."
    if "nigeria" in lower and "capital" in lower:
        return "🏙️ The capital of Nigeria is Abuja."
    if "lagos" in lower and "nigeria" in lower:
        return "🌆 Lagos is the largest city in Nigeria."
    
    # Current info
    if any(phrase in lower for phrase in ["what year is it", "which year is it", "current year"]):
        return f"📅 The current year is {datetime.now().year}."
    if any(phrase in lower for phrase in ["today's date", "todays date", "what date is it"]):
        return f"📅 Today is {datetime.now().strftime('%B %d, %Y')}."
    if "what time" in lower:
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."
    
    # Science
    if "speed of light" in lower:
        return "💡 The speed of light is approximately 299,792,458 m/s."
    if "gravity" in lower and "earth" in lower:
        return "🌍 Gravity on Earth is approximately 9.8 m/s²."
    if "water" in lower and "boiling" in lower:
        return "💧 Water boils at 100°C (212°F) at sea level."
    
    # Space
    if "moon" in lower and "distance" in lower:
        return "🌙 The average distance from Earth to the Moon is about 384,400 km."
    if "sun" in lower and "distance" in lower:
        return "☀️ The average distance from Earth to the Sun is about 149.6 million km."
    
    # Health
    if "drink water" in lower and "daily" in lower:
        return "💧 Health experts recommend drinking about 2-3 liters of water daily."
    
    return None

# ============================================================
# INTELLIGENT RESPONSE GENERATOR
# ============================================================
def generate_intelligent_response(text):
    lower = text.lower()
    
    # Greetings
    if re.match(r'^(hi|hello|hey|greetings|sup|what\'s up|yo|howdy)', lower):
        return random.choice([
            "Hello! 👋 How can I help you today?",
            "Hi there! 😊 What's on your mind?",
            "Hey! Great to talk to you! What can I help with?",
            "Greetings! 🤖 I'm here to assist you."
        ])
    
    # How are you
    if re.search(r'how are you|how\'s it going|how do you do', lower):
        return random.choice([
            "I'm doing great, thanks for asking! 😊 How are you?",
            "I'm functioning perfectly! 🤖 How can I help you today?",
            "I'm always ready to help! 💪 What do you need?"
        ])
    
    # Name
    if re.search(r'what is your name|who are you|your name', lower):
        return "I'm KingsBot! 🤖 Your intelligent AI assistant with memory, emotions, voice, and 68+ features — all with NO installation and NO API key!"
    
    # Time
    if re.search(r'what time is it|current time|time now', lower):
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."
    
    # Date
    if re.search(r'what day is it|what\'s the date|today\'s date', lower):
        return f"📅 Today is {datetime.now().strftime('%A, %B %d, %Y')}."
    
    # Math
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
                if b != 0:
                    result = a / b
                else:
                    return "❌ Cannot divide by zero!"
            return f"🧮 {a} {op} {b} = {result}"
        except:
            pass
    
    # Square root
    sqrt_match = re.search(r'sqrt\s*(\d+)|square root of (\d+)', lower)
    if sqrt_match:
        num = int(sqrt_match.group(1) or sqrt_match.group(2))
        result = num ** 0.5
        return f"√{num} = {result:.2f}"
    
    # Help
    if re.search(r'help|what can you do|capabilities|features', lower):
        return """
🤖 **I can help you with:**

📚 **General Knowledge** — History, geography, science, and more!
🧮 **Mathematics** — Basic arithmetic, square roots, percentages
💻 **Coding** — Python tips, algorithms, and explanations
🎯 **Goals** — Track your goals and achievements
⏰ **Reminders** — Set and manage reminders
💬 **Quotes** — Save your favorite quotes
🧠 **Memory** — I remember facts you share
❤️ **Emotions** — I adapt to how you're feeling
🎭 **Tone** — I match my tone to your mood

**Try these commands:**
- "My name is Alex"
- "My goal is to learn Python"
- "Remind me to call mom"
- "What is 25 x 4?"
- "What can you do?"
- "Forget everything"

I have 68+ features! Just ask me anything! 🚀
"""
    
    # Philosophy
    if re.search(r'meaning of life|purpose of life|why are we here', lower):
        return random.choice([
            "🤔 The meaning of life is a deep question. Many say it's to find happiness, help others, and grow as a person. What do you think?",
            "💭 Some say the meaning of life is what you make it — love, learn, create, and connect with others."
        ])
    
    # Unknown
    return None

# ============================================================
# GENERATE RESPONSE (MAIN BRAIN)
# ============================================================
def generate_response(user_message):
    start_time = time.time()
    
    # Memory detection
    detect_name(user_message)
    detect_goal(user_message)
    detect_reminder(user_message)
    detect_quote(user_message)
    detect_preference(user_message)
    detect_education(user_message)
    
    # Ethical forgetting
    forgotten = forget_information(user_message)
    if forgotten:
        st.session_state.response_time = time.time() - start_time
        return forgotten
    
    # Emotion detection
    emotion = detect_emotion(user_message)
    tone_name, tone_instruction = tone_for(emotion)
    st.session_state.tone = tone_name
    
    # Topic recognition
    st.session_state.last_topic = recognize_topic(user_message)
    st.session_state.interaction_count += 1
    
    # Verified facts
    fact = verified_fact(user_message)
    if fact:
        st.session_state.response_time = time.time() - start_time
        return fact
    
    # Generate intelligent response
    response = generate_intelligent_response(user_message)
    
    if not response:
        response = "I'm here to help! I can answer questions about general knowledge, math, science, coding, and more. What would you like to know?"
    
    st.session_state.response_time = time.time() - start_time
    return response

# ============================================================
# SPEECH TO TEXT (VOICE INPUT)
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
# DISPLAY CONVERSATION
# ============================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

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
            
            with st.chat_message("user"):
                st.write(voice_text)
            
            with st.chat_message("assistant"):
                with st.spinner("🧠 Thinking..."):
                    response = generate_response(voice_text)
                    st.write(response)
            
            st.session_state.messages.append({"role": "user", "content": voice_text})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        else:
            st.error("❌ Could not understand the audio. Please try again.")

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
# SIDEBAR (ALL FEATURES DISPLAYED)
# ============================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712031.png", width=80)
    st.title("🧠 KingsBot")
    st.caption("68+ Features • No API Key")
    st.divider()
    
    # Profile
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
    st.write(f"**Response Time:** {st.session_state.response_time:.2f}s")
    
    st.divider()
    
    # Goals
    st.subheader("🎯 Goals")
    if st.session_state.goals:
        for g in st.session_state.goals:
            st.write(f"• {g}")
    else:
        st.caption("Say 'my goal is...'")
    
    st.divider()
    
    # Reminders
    st.subheader("⏰ Reminders")
    if st.session_state.reminders:
        for i, r in enumerate(st.session_state.reminders):
            if not r["done"]:
                col1, col2 = st.columns([3, 1])
                col1.write(f"• {r['text']} ({r['created']})")
                if col2.button("✅", key=f"rem_{i}"):
                    st.session_state.reminders[i]["done"] = True
                    st.rerun()
    else:
        st.caption("Say 'remind me to...'")
    
    st.divider()
    
    # Quotes
    st.subheader("💬 Favorite Quotes")
    if st.session_state.favorite_quotes:
        for q in st.session_state.favorite_quotes[-5:]:
            st.write(f"• \"{q}\"")
    else:
        st.caption("Put quotes around something: \"...\"")
    
    st.divider()
    
    # Memory
    st.subheader("🧠 Memory")
    if st.session_state.personal_memory:
        for f in st.session_state.personal_memory[-5:]:
            st.write(f"• {f}")
    else:
        st.caption("Say 'remember that...'")
    
    st.divider()
    
    # Preferences
    st.subheader("❤️ Preferences")
    if st.session_state.preferences:
        for p in st.session_state.preferences[-5:]:
            st.write(f"• {p}")
    else:
        st.caption("Say 'I like...'")
    
    st.divider()
    
    # Mood History
    st.subheader("📊 Mood History")
    if st.session_state.mood_history:
        for m in st.session_state.mood_history[-5:]:
            st.write(f"• {m['emotion']} at {m['time']}")
    else:
        st.caption("No mood data yet.")
    
    st.divider()
    
    # Topics
    st.subheader("📚 Topics Discussed")
    if st.session_state.topic_pattern:
        for t in st.session_state.topic_pattern[-5:]:
            st.write(f"• {t}")
    else:
        st.caption("No topics yet.")
    
    st.divider()
    
    # Buttons
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🧹 Forget Everything"):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        st.session_state.goals = []
        st.session_state.reminders = []
        st.session_state.favorite_quotes = []
        st.session_state.mood_history = []
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("🤖 KingsBot Ultimate • 68+ Features")
    st.caption(f"📅 {datetime.now().strftime('%B %d, %Y')}")

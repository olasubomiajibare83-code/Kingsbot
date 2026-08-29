import json
import os
import re
import random
import time
from datetime import datetime
import webbrowser
import threading
import socket
import http.server
import socketserver
import urllib.parse
import base64
import sys
import traceback

# ============================================================
# KINGSBOT AI — NO INSTALLATION EDITION (FULL BRAIN + VOICE)
# ============================================================

PORT = 8501
HOST = "localhost"
MEMORY_FILE = "kingsbot_memory.json"

# ============================================================
# MEMORY SYSTEM
# ============================================================
def default_memory():
    return {
        "name": None,
        "education_level": None,
        "facts": [],
        "preferences": [],
        "topics": [],
        "last_interaction": None,
        "interaction_count": 0,
        "mood_history": [],
        "goals": [],
        "reminders": [],
        "favorite_quotes": []
    }

def load_memory():
    data = default_memory()
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)
                if isinstance(saved, dict):
                    for key in data:
                        if key in saved:
                            data[key] = saved[key]
    except Exception:
        pass
    return data

def save_memory():
    data = {
        "name": st.session_state.get("user_name", None),
        "education_level": st.session_state.get("student_level", None),
        "facts": st.session_state.get("personal_memory", [])[-50:],
        "preferences": st.session_state.get("preferences", [])[-20:],
        "topics": st.session_state.get("topic_pattern", [])[-30:],
        "last_interaction": datetime.now().isoformat(),
        "interaction_count": st.session_state.get("interaction_count", 0) + 1,
        "mood_history": st.session_state.get("mood_history", [])[-50:],
        "goals": st.session_state.get("goals", [])[-20:],
        "reminders": st.session_state.get("reminders", [])[-20:],
        "favorite_quotes": st.session_state.get("favorite_quotes", [])[-20:]
    }
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except Exception:
        pass

# ============================================================
# SESSION STATE
# ============================================================
class SessionState:
    def __init__(self):
        saved = load_memory()
        self.messages = []
        self.user_name = saved.get("name")
        self.student_level = saved.get("education_level")
        self.personal_memory = saved.get("facts", [])
        self.preferences = saved.get("preferences", [])
        self.topic_pattern = saved.get("topics", [])
        self.emotion = "neutral"
        self.tone = "Natural and friendly"
        self.confidence = "Medium"
        self.confidence_score = 0.7
        self.source = "KingsBot Brain"
        self.reason = "Generated using pattern recognition and memory."
        self.last_topic = "general knowledge"
        self.interaction_count = saved.get("interaction_count", 0)
        self.mood_history = saved.get("mood_history", [])
        self.response_time = 0
        self.goals = saved.get("goals", [])
        self.reminders = saved.get("reminders", [])
        self.favorite_quotes = saved.get("favorite_quotes", [])
        self.voice_input = None
        self.is_recording = False

st = SessionState()

# ============================================================
# NAME DETECTION
# ============================================================
def detect_name(text):
    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\bcall me ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\byou can call me ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\bi am ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\bi'm ([A-Za-z][A-Za-z '\-]{1,40})"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) >= 2:
                st.user_name = name
                save_memory()
                return name
    return None

# ============================================================
# GOAL DETECTION
# ============================================================
def detect_goal(text):
    patterns = [
        r"\bmy goal is ([^.!?]+)",
        r"\bi want to ([^.!?]+)",
        r"\bi aim to ([^.!?]+)",
        r"\bi dream of ([^.!?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            goal = match.group(1).strip()
            if goal and len(goal) > 5 and goal not in st.goals:
                st.goals.append(goal)
                st.goals = st.goals[-20:]
                save_memory()
                return goal
    return None

# ============================================================
# REMINDER DETECTION
# ============================================================
def detect_reminder(text):
    patterns = [
        r"\bremind me to ([^.!?]+)",
        r"\bremember to ([^.!?]+)",
        r"\bdon't forget to ([^.!?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            reminder = match.group(1).strip()
            if reminder and len(reminder) > 3:
                st.reminders.append({
                    "text": reminder,
                    "created": datetime.now().isoformat(),
                    "done": False
                })
                st.reminders = st.reminders[-20:]
                save_memory()
                return reminder
    return None

# ============================================================
# QUOTE DETECTION
# ============================================================
def detect_quote(text):
    match = re.search(r'"(.*?)"', text)
    if match:
        quote = match.group(1).strip()
        if quote and len(quote) > 5 and quote not in st.favorite_quotes:
            st.favorite_quotes.append(quote)
            st.favorite_quotes = st.favorite_quotes[-20:]
            save_memory()
            return quote
    return None

# ============================================================
# EDUCATION LEVELS
# ============================================================
LEVELS = {
    "PRIMARY 1": ["primary 1", "primary one", "pry 1", "grade 1"],
    "PRIMARY 2": ["primary 2", "primary two", "pry 2", "grade 2"],
    "PRIMARY 3": ["primary 3", "primary three", "pry 3", "grade 3"],
    "PRIMARY 4": ["primary 4", "primary four", "pry 4", "grade 4"],
    "PRIMARY 5": ["primary 5", "primary five", "pry 5", "grade 5"],
    "PRIMARY 6": ["primary 6", "primary six", "pry 6", "grade 6"],
    "JSS1": ["jss1", "jss 1", "jss one", "junior secondary 1", "grade 7"],
    "JSS2": ["jss2", "jss 2", "jss two", "junior secondary 2", "grade 8"],
    "JSS3": ["jss3", "jss 3", "jss three", "junior secondary 3", "grade 9"],
    "SS1": ["ss1", "ss 1", "ss one", "sss1", "sss 1", "senior secondary 1", "grade 10"],
    "SS2": ["ss2", "ss 2", "ss two", "sss2", "sss 2", "senior secondary 2", "grade 11"],
    "SS3": ["ss3", "ss 3", "ss three", "sss3", "sss 3", "senior secondary 3", "grade 12"],
    "UNIVERSITY": ["university", "undergraduate", "college", "uni", "tertiary", "polytechnic"]
}

def detect_student_level(text):
    lower = text.lower()
    for level, words in LEVELS.items():
        if any(word in lower for word in words):
            st.student_level = level
            save_memory()
            return level
    return None

# ============================================================
# ETHICAL FORGETTING
# ============================================================
def forget_information(text):
    lower = text.lower()
    
    if any(phrase in lower for phrase in [
        "forget everything", "forget all my memory", "delete all my memory",
        "reset memory", "clear memory", "erase everything"
    ]):
        st.user_name = None
        st.student_level = None
        st.personal_memory = []
        st.preferences = []
        st.topic_pattern = []
        st.mood_history = []
        st.goals = []
        st.reminders = []
        st.favorite_quotes = []
        save_memory()
        return "✅ Done. I cleared your saved personal memory."
    
    if "forget my name" in lower or "delete my name" in lower:
        st.user_name = None
        save_memory()
        return "✅ Done. I forgot your saved name."
    
    if "forget my class" in lower or "forget my education level" in lower:
        st.student_level = None
        save_memory()
        return "✅ Done. I forgot your saved education level."
    
    if "forget that" in lower or "delete that fact" in lower:
        if st.personal_memory:
            removed = st.personal_memory.pop()
            save_memory()
            return f"✅ Done. I forgot: '{removed}'"
    
    if "forget my goals" in lower or "delete my goals" in lower:
        st.goals = []
        save_memory()
        return "✅ Done. I forgot your goals."
    
    if "forget my reminders" in lower or "delete my reminders" in lower:
        st.reminders = []
        save_memory()
        return "✅ Done. I forgot your reminders."
    
    return None

# ============================================================
# EMOTIONAL INTELLIGENCE
# ============================================================
EMOTION_KEYWORDS = {
    "very frustrated": ["very angry", "so mad", "extremely frustrated", "furious", "enraged"],
    "frustrated": ["angry", "mad", "annoyed", "frustrated", "you are wrong", "mistake", "terrible", "worst", "useless"],
    "very sad": ["very sad", "so sad", "extremely upset", "devastated", "depressed"],
    "sad": ["sad", "crying", "upset", "hurt", "miserable", "disappointed"],
    "confused": ["confused", "don't understand", "do not understand", "explain again", "huh", "what do you mean", "i don't get"],
    "very worried": ["very worried", "extremely anxious", "terrified", "panicking"],
    "worried": ["worried", "scared", "afraid", "nervous", "anxious", "concerned"],
    "very happy": ["very happy", "so happy", "extremely happy", "ecstatic", "overjoyed"],
    "happy": ["happy", "great", "awesome", "thanks", "thank you", "yesss", "love", "amazing", "perfect", "wonderful", "excellent"]
}

def detect_emotion(text):
    lower = text.lower()
    
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(word in lower for word in keywords):
            st.mood_history.append({
                "emotion": emotion,
                "timestamp": datetime.now().isoformat()
            })
            st.mood_history = st.mood_history[-50:]
            save_memory()
            return emotion
    
    return "neutral"

# ============================================================
# TONE ADAPTATION
# ============================================================
def tone_for(emotion):
    tones = {
        "very frustrated": ("🧘 Very Calm & Patient", "Be extremely calm and patient. Show deep empathy."),
        "frustrated": ("😌 Calm & Direct", "Be calm, respectful, and direct. Acknowledge frustration."),
        "very sad": ("💖 Extra Warm & Caring", "Be very kind, warm, and supportive. Show extra empathy."),
        "sad": ("💙 Warm & Supportive", "Be kind, warm, and supportive. Offer encouragement."),
        "confused": ("🧩 Simple & Step-by-Step", "Use very simple language. Explain step by step."),
        "very worried": ("🤗 Very Reassuring", "Be extremely reassuring. Offer concrete steps."),
        "worried": ("🤝 Reassuring & Practical", "Be reassuring, careful, and practical."),
        "very happy": ("🎉 Very Enthusiastic", "Be very enthusiastic and celebratory."),
        "happy": ("😊 Friendly & Positive", "Be friendly, positive, and energetic."),
        "neutral": ("🤖 Natural & Friendly", "Be natural, friendly, clear, and concise.")
    }
    return tones.get(emotion, tones["neutral"])

# ============================================================
# PATTERN RECOGNITION
# ============================================================
def recognize_topic(text):
    lower = text.lower()
    categories = {
        "coding": ["code", "python", "program", "programming", "app", "software", "javascript", "html", "css"],
        "mathematics": ["math", "calculate", "equation", "algebra", "geometry", "calculus", "fraction", "decimal"],
        "science": ["science", "biology", "chemistry", "physics", "astronomy"],
        "sports": ["football", "soccer", "world cup", "player", "messi", "ronaldo"],
        "education": ["school", "class", "jss", "sss", "primary", "university", "teacher", "student"],
        "history": ["history", "historical", "war", "empire", "ancient"],
        "geography": ["country", "capital", "continent", "geography", "river", "mountain"],
        "technology": ["technology", "computer", "phone", "internet", "ai", "artificial intelligence"],
        "entertainment": ["movie", "film", "actor", "actress", "music", "song"],
        "health": ["health", "doctor", "hospital", "medicine", "sickness", "disease", "fitness", "exercise"],
        "business": ["business", "company", "money", "invest", "stock", "market", "profit"],
        "general knowledge": ["who is", "what is", "where is", "when did", "why is", "how does", "tell me about", "meaning of"]
    }
    for category, words in categories.items():
        if any(word in lower for word in words):
            return category
    return "general knowledge"

def update_topic(text):
    topic = recognize_topic(text)
    st.last_topic = topic
    if topic not in st.topic_pattern:
        st.topic_pattern.append(topic)
        st.topic_pattern = st.topic_pattern[-30:]
        save_memory()
    return topic

# ============================================================
# VERIFIED FACTS
# ============================================================
def verified_fact(question):
    lower = question.lower()
    
    # Sports
    if "messi" in lower and "world cup" in lower:
        return "🏆 Lionel Messi won the 2022 FIFA World Cup with Argentina."
    if "world cup" in lower and "winner" in lower:
        return "🏆 Argentina won the 2022 FIFA World Cup."
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
    
    return None

# ============================================================
# INTELLIGENT RESPONSE GENERATOR (BRAIN)
# ============================================================
def generate_intelligent_response(text):
    lower = text.lower()
    
    # Greetings
    if re.match(r'^(hi|hello|hey|greetings|sup|what\'s up|yo|howdy)', lower):
        responses = [
            "Hello! 👋 How can I help you today?",
            "Hi there! 😊 What's on your mind?",
            "Hey! Great to talk to you. What can I help with?",
            "Greetings! 🤖 I'm here to assist you."
        ]
        return random.choice(responses)
    
    # How are you
    if re.search(r'how are you|how\'s it going|how do you do', lower):
        responses = [
            "I'm doing great, thanks for asking! 😊 How are you?",
            "I'm functioning perfectly! 🤖 How can I help you today?",
            "I'm always ready to help! 💪 What do you need?"
        ]
        return random.choice(responses)
    
    # Name
    if re.search(r'what is your name|who are you|your name', lower):
        return "I'm KingsBot! 🤖 Your intelligent AI assistant. I have memory, emotions, tone adaptation, and a powerful brain — all with NO installation and NO API key!"
    
    # Time
    if re.search(r'what time is it|current time|time now', lower):
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."
    
    # Date
    if re.search(r'what day is it|what\'s the date', lower):
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
- "Forget everything"

Just ask me anything! 🚀
"""
    
    # Unknown
    return None

# ============================================================
# GENERATE RESPONSE
# ============================================================
def generate_response(user_message):
    start_time = time.time()
    
    # Core functions
    detect_name(user_message)
    detect_student_level(user_message)
    detect_goal(user_message)
    detect_reminder(user_message)
    detect_quote(user_message)
    
    forgotten = forget_information(user_message)
    if forgotten:
        st.source = "KingsBot memory system"
        st.confidence = "High"
        st.confidence_score = 0.95
        st.reason = "Memory change requested."
        st.response_time = time.time() - start_time
        return forgotten
    
    emotion = detect_emotion(user_message)
    st.emotion = emotion
    tone_name, tone_instruction = tone_for(emotion)
    st.tone = tone_name
    topic = update_topic(user_message)
    st.interaction_count += 1
    
    # Check verified facts
    fact = verified_fact(user_message)
    if fact:
        st.source = "KingsBot verified fact"
        st.confidence = "High"
        st.confidence_score = 0.92
        st.reason = "Built-in factual safeguard."
        st.response_time = time.time() - start_time
        return fact
    
    # Generate intelligent r

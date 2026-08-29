import streamlit as st
import streamlit.components.v1 as components
import json
import os
import re
import random
import time
from datetime import datetime

# ============================================================
# PAGE SETTINGS
# ============================================================
st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered"
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
    .recording-active {
        animation: pulse 0.8s infinite;
        background: #ff4444 !important;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    .stat-card {
        background: rgba(255,255,255,0.05);
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TITLE
# ============================================================
st.title("🤖 KingsBot AI")
st.caption("No Installation • Voice • Memory • EQ")

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

# ============================================================
# EMOTIONAL INTELLIGENCE
# ============================================================
EMOTION_KEYWORDS = {
    "very frustrated": ["very angry", "furious", "enraged"],
    "frustrated": ["angry", "mad", "annoyed", "frustrated", "wrong", "mistake"],
    "very sad": ["very sad", "devastated", "depressed"],
    "sad": ["sad", "crying", "upset", "hurt", "disappointed"],
    "confused": ["confused", "don't understand", "huh", "what do you mean"],
    "very worried": ["very worried", "terrified", "panicking"],
    "worried": ["worried", "scared", "afraid", "nervous", "anxious"],
    "very happy": ["very happy", "ecstatic", "overjoyed"],
    "happy": ["happy", "great", "awesome", "thanks", "yesss", "love", "amazing"],
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
        "very frustrated": ("🧘 Very Calm", "Be extremely calm and patient."),
        "frustrated": ("😌 Calm & Direct", "Be calm, respectful, and direct."),
        "very sad": ("💖 Extra Warm", "Be very kind, warm, and supportive."),
        "sad": ("💙 Warm", "Be kind, warm, and supportive."),
        "confused": ("🧩 Simple", "Use very simple language."),
        "very worried": ("🤗 Reassuring", "Be extremely reassuring."),
        "worried": ("🤝 Reassuring", "Be reassuring and practical."),
        "very happy": ("🎉 Enthusiastic", "Be very enthusiastic."),
        "happy": ("😊 Friendly", "Be friendly, positive, and energetic."),
        "neutral": ("🤖 Natural", "Be natural, friendly, and clear.")
    }
    return tones.get(emotion, tones["neutral"])

# ============================================================
# PATTERN RECOGNITION
# ============================================================
def recognize_topic(text):
    lower = text.lower()
    categories = {
        "coding": ["code", "python", "program", "programming", "app", "software"],
        "mathematics": ["math", "calculate", "equation", "algebra"],
        "science": ["science", "biology", "chemistry", "physics"],
        "sports": ["football", "soccer", "messi", "ronaldo"],
        "education": ["school", "class", "university", "teacher"],
        "history": ["history", "war", "empire", "ancient"],
        "geography": ["country", "capital", "continent", "river"],
        "technology": ["technology", "computer", "internet", "ai"],
        "entertainment": ["movie", "film", "actor", "music"],
        "general knowledge": ["who is", "what is", "where is", "tell me about"]
    }
    for category, words in categories.items():
        if any(word in lower for word in words):
            return category
    return "general knowledge"

# ============================================================
# NAME DETECTION
# ============================================================
def detect_name(text):
    match = re.search(r"my name is ([A-Za-z ]+)", text, re.IGNORECASE)
    if match:
        st.session_state.user_name = match.group(1).strip()
        return match.group(1).strip()
    return None

# ============================================================
# GOAL DETECTION
# ============================================================
def detect_goal(text):
    match = re.search(r"my goal is ([^.!?]+)", text, re.IGNORECASE)
    if match:
        goal = match.group(1).strip()
        if goal not in st.session_state.goals:
            st.session_state.goals.append(goal)
            st.session_state.goals = st.session_state.goals[-10:]
        return goal
    return None

# ============================================================
# REMINDER DETECTION
# ============================================================
def detect_reminder(text):
    match = re.search(r"remind me to ([^.!?]+)", text, re.IGNORECASE)
    if match:
        reminder = match.group(1).strip()
        st.session_state.reminders.append({
            "text": reminder,
            "done": False
        })
        st.session_state.reminders = st.session_state.reminders[-10:]
        return reminder
    return None

# ============================================================
# VERIFIED FACTS
# ============================================================
def verified_fact(question):
    lower = question.lower()
    
    if "messi" in lower and "world cup" in lower:
        return "🏆 Lionel Messi won the 2022 FIFA World Cup with Argentina."
    if "nigeria" in lower and "capital" in lower:
        return "🏙️ The capital of Nigeria is Abuja."
    if "what year is it" in lower or "current year" in lower:
        return f"📅 The current year is {datetime.now().year}."
    if "today's date" in lower or "what date is it" in lower:
        return f"📅 Today is {datetime.now().strftime('%B %d, %Y')}."
    if "what time" in lower:
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."
    
    return None

# ============================================================
# INTELLIGENT RESPONSE GENERATOR
# ============================================================
def generate_intelligent_response(text):
    lower = text.lower()
    
    if re.match(r'^(hi|hello|hey|greetings|sup|what\'s up|yo)', lower):
        return random.choice([
            "Hello! 👋 How can I help you today?",
            "Hi there! 😊 What's on your mind?",
            "Hey! Great to talk to you!",
            "Greetings! 🤖 I'm here to assist you."
        ])
    
    if re.search(r'how are you|how\'s it going', lower):
        return random.choice([
            "I'm doing great, thanks! 😊 How are you?",
            "I'm functioning perfectly! 🤖 How can I help?",
            "I'm always ready to help! 💪"
        ])
    
    if re.search(r'what is your name|who are you', lower):
        return "I'm KingsBot! 🤖 Your intelligent AI assistant with memory, emotions, voice, and no installation!"
    
    if re.search(r'what time is it|current time', lower):
        return f"🕐 The current time is {datetime.now().strftime('%I:%M %p')}."
    
    if re.search(r'what day is it|what\'s the date', lower):
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
    
    if re.search(r'help|what can you do|capabilities', lower):
        return """
🤖 **I can help you with:**

📚 General Knowledge
🧮 Mathematics
💻 Coding
🎯 Goals Tracking
⏰ Reminders
💬 Favorite Quotes
🧠 Memory
❤️ Emotion Detection
🎭 Tone Adaptation

**Try these:**
- "My name is Alex"
- "My goal is to learn Python"
- "Remind me to call mom"
- "What is 25 x 4?"
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
    
    emotion = detect_emotion(user_message)
    tone_name, tone_instruction = tone_for(emotion)
    st.session_state.tone = tone_name
    st.session_state.last_topic = recognize_topic(user_message)
    st.session_state.interaction_count += 1
    
    fact = verified_fact(user_message)
    if fact:
        return fact
    
    response = generate_intelligent_response(user_message)
    
    if not response:
        response = "I'm here to help! What would you like to know?"
    
    return response

# ============================================================
# DISPLAY CONVERSATION
# ============================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

# ============================================================
# MICROPHONE COMPONENT (LONG PRESS)
# ============================================================
st.subheader("🎤 Voice Input")
components.html("""
<div style="text-align:center;margin:10px 0;">
    <button 
        id="micButton"
        style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 50%;
            width: 70px;
            height: 70px;
            font-size: 30px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 20px rgba(102,126,234,0.4);
        "
        onmousedown="startRecording()"
        onmouseup="stopRecording()"
        onmouseleave="stopRecording()"
        ontouchstart="startRecording()"
        ontouchend="stopRecording()"
    >
        🎤
    </button>
    <div id="status" style="margin-top:8px;font-size:14px;color:#888;">Press and hold to record • Release to send</div>
    <div id="recordingStatus" style="display:none;color:#ff4444;font-weight:bold;margin-top:5px;">🔴 Recording...</div>
</div>
<script>
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;
    let stream = null;
    let timerInterval = null;
    let seconds = 0;

    function startRecording() {
        if (isRecording) return;
        isRecording = true;
        seconds = 0;
        
        document.getElementById('micButton').style.background = '#ff4444';
        document.getElementById('micButton').style.boxShadow = '0 4px 30px rgba(255,68,68,0.6)';
        document.getElementById('recordingStatus').style.display = 'block';
        document.getElementById('recordingStatus').textContent = '🔴 Recording... ' + seconds + 's';
        
        timerInterval = setInterval(function() {
            seconds++;
            document.getElementById('recordingStatus').textContent = '🔴 Recording... ' + seconds + 's';
        }, 1000);

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(streamData) {
                stream = streamData;
                mediaRecorder = new MediaRecorder(streamData);
                audioChunks = [];

                mediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = function() {
                    const blob = new Blob(audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.onload = function() {
                        const audioData = reader.result.split(',')[1];
                        const event = new CustomEvent('streamlit:voice', {
                            detail: { audio_data: audioData }
                        });
                        window.dispatchEvent(event);
                    };
                    reader.readAsDataURL(blob);
                    
                    if (stream) {
                        stream.getTracks().forEach(track => track.stop());
                        stream = null;
                    }
                    isRecording = false;
                    clearInterval(timerInterval);
                    document.getElementById('micButton').style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
                    document.getElementById('micButton').style.boxShadow = '0 4px 20px rgba(102,126,234,0.4)';
                    document.getElementById('recordingStatus').style.display = 'none';
                };

                mediaRecorder.start();
            })
            .catch(function(error) {
                alert('Microphone access denied. Please allow microphone access.');
                isRecording = false;
                clearInterval(timerInterval);
                document.getElementById('micButton').style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
                document.getElementById('micButton').style.boxShadow = '0 4px 20px rgba(102,126,234,0.4)';
                document.getElementById('recordingStatus').style.display = 'none';
            });
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
    }
</script>
""", height=150)

# ============================================================
# TEXT INPUT
# ============================================================
prompt = st.chat_input("Type your message...")

# ============================================================
# PROCESS MESSAGE
# ============================================================
if prompt:
    # Show user message
    st.markdown(f'<div class="user-bubble">👤 {prompt}</div>', unsafe_allow_html=True)
    
    # Generate response
    with st.spinner("🧠 Thinking..."):
        start_time = time.time()
        response = generate_response(prompt)
        elapsed = time.time() - start_time
    
    # Show response
    st.markdown(f'<div class="assistant-bubble">🤖 {response}</div>', unsafe_allow_html=True)
    
    # Show metadata
    emotion_emoji = {
        "happy": "😊", "very happy": "🎉", "sad": "😢", "very sad": "😭",
        "frustrated": "😤", "very frustrated": "💢", "confused": "🤔",
        "worried": "😰", "very worried": "😱", "neutral": "😐"
    }.get(st.session_state.emotion, "🤖")
    
    st.caption(f"⏱️ {elapsed:.2f}s • {emotion_emoji} {st.session_state.emotion} • 🎭 {st.session_state.tone} • 🎯 {st.session_state.last_topic}")
    
    # Save messages
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.rerun()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("👤 Profile")
    st.write(f"Name: {st.session_state.user_name or 'Not set'}")
    st.write(f"Interactions: {st.session_state.interaction_count}")
    
    emotion_emoji = {
        "happy": "😊", "very happy": "🎉", "sad": "😢", "very sad": "😭",
        "frustrated": "😤", "very frustrated": "💢", "confused": "🤔",
        "worried": "😰", "very worried": "😱", "neutral": "😐"
    }.get(st.session_state.emotion, "🤖")
    st.write(f"Emotion: {emotion_emoji} {st.session_state.emotion}")
    
    st.divider()
    
    st.subheader("🎯 Goals")
    for g in st.session_state.goals:
        st.write(f"• {g}")
    if not st.session_state.goals:
        st.caption("Say 'my goal is...'")
    
    st.subheader("⏰ Reminders")
    for r in st.session_state.reminders:
        if not r["done"]:
            col1, col2 = st.columns([4, 1])
            col1.write(f"• {r['text']}")
            if col2.button("✅", key=f"rem_{r['text'][:10]}"):
                r["done"] = True
    
    st.subheader("🧠 Memory")
    for f in st.session_state.personal_memory[-5:]:
        st.write(f"• {f}")
    
    st.divider()
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    st.caption("🤖 KingsBot AI • No Installation")

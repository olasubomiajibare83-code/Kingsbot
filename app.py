import base64
import io
import json
import os
import re

import streamlit as st
import streamlit.components.v1 as components
import speech_recognition as sr
from gtts import gTTS
from groq import Groq

# ============================================================
# KINGSBOT AI — GROQ COMPOUND MINI
# Fast general AI + live web search + code execution
# ============================================================

MODEL_NAME = "groq/compound-mini"
MODEL_VERSION = "latest"
MEMORY_FILE = "kingsbot_memory.json"

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered",
)

# ============================================================
# MEMORY
# ============================================================

def default_memory():
    return {
        "name": None,
        "education_level": None,
        "facts": [],
        "preferences": [],
        "topics": [],
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
        "name": st.session_state.user_name,
        "education_level": st.session_state.student_level,
        "facts": st.session_state.personal_memory,
        "preferences": st.session_state.preferences,
        "topics": st.session_state.topic_pattern,
    }

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ============================================================
# SESSION STATE
# ============================================================

saved = load_memory()

DEFAULT_STATE = {
    "messages": [],
    "user_name": saved["name"],
    "student_level": saved["education_level"],
    "personal_memory": saved["facts"],
    "preferences": saved["preferences"],
    "topic_pattern": saved["topics"],
    "emotion": "neutral",
    "tone": "Natural and friendly",
    "confidence": "Medium",
    "source": "Groq Compound Mini",
    "last_topic": "general knowledge",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GROQ CONNECTION
# ============================================================

def get_api_key():
    key = None

    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

    if not key:
        key = os.environ.get("GROQ_API_KEY")

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY was not found. "
            'Add GROQ_API_KEY = "your-key-here" '
            "to Streamlit Secrets."
        )

    return str(key).strip()


def get_groq_client():
    return Groq(
        api_key=get_api_key(),
        default_headers={
            "Groq-Model-Version": MODEL_VERSION
        },
        timeout=60.0,
        max_retries=2,
    )


# ============================================================
# USER NAME
# ============================================================

def detect_name(text):
    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\bcall me ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\byou can call me ([A-Za-z][A-Za-z '\-]{1,40})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            name = match.group(1).strip()
            st.session_state.user_name = name
            save_memory()
            return name

    return None


# ============================================================
# EDUCATION LEVEL
# ============================================================

LEVELS = {
    "PRIMARY 1": ["primary 1", "primary one", "pry 1"],
    "PRIMARY 2": ["primary 2", "primary two", "pry 2"],
    "PRIMARY 3": ["primary 3", "primary three", "pry 3"],
    "PRIMARY 4": ["primary 4", "primary four", "pry 4"],
    "PRIMARY 5": ["primary 5", "primary five", "pry 5"],
    "PRIMARY 6": ["primary 6", "primary six", "pry 6"],
    "JSS1": ["jss1", "jss 1", "jss one", "junior secondary 1"],
    "JSS2": ["jss2", "jss 2", "jss two", "junior secondary 2"],
    "JSS3": ["jss3", "jss 3", "jss three", "junior secondary 3"],
    "SS1": ["ss1", "ss 1", "ss one", "sss1", "sss 1"],
    "SS2": ["ss2", "ss 2", "ss two", "sss2", "sss 2"],
    "SS3": ["ss3", "ss 3", "ss three", "sss3", "sss 3"],
    "UNIVERSITY": ["university", "undergraduate", "college"],
}


def detect_student_level(text):
    lower = text.lower()

    for level, words in LEVELS.items():
        if any(word in lower for word in words):
            st.session_state.student_level = level
            save_memory()
            return level

    return None


# ============================================================
# PERSONAL MEMORY
# ============================================================

def remember_information(text):
    match = re.search(
        r"\b(?:remember that|remember this|please remember|save this)"
        r"\b\s*[:,-]?\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    fact = match.group(1).strip()

    if fact and fact not in st.session_state.personal_memory:
        st.session_state.personal_memory.append(fact)
        st.session_state.personal_memory = (
            st.session_state.personal_memory[-50:]
        )
        save_memory()

    return fact


def forget_information(text):
    lower = text.lower()

    if any(
        phrase in lower
        for phrase in [
            "forget everything",
            "forget all my memory",
            "delete all my memory",
        ]
    ):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        save_memory()
        return "Done. I cleared your saved personal memory."

    if "forget my name" in lower or "delete my name" in lower:
        st.session_state.user_name = None
        save_memory()
        return "Done. I forgot your saved name."

    if (
        "forget my class" in lower
        or "forget my education level" in lower
    ):
        st.session_state.student_level = None
        save_memory()
        return "Done. I forgot your saved education level."

    return None


# ============================================================
# EMOTION
# ============================================================

def detect_emotion(text):
    lower = text.lower()

    if any(
        word in lower
        for word in [
            "angry",
            "mad",
            "annoyed",
            "frustrated",
            "you are wrong",
            "mistake",
        ]
    ):
        return "frustrated"

    if any(
        word in lower
        for word in ["sad", "crying", "upset", "hurt"]
    ):
        return "sad"

    if any(
        word in lower
        for word in [
            "confused",
            "don't understand",
            "do not understand",
            "explain again",
        ]
    ):
        return "confused"

    if any(
        word in lower
        for word in [
            "worried",
            "scared",
            "afraid",
            "nervous",
        ]
    ):
        return "worried"

    if any(
        word in lower
        for word in [
            "happy",
            "great",
            "awesome",
            "thanks",
            "thank you",
            "yesss",
        ]
    ):
        return "happy"

    return "neutral"


def tone_for(emotion):
    tones = {
        "frustrated": (
            "Calm and direct",
            "Be calm, respectful, direct, and acknowledge frustration.",
        ),
        "sad": (
            "Warm and supportive",
            "Be kind, warm, and supportive without pretending to have human feelings.",
        ),
        "confused": (
            "Simple and step-by-step",
            "Use simple language and explain step by step.",
        ),
        "worried": (
            "Reassuring and practical",
            "Be reassuring, careful, and practical.",
        ),
        "happy": (
            "Friendly and positive",
            "Be friendly, positive, and energetic.",
        ),
        "neutral": (
            "Natural and friendly",
            "Be natural, friendly, clear, and concise.",
        ),
    }

    return tones.get(emotion, tones["neutral"])


# ============================================================
# TOPIC DETECTION
# ============================================================

def recognize_topic(text):
    lower = text.lower()

    categories = {
        "coding": [
            "code", "python", "program", "programming",
            "streamlit", "javascript", "html", "css",
            "debug", "software",
        ],
        "mathematics": [
            "math", "calculate", "equation", "algebra",
            "geometry", "calculus", "percentage",
        ],
        "science": [
            "science", "biology", "chemistry",
            "physics", "space", "astronomy",
        ],
        "sports": [
            "football", "soccer", "world cup",
            "player", "basketball", "tennis",
        ],
        "education": [
            "school", "class", "jss", "sss",
            "primary", "university", "exam",
        ],
        "history": [
            "history", "historical", "war",
            "empire", "ancient",
        ],
        "geography": [
            "country", "capital", "continent",
            "geography", "river", "mountain",
        ],
        "technology": [
            "technology", "computer", "phone",
            "internet", "ai", "artificial intelligence",
        ],
        "entertainment": [
            "movie", "film", "actor", "actress",
            "music", "song", "game", "gaming",
        ],
        "writing": [
            "write", "rewrite", "essay",
            "letter", "story", "poem", "email",
        ],
    }

    for category, words in categories.items():
        if any(word in lower for word in words):
            return category

    return "general knowledge"


def update_topic(text):
    topic = recognize_topic(text)
    st.session_state.last_topic = topic

    if topic not in st.session_state.topic_pattern:
        st.session_state.topic_pattern.append(topic)
        st.session_state.topic_pattern = (
            st.session_state.topic_pattern[-30:]
        )
        save_memory()

    return topic


# ============================================================
# CONTEXT
# ============================================================

def memory_context():
    items = []

    if st.session_state.user_name:
        items.append(
            "User name: " + st.session_state.user_name
        )

    if st.session_state.student_level:
        items.append(
            "Education level: "
            + st.session_state.student_level
        )

    for fact in st.session_state.personal_memory[-20:]:
        items.append("Saved fact: " + fact)

    return "\n".join(items) if items else "No saved personal information."


def education_context():
    if st.session_state.student_level:
        return (
            "Match explanations to the user's level: "
            + st.session_state.student_level
        )

    return "Use clear general explanations."


# ============================================================
# KINGSBOT AI BRAIN
# ============================================================

def generate_response(user_message):
    # These functions are intentionally defined above this function.
    detect_name(user_message)
    detect_student_level(user_message)
    remember_information(user_message)

    forgotten = forget_information(user_message)

    if forgotten:
        st.session_state.source = "KingsBot memory"
        st.session_state.confidence = "High"
        return forgotten

    emotion = detect_emotion(user_message)
    st.session_state.emotion = emotion

    tone_name, tone_instruction = tone_for(emotion)
    st.session_state.tone = tone_name

    topic = update_topic(user_message)

    system_prompt = f"""
You are KingsBot, a fast, intelligent, friendly general-purpose AI assistant.

Your job is to answer the user's actual question helpfully across many areas:
general knowledge, current events, technology, coding, programming,
debugging, mathematics, science, education, history, geography, sports,
entertainment, writing, planning, explanations, and problem solving.

IMPORTANT CURRENT INFORMATION RULE:
You have access to Groq Compound Mini's built-in tools. When a question
requires current or changing information, use the available web search tool
rather than guessing. This includes questions about 2026 events, today's
news, latest releases, current prices, current sports results, current
people, current products, and other time-sensitive facts.

Do not claim something is current unless the available current-information
tools support it.

CODING:
When the user asks for code, give complete working code where appropriate.
Check imports, indentation, syntax, function order, dependencies, and likely
runtime errors. Do not invent APIs.

MATHEMATICS:
Calculate carefully. Use the available code/calculation tools when useful.
Show the important steps when the user needs them.

EDUCATION:
{education_context()}

MEMORY:
{memory_context()}

EMOTION:
The detected emotion is {emotion}.
{tone_instruction}

TOPIC:
{topic}

CONVERSATION:
Use recent conversation messages when they are relevant. Follow the user's
new topic when they change subjects.

STYLE:
Be natural, friendly, direct, and concise for simple questions. Give more
detail for difficult questions. Do not reveal private chain-of-thought.
Give conclusions, explanations, calculations, and useful steps instead.

FOLLOW-UP:
Ask a short follow-up question only when it genuinely helps. Do not ask
unnecessary questions.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Keep recent context for speed and relevance.
    messages.extend(st.session_state.messages[-12:])

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    client = get_groq_client()

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=False,
        max_completion_tokens=4096,
    )

    message = completion.choices[0].message
    response = (message.content or "").strip()

    if not response:
        response = "I couldn't generate an answer. Please try again."

    used_tools = getattr(message, "executed_tools", None)

    if used_tools:
        st.session_state.source = (
            "Groq Compound Mini + built-in tools"
        )
    else:
        st.session_state.source = (
            "Groq Compound Mini"
        )

    st.session_state.confidence = "Medium-High"

    return response


# ============================================================
# SPEECH TO TEXT
# ============================================================

def speech_to_text(audio_file):
    try:
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 250
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.7

        audio_file.seek(0)

        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)

        return recognizer.recognize_google(
            audio_data,
            language="en-US",
        )

    except sr.UnknownValueError:
        return None
    except Exception:
        return None


# ============================================================
# TEXT TO SPEECH
# ============================================================

def text_to_speech(text):
    try:
        audio = io.BytesIO()

        gTTS(
            text=str(text)[:3000],
            lang="en",
            slow=False,
        ).write_to_fp(audio)

        audio.seek(0)
        return audio.getvalue()

    except Exception:
        return None


def play_voice_automatically(audio_bytes):
    if not audio_bytes:
        return

    try:
        encoded = base64.b64encode(audio_bytes).decode("utf-8")

        components.html(
            f"""
            <audio
                id="kingsbot-voice"
                autoplay
                controls
                style="width:100%;"
            >
                <source
                    src="data:audio/mpeg;base64,{encoded}"
                    type="audio/mpeg"
                >
            </audio>
            <script>
                const player =
                    document.getElementById("kingsbot-voice");
                if (player) {{
                    player.play().catch(() => {{
                        console.log("Autoplay was blocked.");
                    }});
                }}
            </script>
            """,
            height=75,
        )
    except Exception:
        pass


# ============================================================
# SAVE CHAT
# ============================================================

def create_chat_file():
    lines = [
        "KINGSBOT AI - SAVED CONVERSATION",
        "=" * 50,
        "",
    ]

    if st.session_state.user_name:
        lines.append(
            "Name: " + st.session_state.user_name
        )

    if st.session_state.student_level:
        lines.append(
            "Education: " + st.session_state.student_level
        )

    lines.extend(
        [
            "",
            "PERSONAL MEMORY",
            "-" * 40,
        ]
    )

    lines.extend(st.session_state.personal_memory)

    lines.extend(
        [
            "",
            "CONVERSATION",
            "=" * 50,
        ]
    )

    for item in st.session_state.messages:
        label = "YOU" if item["role"] == "user" else "KINGSBOT"
        lines.append(label + ":")
        lines.append(item["content"])
        lines.append("")
        lines.append("-" * 50)

    return "\n".join(lines)


# ============================================================
# MAIN INTERFACE
# ============================================================

st.title("🤖 KingsBot AI")
st.caption(
    "⚡ Fast • 🧠 Compound Mini • 🌍 Live web knowledge • "
    "💻 Coding • 🧮 Math • 🎤 Voice"
)

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])


# ============================================================
# MICROPHONE
# ============================================================

st.subheader("🎤 Voice Assistant")

audio_file = st.audio_input(
    "Tap the microphone and speak",
    sample_rate=16000,
    key="kingsbot_microphone",
)

voice_prompt = None

if audio_file:
    with st.spinner("🎧 Understanding your voice..."):
        voice_prompt = speech_to_text(audio_file)

    if voice_prompt:
        st.success("You said: " + voice_prompt)
    else:
        st.error(
            "I couldn't understand the recording. Please try again."
        )


# ============================================================
# TEXT CHAT
# ============================================================

text_prompt = st.chat_input("Ask KingsBot anything...")
prompt = voice_prompt or text_prompt

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("⚡ Thinking..."):
            try:
                response = generate_response(prompt)

            except Exception as error:
                response = (
                    "I couldn't reach the AI brain.\n\n"
                    "Please check your GROQ_API_KEY in Streamlit "
                    "Secrets and confirm that your Groq API access "
                    "is active.\n\n"
                    "Technical error: "
                    + str(error)
                )

                st.session_state.source = "Groq connection error"
                st.session_state.confidence = "Unknown"

        st.markdown(response)

        st.caption(
            "🔎 Source: " + st.session_state.source
        )

        st.caption(
            "📊 Confidence: " + st.session_state.confidence
        )

        with st.spinner("🔊 Preparing voice..."):
            audio = text_to_speech(response)

        if audio:
            play_voice_automatically(audio)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🤖 KingsBot")

    st.subheader("👤 Memory")
    st.write(
        "Name: "
        + (st.session_state.user_name or "Not saved")
    )
    st.write(
        "Class: "
        + (st.session_state.student_level or "Not saved")
    )
    st.write(
        "Saved facts: "
        + str(len(st.session_state.personal_memory))
    )

    st.divider()

    st.subheader("❤️ Emotion")
    st.write(st.session_state.emotion)

    st.subheader("🎭 Tone")
    st.write(st.session_state.tone)

    st.subheader("🧩 Topic")
    st.write(st.session_state.last_topic)

    st.subheader("🧠 Brain")
    st.write("Groq Compound Mini")
    st.write("Live web tools: available")
    st.write("Code execution: available")
    st.write("Speed: optimized")

    st.divider()

    st.subheader("✨ Features")

    features = [
        "⚡ Fast AI",
        "🌍 Current web information",
        "💻 Coding",
        "🧮 Mathematics",
        "🔬 Science",
        "📚 Education",
        "🌍 History",
        "🗺️ Geography",
        "⚽ Sports",
        "🎬 Entertainment",
        "✍️ Writing",
        "❤️ Emotion detection",
        "🎭 Tone adaptation",
        "👤 Memory",
        "🧹 Forget memory",
        "🧩 Topic recognition",
        "💬 Conversation context",
        "🎤 Voice input",
        "🔊 Voice output",
        "💾 Save conversations",
    ]

    for feature in features:
        st.write(feature)

    st.divider()

    if st.session_state.messages:
        st.download_button(
            "💾 Save conversation",
            create_chat_file(),
            "kingsbot_conversation.txt",
            "text/plain",
        )

    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🧹 Forget personal memory"):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        save_memory()
        st.rerun()

    st.caption(
        "Model: " + MODEL_NAME
    )
    st.caption(
        "Keep your GROQ_API_KEY in Streamlit Secrets."
    )

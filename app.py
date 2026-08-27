import io
import json
import os
import re
from datetime import datetime

import requests
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from openai import OpenAI


# ============================================================
# KINGSBOT AI - COMPLETE UPGRADED VERSION
# ============================================================

MODEL_NAME = "gpt-5.6-luna"
CURRENT_DATE = "August 26, 2026"
MEMORY_FILE = "kingsbot_memory.json"
REQUEST_FILE = "kingsbot_request_state.json"
MAX_REQUESTS = 30
REQUEST_WINDOW_SECONDS = 3 * 60 * 60

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


saved = load_memory()


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
# KINGSBOT REQUEST LIMIT
# 30 successful AI requests every 3 hours.
# Failed OpenAI requests are NOT counted.
# ============================================================

def get_request_state():
    now = datetime.now().timestamp()

    data = {
        "count": 0,
        "window_start": now,
    }

    try:
        if os.path.exists(REQUEST_FILE):
            with open(REQUEST_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)

            if isinstance(saved, dict):
                data["count"] = int(saved.get("count", 0))
                data["window_start"] = float(
                    saved.get("window_start", now)
                )
    except Exception:
        data = {
            "count": 0,
            "window_start": now,
        }

    if now - data["window_start"] >= REQUEST_WINDOW_SECONDS:
        data = {
            "count": 0,
            "window_start": now,
        }

        try:
            with open(REQUEST_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
        except Exception:
            pass

    return data


def save_request_state(data):
    try:
        temp_path = REQUEST_FILE + ".tmp"

        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        os.replace(temp_path, REQUEST_FILE)
    except Exception:
        pass


def requests_remaining():
    data = get_request_state()

    return max(
        0,
        MAX_REQUESTS - int(data.get("count", 0)),
    )


def can_make_request():
    data = get_request_state()

    return (
        int(data.get("count", 0))
        < MAX_REQUESTS
    )


def record_request():
    data = get_request_state()

    data["count"] = (
        int(data.get("count", 0)) + 1
    )

    save_request_state(data)


def request_limit_message():
    data = get_request_state()

    remaining = max(
        0,
        MAX_REQUESTS - int(data.get("count", 0)),
    )

    elapsed = (
        datetime.now().timestamp()
        - float(
            data.get(
                "window_start",
                datetime.now().timestamp(),
            )
        )
    )

    seconds_left = max(
        0,
        REQUEST_WINDOW_SECONDS - elapsed,
    )

    hours = int(seconds_left // 3600)

    minutes = int(
        (seconds_left % 3600) // 60
    )

    return (
        f"⏳ You have reached the "
        f"{MAX_REQUESTS}-request limit.\n\n"
        f"Your limit resets in "
        f"**{hours}h {minutes}m**.\n\n"
        f"Requests remaining: "
        f"**{remaining}**"
    )


def is_openai_rate_or_quota_error(error):
    error_name = type(error).__name__.lower()
    error_text = str(error).lower()

    limit_words = [
        "ratelimit",
        "rate limit",
        "rate_limit",
        "quota",
        "insufficient_quota",
        "too many requests",
        "billing",
    ]

    return (
        "ratelimit" in error_name
        or any(word in error_text for word in limit_words)
    )


def openai_limit_error_message(error):
    if is_openai_rate_or_quota_error(error):
        return (
            "⚠️ OpenAI returned a rate-limit or quota error.\n\n"
            "This is separate from KingsBot's "
            f"{MAX_REQUESTS}-request / 3-hour limit.\n\n"
            "KingsBot did NOT use one of your requests for this "
            "failed OpenAI call.\n\n"
            "Please check the OpenAI API project's usage, billing, "
            "quota, or model access."
        )

    return (
        "KingsBot couldn't reach the OpenAI AI brain right now.\n\n"
        "Please check your OpenAI API key, model access, and internet "
        "connection.\n\n"
        "Technical detail: " + str(error)
    )


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "messages": [],
    "user_name": saved["name"],
    "student_level": saved["education_level"],
    "personal_memory": saved["facts"],
    "preferences": saved["preferences"],
    "topic_pattern": saved["topics"],
    "emotion": "neutral",
    "tone": "Natural and friendly",
    "confidence": "Medium",
    "source": "GPT-5.6 Luna",
    "reason": "Generated by the OpenAI cloud model.",
    "last_topic": "general knowledge",
    "last_user_question": "",
    "last_response": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# MODEL / OPENAI BRAIN
# ============================================================

def get_openai_client():
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


client = get_openai_client()

if client is None:
    st.error(
        "KingsBot cannot find OPENAI_API_KEY in Streamlit Secrets. "
        "Add the secret, then restart the app."
    )
    st.stop()


# NAME / EDUCATION / MEMORY
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
    "SS1": ["ss1", "ss 1", "ss one", "sss1", "sss 1", "senior secondary 1"],
    "SS2": ["ss2", "ss 2", "ss two", "sss2", "sss 2", "senior secondary 2"],
    "SS3": ["ss3", "ss 3", "ss three", "sss3", "sss 3", "senior secondary 3"],
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


def remember_information(text):
    match = re.search(
        r"\b(?:remember that|remember this|please remember|save this)\b"
        r"\s*[:,-]?\s*(.+)",
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


def remember_preference(text):
    match = re.search(
        r"\b(?:i prefer|i like|i love|my favorite is|my favourite is)\b"
        r"\s+(.+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    preference = match.group(1).strip()

    if preference and preference not in st.session_state.preferences:
        st.session_state.preferences.append(preference)
        st.session_state.preferences = (
            st.session_state.preferences[-30:]
        )
        save_memory()

    return preference


def forget_information(text):
    lower = text.lower()

    if any(
        phrase in lower
        for phrase in [
            "forget everything",
            "forget all my memory",
            "delete all my memory",
            "clear all my memory",
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
# EMOTION + TONE
# ============================================================

def detect_emotion(text):
    lower = text.lower()

    groups = {
        "frustrated": [
            "angry",
            "mad",
            "annoyed",
            "frustrated",
            "you are wrong",
            "mistake",
            "this is wrong",
        ],
        "sad": ["sad", "crying", "upset", "hurt", "unhappy"],
        "confused": [
            "confused",
            "don't understand",
            "do not understand",
            "explain again",
            "i don't get it",
        ],
        "worried": [
            "worried",
            "scared",
            "afraid",
            "nervous",
            "anxious",
        ],
        "excited": [
            "excited",
            "amazing",
            "wow",
            "can't wait",
        ],
        "happy": [
            "happy",
            "great",
            "awesome",
            "thanks",
            "thank you",
            "yesss",
        ],
    }

    for emotion, words in groups.items():
        if any(word in lower for word in words):
            return emotion

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
            "Use simple words, examples, and numbered steps when useful.",
        ),
        "worried": (
            "Reassuring and practical",
            "Be reassuring, careful, realistic, and practical.",
        ),
        "excited": (
            "Energetic and positive",
            "Match the user's excitement while staying accurate.",
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
# TOPIC RECOGNITION
# ============================================================

TOPIC_KEYWORDS = {
    "coding": [
        "code", "python", "program", "programming", "streamlit",
        "app", "software", "javascript", "html", "css", "github",
    ],
    "mathematics": [
        "math", "calculate", "equation", "algebra", "geometry",
        "calculus", "percentage", "fraction", "multiply", "divide",
    ],
    "science": [
        "science", "biology", "chemistry", "physics", "experiment",
        "atom", "cell", "energy",
    ],
    "sports": [
        "football", "soccer", "world cup", "player", "messi",
        "ronaldo", "basketball", "tennis",
    ],
    "education": [
        "school", "class", "jss", "sss", "primary", "university",
        "exam", "lesson", "homework",
    ],
    "history": [
        "history", "historical", "war", "empire", "ancient",
        "kingdom", "president",
    ],
    "geography": [
        "country", "capital", "continent", "geography", "river",
        "mountain", "ocean", "city",
    ],
    "technology": [
        "technology", "computer", "phone", "internet", "ai",
        "artificial intelligence", "android",
    ],
    "entertainment": [
        "movie", "film", "actor", "actress", "music", "song",
        "singer", "game", "gaming",
    ],
    "business": [
        "business", "company", "money", "startup", "customer",
        "marketing", "selling",
    ],
    "health": [
        "health", "body", "exercise", "food", "sleep",
    ],
    "general knowledge": [
        "who is", "what is", "where is", "when did", "why is",
        "how does", "tell me about", "meaning of",
    ],
}


def recognize_topic(text):
    lower = text.lower()

    best_topic = "general knowledge"
    best_score = 0

    for topic, words in TOPIC_KEYWORDS.items():
        score = sum(1 for word in words if word in lower)

        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic


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
# VERIFIED FACTS
# ============================================================

def verified_fact(question):
    lower = question.lower()

    if "messi" in lower and "world cup" in lower:
        return (
            "Lionel Messi has won the FIFA World Cup once, "
            "with Argentina at the 2022 FIFA World Cup."
        )

    if (
        "what year is it" in lower
        or "which year is it" in lower
        or "current year" in lower
    ):
        return "The current year is 2026."

    if (
        "today's date" in lower
        or "todays date" in lower
        or "what date is it" in lower
    ):
        return "Today is August 26, 2026."

    if (
        ("spider-man" in lower or "spiderman" in lower)
        and "2026" in lower
    ):
        return (
            "The Spider-Man film scheduled for 2026 is "
            "Spider-Man: Brand New Day."
        )

    return None


# ============================================================
# CURRENT INFORMATION
# ============================================================

def needs_current_lookup(text):
    lower = text.lower()

    return any(
        word in lower
        for word in [
            "today",
            "right now",
            "currently",
            "latest",
            "recent",
            "this year",
            "this month",
            "this week",
            "2026",
            "news",
        ]
    )


def current_lookup(question):
    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": question,
                "format": "json",
                "utf8": "1",
                "srlimit": 3,
            },
            headers={"User-Agent": "KingsBotAI/2.0"},
            timeout=8,
        )
        response.raise_for_status()

        results = []
        items = (
            response.json()
            .get("query", {})
            .get("search", [])
        )

        for item in items:
            title = item.get("title")

            if not title:
                continue

            try:
                page = requests.get(
                    "https://en.wikipedia.org/api/rest_v1/page/summary/"
                    + requests.utils.quote(title),
                    headers={"User-Agent": "KingsBotAI/2.0"},
                    timeout=8,
                )
                page.raise_for_status()

                summary = page.json().get("extract")

                if summary:
                    results.append(
                        title + ":\n" + summary
                    )

            except Exception:
                continue

        if results:
            return "\n\n".join(results[:3])

    except Exception:
        pass

    return None


# ============================================================
# CONTEXT
# ============================================================

def memory_context():
    items = []

    if st.session_state.user_name:
        items.append(
            "User's name: " + st.session_state.user_name
        )

    if st.session_state.student_level:
        items.append(
            "User's education level: "
            + st.session_state.student_level
        )

    for fact in st.session_state.personal_memory[-20:]:
        items.append("Saved user fact: " + fact)

    for preference in st.session_state.preferences[-10:]:
        items.append("User preference: " + preference)

    return "\n".join(items) if items else "No personal information is saved."


def education_context():
    if st.session_state.student_level:
        return (
            "The user's education level is "
            + st.session_state.student_level
            + ". Match educational explanations to that level. "
              "If the user requests advanced material, teach it at "
              "the requested level."
        )

    return (
        "The user's education level is unknown. "
        "Use a clear general explanation."
    )


def conversation_context():
    recent = st.session_state.messages[-10:]

    if not recent:
        return "No previous conversation."

    lines = []

    for message in recent:
        role = message.get("role", "user").upper()
        content = str(message.get("content", ""))
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


# ============================================================
# PROACTIVE FOLLOW-UP QUESTION
# ============================================================

def should_ask_followup(text):
    lower = text.lower().strip()

    if len(lower) < 12:
        return False

    if lower.endswith("?"):
        return False

    return any(
        word in lower
        for word in [
            "tell me about",
            "explain",
            "teach me",
            "how",
            "why",
            "what",
            "learn",
        ]
    )


def add_proactive_instruction(prompt, user_message, topic):
    if not should_ask_followup(user_message):
        return prompt

    return (
        prompt
        + "\nPROACTIVE QUESTION:\n"
        + "After answering, you may ask ONE short, useful follow-up "
          "question related to the user's current topic. Do not ask "
          "a question every time. Never ask an unrelated question. "
          "Current topic: "
        + topic
        + ".\n\n"
    )


# ============================================================
# GENERATE RESPONSE
# ============================================================

def generate_response(user_message):
    detect_name(user_message)
    detect_student_level(user_message)
    remember_information(user_message)
    remember_preference(user_message)

    forgotten = forget_information(user_message)

    if forgotten:
        st.session_state.source = "KingsBot memory system"
        st.session_state.confidence = "High"
        st.session_state.reason = (
            "The user explicitly requested a memory change."
        )
        return forgotten

    emotion = detect_emotion(user_message)
    st.session_state.emotion = emotion

    tone_name, tone_instruction = tone_for(emotion)
    st.session_state.tone = tone_name

    topic = update_topic(user_message)

    fact = verified_fact(user_message)

    if fact:
        st.session_state.source = "KingsBot verified fact"
        st.session_state.confidence = "High"
        st.session_state.reason = (
            "A built-in factual safeguard matched the question."
        )
        return fact

    retrieved = None

    if needs_current_lookup(user_message):
        retrieved = current_lookup(user_message)

    prompt = (
        "You are KingsBot, a helpful AI assistant.\n\n"
        "CURRENT DATE:\n"
        "Today is August 26, 2026. The current year is 2026. "
        "Do not incorrectly call 2026 the future.\n\n"
        "GENERAL KNOWLEDGE:\n"
        "Answer broad questions about history, geography, countries, "
        "people, culture, technology, computers, mathematics, science, "
        "space, animals, languages, literature, entertainment, sports, "
        "education, business, coding, and everyday life. "
        "Do not invent facts. If uncertain, say so.\n\n"
        "MULTI-STEP REASONING:\n"
        "For difficult questions, break the task into useful steps, "
        "check calculations and code carefully, then provide the answer. "
        "Do not reveal private chain-of-thought.\n\n"
        "EDUCATION:\n"
        + education_context()
        + "\n\n"
        "EMOTIONAL INTELLIGENCE:\n"
        "Detected emotion: "
        + emotion
        + ". "
        + tone_instruction
        + "\n\n"
        "TONE ADAPTATION:\n"
        "Use the selected tone naturally. Do not announce the tone.\n\n"
        "CONTEXT AWARENESS:\n"
        "Use recent conversation when relevant. If the user changes "
        "topic, follow the new topic.\n\n"
        "PATTERN RECOGNITION:\n"
        "Current topic: "
        + topic
        + ". Use recurring topics only when relevant.\n\n"
        "PERSONAL MEMORY:\n"
        + memory_context()
        + "\n\n"
        "RECENT CONVERSATION:\n"
        + conversation_context()
        + "\n\n"
    )

    if retrieved:
        prompt += (
            "CURRENT RETRIEVED INFORMATION:\n"
            + retrieved
            + "\n\n"
            "Use this information as evidence. "
            "Do not pretend it is your own memory.\n\n"
        )

    prompt = add_proactive_instruction(
        prompt,
        user_message,
        topic,
    )

    messages = [
        {
            "role": "user",
            "content": user_message,
        }
    ]

    for message in st.session_state.messages[-10:]:
        role = message.get("role")
        content = str(message.get("content", ""))
        if role in {"user", "assistant"} and content:
            messages.insert(-1, {
                "role": role,
                "content": content,
            })

    # Do not call OpenAI after KingsBot's own limit is reached.
    if not can_make_request():
        st.session_state.source = "KingsBot request limit"
        st.session_state.confidence = "High"
        st.session_state.reason = (
            "KingsBot's local 30-request / 3-hour limit was reached."
        )
        return request_limit_message()

    try:
        result = client.responses.create(
            model=MODEL_NAME,
            instructions=prompt,
            input=messages,
            max_output_tokens=1200,
        )

        response = (result.output_text or "").strip()

    except Exception as error:
        st.session_state.source = "OpenAI API error"
        st.session_state.confidence = "Unknown"

        if is_openai_rate_or_quota_error(error):
            st.session_state.reason = (
                "OpenAI rejected the request because of a "
                "rate limit or quota restriction."
            )
        else:
            st.session_state.reason = (
                "The cloud AI request failed. Check the API key, "
                "billing, model access, or internet connection."
            )

        # IMPORTANT:
        # A failed OpenAI request is not counted against KingsBot's
        # 30-request / 3-hour limit.
        return openai_limit_error_message(error)

    # Count only a successful OpenAI AI response.
    record_request()

    if not response:
        response = "I couldn't generate an answer. Please try again."

    if retrieved:
        st.session_state.source = (
            "GPT-5.6 Luna + current information lookup"
        )
        st.session_state.confidence = "High"
        st.session_state.reason = (
            "The OpenAI model answered using the KingsBot context "
            "and retrieved current information when requested."
        )
    else:
        st.session_state.source = "GPT-5.6 Luna"
        st.session_state.confidence = "High"
        st.session_state.reason = (
            "Generated by the OpenAI cloud model using KingsBot's "
            "memory, conversation context, topic recognition, "
            "education level, and tone instructions."
        )

    st.session_state.last_user_question = user_message
    st.session_state.last_response = response

    return response


# ============================================================
# SPEECH TO TEXT
# ============================================================

def speech_to_text(audio_file):
    try:
        recognizer = sr.Recognizer()

        audio_file.seek(0)

        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)

        if not audio_data:
            return None

        text = recognizer.recognize_google(
            audio_data,
            language="en-US",
        )

        return text.strip() if text else None

    except sr.UnknownValueError:
        return None

    except sr.RequestError:
        return None

    except Exception:
        return None


# ============================================================
# TEXT TO SPEECH
# ============================================================

def text_to_speech(text):
    try:
        audio = io.BytesIO()

        speech = gTTS(
            text=str(text)[:3000],
            lang="en",
            slow=False,
        )

        speech.write_to_fp(audio)
        audio.seek(0)

        return audio.getvalue()

    except Exception:
        return None


# ============================================================
# SAVE CONVERSATION
# ============================================================

def create_chat_file():
    lines = [
        "KINGSBOT AI - SAVED CONVERSATION",
        "=" * 50,
        "Date: " + CURRENT_DATE,
        "",
    ]

    if st.session_state.user_name:
        lines.append(
            "Name: " + st.session_state.user_name
        )

    if st.session_state.student_level:
        lines.append(
            "Education level: "
            + st.session_state.student_level
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
            "PREFERENCES",
            "-" * 40,
        ]
    )

    lines.extend(st.session_state.preferences)

    lines.extend(
        [
            "",
            "CONVERSATION",
            "=" * 50,
        ]
    )

    for message in st.session_state.messages:
        if message["role"] == "user":
            lines.append("YOU:")
        else:
            lines.append("KINGSBOT:")

        lines.append(message["content"])
        lines.extend(["", "-" * 50])

    return "\n".join(lines)


# ============================================================
# USER INTERFACE
# ============================================================

st.title("🤖 KingsBot AI")

st.caption(
    "AI • General Knowledge • Memory • EQ • "
    "Multi-Step Reasoning • Voice • 2026"
)


# ============================================================
# CONVERSATION
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# VOICE ASSISTANT
# ============================================================

st.subheader("🎤 Voice Assistant")

st.caption(
    "Tap the microphone, speak, then stop the recording. "
    "KingsBot will convert your voice to text and answer."
)

audio_file = st.audio_input(
    "🎙️ Record your message",
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
            "I couldn't understand the recording. "
            "Check your microphone permission and try again."
        )


# ============================================================
# TEXT INPUT
# ============================================================

text_prompt = st.chat_input(
    "Ask KingsBot anything..."
)

prompt = voice_prompt or text_prompt


# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            try:
                response = generate_response(prompt)

            except Exception as error:
                response = (
                    "KingsBot encountered an error:\n\n"
                    + str(error)
                )

                st.session_state.source = "Error handler"
                st.session_state.confidence = "Unknown"
                st.session_state.reason = (
                    "An error occurred while processing the request."
                )

        st.markdown(response)

        st.caption(
            "🔎 Source: " + st.session_state.source
        )

        st.caption(
            "📊 Confidence: "
            + st.session_state.confidence
        )

        st.caption(
            "ℹ️ " + st.session_state.reason
        )

        with st.spinner("🔊 Preparing voice..."):
            audio = text_to_speech(response)

        if audio:
            try:
                st.audio(
                    audio,
                    format="audio/mp3",
                    autoplay=True,
                )
            except TypeError:
                # Compatibility fallback for older Streamlit versions.
                st.audio(
                    audio,
                    format="audio/mp3",
                )

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

    st.session_state.last_user_question = prompt
    st.session_state.last_response = response


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🤖 KingsBot")

    st.subheader("👤 Personal Memory")

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

    st.write(
        "Preferences: "
        + str(len(st.session_state.preferences))
    )

    st.write(
        "Requests remaining: "
        + str(requests_remaining())
        + " / "
        + str(MAX_REQUESTS)
    )

    st.divider()

    st.subheader("📚 Conversation History")

    if st.session_state.messages:
        number = 0

        for message in st.session_state.messages:
            if message["role"] == "user":
                number += 1
                preview = message["content"]

                if len(preview) > 55:
                    preview = preview[:55] + "..."

                st.write(
                    f"💬 {number}. {preview}"
                )
    else:
        st.write("No conversations yet.")

    if st.session_state.messages:
        st.download_button(
            "💾 Save conversation",
            create_chat_file(),
            "kingsbot_conversation.txt",
            "text/plain",
        )

    st.divider()

    st.subheader("❤️ Emotional Intelligence")
    st.write(
        "Emotion: " + st.session_state.emotion
    )

    st.subheader("🎭 Tone Adaptation")
    st.write(st.session_state.tone)

    st.subheader("🔍 Radical Transparency")

    st.write(
        "Source: " + st.session_state.source
    )

    st.write(
        "Confidence: "
        + st.session_state.confidence
    )

    st.caption(st.session_state.reason)

    st.subheader("🧩 Pattern Recognition")

    st.write(
        "Current topic: "
        + st.session_state.last_topic
    )

    st.divider()

    st.subheader("Features")

    features = [
        "🧠 GPT-5.6 Luna cloud brain",
        "🌍 General knowledge",
        "📅 2026 awareness",
        "🔎 Current information lookup",
        "👤 Personal memory",
        "🧹 Ethical forgetting",
        "🎓 Primary → University",
        "❤️ Emotional intelligence",
        "🎭 Advanced tone adaptation",
        "🧩 Topic pattern recognition",
        "🧠 Multi-step reasoning",
        "💬 Conversation memory",
        "❓ Proactive follow-up questions",
        "🎤 Voice input",
        "🔊 Automatic voice output",
        "🧮 Mathematics",
        "💻 Coding",
        "📚 Education",
        "🔬 Science",
        "🌍 History and geography",
        "⚽ Sports",
        "🎬 Entertainment",
        "💼 Business",
        "💾 Save conversations",
        "🧠 Stronger cloud reasoning",
        "💻 Advanced coding help",
        "🧮 Advanced math help",
        "❓ Proactive follow-up questions",
    ]

    for feature in features:
        st.write(feature)

    st.divider()

    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.last_user_question = ""
        st.session_state.last_response = ""
        st.rerun()

    if st.button("🧹 Forget personal memory"):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        save_memory()

        st.success("Personal memory cleared.")
        st.rerun()

    st.divider()

    st.caption("Model: GPT-5.6 Luna")
    st.caption("OpenAI API key is stored securely in Streamlit Secrets.")

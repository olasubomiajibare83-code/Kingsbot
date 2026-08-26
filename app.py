import base64
import io
import json
import os
import re

import requests
import streamlit as st
import streamlit.components.v1 as components
import speech_recognition as sr
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# ============================================================
# KINGSBOT AI
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
CURRENT_DATE = "August 25, 2026"
MEMORY_FILE = "kingsbot_memory.json"


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered"
)


# ============================================================
# MEMORY SYSTEM
# ============================================================

def default_memory():
    return {
        "name": None,
        "education_level": None,
        "facts": [],
        "preferences": [],
        "topics": []
    }


def load_memory():

    data = default_memory()

    try:

        if os.path.exists(MEMORY_FILE):

            with open(
                MEMORY_FILE,
                "r",
                encoding="utf-8"
            ) as file:

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

        "name":
            st.session_state.user_name,

        "education_level":
            st.session_state.student_level,

        "facts":
            st.session_state.personal_memory,

        "preferences":
            st.session_state.preferences,

        "topics":
            st.session_state.topic_pattern

    }

    try:

        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

    except Exception:

        pass


saved = load_memory()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_name" not in st.session_state:
    st.session_state.user_name = saved["name"]

if "student_level" not in st.session_state:
    st.session_state.student_level = saved["education_level"]

if "personal_memory" not in st.session_state:
    st.session_state.personal_memory = saved["facts"]

if "preferences" not in st.session_state:
    st.session_state.preferences = saved["preferences"]

if "topic_pattern" not in st.session_state:
    st.session_state.topic_pattern = saved["topics"]

if "emotion" not in st.session_state:
    st.session_state.emotion = "neutral"

if "tone" not in st.session_state:
    st.session_state.tone = "Natural and friendly"

if "confidence" not in st.session_state:
    st.session_state.confidence = "Medium"

if "source" not in st.session_state:
    st.session_state.source = "Qwen2.5-0.5B-Instruct"

if "reason" not in st.session_state:
    st.session_state.reason = (
        "Generated from the local language model."
    )

if "last_topic" not in st.session_state:
    st.session_state.last_topic = "general knowledge"

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "voice_speed" not in st.session_state:
    st.session_state.voice_speed = "Normal"

if "response_style" not in st.session_state:
    st.session_state.response_style = "Balanced"

if "last_voice_text" not in st.session_state:
    st.session_state.last_voice_text = ""

if "last_voice_audio" not in st.session_state:
    st.session_state.last_voice_audio = None


# ============================================================
# LOAD MODEL
# ============================================================

@st.cache_resource(
    show_spinner="🧠 Loading KingsBot's brain..."
)
def load_model():

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto"
    )

    model.eval()

    return tokenizer, model


try:

    tokenizer, model = load_model()

except Exception as error:

    st.error(
        "KingsBot could not load its AI model."
    )

    st.code(str(error))

    st.stop()


# ============================================================
# NAME MEMORY
# ============================================================

def detect_name(text):

    patterns = [

        r"\bmy name is ([A-Za-z][A-Za-z '\-]{1,40})",

        r"\bcall me ([A-Za-z][A-Za-z '\-]{1,40})",

        r"\byou can call me ([A-Za-z][A-Za-z '\-]{1,40})"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            name = match.group(1).strip()

            st.session_state.user_name = name

            save_memory()

            return name

    return None


# ============================================================
# EDUCATION LEVELS
# ============================================================

LEVELS = {

    "PRIMARY 1": [
        "primary 1",
        "primary one",
        "pry 1"
    ],

    "PRIMARY 2": [
        "primary 2",
        "primary two",
        "pry 2"
    ],

    "PRIMARY 3": [
        "primary 3",
        "primary three",
        "pry 3"
    ],

    "PRIMARY 4": [
        "primary 4",
        "primary four",
        "pry 4"
    ],

    "PRIMARY 5": [
        "primary 5",
        "primary five",
        "pry 5"
    ],

    "PRIMARY 6": [
        "primary 6",
        "primary six",
        "pry 6"
    ],

    "JSS1": [
        "jss1",
        "jss 1",
        "jss one",
        "junior secondary 1"
    ],

    "JSS2": [
        "jss2",
        "jss 2",
        "jss two",
        "junior secondary 2"
    ],

    "JSS3": [
        "jss3",
        "jss 3",
        "jss three",
        "junior secondary 3"
    ],

    "SS1": [
        "ss1",
        "ss 1",
        "ss one",
        "sss1",
        "sss 1",
        "senior secondary 1"
    ],

    "SS2": [
        "ss2",
        "ss 2",
        "ss two",
        "sss2",
        "sss 2",
        "senior secondary 2"
    ],

    "SS3": [
        "ss3",
        "ss 3",
        "ss three",
        "sss3",
        "sss 3",
        "senior secondary 3"
    ],

    "UNIVERSITY": [
        "university",
        "undergraduate",
        "college"
    ]
}


def detect_student_level(text):

    lower = text.lower()

    for level, words in LEVELS.items():

        if any(
            word in lower
            for word in words
        ):

            st.session_state.student_level = level

            save_memory()

            return level

    return None


# ============================================================
# PERSONAL MEMORY
# ============================================================

def remember_information(text):

    match = re.search(
        r"\b(?:remember that|remember this|please remember|save this)\b\s*[:,-]?\s*(.+)",
        text,
        re.IGNORECASE
    )

    if match:

        fact = match.group(1).strip()

        if fact:

            if fact not in st.session_state.personal_memory:

                st.session_state.personal_memory.append(
                    fact
                )

                st.session_state.personal_memory = (
                    st.session_state.personal_memory[-50:]
                )

                save_memory()

        return fact

    return None


# ============================================================
# FORGETTING
# ============================================================

def forget_information(text):

    lower = text.lower()

    if any(
        phrase in lower
        for phrase in [
            "forget everything",
            "forget all my memory",
            "delete all my memory"
        ]
    ):

        st.session_state.user_name = None

        st.session_state.student_level = None

        st.session_state.personal_memory = []

        st.session_state.preferences = []

        save_memory()

        return (
            "Done. I cleared your saved personal memory."
        )


    if (
        "forget my name" in lower
        or "delete my name" in lower
    ):

        st.session_state.user_name = None

        save_memory()

        return (
            "Done. I forgot your saved name."
        )


    if (
        "forget my class" in lower
        or "forget my education level" in lower
    ):

        st.session_state.student_level = None

        save_memory()

        return (
            "Done. I forgot your saved education level."
        )


    return None


# ============================================================
# EMOTIONAL INTELLIGENCE
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
            "this is wrong"
        ]
    ):

        return "frustrated"


    if any(
        word in lower
        for word in [
            "sad",
            "crying",
            "upset",
            "hurt",
            "depressed"
        ]
    ):

        return "sad"


    if any(
        word in lower
        for word in [
            "confused",
            "don't understand",
            "do not understand",
            "explain again",
            "i don't get it"
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
            "fear"
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
            "excited"
        ]
    ):

        return "happy"


    return "neutral"


# ============================================================
# UPGRADED TONE ADAPTATION
# ============================================================

def tone_for(emotion):

    tones = {

        "frustrated": (
            "Calm and direct",
            "Be calm, respectful, direct, "
            "and acknowledge the user's frustration. "
            "Do not argue unnecessarily."
        ),

        "sad": (
            "Warm and supportive",
            "Use warm, respectful and supportive "
            "language. Be helpful without pretending "
            "to have human emotions."
        ),

        "confused": (
            "Simple and step-by-step",
            "Use simple words, short explanations, "
            "examples and clear steps."
        ),

        "worried": (
            "Reassuring and practical",
            "Be reassuring but honest. Give practical "
            "next steps instead of making promises."
        ),

        "happy": (
            "Friendly and energetic",
            "Be positive, friendly and encouraging "
            "without becoming excessive."
        ),

        "neutral": (
            "Natural and friendly",
            "Be natural, friendly, clear and concise."
        )

    }

    return tones.get(
        emotion,
        tones["neutral"]
    )


# ============================================================
# TOPIC RECOGNITION
# ============================================================

def recognize_topic(text):

    lower = text.lower()

    categories = {

        "coding": [
            "code",
            "python",
            "program",
            "programming",
            "streamlit",
            "app",
            "software",
            "bug",
            "error"
        ],

        "mathematics": [
            "math",
            "calculate",
            "equation",
            "algebra",
            "geometry",
            "calculus",
            "percentage",
            "fraction"
        ],

        "science": [
            "science",
            "biology",
            "chemistry",
            "physics",
            "atom",
            "cell"
        ],

        "sports": [
            "football",
            "soccer",
            "world cup",
            "player",
            "messi",
            "ronaldo",
            "premier league"
        ],

        "education": [
            "school",
            "class",
            "jss",
            "sss",
            "primary",
            "university",
            "exam"
        ],

        "history": [
            "history",
            "historical",
            "war",
            "empire",
            "ancient",
            "kingdom"
        ],

        "geography": [
            "country",
            "capital",
            "continent",
            "geography",
            "river",
            "mountain",
            "ocean"
        ],

        "technology": [
            "technology",
            "computer",
            "phone",
            "internet",
            "ai",
            "artificial intelligence",
            "android"
        ],

        "entertainment": [
            "movie",
            "film",
            "actor",
            "actress",
            "music",
            "song",
            "singer",
            "game"
        ],

        "general knowledge": [
            "who is",
            "what is",
            "where is",
            "when did",
            "why is",
            "how does",
            "tell me about",
            "meaning of"
        ]

    }

    for category, words in categories.items():

        if any(
            word in lower
            for word in words
        ):

            return category

    return "general knowledge"


def update_topic(text):

    topic = recognize_topic(text)

    st.session_state.last_topic = topic

    if topic not in st.session_state.topic_pattern:

        st.session_state.topic_pattern.append(
            topic
        )

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

    if (
        "messi" in lower
        and "world cup" in lower
    ):

        return (
            "Lionel Messi has won the FIFA World Cup "
            "once, with Argentina at the 2022 FIFA "
            "World Cup."
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

        return "Today is August 25, 2026."


    if (
        (
            "spider-man" in lower
            or "spiderman" in lower
        )
        and "2026" in lower
    ):

        return (
            "The Spider-Man film scheduled for "
            "2026 is Spider-Man: Brand New Day."
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
            "news"
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
                "srlimit": 3
            },

            headers={
                "User-Agent": "KingsBotAI/1.0"
            },

            timeout=8
        )

        response.raise_for_status()

        results = []

        for item in (
            response.json()
            .get("query", {})
            .get("search", [])
        ):

            title = item.get("title")

            if not title:
                continue

            try:

                page = requests.get(

                    "https://en.wikipedia.org/api/rest_v1/page/summary/"
                    + requests.utils.quote(title),

                    headers={
                        "User-Agent": "KingsBotAI/1.0"
                    },

                    timeout=8
                )

                page.raise_for_status()

                summary = page.json().get(
                    "extract"
                )

                if summary:

                    results.append(
                        title
                        + ":\n"
                        + summary
                    )

            except Exception:

                continue

        if results:

            return "\n\n".join(
                results[:3]
            )

    except Exception:

        pass

    return None


# ============================================================
# MEMORY CONTEXT
# ============================================================

def memory_context():

    items = []

    if st.session_state.user_name:

        items.append(
            "User's name: "
            + st.session_state.user_name
        )

    if st.session_state.student_level:

        items.append(
            "User's education level: "
            + st.session_state.student_level
        )

    for fact in (
        st.session_state.personal_memory[-20:]
    ):

        items.append(
            "Saved user fact: "
            + fact
        )

    if items:

        return "\n".join(items)

    return "No personal information is saved."


# ============================================================
# EDUCATION CONTEXT
# ============================================================

def education_context():

    if st.session_state.student_level:

        return (
            "The user's education level is "
            + st.session_state.student_level
            + ". Match school explanations to "
            "that level. If the user asks for "
            "advanced material, teach at the "
            "requested level."
        )

    return (
        "The user's education level is unknown. "
        "Use a clear general explanation."
    )


# ============================================================
# RESPONSE STYLE
# ============================================================

def response_style_instruction():

    styles = {

        "Short": (
            "Keep answers short and direct. "
            "Use only the necessary information."
        ),

        "Balanced": (
            "Give a useful answer with enough "
            "explanation without becoming unnecessarily long."
        ),

        "Detailed": (
            "Give a detailed explanation with "
            "examples and steps when useful."
        )

    }

    return styles.get(
        st.session_state.response_style,
        styles["Balanced"]
    )


# ============================================================
# GENERATE RESPONSE
# ===================

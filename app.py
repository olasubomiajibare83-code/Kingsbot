import ast
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
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# ============================================================
# KINGSBOT AI - UPGRADED EDITION
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
CURRENT_DATE = "August 26, 2026"
MEMORY_FILE = "kingsbot_memory.json"


# ============================================================
# PAGE
# ============================================================

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
        "project": None,
        "question_mode": True,
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
        "project": st.session_state.project,
        "question_mode": st.session_state.question_mode,
    }

    try:
        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    except Exception:
        pass


# ============================================================
# SESSION STATE
# ============================================================

initial_state = {
    "messages": [],
    "user_name": saved["name"],
    "student_level": saved["education_level"],
    "personal_memory": (
        saved["facts"]
        if isinstance(saved["facts"], list)
        else []
    ),
    "preferences": (
        saved["preferences"]
        if isinstance(saved["preferences"], list)
        else []
    ),
    "topic_pattern": (
        saved["topics"]
        if isinstance(saved["topics"], list)
        else []
    ),
    "project": saved["project"],
    "question_mode": bool(
        saved["question_mode"]
    ),
    "emotion": "neutral",
    "tone": "Natural and friendly",
    "confidence": "Medium",
    "source": "Qwen2.5-0.5B-Instruct",
    "reason": (
        "Generated from the local language model."
    ),
    "last_topic": "general knowledge",
    "last_task": "conversation",
    "last_question": "",
    "last_voice_prompt": "",
}


for key, value in initial_state.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# LOAD BRAIN
# ============================================================

@st.cache_resource(
    show_spinner="🧠 Loading KingsBot's brain..."
)
def load_model():

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    if torch.cuda.is_available():

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto",
        )

    else:

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
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


def model_device():

    return next(
        model.parameters()
    ).device


# ============================================================
# NAME MEMORY
# ============================================================

def detect_name(text):

    patterns = [

        r"\bmy name is ([A-Za-z][A-Za-z '\-]{1,40})",

        r"\bcall me ([A-Za-z][A-Za-z '\-]{1,40})",

        r"\byou can call me ([A-Za-z][A-Za-z '\-]{1,40})",

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
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
        "pry 1",
    ],

    "PRIMARY 2": [
        "primary 2",
        "primary two",
        "pry 2",
    ],

    "PRIMARY 3": [
        "primary 3",
        "primary three",
        "pry 3",
    ],

    "PRIMARY 4": [
        "primary 4",
        "primary four",
        "pry 4",
    ],

    "PRIMARY 5": [
        "primary 5",
        "primary five",
        "pry 5",
    ],

    "PRIMARY 6": [
        "primary 6",
        "primary six",
        "pry 6",
    ],

    "JSS1": [
        "jss1",
        "jss 1",
        "jss one",
        "junior secondary 1",
    ],

    "JSS2": [
        "jss2",
        "jss 2",
        "jss two",
        "junior secondary 2",
    ],

    "JSS3": [
        "jss3",
        "jss 3",
        "jss three",
        "junior secondary 3",
    ],

    "SS1": [
        "ss1",
        "ss 1",
        "ss one",
        "sss1",
        "sss 1",
        "senior secondary 1",
    ],

    "SS2": [
        "ss2",
        "ss 2",
        "ss two",
        "sss2",
        "sss 2",
        "senior secondary 2",
    ],

    "SS3": [
        "ss3",
        "ss 3",
        "ss three",
        "sss3",
        "sss 3",
        "senior secondary 3",
    ],

    "UNIVERSITY": [
        "university",
        "undergraduate",
        "college",
    ],
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
        r"\b(?:remember that|remember this|please remember|save this)\b"
        r"\s*[:,-]?\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if not match:

        return None

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


# ============================================================
# PROJECT MEMORY
# ============================================================

def detect_project(text):

    match = re.search(
        r"\b(?:my project is|i am building|i'm building|"
        r"we are building|we're building)\b\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if not match:

        return None

    project = match.group(1).strip()

    if project:

        st.session_state.project = project[:500]

        save_memory()

        return project

    return None


# ============================================================
# FORGET MEMORY
# ============================================================

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
        st.session_state.project = None

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


    if "forget my project" in lower:

        st.session_state.project = None

        save_memory()

        return (
            "Done. I forgot your saved project."
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


# ============================================================
# TONE ADAPTATION
# ============================================================

def tone_for(emotion):

    tones = {

        "frustrated": (
            "Calm and direct",
            "Be calm, respectful, direct, acknowledge "
            "frustration, and focus on fixing the problem.",
        ),

        "sad": (
            "Warm and supportive",
            "Be kind, warm, practical, and supportive "
            "without pretending to have human feelings.",
        ),

        "confused": (
            "Simple and step-by-step",
            "Use simple language, short steps, examples, "
            "and check understanding.",
        ),

        "worried": (
            "Reassuring and practical",
            "Be reassuring, careful, factual, and practical.",
        ),

        "happy": (
            "Friendly and positive",
            "Be friendly, positive, energetic, and useful.",
        ),

        "neutral": (
            "Natural and friendly",
            "Be natural, friendly, clear, and concise.",
        ),
    }

    return tones.get(
        emotion,
        tones["neutral"],
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
            "javascript",
            "html",
            "css",
            "program",
            "programming",
            "streamlit",
            "app",
            "software",
            "bug",
            "error",
            "function",
            "class",
            "api",
            "github",
        ],

        "mathematics": [
            "math",
            "calculate",
            "equation",
            "algebra",
            "geometry",
            "calculus",
            "percentage",
            "fraction",
            "multiply",
            "divide",
        ],

        "science": [
            "science",
            "biology",
            "chemistry",
            "physics",
            "experiment",
            "atom",
            "cell",
            "energy",
            "planet",
        ],

        "sports": [
            "football",
            "soccer",
            "world cup",
            "player",
            "messi",
            "ronaldo",
            "premier league",
            "basketball",
            "tennis",
        ],

        "education": [
            "school",
            "class",
            "jss",
            "sss",
            "primary",
            "university",
            "exam",
            "homework",
            "lesson",
            "study",
        ],

        "history": [
            "history",
            "historical",
            "war",
            "empire",
            "ancient",
            "president",
            "king",
            "kingdom",
        ],

        "geography": [
            "country",
            "capital",
            "continent",
            "geography",
            "river",
            "mountain",
            "city",
            "africa",
            "nigeria",
        ],

        "technology": [
            "technology",
            "computer",
            "phone",
            "internet",
            "ai",
            "artificial intelligence",
            "android",
            "browser",
        ],

        "entertainment": [
            "movie",
            "film",
            "actor",
            "actress",
            "music",
            "song",
            "artist",
            "netflix",
            "game",
            "gaming",
        ],

        "health_and_wellness": [
            "health",
            "exercise",
            "sleep",
            "food",
            "diet",
        ],

        "general knowledge": [
            "who is",
            "what is",
            "where is",
            "when did",
            "why is",
            "how does",
            "tell me about",
            "meaning of",
        ],
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
# TASK DETECTION
# ============================================================

def detect_task(text):

    lower = text.lower()

    if any(
        phrase in lower
        for phrase in [
            "write code",
            "create code",
            "make code",
            "fix my code",
            "debug",
            "debugging",
            "python code",
            "streamlit code",
            "html code",
            "javascript code",
        ]
    ):

        return "coding"


    if (
        any(
            word in lower
            for word in [
                "calculate",
                "solve",
                "equation",
                "how much",
            ]
        )
        and re.search(
            r"\d",
            lower,
        )
    ):

        return "math"


    if any(
        phrase in lower
        for phrase in [
            "quiz me",
            "test me",
            "ask me questions",
        ]
    ):

        return "quiz"


    if any(
        phrase in lower
        for phrase in [
            "summarize",
            "summary",
            "shorten this",
        ]
    ):

        return "summarization"


    if any(
        phrase in lower
        for phrase in [
            "plan",
            "planning",
            "steps to",
            "how do i",
        ]
    ):

        return "planning"


    return "conversation"


# ============================================================
# PYTHON CODE CHECK
# ============================================================

def validate_python_code(text):

    blocks = re.findall(
        r"```python\s*(.*?)```",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not blocks:

        blocks = re.findall(
            r"```\s*(.*?)```",
            text,
            re.DOTALL,
        )

    if not blocks:

        return None


    problems = []

    for block in blocks[:3]:

        try:

            ast.parse(block)

        except SyntaxError as error:

            problems.append(
                "Python syntax error near line "
                + str(error.lineno)
                + ": "
                + error.msg
            )


    return problems if problems else []


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


    if any(
        phrase in lower
        for phrase in [
            "what year is it",
            "which year is it",
            "current year",
        ]
    ):

        return (
            "The current year is 2026."
        )


    if any(
        phrase in lower
        for phrase in [
            "today's date",
            "todays date",
            "what date is it",
        ]
    ):

        return (
            "Today is "
            + CURRENT_DATE
            + "."
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
            headers={
                "User-Agent": "KingsBotAI/2.0"
            },
            timeout=8,
        )

        response.raise_for_status()

        results = []


        for item in (
            response.json()
            .get("query", {})
         

import io
import json
import os
import re

import requests
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
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
        "name": st.session_state.user_name,
        "education_level": st.session_state.student_level,
        "facts": st.session_state.personal_memory,
        "preferences": st.session_state.preferences,
        "topics": st.session_state.topic_pattern
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
# ALL EDUCATION LEVELS
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

            if fact not in (
                st.session_state.personal_memory
            ):

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
# ETHICAL FORGETTING
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
            "mistake"
        ]
    ):

        return "frustrated"


    if any(
        word in lower
        for word in [
            "sad",
            "crying",
            "upset",
            "hurt"
        ]
    ):

        return "sad"


    if any(
        word in lower
        for word in [
            "confused",
            "don't understand",
            "do not understand",
            "explain again"
        ]
    ):

        return "confused"


    if any(
        word in lower
        for word in [
            "worried",
            "scared",
            "afraid",
            "nervous"
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
            "yesss"
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
            "Be calm, respectful, direct, "
            "and acknowledge frustration."
        ),

        "sad": (
            "Warm and supportive",
            "Be kind, warm, and supportive "
            "without pretending to have human feelings."
        ),

        "confused": (
            "Simple and step-by-step",
            "Use simple language and explain "
            "step by step."
        ),

        "worried": (
            "Reassuring and practical",
            "Be reassuring, careful, and practical."
        ),

        "happy": (
            "Friendly and positive",
            "Be friendly, positive, and energetic."
        ),

        "neutral": (
            "Natural and friendly",
            "Be natural, friendly, clear, and concise."
        )

    }

    return tones.get(
        emotion,
        tones["neutral"]
    )


# ============================================================
# PATTERN RECOGNITION
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
            "software"
        ],

        "mathematics": [
            "math",
            "calculate",
            "equation",
            "algebra",
            "geometry",
            "calculus"
        ],

        "science": [
            "science",
            "biology",
            "chemistry",
            "physics"
        ],

        "sports": [
            "football",
            "soccer",
            "world cup",
            "player",
            "messi"
        ],

        "education": [
            "school",
            "class",
            "jss",
            "sss",
            "primary",
            "university"
        ],

        "history": [
            "history",
            "historical",
            "war",
            "empire",
            "ancient"
        ],

        "geography": [
            "country",
            "capital",
            "continent",
            "geography",
            "river",
            "mountain"
        ],

        "technology": [
            "technology",
            "computer",
            "phone",
            "internet",
            "ai",
            "artificial intelligence"
        ],

        "entertainment": [
            "movie",
            "film",
            "actor",
            "actress",
            "music",
            "song"
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


    # Messi World Cup

    if (
        "messi" in lower
        and "world cup" in lower
    ):

        return (
            "Lionel Messi has won the FIFA World Cup "
            "once, with Argentina at the 2022 FIFA "
            "World Cup."
        )


    # Current year

    if (
        "what year is it" in lower
        or "which year is it" in lower
        or "current year" in lower
    ):

        return (
            "The current year is 2026."
        )


    # Current date

    if (
        "today's date" in lower
        or "todays date" in lower
        or "what date is it" in lower
    ):

        return (
            "Today is August 25, 2026."
        )


    # Spider-Man 2026

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


    return (
        "No personal information is saved."
    )


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
              "advanced or university material, "
              "you may teach it at the requested level."
        )


    return (
        "The user's education level is unknown. "
        "Use a clear general explanation."
    )


# ============================================================
# GENERATE RESPONSE
# ============================================================

def generate_response(user_message):

    detect_name(
        user_message
    )

    detect_student_level(
        user_message
    )

    remember_information(
        user_message
    )


    forgotten = forget_information(
        user_message
    )


    if forgotten:

        st.session_state.source = (
            "KingsBot memory system"
        )

        st.session_state.confidence = "High"

        st.session_state.reason = (
            "The user explicitly requested "
            "a memory change."
        )

        return forgotten


    emotion = detect_emotion(
        user_message
    )

    st.session_state.emotion = emotion


    tone_name, tone_instruction = tone_for(
        emotion
    )

    st.session_state.tone = tone_name


    topic = update_topic(
        user_message
    )


    fact = verified_fact(
        user_message
    )


    if fact:

        st.session_state.source = (
            "KingsBot verified fact"
        )

        st.session_state.confidence = "High"

        st.session_state.reason = (
            "A built-in factual safeguard "
            "matched the question."
        )

        return fact


    retrieved = None


    if needs_current_lookup(
        user_message
    ):

        retrieved = current_lookup(
            user_message
        )


    # ========================================================
    # KINGSBOT BRAIN INSTRUCTIONS
    # ========================================================

    prompt = (

        "You are KingsBot, a helpful AI assistant.\n\n"

        "CURRENT DATE:\n"
        "Today is August 25, 2026. "
        "The current year is 2026. "
        "Do not incorrectly call 2026 the future.\n\n"

        "GENERAL KNOWLEDGE:\n"
        "You are designed to answer broad "
        "general-knowledge questions about "
        "history, geography, countries, people, "
        "culture, technology, computers, "
        "mathematics, science, space, animals, "
        "languages, literature, entertainment, "
        "sports, education, and everyday life. "
        "Answer clearly and accurately. "
        "Never invent facts. If you do not know "
        "something, say that you are not certain.\n\n"

        "CURRENT INFORMATION:\n"
        "If current retrieved information is supplied "
        "below, use it as additional evidence. "
        "Do not claim that retrieved information "
        "is your own memory.\n\n"

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
        "Use the selected tone naturally. "
        "Do not repeatedly announce the tone.\n\n"

        "PROACTIVE GLUE:\n"
        "Connect the current request to useful "
        "recent context when relevant. "
        "If the user changes topic, follow the "
        "new topic instead of forcing the old one.\n\n"

        "PATTERN RECOGNITION:\n"
        "Current topic category: "
        + topic
        + ". Use recurring topics only when "
          "they are relevant.\n\n"

        "MULTI-STEP REASONING:\n"
        "For complex questions, reason through "
        "the problem carefully, verify calculations "
        "and code structure, and present a concise "
        "explanation or steps. Do not reveal "
        "private chain-of-thought.\n\n"

        "PERSONAL MEMORY:\n"
        + memory_context()
        + "\n\n"
    )


    if retrieved:

        prompt += (
            "RETRIEVED CURRENT INFORMATION:\n"
            + retrieved
            + "\n\n"
        )


    messages = [

        {
            "role": "system",
            "content": prompt
        }

    ]


    # Recent conversation memory

    messages.extend(
        st.session_state.messages[-12:]
    )


    # Current question

    messages.append(

        {
            "role": "user",
            "content": user_message
        }

    )


    # ========================================================
    # CHAT TEMPLATE
    # ========================================================

    text = tokenizer.apply_chat_template(

        messages,

        tokenize=False,

        add_generation_prompt=True
    )


    # ========================================================
    # TOKENIZE
    # ========================================================

    inputs = tokenizer(

        [text],

        return_tensors="pt",

        truncation=True,

        max_length=2048

    ).to(model.device)


    # ========================================================
    # GENERATE
    # ========================================================

    with torch.no_grad():

        generated = model.generate(

            **inputs,

            max_new_tokens=512,

            do_sample=True,

            temperature=0.6,

            top_p=0.9,

            repetition_penalty=1.05,

            pad_token_id=tokenizer.eos_token_id

        )


    # ========================================================
    # REMOVE PROMPT
    # ========================================================

    new_tokens = [

        output_ids[len(input_ids):]

        for input_ids, output_ids in zip(
            inputs.input_ids,
            generated
        )

    ]


    # ========================================================
    # DECODE
    # ========================================================

    response = tokenizer.batch_decode(

        new_tokens,

        skip_special_tokens=True

    )[0].strip()


    if not response:

        response = (
            "I couldn't generate an answer. "
            "Please try again."
        )


    # ========================================================
    # TRANSPARENCY
    # ========================================================

    if retrieved:

        st.session_state.source = (
            "Qwen + current information lookup"
        )

        st.session_state.confidence = (
            "Medium-High"
        )

        st.session_state.reason = (
            "Current information was retrieved "
            "before generating the answer."
        )

    else:

        st.session_state.source = (
            "Qwen2.5-0.5B-Instruct"
        )

        st.session_state.confidence = "Medium"

        st.session_state.reason = (
            "Generated from the local model, "
            "memory, conversation context, "
            "and KingsBot instructions."
        )


    return response


# ============================================================
# SPEECH TO TEXT
# ============================================================

def speech_to_text(audio_file):

    try:

        recognizer = sr.Recognizer()

        audio_file.seek(0)

        with sr.AudioFile(
            audio_file
        ) as source:

            audio_data = recognizer.record(
                source
            )


        return recognizer.recognize_google(
            audio_data,
            language="en-US"
        )


    except Exception:

        return None


# ============================================================
# TEXT TO SPEECH
# ============================================================

def text_to_speech(text):

    try:

        audio = io.BytesIO()

        speech = gTTS(
            text=text[:3000],
            lang="en",
            slow=False
        )

        speech.write_to_fp(
            audio
        )

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

        "Date: "
        + CURRENT_DATE,

        ""
    ]


    if st.session_state.user_name:

        lines.append(
            "Name: "
            + st.session_state.user_name
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
            "-" * 40
        ]
    )


    lines.extend(
        st.session_state.personal_memory
    )


    lines.extend(
        [
            "",
            "CONVERSATION",
            "=" * 50
        ]
    )


    for message in (
        st.session_state.messages
    ):

        if message["role"] == "user":

            lines.append(
                "YOU:"
            )

        else:

            lines.append(
                "KINGSBOT:"
            )


        lines.append(
            message["content"]
        )

        lines.extend(
            [
                "",
                "-" * 50
            ]
        )


    return "\n".join(lines)


# ============================================================
# TITLE
# ============================================================

st.title(
    "🤖 KingsBot AI"
)

st.caption(
    "AI • General Knowledge • Memory • EQ • "
    "Reasoning • Voice • 2026"
)


# ============================================================
# SHOW CONVERSATION
# ============================================================

for message in (
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# VOICE ASSISTANT
# ============================================================

st.subheader(
    "🎤 Voice Assistant"
)


audio_file = st.audio_input(

    "Tap the microphone and speak",

    sample_rate=16000,

    key="kingsbot_microphone"
)


voice_prompt = None


if audio_file:

    with st.spinner(
        "🎧 Understanding your voice..."
    ):

        voice_prompt = speech_to_text(
            audio_file
        )


    if voice_prompt:

        st.success(
            "You said: "
            + voice_prompt
        )

    else:

        st.error(
            "I couldn't understand that recording. "
            "Please try again."
        )


# ============================================================
# TEXT INPUT
# ============================================================

text_prompt = st.chat_input(
    "Ask KingsBot anything..."
)


prompt = (
    voice_prompt
    if voice_prompt
    else text_prompt
)


# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )


    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "🧠 Thinking..."
        ):

            try:

                response = generate_response(
                    prompt
                )

            except Exception as error:

                response = (
                    "KingsBot encountered an error:\n\n"
                    + str(error)
                )

                st.session_state.source = (
                    "Error handler"
                )

                st.session_state.confidence = (
                    "Unknown"
                )

                st.session_state.reason = (
                    "An error occurred while "
                    "processing the request."
                )


        st.markdown(
            response
        )


        # Radical transparency

        st.caption(
            "🔎 Source: "
            + st.session_state.source
        )

        st.caption(
            "📊 Confidence: "
            + st.session_state.confidence
        )

        st.caption(
            "ℹ️ "
            + st.session_state.reason
        )


        # Voice response

        with st.spinner(
            "🔊 Preparing voice..."
        ):

            audio = text_to_speech(
                response
            )


        if audio:

            st.audio(
                audio,
                format="audio/mp3"
            )


    # Save AFTER generating response

    st.session_state.messages.append(

        {
            "role": "user",
            "content": prompt
        }

    )


    st.session_state.messages.append(

        {
            "role": "assistant",
            "content": response
        }

    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🤖 KingsBot"
    )


    # ========================================================
    # MEMORY
    # ========================================================

    st.subheader(
        "👤 Personal Memory"
    )


    st.write(
        "Name: "
        + (
            st.session_state.user_name
            or "Not saved"
        )
    )


    st.write(
        "Class: "
        + (
            st.session_state.student_level
            or "Not saved"
        )
    )


    st.write(
        "Saved facts: "
        + str(
            len(
                st.session_state.personal_memory
            )
        )
    )


    st.divider()


    # ========================================================
    # CONVERSATION HISTORY
    # ========================================================

    st.subheader(
        "📚 Conversation History"
    )


    if st.session_state.messages:

        number = 0


        for message in (
            st.session_state.messages
        ):

            if message["role"] == "user":

                number += 1

                preview = message["content"]


                if len(preview) > 55:

                    preview = (
                        preview[:55]
                        + "..."
                    )


                st.write(
                    f"💬 {number}. {preview}"
                )

    else:

        st.write(
            "No conversations yet."
        )


    if st.session_state.messages:

        st.download_button(

            "💾 Save conversation",

            create_chat_file(),

            "kingsbot_conversation.txt",

            "text/plain"
        )


    st.divider()


    # ========================================================
    # EQ
    # ========================================================

    st.subheader(
        "❤️ Emotional Intelligence"
    )


    st.write(
        "Emotion: "
        + st.session_state.emotion
    )


    # ========================================================
    # TONE
    # ========================================================

    st.subheader(
        "🎭 Tone Adaptation"
    )


    st.write(
        st.session_state.tone
    )


    # ========================================================
    # RADICAL TRANSPARENCY
    # ========================================================

    st.subheader(
        "🔍 Radical Transparency"
    )


    st.write(
        "Source: "
        + st.session_state.source
    )


    st.write(
        "Confidence: "
        + st.session_state.confidence
    )


    st.caption(
        st.session_state.reason
    )


    # ========================================================
    # PATTERN RECOGNITION
    # ========================================================

    st.subheader(
        "🧩 Pattern Recognition"
    )


    st.write(
        "Topic: "
        + st.session_state.last_topic
    )


    st.divider()


    # ========================================================
    # FEATURES
    # ========================================================

    st.subheader(
        "Features"
    )


    features = [

        "🧠 Real language model",

        "🌍 General knowledge",

        "📅 2026 awareness",

        "🔎 Current information lookup",

        "👤 Personal memory",

        "🧹 Ethical forgetting",

        "🎓 Primary → University",

        "❤️ Emotional intelligence",

        "🎭 Tone adaptation",

        "🧩 Proactive glue",

        "🔎 Pattern recognition",

        "🧠 Multi-step reasoning",

        "🔍 Radical transparency",

        "💬 Conversation memory",

        "🎤 Voice input",

        "🔊 Voice output",

        "🧮 Mathematics",

        "💻 Coding",

        "📚 Education",

        "🔬 Science",

        "🌍 History and geography",

        "⚽ Sports",

        "🎬 Entertainment",

        "💾 Save conversations"

    ]


    for feature in features:

        st.write(
            feature
        )


    st.divider()


    # ========================================================
    # CLEAR CONVERSATION
    # ========================================================

    if st.button(
        "🗑️ Clear conversation"
    ):

        st.session_state.messages = []

        st.rerun()


    # ========================================================
    # FORGET PERSONAL MEMORY
    # ========================================================

    if st.button(
        "🧹 Forget personal memory"
    ):

        st.session_state.user_name = None

        st.session_state.student_level = None

        st.session_state.personal_memory = []

        st.session_state.preferences = []

        save_memory()

        st.success(
            "Personal memory cleared."
        )

        st.rerun()


    st.divider()


    st.caption(
        "Model: Qwen2.5-0.5B-Instruct"
    )


    st.caption(
        "No Hugging Face token required."
    )

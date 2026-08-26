
import base64
import io
import json
import os
import re
import uuid
from datetime import datetime

import streamlit as st
from groq import Groq
from gtts import gTTS

MODEL_NAME = "groq/compound"
MEMORY_FILE = "kingsbot_memory.json"
CHATS_FILE = "kingsbot_chats.json"

st.set_page_config(page_title="KingsBot AI", page_icon="🤖", layout="wide")


# ============================================================
# STORAGE
# ============================================================

def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def write_json(path, data):
    try:
        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        os.replace(temp_path, path)
    except Exception:
        pass


def create_chat():
    return {
        "id": uuid.uuid4().hex,
        "title": "New conversation",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "messages": [],
    }


def load_chats():
    chats = read_json(CHATS_FILE, [])
    if not isinstance(chats, list):
        chats = []
    if not chats:
        chats = [create_chat()]
        write_json(CHATS_FILE, chats)
    return chats


def load_memory():
    data = read_json(MEMORY_FILE, {})
    return {
        "name": data.get("name"),
        "education_level": data.get("education_level"),
        "facts": data.get("facts", []),
        "preferences": data.get("preferences", []),
    }


def save_memory():
    write_json(
        MEMORY_FILE,
        {
            "name": st.session_state.user_name,
            "education_level": st.session_state.student_level,
            "facts": st.session_state.personal_memory,
            "preferences": st.session_state.preferences,
        },
    )


def current_chat():
    for chat in st.session_state.saved_chats:
        if chat["id"] == st.session_state.current_chat_id:
            return chat
    return None


def save_current_chat():
    chat = current_chat()
    if chat is None:
        return

    chat["messages"] = list(st.session_state.messages)
    chat["updated_at"] = datetime.now().isoformat(timespec="seconds")

    first_user_message = next(
        (
            message["content"]
            for message in st.session_state.messages
            if message["role"] == "user"
        ),
        None,
    )

    if first_user_message:
        title = re.sub(r"\s+", " ", first_user_message.strip())
        chat["title"] = title[:45] + ("..." if len(title) > 45 else "")

    write_json(CHATS_FILE, st.session_state.saved_chats)


def start_new_chat():
    chat = create_chat()
    st.session_state.saved_chats.insert(0, chat)
    st.session_state.current_chat_id = chat["id"]
    st.session_state.messages = []
    write_json(CHATS_FILE, st.session_state.saved_chats)


def open_chat(chat_id):
    for chat in st.session_state.saved_chats:
        if chat["id"] == chat_id:
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = list(chat.get("messages", []))
            return


def delete_current_chat():
    current_id = st.session_state.current_chat_id
    st.session_state.saved_chats = [
        chat for chat in st.session_state.saved_chats
        if chat["id"] != current_id
    ]

    if not st.session_state.saved_chats:
        st.session_state.saved_chats = [create_chat()]

    st.session_state.current_chat_id = st.session_state.saved_chats[0]["id"]
    st.session_state.messages = list(
        st.session_state.saved_chats[0].get("messages", [])
    )
    write_json(CHATS_FILE, st.session_state.saved_chats)


memory = load_memory()
chats = load_chats()

if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = chats

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = chats[0]["id"]

if "messages" not in st.session_state:
    chat = current_chat()
    st.session_state.messages = list(chat.get("messages", []) if chat else [])

if "user_name" not in st.session_state:
    st.session_state.user_name = memory["name"]

if "student_level" not in st.session_state:
    st.session_state.student_level = memory["education_level"]

if "personal_memory" not in st.session_state:
    st.session_state.personal_memory = memory["facts"]

if "preferences" not in st.session_state:
    st.session_state.preferences = memory["preferences"]

if "last_topic" not in st.session_state:
    st.session_state.last_topic = "general"

if "emotion" not in st.session_state:
    st.session_state.emotion = "neutral"

if "source" not in st.session_state:
    st.session_state.source = "Ready"

if "last_voice_audio" not in st.session_state:
    st.session_state.last_voice_audio = None


# ============================================================
# API
# ============================================================

def get_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        key = None

    key = key or os.environ.get("GROQ_API_KEY")

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add your Groq key to Streamlit Secrets."
        )

    return str(key).strip()


def get_client():
    return Groq(
        api_key=get_api_key(),
        timeout=90.0,
        max_retries=2,
    )


# ============================================================
# MEMORY / UNDERSTANDING
# ============================================================

def detect_name(text):
    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\bcall me ([A-Za-z][A-Za-z '\-]{1,40})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            st.session_state.user_name = match.group(1).strip()
            save_memory()
            return st.session_state.user_name

    return None


def detect_student_level(text):
    levels = {
        "PRIMARY 1": ["primary 1", "primary one"],
        "PRIMARY 2": ["primary 2", "primary two"],
        "PRIMARY 3": ["primary 3", "primary three"],
        "PRIMARY 4": ["primary 4", "primary four"],
        "PRIMARY 5": ["primary 5", "primary five"],
        "PRIMARY 6": ["primary 6", "primary six"],
        "JSS1": ["jss1", "jss 1"],
        "JSS2": ["jss2", "jss 2"],
        "JSS3": ["jss3", "jss 3"],
        "SS1": ["ss1", "ss 1", "sss1"],
        "SS2": ["ss2", "ss 2", "sss2"],
        "SS3": ["ss3", "ss 3", "sss3"],
        "UNIVERSITY": ["university", "undergraduate"],
    }

    lower = text.lower()

    for level, words in levels.items():
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
        st.session_state.personal_memory = st.session_state.personal_memory[-50:]
        save_memory()

    return fact


def forget_information(text):
    lower = text.lower()

    if "forget everything" in lower or "delete all my memory" in lower:
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        save_memory()
        return "Done. I cleared your saved personal memory."

    if "forget my name" in lower:
        st.session_state.user_name = None
        save_memory()
        return "Done. I forgot your saved name."

    return None


def detect_emotion(text):
    lower = text.lower()

    if any(word in lower for word in ["angry", "mad", "annoyed", "frustrated"]):
        return "frustrated"

    if any(word in lower for word in ["sad", "crying", "upset", "hurt"]):
        return "sad"

    if any(word in lower for word in ["confused", "don't understand"]):
        return "confused"

    if any(word in lower for word in ["worried", "scared", "afraid", "nervous"]):
        return "worried"

    if any(word in lower for word in ["happy", "great", "awesome", "thanks"]):
        return "happy"

    return "neutral"


def detect_topic(text):
    lower = text.lower()

    groups = {
        "coding": ["code", "python", "program", "streamlit", "javascript", "html"],
        "math": ["math", "calculate", "equation", "algebra", "percentage"],
        "science": ["science", "biology", "chemistry", "physics", "space"],
        "sports": ["football", "soccer", "basketball", "tennis"],
        "education": ["school", "class", "jss", "sss", "primary", "university"],
        "history": ["history", "historical", "war", "empire", "ancient"],
        "geography": ["country", "capital", "continent", "geography"],
        "technology": ["technology", "computer", "phone", "internet", "ai"],
        "entertainment": ["movie", "film", "music", "song", "game", "gaming"],
        "writing": ["write", "rewrite", "essay", "letter", "story", "poem"],
    }

    for topic, words in groups.items():
        if any(word in lower for word in words):
            return topic

    return "general"


def memory_context():
    pieces = []

    if st.session_state.user_name:
        pieces.append("User name: " + st.session_state.user_name)

    if st.session_state.student_level:
        pieces.append("Education level: " + st.session_state.student_level)

    pieces.extend(
        "Saved fact: " + fact
        for fact in st.session_state.personal_memory[-20:]
    )

    return "\n".join(pieces) or "No saved personal information."


# ============================================================
# VOICE + CHAT
# ============================================================

st.subheader("🎤 Voice Assistant")
st.caption("Tap the microphone, speak, then stop the recording. KingsBot will transcribe and send it.")

audio_input = st.audio_input("🎤 Record your message", sample_rate=16000)
voice_prompt = None

if audio_input:
    with st.spinner("🎤 Transcribing..."):
        voice_prompt = transcribe_audio(audio_input)
    if voice_prompt:
        st.success("You said: " + voice_prompt)
    else:
        st.error("I couldn't understand the recording. Check microphone permission and try again.")

if st.session_state.get("last_voice_audio"):
    st.audio(st.session_state.last_voice_audio, format="audio/mp3")

text_prompt = st.chat_input("Ask KingsBot anything...")

prompt = voice_prompt or text_prompt

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("assistant"):
        with st.spinner("⚡ KingsBot is thinking..."):
            try:
                answer = generate_response(prompt, file_text=file_text)
            except Exception as error:
                answer = (
                    "I couldn't reach my AI brain.\n\n"
                    "Please check that your GROQ_API_KEY is saved correctly "
                    "in Streamlit Secrets.\n\n"
                    "Technical error: " + str(error)
                )

        st.markdown(answer)

        voice_output = text_to_speech(answer)
        if voice_output:
            st.session_state.last_voice_audio = voice_output
            st.audio(voice_output, format="audio/mp3")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    save_current_chat()
    st.rerun()

# ============================================================
# PRIVATE POWER AGENT
# ============================================================

def run_power_agent(user_message, conversation):
    messages = [{
        "role": "system",
        "content": (
            "You are KingsBot, a highly capable general AI assistant. "
            "Use Groq Compound's built-in tools automatically when useful: "
            "web search for current information, website visiting for "
            "specific pages, code execution for calculations/data/code "
            "verification, and Wolfram Alpha when appropriate. Verify "
            "changing facts. Never reveal private chain-of-thought."
        ),
    }]

    for item in conversation[-12:]:
        if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
            messages.append({
                "role": item["role"],
                "content": str(item.get("content", "")),
            })

    messages.append({"role": "user", "content": str(user_message)})

    response = get_client().chat.completions.create(
        model="groq/compound",
        messages=messages,
        max_completion_tokens=8192,
    )

    content = getattr(response.choices[0].message, "content", None)
    return (content or "").strip() or "I couldn't generate an answer. Please try again."


def generate_response(user_message):
    detect_name(user_message)
    detect_student_level(user_message)
    remember_information(user_message)

    forgotten = forget_information(user_message)
    if forgotten:
        return forgotten

    st.session_state.emotion = detect_emotion(user_message)
    st.session_state.last_topic = detect_topic(user_message)

    try:
        answer = run_power_agent(user_message, st.session_state.messages)
        st.session_state.source = "Groq Compound"
        return answer
    except Exception as error:
        return (
            "I couldn't reach the AI brain. Check that your GROQ_API_KEY "
            "is saved correctly in Streamlit Secrets and try again.\n\n"
            "Technical error: " + str(error)
        )



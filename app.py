
import base64
import io
import json
import os
import re
import uuid
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
import speech_recognition as sr
from gtts import gTTS
from groq import Groq

MODEL_NAME = "groq/compound-mini"
MEMORY_FILE = "kingsbot_memory.json"
CHATS_FILE = "kingsbot_chats.json"

st.set_page_config(page_title="KingsBot AI", page_icon="🤖")

def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass

def load_memory():
    data = read_json(MEMORY_FILE, {})
    return {
        "name": data.get("name"),
        "education_level": data.get("education_level"),
        "facts": data.get("facts", []),
        "preferences": data.get("preferences", []),
        "topics": data.get("topics", []),
    }

def save_memory():
    write_json(MEMORY_FILE, {
        "name": st.session_state.user_name,
        "education_level": st.session_state.student_level,
        "facts": st.session_state.personal_memory,
        "preferences": st.session_state.preferences,
        "topics": st.session_state.topic_pattern,
    })

def load_chats():
    chats = read_json(CHATS_FILE, [])
    return chats if isinstance(chats, list) else []

def save_chats():
    write_json(CHATS_FILE, st.session_state.saved_chats)

def create_chat():
    return {
        "id": uuid.uuid4().hex,
        "title": "New conversation",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "messages": [],
    }

def create_chat_title(text):
    text = re.sub(r"\s+", " ", str(text).strip())
    return text[:45] + ("..." if len(text) > 45 else "") or "New conversation"

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
    first = next(
        (m["content"] for m in st.session_state.messages if m["role"] == "user"),
        None,
    )
    if first:
        chat["title"] = create_chat_title(first)
    save_chats()

def new_chat():
    chat = create_chat()
    st.session_state.saved_chats.insert(0, chat)
    st.session_state.current_chat_id = chat["id"]
    st.session_state.messages = []
    save_chats()

def open_chat(chat_id):
    for chat in st.session_state.saved_chats:
        if chat["id"] == chat_id:
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = list(chat.get("messages", []))
            return

def delete_current_chat():
    chat_id = st.session_state.current_chat_id
    st.session_state.saved_chats = [
        c for c in st.session_state.saved_chats if c["id"] != chat_id
    ]
    if not st.session_state.saved_chats:
        st.session_state.saved_chats = [create_chat()]
    st.session_state.current_chat_id = st.session_state.saved_chats[0]["id"]
    st.session_state.messages = list(
        st.session_state.saved_chats[0].get("messages", [])
    )
    save_chats()

memory = load_memory()
chats = load_chats()
if not chats:
    chats = [create_chat()]
    write_json(CHATS_FILE, chats)

if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = chats
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = chats[0]["id"]
if "messages" not in st.session_state:
    chat = current_chat()
    st.session_state.messages = list(chat.get("messages", []) if chat else [])

defaults = {
    "user_name": memory["name"],
    "student_level": memory["education_level"],
    "personal_memory": memory["facts"],
    "preferences": memory["preferences"],
    "topic_pattern": memory["topics"],
    "emotion": "neutral",
    "tone": "Natural and friendly",
    "last_topic": "general knowledge",
    "source": "Groq Compound Mini",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def get_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        key = None
    key = key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing from Streamlit Secrets.")
    return str(key).strip()

def get_client():
    return Groq(api_key=get_api_key(), timeout=60.0, max_retries=2)

def detect_name(text):
    for pattern in [
        r"\bmy name is ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\bcall me ([A-Za-z][A-Za-z '\-]{1,40})",
    ]:
        match = re.search(pattern, text, re.I)
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
        if any(w in lower for w in words):
            st.session_state.student_level = level
            save_memory()
            return level
    return None

def remember_information(text):
    match = re.search(
        r"\b(?:remember that|remember this|please remember|save this)\b\s*[:,-]?\s*(.+)",
        text,
        re.I,
    )
    if match:
        fact = match.group(1).strip()
        if fact and fact not in st.session_state.personal_memory:
            st.session_state.personal_memory.append(fact)
            st.session_state.personal_memory = st.session_state.personal_memory[-50:]
            save_memory()
        return fact
    return None

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
    if any(x in lower for x in ["angry", "mad", "annoyed", "frustrated"]):
        return "frustrated"
    if any(x in lower for x in ["sad", "crying", "upset", "hurt"]):
        return "sad"
    if any(x in lower for x in ["confused", "don't understand", "do not understand"]):
        return "confused"
    if any(x in lower for x in ["worried", "scared", "afraid", "nervous"]):
        return "worried"
    if any(x in lower for x in ["happy", "great", "awesome", "thanks"]):
        return "happy"
    return "neutral"

def topic_of(text):
    lower = text.lower()
    groups = {
        "coding": ["code", "python", "program", "streamlit", "javascript", "html", "css"],
        "mathematics": ["math", "calculate", "equation", "algebra", "geometry", "percentage"],
        "science": ["science", "biology", "chemistry", "physics", "space"],
        "sports": ["football", "soccer", "basketball", "tennis", "world cup"],
        "education": ["school", "class", "jss", "sss", "primary", "university", "exam"],
        "history": ["history", "historical", "war", "empire", "ancient"],
        "geography": ["country", "capital", "continent", "geography"],
        "technology": ["technology", "computer", "phone", "internet", "ai"],
        "entertainment": ["movie", "film", "music", "song", "game", "gaming"],
        "writing": ["write", "rewrite", "essay", "letter", "story", "poem"],
    }
    for topic, words in groups.items():
        if any(w in lower for w in words):
            return topic
    return "general knowledge"

def memory_context():
    parts = []
    if st.session_state.user_name:
        parts.append("Name: " + st.session_state.user_name)
    if st.session_state.student_level:
        parts.append("Education: " + st.session_state.student_level)
    parts.extend("Saved fact: " + x for x in st.session_state.personal_memory[-20:])
    return "\n".join(parts) or "No saved personal information."

def generate_response(user_message):
    detect_name(user_message)
    detect_student_level(user_message)
    remember_information(user_message)

    forgotten = forget_information(user_message)
    if forgotten:
        return forgotten

    emotion = detect_emotion(user_message)
    topic = topic_of(user_message)
    st.session_state.emotion = emotion
    st.session_state.last_topic = topic
    if topic not in st.session_state.topic_pattern:
        st.session_state.topic_pattern.append(topic)
        st.session_state.topic_pattern = st.session_state.topic_pattern[-30:]
        save_memory()

    system = f"""
You are KingsBot, a fast general-purpose AI assistant.
Answer questions about general knowledge, current events, 2026 information,
coding, debugging, mathematics, science, education, history, geography,
sports, entertainment, writing, planning, and problem solving.

Use Groq Compound Mini's built-in tools when current information is needed.
Do not guess current facts. For current news, today's events, latest releases,
prices, sports results, people, products, or other changing information,
use the available web tools.

For coding, give complete syntactically valid code and check imports,
indentation, function definitions, dependencies, and likely errors.
For math, calculate carefully and show useful steps.
Do not reveal private chain-of-thought.

User memory:
{memory_context()}

Detected emotion: {emotion}
Current topic: {topic}

Be natural, friendly, direct, and helpful. Ask a short follow-up question
only when it genuinely helps.
"""
    messages = [{"role": "system", "content": system}]
    messages.extend(st.session_state.messages[-12:])
    messages.append({"role": "user", "content": user_message})

    result = get_client().chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=False,
        max_completion_tokens=4096,
    )
    response = (result.choices[0].message.content or "").strip()
    if not response:
        response = "I couldn't generate an answer. Please try again."
    st.session_state.source = "Groq Compound Mini"
    return response

def speech_to_text(audio_file):
    try:
        recognizer = sr.Recognizer()
        audio_file.seek(0)
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="en-US")
    except Exception:
        return None

def text_to_speech(text):
    try:
        audio = io.BytesIO()
        gTTS(text=str(text)[:3000], lang="en", slow=False).write_to_fp(audio)
        return audio.getvalue()
    except Exception:
        return None

def play_voice(audio_bytes):
    if not audio_bytes:
        return
    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    components.html(
        f'<audio controls autoplay style="width:100%;"><source src="data:audio/mpeg;base64,{encoded}" type="audio/mpeg"></audio>',
        height=70,
    )

def chat_text():
    lines = []
    for item in st.session_state.messages:
        label = "YOU" if item["role"] == "user" else "KINGSBOT"
        lines += [label + ":", item["content"], "", "-" * 40]
    return "\n".join(lines)

st.title("🤖 KingsBot AI")
st.caption("⚡ Fast AI • 🌍 Current information • 💬 Permanent chat history • 🎤 Voice")

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

st.subheader("🎤 Voice Assistant")
audio_file = st.audio_input("Tap the microphone and speak", sample_rate=16000)
voice_prompt = speech_to_text(audio_file) if audio_file else None
if voice_prompt:
    st.success("You said: " + voice_prompt)

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
                    "Check GROQ_API_KEY in Streamlit Secrets.\n\n"
                    "Technical error: " + str(error)
                )
                st.session_state.source = "Groq connection error"
        st.markdown(response)
        audio = text_to_speech(response)
        if audio:
            play_voice(audio)

    st.session_state.messages.extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response},
    ])
    save_current_chat()
    st.rerun()

with st.sidebar:
    st.header("💬 Chat History")
    if st.button("➕ New conversation", use_container_width=True):
        new_chat()
        st.rerun()

    for chat in st.session_state.saved_chats:
        title = chat.get("title", "Conversation")
        if len(title) > 30:
            title = title[:30] + "..."
        prefix = "🟢 " if chat["id"] == st.session_state.current_chat_id else "💬 "
        if st.button(prefix + title, key="chat_" + chat["id"], use_container_width=True):
            open_chat(chat["id"])
            st.rerun()

    if st.button("🗑️ Delete current chat", use_container_width=True):
        delete_current_chat()
        st.rerun()

    if st.session_state.messages:
        st.download_button(
            "💾 Download current chat",
            chat_text(),
            "kingsbot_conversation.txt",
            "text/plain",
            use_container_width=True,
        )

    st.divider()
    st.subheader("👤 Memory")
    st.write("Name:", st.session_state.user_name or "Not saved")
    st.write("Class:", st.session_state.student_level or "Not saved")
    st.write("Saved facts:", len(st.session_state.personal_memory))

    st.divider()
    st.subheader("🧠 Brain")
    st.write(MODEL_NAME)
    st.write("Topic:", st.session_state.last_topic)
    st.write("Emotion:", st.session_state.emotion)
    st.write("Source:", st.session_state.source)

    st.divider()
    if st.button("🧹 Forget personal memory", use_container_width=True):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        save_memory()
        st.rerun()

    st.caption("Chat history is stored in " + CHATS_FILE)


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

MODEL_NAME = "groq/compound-mini"
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
# KNOWLEDGE WORKSPACE
# ============================================================

# ============================================================
# FILE READING
# ============================================================

def extract_text_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith((".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".csv")):
        return data.decode("utf-8", errors="replace")[:120000]

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            pages = []

            for page in reader.pages:
                pages.append(page.extract_text() or "")

            return "\n\n".join(pages)[:120000]
        except Exception as error:
            return f"PDF could not be read: {error}"

    return ""


# ============================================================
# MAIN AI BRAIN
# ============================================================

def generate_response(user_message, file_text=""):
    detect_name(user_message)
    detect_student_level(user_message)
    remember_information(user_message)

    forgotten = forget_information(user_message)
    if forgotten:
        return forgotten

    st.session_state.emotion = detect_emotion(user_message)
    st.session_state.last_topic = detect_topic(user_message)

    system_prompt = f"""
You are KingsBot, a fast general-purpose AI assistant.

Your main model is Groq Compound Mini. Use its available built-in tools when
appropriate. For questions requiring current information, news, recent events,
prices, sports results, current people, current products, or other changing
facts, use live web capabilities instead of guessing.

You can help with:
- general questions
- reasoning and problem solving
- mathematics
- coding and debugging
- science
- history
- geography
- education
- technology
- sports
- entertainment
- writing and rewriting
- translation
- planning
- research

For coding, provide complete valid code and check imports, indentation,
function definitions, and dependencies.

For mathematics, calculate carefully and show useful steps.

Do not claim to have capabilities that were not actually used.
Do not reveal private chain-of-thought. Give concise useful reasoning or
explanations instead.

User memory:
{memory_context()}

Detected emotion: {st.session_state.emotion}
Detected topic: {st.session_state.last_topic}

Additional uploaded file text:
{file_text[:60000]}
"""

    messages = [{"role": "system", "content": system_prompt}]

    # Keep enough recent context for continuity without sending an unlimited
    # conversation on every request.
    messages.extend(st.session_state.messages[-16:])
    messages.append({"role": "user", "content": user_message})

    result = get_client().chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_completion_tokens=8192,
        stream=False,
    )

    answer = (result.choices[0].message.content or "").strip()

    if not answer:
        answer = "I couldn't generate an answer. Please try again."

    st.session_state.source = "Groq Compound Mini"
    return answer


# ============================================================
# VOICE
# ============================================================

def transcribe_audio(audio_file):
    if audio_file is None:
        return None

    try:
        raw = audio_file.getvalue() if hasattr(audio_file, "getvalue") else audio_file
        temp = io.BytesIO(raw)
        temp.name = "kingsbot_voice.webm"

        result = get_client().audio.transcriptions.create(
            file=temp,
            model="whisper-large-v3-turbo",
            response_format="json",
        )

        text = getattr(result, "text", None)
        return text.strip() if text else None
    except Exception:
        return None


def text_to_speech(text):
    try:
        audio = io.BytesIO()
        gTTS(text=str(text)[:3000], lang="en", slow=False).write_to_fp(audio)
        return audio.getvalue()
    except Exception:
        return None


def play_audio(audio_bytes):
    if not audio_bytes:
        return

    encoded = base64.b64encode(audio_bytes).decode("utf-8")

    st.audio(
        base64.b64decode(encoded),
        format="audio/mp3",
    )


# ============================================================
# DOWNLOAD
# ============================================================

def conversation_text():
    lines = []

    for message in st.session_state.messages:
        label = "YOU" if message["role"] == "user" else "KINGSBOT"
        lines.append(label + ":")
        lines.append(message["content"])
        lines.append("")
        lines.append("-" * 50)

    return "\n".join(lines)


# ============================================================
# INTERFACE
# ============================================================

st.title("🤖 KingsBot AI")
st.caption(
    "⚡ Fast AI • 🌐 Live information • 📚 Workspace • 🎤 Voice • 💬 Memory"
)

with st.sidebar:
    st.header("💬 Conversations")

    if st.button("➕ New conversation", use_container_width=True):
        start_new_chat()
        st.rerun()

    for chat in st.session_state.saved_chats:
        title = chat.get("title", "Conversation")
        if len(title) > 30:
            title = title[:30] + "..."

        prefix = (
            "🟢 " if chat["id"] == st.session_state.current_chat_id else "💬 "
        )

        if st.button(
            prefix + title,
            key="chat_" + chat["id"],
            use_container_width=True,
        ):
            open_chat(chat["id"])
            st.rerun()

    if st.button("🗑️ Delete current chat", use_container_width=True):
        delete_current_chat()
        st.rerun()

    if st.session_state.messages:
        st.download_button(
            "💾 Download current chat",
            conversation_text(),
            "kingsbot_conversation.txt",
            "text/plain",
            use_container_width=True,
        )

    st.divider()
    st.header("🧠 Memory")
    st.write("Name:", st.session_state.user_name or "Not saved")
    st.write("Class:", st.session_state.student_level or "Not saved")
    st.write("Saved facts:", len(st.session_state.personal_memory))

    if st.button("🧹 Forget personal memory", use_container_width=True):
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.preferences = []
        save_memory()
        st.rerun()

    st.divider()
    st.header("⚙️ AI")
    st.write("Brain:", MODEL_NAME)
    st.write("Workspace:", "PDF + code + CSV + text")
    st.write("Topic:", st.session_state.last_topic)
    st.write("Emotion:", st.session_state.emotion)
    st.write("Source:", st.session_state.source)


# Display conversation.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# KNOWLEDGE WORKSPACE
# ============================================================

st.subheader("📚 Knowledge Workspace")
st.caption("Upload PDFs, notes, code, JSON, CSV or text and ask KingsBot to summarize, explain, debug, compare or create study material.")

uploaded_file = st.file_uploader(
    "Upload a document or code file",
    type=["txt", "md", "py", "js", "html", "css", "json", "csv", "pdf"],
    key="document_upload",
)

file_text = ""
if uploaded_file:
    file_text = extract_text_from_file(uploaded_file)
    if file_text:
        st.success(f"Loaded {uploaded_file.name}")
        task = st.text_input(
            "What should KingsBot do with this file?",
            placeholder="Summarize it, explain it, find mistakes, make study questions...",
            key="workspace_task",
        )
        if st.button("🧠 Analyze file", use_container_width=True):
            try:
                with st.spinner("Analyzing your file..."):
                    result = get_client().chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are KingsBot's Knowledge Workspace. "
                                    "Use the supplied document as the source of truth. "
                                    "Summarize, explain, compare, debug code, extract facts, "
                                    "make study guides and answer questions accurately. "
                                    "Never invent information not present in the file."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    (task or "Give me a useful summary of this file.")
                                    + "\n\nDOCUMENT:\n"
                                    + file_text[:120000]
                                ),
                            },
                        ],
                        max_completion_tokens=8192,
                    )
                    answer = (result.choices[0].message.content or "").strip()
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "user", "content": task or "Analyze this file."})
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    save_current_chat()
            except Exception as error:
                st.error("File analysis error: " + str(error))
    else:
        st.warning("I could not extract readable text from this file.")

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

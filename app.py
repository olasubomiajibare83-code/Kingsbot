import io
import json
import os
import re
from datetime import datetime

import streamlit as st
from groq import Groq
from gtts import gTTS

# ============================================================
# KINGSBOT AI - CLEAN FINAL BUILD
# ============================================================

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered",
)

MODEL_NAME = "groq/compound"

# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "messages": [],
        "memory": {},
        "user_name": "",
        "emotion": "neutral",
        "topic": "general",
        "last_voice_audio": None,
        "chat_started": datetime.now().isoformat(timespec="seconds"),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

# ============================================================
# API
# ============================================================

def get_api_key():
    try:
        value = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        value = ""
    if not value:
        value = os.getenv("GROQ_API_KEY", "")
    return str(value).strip()


def get_client():
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add GROQ_API_KEY to Streamlit Secrets."
        )
    return Groq(
        api_key=key,
        default_headers={"Groq-Model-Version": "latest"},
    )

# ============================================================
# SMALL LOCAL BRAIN HELPERS
# ============================================================

def detect_name(text):
    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z .'-]{1,40})",
        r"\bcall me ([A-Za-z][A-Za-z .'-]{1,40})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip(" .,!?")
            if name:
                st.session_state.user_name = name
                st.session_state.memory["name"] = name
                return name
    return st.session_state.user_name


def remember_information(text):
    lowered = text.lower()
    if "remember that" in lowered:
        part = text[lowered.find("remember that") + len("remember that"):].strip()
        if part:
            st.session_state.memory["note"] = part[:500]


def forget_information(text):
    lowered = text.lower().strip()
    if lowered in {"forget my name", "forget my name please"}:
        st.session_state.user_name = ""
        st.session_state.memory.pop("name", None)
        return "Done. I forgot your name."
    if lowered.startswith("forget that"):
        st.session_state.memory.pop("note", None)
        return "Done. I forgot that saved note."
    return None


def detect_emotion(text):
    lowered = text.lower()
    if any(word in lowered for word in ("sad", "angry", "upset", "cry", "worried")):
        return "supportive"
    if any(word in lowered for word in ("happy", "excited", "great", "amazing")):
        return "positive"
    return "neutral"


def detect_topic(text):
    lowered = text.lower()
    if any(x in lowered for x in ("python", "code", "program", "bug", "error")):
        return "coding"
    if any(x in lowered for x in ("math", "calculate", "equation", "percent")):
        return "math"
    if any(x in lowered for x in ("news", "today", "latest", "2026", "current")):
        return "current information"
    if any(x in lowered for x in ("school", "study", "exam", "homework")):
        return "learning"
    return "general"

# ============================================================
# PRIVATE POWER BRAIN
# ============================================================

def power_agent(user_text):
    """Private backend capability. Nothing new is displayed on screen."""
    client = get_client()

    system_prompt = """
You are KingsBot, a highly capable general-purpose AI assistant.

Your private job is to produce the strongest useful answer you can. You may
use Groq Compound's server-side tools automatically when useful:
- web_search for current or changing information
- visit_website for a specific webpage
- code_interpreter for calculations, data work, and code verification
- wolfram_alpha for advanced mathematical/computational questions

Do not expose private chain-of-thought. Instead, give the user the answer,
important steps, assumptions, and useful conclusions. If a fact is current or
likely to have changed, verify it with web search. If a calculation is
important, use a computational tool when useful. If the user asks for code,
write complete code and check it carefully before presenting it.

Be fast for simple questions and use deeper tool-assisted work for complex
questions. Never pretend that a tool was used if it was not.
""".strip()

    messages = [{"role": "system", "content": system_prompt}]

    if st.session_state.user_name:
        messages.append({
            "role": "system",
            "content": f"The user's saved name is {st.session_state.user_name}.",
        })

    if st.session_state.memory.get("note"):
        messages.append({
            "role": "system",
            "content": "Saved user note: " + st.session_state.memory["note"],
        })

    # Keep context small enough to stay fast and reliable.
    for message in st.session_state.messages[-12:]:
        role = message.get("role")
        content = str(message.get("content", "")).strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        compound_custom={
            "tools": {
                "enabled_tools": [
                    "web_search",
                    "code_interpreter",
                    "visit_website",
                    "wolfram_alpha",
                ]
            }
        },
        max_completion_tokens=8192,
    )

    answer = getattr(response.choices[0].message, "content", "")
    return str(answer).strip() or "I couldn't generate an answer. Please try again."

# ============================================================
# VOICE
# ============================================================

def transcribe_audio(audio_file):
    if audio_file is None:
        return ""
    try:
        raw = audio_file.getvalue()
        audio = io.BytesIO(raw)
        audio.name = "kingsbot_voice.wav"
        result = get_client().audio.transcriptions.create(
            file=audio,
            model="whisper-large-v3-turbo",
            response_format="json",
        )
        return str(getattr(result, "text", "") or "").strip()
    except Exception as exc:
        st.error("Voice transcription failed: " + str(exc))
        return ""


def make_voice(text):
    try:
        output = io.BytesIO()
        gTTS(text=str(text)[:4500], lang="en", slow=False).write_to_fp(output)
        return output.getvalue()
    except Exception:
        return None

# ============================================================
# UI
# ============================================================

with st.sidebar:
    st.title("🤖 KingsBot")
    st.caption("Private Power Agent • Voice • Memory")

    if st.button("➕ New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.topic = "general"
        st.session_state.emotion = "neutral"
        st.session_state.last_voice_audio = None
        st.session_state.chat_started = datetime.now().isoformat(timespec="seconds")
        st.rerun()

    if st.button("🧹 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_voice_audio = None
        st.rerun()

    st.divider()
    st.write("Brain: Groq Compound")
    st.write("Private tools: Web + Code + Website + Math")
    st.write("Topic:", st.session_state.topic)
    if st.session_state.user_name:
        st.write("Name:", st.session_state.user_name)

st.title("🤖 KingsBot AI")
st.caption("Fast, tool-assisted AI with voice input and voice output.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice input uses Streamlit's built-in recorder, so there is no fragile
# third-party microphone component on the page.
audio_input = st.audio_input("🎤 Record a message", sample_rate=16000)
voice_text = transcribe_audio(audio_input) if audio_input else ""

if voice_text:
    st.info("You said: " + voice_text)

text_input = st.chat_input("Ask KingsBot anything...")
prompt = voice_text or text_input

if prompt:
    detect_name(prompt)
    remember_information(prompt)
    st.session_state.topic = detect_topic(prompt)
    st.session_state.emotion = detect_emotion(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("⚡ Thinking..."):
            try:
                answer = power_agent(prompt)
            except Exception as exc:
                answer = (
                    "I couldn't reach the AI brain. Please check your "
                    "GROQ_API_KEY in Streamlit Secrets.\n\n"
                    "Technical error: " + str(exc)
                )

        st.markdown(answer)

        audio = make_voice(answer)
        if audio:
            st.session_state.last_voice_audio = audio
            st.audio(audio, format="audio/mp3")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# Keep the last voice response available after Streamlit reruns.
if st.session_state.last_voice_audio:
    st.divider()
    st.caption("🔊 Last voice response")
    st.audio(st.session_state.last_voice_audio, format="audio/mp3")

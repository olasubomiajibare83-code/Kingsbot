import io
import os
import re
import hashlib
from datetime import datetime

import streamlit as st
from groq import Groq

# Optional PDF support
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except Exception:
    PDF_SUPPORT = False


# ============================================================
# KINGSBOT AI - REAL AI POWER BUILD
# ============================================================

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

MODEL_NAME = "groq/compound"

# These limits protect the API from oversized requests / 413 errors.
MAX_HISTORY_MESSAGES = 10
MAX_MESSAGE_CHARS = 7000
MAX_MEMORY_CHARS = 5000
MAX_FILE_CHARS_EACH = 12000
MAX_TOTAL_FILE_CHARS = 25000

TTS_MAX_CHARS = 190


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "messages": [],
        "memory_notes": [],
        "user_name": "",
        "topic": "general",
        "emotion": "neutral",
        "uploaded_files": {},
        "file_context": "",
        "last_voice_audio": None,
        "last_voice_hash": "",
        "last_user_prompt": "",
        "last_answer": "",
        "chat_started": datetime.now().isoformat(
            timespec="seconds"
        ),

        # Power switches
        "turbo": True,
        "web_search": True,
        "deep_reasoning": True,
        "advanced_coding": True,
        "factual_grounding": True,
        "steel_memory": True,
        "voice_output": True,
        "show_tools": True,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ============================================================
# API
# ============================================================

def get_secret(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    if not value:
        value = os.getenv(name, "")

    return str(value).strip()


def get_client():
    key = get_secret("GROQ_API_KEY")

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to Streamlit Secrets."
        )

    return Groq(
        api_key=key,
        default_headers={
            "Groq-Model-Version": "latest"
        },
    )


# ============================================================
# MEMORY
# ============================================================

def add_memory(text):
    text = str(text).strip()

    if not text:
        return

    if text in st.session_state.memory_notes:
        return

    st.session_state.memory_notes.append(text)

    # Keep memory controlled.
    if len(st.session_state.memory_notes) > 30:
        st.session_state.memory_notes = (
            st.session_state.memory_notes[-30:]
        )


def detect_name(text):
    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z .'-]{1,40})",
        r"\bcall me ([A-Za-z][A-Za-z .'-]{1,40})",
        r"\byou can call me ([A-Za-z][A-Za-z .'-]{1,40})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            name = match.group(1).strip(
                " .,!?;"
            )

            if name:
                st.session_state.user_name = name
                add_memory(
                    "The user's name is " + name
                )
                return name

    return st.session_state.user_name


def remember_information(text):
    if not st.session_state.steel_memory:
        return

    lowered = text.lower()

    triggers = [
        "remember that",
        "remember this",
        "don't forget that",
        "dont forget that",
    ]

    for trigger in triggers:
        if trigger in lowered:
            position = lowered.find(trigger)

            note = text[
                position + len(trigger):
            ].strip()

            if note:
                add_memory(
                    note[:500]
                )
                return

    preferences = [
        r"\bi like (.+)",
        r"\bi love (.+)",
        r"\bi prefer (.+)",
        r"\bmy favorite (.+)",
    ]

    for pattern in preferences:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            value = match.group(0).strip()

            if len(value) <= 250:
                add_memory(value)

            return


def forget_information(text):
    lowered = text.lower().strip()

    if lowered in {
        "forget my name",
        "forget my name please",
    }:
        st.session_state.user_name = ""

        st.session_state.memory_notes = [
            item
            for item in st.session_state.memory_notes
            if "name" not in item.lower()
        ]

        return "Done. I forgot your name."

    if lowered.startswith("forget that"):
        if st.session_state.memory_notes:
            st.session_state.memory_notes.pop()

        return "Done. I forgot the latest saved memory."

    if lowered in {
        "forget everything",
        "forget all my memory",
        "clear my memory",
    }:
        st.session_state.memory_notes = []
        st.session_state.user_name = ""

        return "Done. I cleared the saved memory."

    return None


# ============================================================
# TOPIC / EMOTION
# ============================================================

def detect_topic(text):
    t = text.lower()

    if any(
        x in t
        for x in [
            "python",
            "javascript",
            "html",
            "css",
            "code",
            "coding",
            "program",
            "bug",
            "error",
            "api",
            "streamlit",
        ]
    ):
        return "coding"

    if any(
        x in t
        for x in [
            "math",
            "calculate",
            "equation",
            "percentage",
            "percent",
            "algebra",
            "geometry",
            "calculus",
        ]
    ):
        return "math"

    if any(
        x in t
        for x in [
            "today",
            "latest",
            "current",
            "news",
            "recent",
            "yesterday",
            "tomorrow",
        ]
    ):
        return "current information"

    if any(
        x in t
        for x in [
            "school",
            "exam",
            "homework",
            "study",
            "learn",
        ]
    ):
        return "learning"

    if any(
        x in t
        for x in [
            "business",
            "money",
            "company",
            "startup",
        ]
    ):
        return "business"

    return "general"


def detect_emotion(text):
    t = text.lower()

    if any(
        x in t
        for x in [
            "sad",
            "angry",
            "upset",
            "worried",
            "scared",
            "frustrated",
        ]
    ):
        return "supportive"

    if any(
        x in t
        for x in [
            "happy",
            "excited",
            "amazing",
            "awesome",
            "great",
        ]
    ):
        return "positive"

    return "neutral"


# ============================================================
# FILE READER
# ============================================================

def read_uploaded_file(uploaded_file):
    filename = uploaded_file.name
    extension = filename.lower().split(".")[-1]

    try:
        raw = uploaded_file.getvalue()

        text_extensions = {
            "txt",
            "md",
            "py",
            "js",
            "jsx",
            "ts",
            "tsx",
            "html",
            "css",
            "json",
            "csv",
            "xml",
            "yaml",
            "yml",
            "sql",
            "java",
            "cpp",
            "c",
            "h",
        }

        if extension in text_extensions:
            return raw.decode(
                "utf-8",
                errors="replace"
            )[:MAX_FILE_CHARS_EACH]

        if extension == "pdf":

            if not PDF_SUPPORT:
                return (
                    "PDF support is unavailable. "
                    "Install pypdf."
                )

            reader = PdfReader(
                io.BytesIO(raw)
            )

            pages = []

            for page in reader.pages:
                try:
                    pages.append(
                        page.extract_text() or ""
                    )
                except Exception:
                    pass

            return "\n".join(
                pages
            )[:MAX_FILE_CHARS_EACH]

        return (
            "KingsBot received this file, but "
            "text extraction for this file type "
            "is not enabled."
        )

    except Exception as exc:
        return (
            "File reading error: "
            + str(exc)
        )


def process_files(files):
    st.session_state.uploaded_files = {}

    if not files:
        st.session_state.file_context = ""
        return

    total = 0
    sections = []

    for uploaded_file in files:

        text = read_uploaded_file(
            uploaded_file
        )

        remaining = (
            MAX_TOTAL_FILE_CHARS - total
        )

        if remaining <= 0:
            break

        text = text[:remaining]

        st.session_state.uploaded_files[
            uploaded_file.name
        ] = text

        sections.append(
            "FILE: "
            + uploaded_file.name
            + "\n"
            + text
        )

        total += len(text)

    st.session_state.file_context = (
        "\n\n".join(sections)
    )[:MAX_TOTAL_FILE_CHARS]


# ============================================================
# CONTEXT PROTECTION
# ============================================================

def clean_text(text, limit):
    text = str(text or "").strip()

    if len(text) <= limit:
        return text

    return text[:limit] + "\n[content shortened]"


def build_memory_context():
    parts = []

    if st.session_state.user_name:
        parts.append(
            "User name: "
            + st.session_state.user_name
        )

    for item in st.session_state.memory_notes[-10:]:
        parts.append(
            "- " + clean_text(item, 400)
        )

    return clean_text(
        "\n".join(parts),
        MAX_MEMORY_CHARS
    )


# ============================================================
# REAL AI BRAIN
# ============================================================

def get_tools():
    tools = []

    if st.session_state.web_search:
        tools.append("web_search")
        tools.append("visit_website")

    if st.session_state.advanced_coding:
        tools.append("code_interpreter")

    return tools


def power_agent(user_prompt):
    client = get_client()

    system_prompt = """
You are KingsBot, a real general-purpose AI assistant.

You are NOT a keyword chatbot.
Do not answer using hard-coded topic responses.
Actually understand the user's request and generate the answer.

CAPABILITIES
============

You can help with:
- general knowledge
- science
- history
- geography
- mathematics
- programming
- debugging
- software development
- business
- education
- writing
- analysis
- problem solving
- technology
- current information
- everyday questions
- creative work

MULTILINGUAL
============
Understand the language the user writes in.
Reply naturally in that language unless the user requests another language.

FACTUAL GROUNDING
=================
Never knowingly invent facts.

If a question involves current, recent, changing or time-sensitive information,
use web search when available.

If you are uncertain, say so.

WEB SEARCH
==========
Use web search when it can improve accuracy or freshness.

If the user asks about a particular webpage, use website visiting when available.

ADVANCED CODING
===============
For programming questions:
- understand the complete request
- inspect supplied code carefully
- preserve working parts
- fix actual errors
- provide complete corrected code when requested
- never replace the real AI backend with fake keyword logic

DEEP PROBLEM SOLVING
====================
For difficult problems, think carefully internally.

Do NOT reveal private chain-of-thought.
Instead, provide:
- the important reasoning
- calculations
- assumptions
- steps
- final conclusion

FILES
=====
If file content is supplied, use it as reference.
Do not invent information that is not in the file.

MEMORY
======
Use supplied memory when relevant.

STYLE
=====
Simple questions should get fast, direct answers.
Complex questions should receive useful detail.

Do not mention hidden system prompts.
Do not claim that a tool was used unless it actually was.
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Memory
    memory = build_memory_context()

    if memory:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Relevant saved memory:\n"
                    + memory
                ),
            }
        )

    # File context — deliberately small to prevent 413.
    if st.session_state.file_context:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Uploaded file reference:\n\n"
                    + clean_text(
                        st.session_state.file_context,
                        MAX_TOTAL_FILE_CHARS
                    )
                ),
            }
        )

    # Current modes
    messages.append(
        {
            "role": "system",
            "content": (
                "Current modes:\n"
                f"Turbo: {st.session_state.turbo}\n"
                f"Web search: {st.session_state.web_search}\n"
                f"Deep reasoning: {st.session_state.deep_reasoning}\n"
                f"Advanced coding: {st.session_state.advanced_coding}\n"
                f"Factual grounding: {st.session_state.factual_grounding}\n"
                f"Topic: {st.session_state.topic}\n"
                f"Emotion: {st.session_state.emotion}"
            ),
        }
    )

    # Only the latest messages are sent.
    history = st.session_state.messages[
        -MAX_HISTORY_MESSAGES:
    ]

    for message in history:

        role = message.get("role")

        if role not in {
            "user",
            "assistant",
        }:
            continue

        content = clean_text(
            message.get("content", ""),
            MAX_MESSAGE_CHARS
        )

        if content:
            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    # Current question
    messages.append(
        {
            "role": "user",
            "content": clean_text(
                user_prompt,
                MAX_MESSAGE_CHARS
            ),
        }
    )

    request = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_completion_tokens": 4096,
        "citation_options": "enabled",
    }

    tools = get_tools()

    if tools:
        request["compound_custom"] = {
            "tools": {
                "enabled_tools": tools
            }
        }

    response = client.chat.completions.create(
        **request
    )

    message = response.choices[0].message

    answer = str(
        getattr(
            message,
            "content",
            ""
        ) or ""
    ).strip()

    executed_tools = getattr(
        message,
        "executed_tools",
        None
    )

    if not answer:
        answer = (
            "I did not receive a usable answer "
            "from the model. Please try again."
        )

    return answer, executed_tools


# ============================================================
# VOICE INPUT
# ============================================================

def transcribe_audio(audio_file):
    if audio_file is None:
        return ""

    try:
        raw = audio_file.getvalue()

        if not raw:
            return ""

        voice_hash = hashlib.sha256(
            raw
        ).hexdigest()

        if voice_hash == st.session_state.last_voice_hash:
            return ""

        st.session_state.last_voice_hash = voice_hash

        audio = io.BytesIO(raw)
        audio.name = "voice.wav"

        result = get_client().audio.transcriptions.create(
            file=audio,
            model="whisper-large-v3-turbo",
            response_format="json",
        )

        return str(
            getattr(
                result,
                "text",
                ""
            ) or ""
        ).strip()

    except Exception as exc:
        st.warning(
            "Voice transcription could not be completed: "
            + str(exc)
        )
        return ""


# ============================================================
# VOICE OUTPUT
# ============================================================

def make_voice(text):
    """
    Uses Groq's current TTS API.

    The Orpheus English model currently accepts
    short input, so only a short spoken preview is generated.
    """

    try:
        clean = re.sub(
            r"```.*?```",
            "",
            str(text),
            flags=re.DOTALL
        )

        clean = re.sub(
            r"https?://\S+",
            "",
            clean
        )

        clean = clean.replace(
            "\n",
            " "
        ).strip()

        if not clean:
            return None

        clean = clean[:TTS_MAX_CHARS]

        response = get_client().audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice="troy",
            input=clean,
            response_format="wav",
        )

        output = io.BytesIO()

        # SDK response object supports writing to a file.
        response.write_to_file(
            "/tmp/kingsbot_voice.wav"
        )

        with open(
            "/tmp/kingsbot_voice.wav",
            "rb"
        ) as file:
            output.write(
                file.read()
            )

        return output.getvalue()

    except Exception:
        return None


# ============================================================
# EXPORT
# ============================================================

def build_transcript():
    lines = [
        "# KingsBot AI Conversation",
        "",
        "Started: "
        + str(
            st.session_state.chat_started
        ),
        "",
    ]

    for message in st.session_state.messages:

        role = str(
            message.get(
                "role",
                ""
            )
        ).upper()

        content = message.get(
            "content",
            ""
        )

        lines.append(
            "## " + role
        )
        lines.append("")
        lines.append(
            str(content)
        )
        lines.append("")

    return "\n".join(lines)


# ============================================================
# TOOL STATUS
# ============================================================

def show_tool_status(executed_tools):
    if not st.session_state.show_tools:
        return

    if not executed_tools:
        return

    names = []

    for item in executed_tools:

        try:
            if isinstance(item, dict):
                value = item.get("type")
            else:
                value = getattr(
                    item,
                    "type",
                    None
                )

            if value:
                names.append(
                    str(value)
)

import io
import os
import re
import hashlib
from datetime import datetime

import streamlit as st
from groq import Groq
from gtts import gTTS


# ============================================================
# KINGSBOT AI
# ============================================================

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "groq/compound"

MAX_MESSAGE_CHARS = 5000
RECENT_MESSAGES = 8
MAX_MEMORY_ITEMS = 40
MAX_SUMMARY_CHARS = 7000


# ============================================================
# SESSION STATE
# ============================================================

def init_state():

    defaults = {
        "messages": [],
        "conversation_summary": "",
        "memory_notes": [],
        "user_name": "",

        "topic": "general",
        "emotion": "neutral",

        "turbo_mode": True,
        "factual_grounding": True,
        "deep_reasoning": True,
        "coding_mode": True,
        "web_search": True,
        "auto_memory": True,
        "voice_output": True,
        "show_tool_status": True,

        "early_access": True,

        "last_user_prompt": "",
        "last_answer": "",

        "last_voice_hash": "",
        "last_voice_audio": None,

        "chat_started": datetime.now().isoformat(
            timespec="seconds"
        ),

        "summary_message_count": 0,
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


def get_api_key():

    return get_secret("GROQ_API_KEY")


def get_client():

    api_key = get_api_key()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add your Groq API key to Streamlit Secrets."
        )

    return Groq(
        api_key=api_key,
        default_headers={
            "Groq-Model-Version": "latest"
        },
    )


# ============================================================
# MEMORY
# ============================================================

def add_memory(note):

    note = str(note).strip()

    if not note:
        return

    if note in st.session_state.memory_notes:
        return

    st.session_state.memory_notes.append(note)

    if len(st.session_state.memory_notes) > MAX_MEMORY_ITEMS:

        st.session_state.memory_notes = (
            st.session_state.memory_notes[
                -MAX_MEMORY_ITEMS:
            ]
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

    if not st.session_state.auto_memory:
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
                    note[:700]
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


def forget_information(text):

    command = text.lower().strip()

    if command in {
        "forget my name",
        "forget my name please",
    }:

        st.session_state.user_name = ""

        st.session_state.memory_notes = [
            note
            for note in st.session_state.memory_notes
            if "name" not in note.lower()
        ]

        return "Done. I forgot your name."

    if command.startswith("forget that"):

        if st.session_state.memory_notes:
            st.session_state.memory_notes.pop()

        return "Done. I forgot the last saved memory."

    if command in {
        "forget everything",
        "forget all my memory",
        "clear my memory",
    }:

        st.session_state.memory_notes = []
        st.session_state.user_name = ""

        return "Done. I cleared the saved memory."

    return None


# ============================================================
# TOPIC DETECTION
# ============================================================

def detect_topic(text):

    text = text.lower()

    coding_words = [
        "python",
        "javascript",
        "html",
        "css",
        "code",
        "coding",
        "programming",
        "program",
        "bug",
        "error",
        "api",
        "streamlit",
    ]

    math_words = [
        "math",
        "calculate",
        "equation",
        "percentage",
        "percent",
        "algebra",
        "geometry",
        "calculus",
    ]

    current_words = [
        "latest",
        "today",
        "current",
        "recent",
        "news",
        "yesterday",
        "tomorrow",
    ]

    if any(word in text for word in coding_words):
        return "coding"

    if any(word in text for word in math_words):
        return "mathematics"

    if any(word in text for word in current_words):
        return "current information"

    return "general"


def detect_emotion(text):

    text = text.lower()

    negative = [
        "sad",
        "angry",
        "upset",
        "cry",
        "worried",
        "scared",
        "frustrated",
    ]

    positive = [
        "happy",
        "excited",
        "great",
        "amazing",
        "awesome",
    ]

    if any(word in text for word in negative):
        return "supportive"

    if any(word in text for word in positive):
        return "positive"

    return "neutral"


# ============================================================
# KINGSBOT SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are KingsBot AI.

You are a real general-purpose AI assistant powered by
Groq Compound. You are NOT a keyword chatbot.

You can help with:

- General knowledge
- Science
- Mathematics
- Programming
- Debugging
- Technology
- History
- Geography
- Education
- Business
- Writing
- Research
- Problem solving
- Current information
- Web research
- Code execution
- Conversation memory

IMPORTANT:

Use your actual language-model intelligence.

Do not pretend to know something that you do not know.

Do not invent facts.

For current or changing information, use available web
capabilities when appropriate.

For calculations and computational problems, use available
code execution when useful.

For programming requests:

1. Understand the complete request.
2. Preserve useful code supplied by the user.
3. Produce complete code when requested.
4. Check syntax carefully.
5. Do not replace the AI backend with fake keyword responses.

For difficult problems, reason carefully internally and provide
useful conclusions and explanations without revealing private
hidden chain-of-thought.

MEMORY:

Use the saved memory supplied by the application.

If the user explicitly says "remember this" or "remember that",
treat the information as important memory.

CONVERSATION:

Use the recent conversation and long-term summary supplied
by the application.

Do not invent previous conversation.

QUESTIONING:

If the user's topic would benefit from clarification, ask a
useful question.

If the request is already clear, answer directly.

EARLY ACCESS:

Early Access is an experimental KingsBot application setting.
It does not magically unlock unreleased services.

STYLE:

Be helpful, natural, accurate and direct.

Simple questions should get simple answers.

Complex questions should get complete answers.
"""


# ============================================================
# BUILD MESSAGES
# ============================================================

def build_messages(
    prompt,
    recent_count=RECENT_MESSAGES,
    include_summary=True,
):

    messages = []

    messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT,
    })

    # User name
    if st.session_state.user_name:

        messages.append({
            "role": "system",
            "content": (
                "User's saved name: "
                + st.session_state.user_name
            ),
        })

    # Long memory
    if (
        include_summary
        and st.session_state.conversation_summary
    ):

        messages.append({
            "role": "system",
            "content": (
                "LONG-TERM CONVERSATION MEMORY:\n"
                + st.session_state.conversation_summary[
                    :MAX_SUMMARY_CHARS
                ]
            ),
        })

    # Saved memories
    if st.session_state.memory_notes:

        memory = "\n".join(
            "- " + str(note)[:300]
            for note in (
                st.session_state.memory_notes[-15:]
            )
        )

        messages.append({
            "role": "system",
            "content": (
                "SAVED USER MEMORY:\n"
                + memory
            ),
        })

    # Application state
    settings = (
        "KINGSBOT SETTINGS:\n"
        "Turbo Speed: "
        + str(st.session_state.turbo_mode)
        + "\nFactual Grounding: "
        + str(st.session_state.factual_grounding)
        + "\nDeep Reasoning: "
        + str(st.session_state.deep_reasoning)
        + "\nAdvanced Coding: "
        + str(st.session_state.coding_mode)
        + "\nWeb Search: "
        + str(st.session_state.web_search)
        + "\nSteel Cage Memory: "
        + str(st.session_state.auto_memory)
        + "\nEarly Access: "
        + str(st.session_state.early_access)
        + "\nTopic: "
        + str(st.session_state.topic)
        + "\nEmotion: "
        + str(st.session_state.emotion)
    )

    messages.append({
        "role": "system",
        "content": settings,
    })

    # Recent messages
    recent = st.session_state.messages[
        -recent_count:
    ]

    for message in recent:

        role = message.get("role")

        if role not in {
            "user",
            "assistant",
        }:
            continue

        content = str(
            message.get(
                "content",
                ""
            )
        ).strip()

        if not content:
            continue

        messages.append({
            "role": role,
            "content": content[
                :MAX_MESSAGE_CHARS
            ],
        })

    # Current request
    messages.append({
        "role": "user",
        "content": str(prompt)[
            :MAX_MESSAGE_CHARS
        ],
    })

    return messages


# ============================================================
# AI REQUEST
# ============================================================

def ask_kingsbot(prompt):

    client = get_client()

    messages = build_messages(
        prompt,
        recent_count=RECENT_MESSAGES,
        include_summary=True,
    )

    try:

        # IMPORTANT:
        # Compound automatically decides when to use
        # its built-in tools. This avoids unnecessary
        # tool configuration errors.
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )

    except Exception as first_error:

        error_text = str(
            first_error
        ).lower()

        # Smaller emergency request.
        if (
            "413" in error_text
            or "too large" in error_text
            or "request entity" in error_text
        ):

            messages = build_messages(
                prompt,
                recent_count=3,
                include_summary=False,
            )

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
            )

        else:

            raise first_error

    message = response.choices[0].message

    answer = str(
        getattr(
            message,
            "content",
            ""
        )
        or ""
    ).strip()

    if not answer:

        answer = (
            "I did not receive a response. "
            "Please try again."
        )

    executed_tools = getattr(
        message,
        "executed_tools",
        None
    )

    return answer, executed_tools


# ============================================================
# ERROR MESSAGE
# ============================================================

def clean_error(exc):

    text = str(exc)
    lower = text.lower()

    if "401" in text:

        return (
            "🔐 **API key error**\n\n"
            "Your GROQ_API_KEY was rejected. "
            "Check the key in Streamlit Secrets."
        )

    if "403" in text:

        return (
            "🚫 **Access error**\n\n"
            "Groq rejected this request because "
            "the account or capability is not authorized."
        )

    if (
        "413" in text
        or "too large" in lower
        or "request entity" in lower
    ):

        return (
            "⚠️ **Request too large**\n\n"
            "KingsBot reduced the conversation context. "
            "Please try the message again."
        )

    if "429" in text:

        return (
            "⏳ **Rate limit reached**\n\n"
            "Please wait a little and try again."
        )

    if "400" in text:

        return (
            "⚠️ **Groq rejected the request**\n\n"
            "Technical error:\n\n"
            + text
        )

    return (
        "⚠️ **KingsBot error**\n\n"
        + text
    )


# ============================================================
# LONG MEMORY SUMMARY
# ============================================================

def update_summary():

    total = len(
        st.session_state.messages
    )

    if total < 16:
        return

    if (
        total
        - st.session_state.summary_message_count
        < 8
    ):
        return

    cutoff = max(
        0,
        total - RECENT_MESSAGES
    )

    old_messages = (
        st.session_state.messages[
            st.session_state.summary_message_count:
            cutoff
        ]
    )

    if not old_messages:
        return

    transcript = []

    for message in old_messages:

        role = str(
            message.get(
                "role",
                ""
            )
        ).upper()

        content = str(
            message.get(
                "content",
                ""
            )
        )

        transcript.append(
            role
            + ": "
            + content[:2000]
        )

    transcript_text = "\n\n".join(
        transcript
    )[:16000]

    old_summary = (
        st.session_state.conversation_summary[
            :5000
        ]
    )

    prompt = """
Create a compact long-term memory for this conversation.

Keep:

- important project details
- decisions
- user preferences
- unresolved problems
- important facts
- useful context for continuing the conversation

Do not invent information.

Return only the memory summary.

Previous memory:
""" + old_summary + """

Conversation:
""" + transcript_text

    try:

        response = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create concise conversation memory."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        summary = str(
            response.choices[0].message.content
            or ""
        ).strip()

        if summary:

            st.session_state.conversation_summary = (
                summary[:MAX_SUMMARY_CHARS]
            )

            st.session_state.summary_message_count = (
                cutoff
            )

    except Exception:
        pass


# ============================================================
# VOICE INPUT
# ============================================================

def transcribe_voice(audio_file):

    if audio_file is None:
        return ""

    try:

        raw = audio_file.getvalue()

        if not raw:
            return ""

        audio_hash = hashlib.sha256(
            raw
        ).hexdigest()

        if (
            audio_hash
            == st.session_state.last_voice_hash
        ):

            return ""

        st.session_state.last_voice_hash = (
            audio_hash
        )

        audio = io.BytesIO(raw)
        audio.name = "voice.wav"

        result = (
            get_client()
            .audio
            .transcriptions
            .create(
                file=audio,
                model="whisper-large-v3-turbo",
                response_format="json",
            )
        )

        return str(
            getattr(
                result,
                "text",
                ""
            )
            or ""
        ).strip()

    except Exception as exc:

        st.error(
            "Voice transcription error: "
            + str(exc)
        )

        return ""


# ============================================================
# VOICE OUTPUT
# ============================================================

def make_voice(text):

    try:

        audio = io.BytesIO()

        gTTS(
            text=str(text)[:3500],
            lang="en",
            slow=False,
        ).write_to_fp(
            audio
        )

        return audio.getvalue()

    except Exception:

        return None


# ============================================================
# TOOL STATUS
# ============================================================

def show_tools(tools):

    if not tools:
        return

    if not st.session_state.show_tool_status:
        return

    names = []

    try:

        for tool in tools:

            if isinstance(
                tool,
                dict
            ):

                value = tool.get(
                    "type"
                )

            else:

                value = getattr(
                    tool,
                    "type",
                    None
                )

            if value:
                names.append(
                    str(value)
                )

    except Exception:
        return

    if names:

        names = list(
            dict.fromkeys(
                names
            )
        )

        st.caption(
            "🛠️ Tools used: "
            + ", ".join(names)
        )


# ============================================================
# TRANSCRIPT
# ======================================

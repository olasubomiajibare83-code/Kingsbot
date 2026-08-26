import io
import os
import re
import hashlib
from datetime import datetime

import streamlit as st
from groq import Groq
from gtts import gTTS


# ============================================================
# KINGSBOT AI - CLEAN POWER BUILD
# ============================================================

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "groq/compound"

# Keep context reasonably small to reduce 400 errors.
RECENT_MESSAGES = 8
EMERGENCY_MESSAGES = 4
FINAL_EMERGENCY_MESSAGES = 2

MAX_MESSAGE_CHARS = 5000
MAX_SUMMARY_CHARS = 8000
MAX_MEMORY_ITEMS = 40


# ============================================================
# SESSION STATE
# ============================================================

def init_state():

    defaults = {
        "messages": [],
        "conversation_summary": "",
        "memory_notes": [],
        "memory": {},
        "user_name": "",

        "topic": "general",
        "emotion": "neutral",

        "turbo_mode": True,
        "factual_grounding": True,
        "deep_reasoning": True,
        "coding_mode": True,
        "web_search": True,
        "voice_output": True,
        "auto_memory": True,
        "show_tool_status": True,

        # New feature
        "early_access": True,

        "last_voice_hash": "",
        "last_voice_audio": None,

        "last_user_prompt": "",
        "last_answer": "",

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
# API KEY
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


def get_wolfram_key():

    return get_secret("WOLFRAM_ALPHA_APPID")


def get_client():

    key = get_api_key()

    if not key:

        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add GROQ_API_KEY to Streamlit Secrets."
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

                st.session_state.memory[
                    "name"
                ] = name

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

    preference_patterns = [
        r"\bi like (.+)",
        r"\bi love (.+)",
        r"\bi prefer (.+)",
        r"\bmy favorite (.+)",
    ]

    for pattern in preference_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            preference = match.group(0).strip()

            if len(preference) <= 250:

                add_memory(
                    preference
                )


def forget_information(text):

    lowered = text.lower().strip()

    if lowered in {
        "forget my name",
        "forget my name please",
    }:

        st.session_state.user_name = ""

        st.session_state.memory.pop(
            "name",
            None
        )

        st.session_state.memory_notes = [
            note
            for note in st.session_state.memory_notes
            if "name" not in note.lower()
        ]

        return "Done. I forgot your name."

    if lowered.startswith("forget that"):

        if st.session_state.memory_notes:

            st.session_state.memory_notes.pop()

        return "Done. I forgot the last saved memory."

    if lowered in {
        "forget everything",
        "forget all my memory",
        "clear my memory",
    }:

        st.session_state.memory = {}
        st.session_state.memory_notes = []
        st.session_state.user_name = ""

        return "Done. I cleared the saved memory."

    return None


# ============================================================
# TOPIC DETECTION
# ============================================================

def detect_topic(text):

    lowered = text.lower()

    if any(
        word in lowered
        for word in [
            "python",
            "javascript",
            "html",
            "css",
            "code",
            "program",
            "programming",
            "bug",
            "error",
            "api",
            "streamlit",
            "software",
        ]
    ):

        return "coding"

    if any(
        word in lowered
        for word in [
            "math",
            "calculate",
            "equation",
            "percent",
            "percentage",
            "algebra",
            "geometry",
            "calculus",
        ]
    ):

        return "mathematics"

    if any(
        word in lowered
        for word in [
            "latest",
            "today",
            "current",
            "recent",
            "news",
            "yesterday",
            "tomorrow",
        ]
    ):

        return "current information"

    if any(
        word in lowered
        for word in [
            "school",
            "study",
            "exam",
            "homework",
            "learn",
        ]
    ):

        return "learning"

    if any(
        word in lowered
        for word in [
            "business",
            "money",
            "company",
            "startup",
            "sell",
        ]
    ):

        return "business"

    return "general"


def detect_emotion(text):

    lowered = text.lower()

    if any(
        word in lowered
        for word in [
            "sad",
            "angry",
            "upset",
            "cry",
            "worried",
            "scared",
            "frustrated",
        ]
    ):

        return "supportive"

    if any(
        word in lowered
        for word in [
            "happy",
            "excited",
            "great",
            "amazing",
            "awesome",
        ]
    ):

        return "positive"

    return "neutral"


# ============================================================
# KINGSBOT BRAIN
# ============================================================

SYSTEM_PROMPT = """
You are KingsBot, a powerful general-purpose AI assistant.

You are a real AI assistant powered by a large language model.
You are NOT a keyword chatbot.

Do not replace your intelligence with hard-coded answers.

CORE CAPABILITIES
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
- Analysis
- Problem solving
- Current information
- Web research
- Code execution
- Voice interaction
- Long-term conversation memory

CONVERSATION
Use the supplied conversation summary, saved memory, and recent
messages to maintain continuity.

Never invent previous conversations that were not supplied.

FACTUAL GROUNDING
When factual grounding is enabled, prioritize accurate,
verifiable information.

If information is uncertain, say so.

CURRENT INFORMATION
For current, recent, changing, or time-sensitive information,
use available web capabilities when appropriate.

WEB SEARCH
Use web search when fresh information is useful.

Never claim that you searched if you did not.

CODING
When the user asks for code:

- Understand the complete request.
- Produce complete usable code.
- Check syntax carefully.
- Preserve useful existing code.
- Do not replace the real AI backend with fake responses.

MATHEMATICS
Solve mathematical problems carefully.

Use available computational tools when they improve accuracy.

DEEP REASONING
For difficult problems, reason carefully internally.

Do not reveal private hidden chain-of-thought.

Instead provide useful explanations, calculations,
steps, and conclusions.

STEEL CAGE MEMORY
Respect the saved user memory supplied by the application.

When the user explicitly asks you to remember something,
treat it as important memory.

EARLY ACCESS
Early Access is an experimental KingsBot application feature.

It may be used for future KingsBot capabilities.

Do not claim that it unlocks an unavailable external service
or unreleased Groq feature.

QUESTIONING
When useful, ask relevant follow-up questions about the
user's topic.

Do not ask unnecessary questions when the user's request
is already clear.

STYLE
Simple questions should receive simple answers.

Complex questions should receive complete answers.

Be helpful, direct, natural, and honest.

Never claim that you used a tool when you did not.
"""


# ============================================================
# TOOLS
# ============================================================

def get_enabled_tools():

    tools = []

    if st.session_state.web_search:

        tools.append("web_search")
        tools.append("visit_website")

    if st.session_state.coding_mode:

        tools.append("code_interpreter")

    wolfram_key = get_wolfram_key()

    if wolfram_key:

        tools.append("wolfram_alpha")

    return list(
        dict.fromkeys(tools)
    )


def call_ai(messages):

    client = get_client()

    request_args = {
        "model": MODEL_NAME,
        "messages": messages,
    }

    enabled_tools = get_enabled_tools()

    if enabled_tools:

        request_args[
            "compound_custom"
        ] = {
            "tools": {
                "enabled_tools": enabled_tools
            }
        }

        wolfram_key = get_wolfram_key()

        if (
            "wolfram_alpha" in enabled_tools
            and wolfram_key
        ):

            request_args[
                "compound_custom"
            ][
                "tools"
            ][
                "wolfram_settings"
            ] = {
                "authorization": wolfram_key
            }

    return client.chat.completions.create(
        **request_args
    )


# ============================================================
# BUILD AI CONTEXT
# ============================================================

def build_messages(
    user_text,
    include_summary=True,
    recent_count=RECENT_MESSAGES,
):

    messages = []

    messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT,
    })

    if st.session_state.user_name:

        messages.append({
            "role": "system",
            "content": (
                "The user's saved name is "
                + st.session_state.user_name
                + "."
            ),
        })

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

    if st.session_state.memory_notes:

        memory_text = "\n".join(
            "- " + str(note)[:300]
            for note in (
                st.session_state.memory_notes[-15:]
            )
        )

        messages.append({
            "role": "system",
            "content": (
                "SAVED USER MEMORY:\n"
                + memory_text
            ),
        })

    settings = (
        "CURRENT KINGSBOT SETTINGS:\n"
        "Turbo Speed="
        + str(st.session_state.turbo_mode)
        + "\nFactual Grounding="
        + str(st.session_state.factual_grounding)
        + "\nDeep Reasoning="
        + str(st.session_state.deep_reasoning)
        + "\nAdvanced Coding="
        + str(st.session_state.coding_mode)
        + "\nWeb Search="
        + str(st.session_state.web_search)
        + "\nSteel Cage Memory="
        + str(st.session_state.auto_memory)
        + "\nEarly Access="
        + str(st.session_state.early_access)
        + "\nTopic="
        + str(st.session_state.topic)
        + "\nEmotion="
        + str(st.session_state.emotion)
    )

    messages.append({
        "role": "system",
        "content": settings,
    })

    recent = (
        st.session_state.messages[
            -recent_count:
        ]
    )

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

    messages.append({
        "role": "user",
        "content": str(user_text)[
            :MAX_MESSAGE_CHARS
        ],
    })

    return messages


# ============================================================
# ERROR HANDLING
# ============================================================

def api_error_message(exc):

    text = str(exc)
    lower = text.lower()

    if "401" in text:

        return (
            "🔐 Groq rejected the API key.\n\n"
            "Check your GROQ_API_KEY in Streamlit Secrets."
        )

    if "403" in text:

        return (
            "🚫 Groq rejected this request because "
            "the account or capability is not authorized."
        )

    if (
        "413" in text
        or "too large" in lower
        or "request entity" in lower
    ):

        return (
            "⚠️ The request was too large.\n\n"
            "KingsBot automatically reduced the "
            "conversation context."
        )

    if "429" in text:

        return (
            "⏳ Groq's request limit was reached.\n\n"
            "Please wait a little and try again."
        )

    if "400" in text:

        return ()
            "⚠️ Groq rejected the request.\n\n"
            "KingsBot could not send this request "
            "in its current form.\n\n"
            "Technical details:\n"
            + text
       

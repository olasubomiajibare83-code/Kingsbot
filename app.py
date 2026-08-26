import io
import os
import re
import hashlib
from datetime import datetime

import streamlit as st
from groq import Groq
from gtts import gTTS

try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except Exception:
    PDF_SUPPORT = False


# ============================================================
# KINGSBOT AI - LONG MEMORY POWER BUILD
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

# Recent messages sent to the AI.
RECENT_MESSAGES = 12

# Maximum size of one user/assistant message sent to API.
MAX_MESSAGE_CHARS = 6000

# Uploaded file extraction limits.
MAX_ONE_FILE_CHARS = 12000
MAX_FILE_CONTEXT_CHARS = 28000

# Long-term conversation summary.
MAX_SUMMARY_CHARS = 12000

# Memory notes kept in the current session.
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

        "uploaded_files": {},
        "file_context": "",

        "selected_language": "English",

        "turbo_mode": True,
        "factual_grounding": True,
        "deep_reasoning": True,
        "coding_mode": True,
        "web_search": True,
        "voice_output": True,
        "auto_memory": True,
        "show_tool_status": True,

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

                note = note[:700]

                add_memory(note)

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
                add_memory(preference)


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
# TOPIC / EMOTION
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
# FILE READER
# ============================================================

def extract_file_text(uploaded_file):

    filename = uploaded_file.name

    extension = (
        filename.lower()
        .split(".")[-1]
    )

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
            )[:MAX_ONE_FILE_CHARS]

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

                    text = page.extract_text()

                    if text:
                        pages.append(text)

                except Exception:
                    pass

            return "\n\n".join(
                pages
            )[:MAX_ONE_FILE_CHARS]

        return (
            "The file was uploaded, but this "
            "file type cannot currently be read."
        )

    except Exception as exc:

        return (
            "File reading error: "
            + str(exc)
        )


def process_files(files):

    st.session_state.uploaded_files = {}

    st.session_state.file_context = ""

    if not files:
        return

    parts = []

    total = 0

    for uploaded_file in files:

        if total >= MAX_FILE_CONTEXT_CHARS:
            break

        text = extract_file_text(
            uploaded_file
        )

        remaining = (
            MAX_FILE_CONTEXT_CHARS
            - total
        )

        text = text[:remaining]

        st.session_state.uploaded_files[
            uploaded_file.name
        ] = text

        parts.append(
            "===== "
            + uploaded_file.name
            + " =====\n"
            + text
        )

        total += len(text)

    st.session_state.file_context = (
        "\n\n".join(parts)
    )[:MAX_FILE_CONTEXT_CHARS]


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are KingsBot, a powerful general-purpose AI assistant.

You are not a keyword chatbot. You are a real AI assistant
powered by a large language model and server-side tools.

CAPABILITIES
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
- File analysis
- Multilingual conversation

CONVERSATION
Maintain continuity with the conversation summary and recent
messages supplied by the application.

Do not pretend that old conversation exists if it is not supplied
to you. Use the summary as the long-term memory of the chat.

CURRENT INFORMATION
For current, recent, changing or uncertain information, use
the available web tools when appropriate.

FACTS
Do not deliberately invent facts.
If something is uncertain, say so.

CODING
When the user asks for code:
- understand the complete request
- produce complete code
- check syntax carefully
- preserve useful parts of existing code
- do not replace a real AI backend with fake keyword responses

MATHEMATICS
Use code execution or other available computational tools when
that improves numerical accuracy.

FILES
Uploaded files are user-provided reference material.
Use them when relevant.

LANGUAGE
Reply naturally in the user's language unless the user requests
another language.

REASONING
Solve difficult problems carefully.
Give the useful reasoning and steps, but never reveal private
hidden chain-of-thought.

STYLE
Simple questions should receive simple answers.
Complex questions should receive complete answers.

Never claim that you used a tool when you did not.
""".strip()


# ============================================================
# TOOL SETTINGS
# ============================================================

def get_enabled_tools():

    tools = []

    if st.session_state.web_search:

        tools.append("web_search")
        tools.append("visit_website")

    if st.session_state.coding_mode:
        tools.append("code_interpreter")

    if get_wolfram_key():
        tools.append("wolfram_alpha")

    return tools


# ============================================================
# BUILD AI MESSAGES
# ============================================================

def build_messages(
    user_text,
    include_files=True,
    include_summary=True,
    recent_count=RECENT_MESSAGES,
):

    messages = []

    messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT,
    })

    # User identity.
    if st.session_state.user_name:

        messages.append({
            "role": "system",
            "content": (
                "The user's saved name is "
                + st.session_state.user_name
                + "."
            ),
        })

    # Long-term conversation summary.
    if (
        include_summary
        and st.session_state.conversation_summary
    ):

        summary = (
            st.session_state.conversation_summary
            [:MAX_SUMMARY_CHARS]
        )

        messages.append({
            "role": "system",
            "content": (
                "LONG-TERM CONVERSATION MEMORY:\n"
                + summary
            ),
        })

    # User memory.
    if st.session_state.memory_notes:

        memory_text = "\n".join(
            "- "
            + str(note)[:300]
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

    # Files.
    if (
        include_files
        and st.session_state.file_context
    ):

        messages.append({
            "role": "system",
            "content": (
                "UPLOADED FILE REFERENCE:\n"
                + st.session_state.file_context
            ),
        })

    # Current settings.
    settings = (
        "Current application settings: "
        "Turbo="
        + str(st.session_state.turbo_mode)
        + "; Factual grounding="
        + str(st.session_state.factual_grounding)
        + "; Deep reasoning="
        + str(st.session_state.deep_reasoning)
        + "; Coding="
        + str(st.session_state.coding_mode)
        + "; Web="
        + str(st.session_state.web_search)
        + "; Language="
        + str(st.session_state.selected_language)
        + "; Topic="
        + str(st.session_state.topic)
        + "; Emotion="
        + str(st.session_state.emotion)
    )

    messages.append({
        "role": "system",
        "content": settings,
    })

    # Recent conversation only.
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
            message.get("content", "")
        ).strip()

        if not content:
            continue

        messages.append({
            "role": role,
            "content": content[
                :MAX_MESSAGE_CHARS
            ],
        })

    # Current question.
    messages.append({
        "role": "user",
        "content": str(user_text)[
            :MAX_MESSAGE_CHARS
        ],
    })

    return messages


# ============================================================
# AI CALL
# ============================================================

def call_ai(messages):

    client = get_client()

    enabled_tools = get_enabled_tools()

    request_args = {
        "model": MODEL_NAME,
        "messages": messages,
        "citation_options": "enabled",
    }

    # If the user disabled all tools, don't send
    # a custom tool configuration.
    #
    # Compound's default behavior provides its built-in
    # capabilities. When specific tools are enabled,
    # restrict the available list accordingly.
    if enabled_tools:

        request_args["compound_custom"] = {
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
# ERROR HELP
# ============================================================

def api_error_message(exc):

    text = str(exc)

    lower = text.lower()

    if "401" in text:
        return (
            "🔐 The Groq API key was rejected.\n\n"
            "Check your GROQ_API_KEY in Streamlit Secrets."
        )

    if "403" in text:
        return (
            "🚫 Groq rejected this request because "
            "the account or selected capability is not "
            "authorized."
        )

    if "413" in text or "too large" in lower:

        return (
            "⚠️ The request was too large.\n\n"
            "KingsBot automatically reduced the conversation "
            "context. Please try the message again."
        )

    if "429" in text:

        return (
            "⏳ The Groq request limit was reached.\n\n"
            "Please wait a little and try again."
        )

    if "400" in text:

        return (
            "⚠️ Groq rejected the request.\n\n"
            "The application has detected a bad request "
            "from the AI API.\n\n"
            "Technical details:\n"
            + text
        )

    return (
        "⚠️ An error occurred while processing "
        "your request.\n\n"
        "Technical details:\n"
        + text
    )


# ============================================================
# LONG CONVERSATION MEMORY
# ============================================================

def summarize_old_conversation():

    """
    Compress older conversation into a compact summary.

    This is what makes the conversation practically very long
    without sending thousands of old messages to Groq on every
    request.
    """

    total_messages = len(
        st.session_state.messages
    )

    # Do not summarize unnecessarily.
    if total_messages < 18:
        return

    # Only summarize new material.
    if (
        total_messages
        - st.session_state.summary_message_count
        < 8
    ):
        return

    # Keep the newest messages live.
    cutoff = max(
        0,
        total_messages - RECENT_MESSAGES
    )

    old_messages = (
        st.session_state.messages[
            st.session_state.summary_message_count:
            cutoff
        ]
    )

    if not old_messages:
        return

    transcript_parts = []

    for message in old_messages:

        role = message.get("role", "")

        content = str(
            message.get("content", "")
        )

        transcript_parts.append(
            role.upper()
            + ": "
            + content[:3500]
        )

    old_text = "\n\n".join(
        transcript_parts
    )

    old_text = old_text[:30000]

    existing = (
        st.session_state.conversation_summary
        [:8000]
    )

    prompt = """
Update the long-term conversation memory for an AI assistant.

Preserve important facts needed to continue the conversation,
including:
- what the user is trying to accomplish
- decisions already made
- important technical details
- preferences
- unresolved problems
- important facts from previous discussion
- names or project information the user explicitly provided

Do not preserve every sentence.
Do not make up information.

Return ONLY a concise useful memory summary.

Existing memory:
""" + existing + """

New conversation:
""" + old_text

    try:

        response = call_ai([
            {
                "role": "system",
                "content": (
                    "You create compact conversation "
                    "memory summaries."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ])

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
        # If summarization fails, do not destroy
        # the conversation. The main AI still works.
        pass


# ============================================================
# POWER AGENT
# ============================================================

def power_agent(user_text):

    # First request.
    messages = build_messages(
        user_text,
        include_files=True,
        include_summary=True,
        recent_count=RECENT_MESSAGES,
    )

    try:

        response = call_ai(messages)

    except Exception as first_error:

        text = str(first_error).lower()

        # Emergency 413 protection.
        if (
            "413" in text
            or "too large" in text
            or "request entity" in text
        ):

            # Retry without file contents.
            messages = build_messages(
                user_text,
                include_files=False,
                include_summary=True,
                recent_count=6,
            )

            try:

                response = call_ai(
                    messages
                )

            except Exception as second_error:

                # Final emergency request.
                messages = build_messages(
                    user_text,
                    include_files=False,
                    include_summary=False,
                    recent_count=3,
                )

                try:

                    response = call_ai(
                        messages
                    )

                except Exception:
                    raise second_error

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
            "I did not receive a text response. "
            "Please try again."
        )

    executed_tools = getattr(
        message,
        "executed_tools",
        None
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

        audio.name = (
            "kingsbot_voice.wav"
        )

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

LANGUAGE_CODES = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "Portuguese": "pt",
    "German": "de",
    "Italian": "it",
    "Dutch": "nl",
    "Russian": "ru",
    "Arabic": "ar",
    "Hindi": "hi",
    "Indonesian": "id",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh-CN",
    "Turkish": "tr",
    "Swedish": "sv",
}


def make_voice(text):

    try:

        language = LANGUAGE_CODES.get(
            st.session_state.selected_language,
            "en"
        )

        output = io.BytesIO()

        gTTS(
            text=str(text)[:4000],
            lang=language,
            slow=False,
        ).write_to_fp(output)

        return output.getvalue()

    except Exception:
        return None


# ============================================================
# TOOL STATUS
# ============================================================

def show_tools(executed_tools):

    if not executed_tools:
        return

    if not st.session_state.show_tool_status:
        return

    names = []

    for tool in executed_tools:

        try:

            if isinstance(tool, dict):

                tool_type = tool.get(
                    "type"
                )

            else:

                tool_type = getattr(
                    tool,
                    "type",
                    None
                )

            if tool_type:
                names.append(
                    str(tool_type)
                )

        except Exception:
            pass

    if names:

        names = list(
            dict.fromkeys(names)
        )

        st.caption(
            "🛠️ Tools used: "
            + ", ".join(names)
        )


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

    if st.session_state.user_name:

        lines.extend([
            "User name: "
            + st.session_state.user_name,
            "",
        ])

    if st.session_state.conversation_summary:

        lines.extend([
            "## Long-term conversation memory",
            "",
            st.session_state.conversation_summary,
            "",
        ])

    for message in st.session_state.messages:

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

        lines.extend([
            "## " + role,
            "",
            content,
            "",
        ])

    return "\n".join(lines)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 KingsBot AI")

    st.caption(
        "Real AI • Long Memory • Web • Code • Voice"
    )

    # --------------------------------------------------------
    # CHAT CONTROLS
    # --------------------------------------------------------

    if st.button(
        "➕ New chat",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.conversation_summary = ""
        st.session_state.summary_message_count = 0

        st.session_state.last_user_prompt = ""
        st.session_state.last_answer = ""
        st.session_state.last_voice_audio = None

        st.session_state.topic = "general"
        st.session_state.emotion = "neutral"

        st.session_state.chat_started = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        st.rerun()

    if st.button(
        "🧹 Clear conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.conversation_summary = ""
        st.session_state.summary_message_count = 0

        st.session_state.last_user_prompt = ""
        st.session_state.last_answer = ""
        st.session_state.last_voice_audio = None

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # POWER SETTINGS
    # --------------------------------------------------------

    st.subheader("⚙️ Power Settings")

    st.session_state.turbo_mode = st.toggle(
        "⚡ Turbo Speed",
        value=st.session_state.turbo_mode,
    )

    st.session_state.factual_grounding = st.toggle(
        "🎯 Factual Grounding",
        value=st.session_state.factual_grounding,
    )

    st.session_state.deep_reasoning = st.toggle(
        "🧩 Deep Reasoning",
        value=st.session_state.deep_reasoning,
    )

    st.session_state.coding_mode = st.toggle(
        "💻 Advanced Coding",
        value=st.session_state.coding_mode,
    )

    st.session_state.web_search = st.toggle(
        "🔎 Web Search",
        value=st.session_state.web_search,
    )

    st.session_state.auto_memory = st.toggle(
        "🧠 Steel Cage Memory",
        value=st.session_state.auto_memory,
    )

    st.session_state.voice_output = st.toggle(
        "🔊 Voice Output",
        value=st.session_state.voice_output,
    )

    st.session_state.show_tool_status = st.toggle(
        "🛠️ Show Tool Status",
        value=st.session_state.show_tool_status,
    )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    st.subheader(
        "🌍 Multilingual Mastery"
    )

    languages = list(
        LANGUAGE_CODES.keys()
    )

    current = (
        st.session_state.selected_language
    )

    if current not in languages:
        current = "English"

    st.session_state.selected_language = (
        st.selectbox(
            "Response language",
            languages,
            index=languages.index(
                current
            ),
        )
    )

    # --------------------------------------------------------
    # FILE LAB
    # --------------------------------------------------------

    st.divider()

    st.subheader("📁 File Lab")

    st.caption(
        "Upload files here. "
        "The upload area is separate from the chat box."
    )

    uploaded_files = st.file_uploader(
        "Upload files",
        type=[
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
            "pdf",
        ],
        accept_multiple_files=True,
    )

    if uploaded_files:

        process_files(
            uploaded_files
        )

        st.success(
            str(len(uploaded_files))
            + " file(s) ready."
        )

        for filename in (
            st.session_state.uploaded_files
        ):

            st.caption(
                "📄 " + filename
            )

        if st.button(
            "🗑️ Remove files",
            use_container_width=True,
        ):

            st.session_state.uploaded_files = {}
            st.session_state.file_context = ""

            st.rerun()

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🧠 Memory Center"
    )

    if st.session_state.user_name:

        st.write(
            "👤 "
            + st.session_state.user_name
        )

    else:

        st.caption(
            "No name saved."
        )

    st.write(
        "Saved memories: "
        + str(
            len(
                st.session_state.memory_notes
            )
        )
    )

    if st.session_state.memory_notes:

        with st.expander(
            "View memory"
        ):

            for note in (
                st.session_state.memory_notes[
                    -10:
                ]
            ):

                st.write(
                    "• " + str(note)
                )

    if st.session_state.conversation_summary:

        with st.expander(
            "Long conversation memory"
        ):

            st.write(
                st.session_state.conversation_summary
            )

    if st.button(
        "🧠 Clear saved memory",
        use_container_width=True,
    ):

        st.session_state.memory = {}
        st.session_state.memory_notes = []
        st.session_state.user_name = ""

        st.rerun()

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "💾 Conversation"
    )

    st.download_button(
        "⬇️ Download conversation",
        data=build_transcript(),
        file_name="kingsbot_conversation.md",
        mime="text/markdown",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    st.divider()

    st.caption(
        "🧠 Brain: Groq Compound"
    )

    st.caption(
        "💬 Long memory: ON"
    )

    st.caption(
        "🌐 Web: "
        + (
            "ON"
            if st.session_state.web_search
            else "OFF"
        )
    )

    st.caption(
        "💻 Code: "
        + (
            "ON"
            if st.session_state.coding_mode
            else "OFF"
        )
    )

    st.caption(
        "🎤 Voice: ON"
    )


# ============================================================
# MAIN SCREEN
# ============================================================

st.title(
    "🤖 KingsBot AI"
)

st.caption(
    "Real AI brain • Long conversations • "
    "Web • Coding • Files • Voice • Memory"
)


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# VOICE INPUT
# ============================================================

audio_input = st.audio_input(
    "🎤 Record a message",
    sample_rate=16000,
)

voice_text = ""

if audio_input:

    voice_text = transcribe_audio(
        audio_input
    )

if voice_text:

    st.info(
        "You said: "
        + voice_text
    )


# ============================================================
# CHAT INPUT
# ============================================================

text_input = st.chat_input(
    "Ask KingsBot anything..."
)

prompt = voice_text or text_input


# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:

    prompt = str(
        prompt
    ).strip()

    if not prompt:
        st.stop()

    # --------------------------------------------------------
    # LOCAL MEMORY / UNDERSTANDING
    # --------------------------------------------------------

    detect_name(prompt)

    remember_information(
        prompt
    )

    forget_result = (
        forget_information(
            prompt
        )
    )

    st.session_state.topic = (
        detect_topic(prompt)
    )

    st.session_state.emotion = (
        detect_emotion(prompt)
    )

    # --------------------------------------------------------
    # FORGET COMMAND
    # --------------------------------------------------------

    if forget_result:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": forget_result,
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            st.markdown(
                forget_result
            )

        st.rerun()

    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    st.session_state.last_user_prompt = prompt

    with st.chat_message("user"):
        st.markdown(prompt)

    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "⚡ KingsBot is thinking..."
        ):

            try:

                answer, executed_tools = (
                    power_agent(prompt)
                )

            except Exception as exc:

                answer = api_error_message(
                    exc
                )

                executed_tools = None

        st.markdown(
            answer
        )

        show_tools(
            executed_tools
        )

        # Voice.
        if (
            st.session_state.voice_output
            and answer
        ):

            audio = make_voice(
                answer
            )

            if audio:

                st.session_state.last_voice_audio = (
                    audio
                )

                st.audio(
                    audio,
                    format="audio/mp3"
                )

    # --------------------------------------------------------
    # SAVE RESPONSE
    # --------------------------------------------------------

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
    })

    st.session_state.last_answer = answer

    # --------------------------------------------------------
    # UPDATE LONG-TERM MEMORY
    # --------------------------------------------------------

    summarize_old_conversation()

    st.rerun()


# ============================================================
# LAST VOICE RESPONSE
# ============================================================

if (
    st.session_state.last_voice_audio
    and not prompt
):

    st.divider()

    st.caption(
        "🔊 Last voice response"
    )

    st.audio(
        st.session_state.last_voice_audio,
        format="audio/mp3"
    )


# ============================================================
# REGENERATE
# ============================================================

if (
    st.session_state.last_user_prompt
    and st.session_state.messages
):

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔄 Regenerate",
            use_container_width=True,
        ):

            # Remove last assistant answer.
            if (
                st.session_state.messages
                and st.session_state.messages[-1][
                    "role"
                ] == "assistant"
            ):

                st.session_state.messages.pop()

            with st.spinner(
                "⚡ Regenerating..."
            ):

                try:

                    answer, executed_tools = (
                        power_agent(
                            st.session_state.last_user_prompt
                        )
                    )

                except Exception as exc:

                    answer = api_error_message(
                        exc
                    )

                    executed_tools = None

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
            })

            st.session_state.last_answer = answer

            summarize_old_conversation()

            st.rerun()

    with col2:

        st.download_button(
            "💾 Save chat",
            data=build_transcript(),
            file_name="kingsbot_conversation.md",
            mime="text/markdown",
            use_container_width=True,
        )

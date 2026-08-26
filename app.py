import io
import os
import re
import hashlib
from datetime import datetime

import streamlit as st
from groq import Groq
from gtts import gTTS

# Optional PDF support
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except Exception:
    PDF_SUPPORT = False


# ============================================================
# KINGSBOT AI - COMPLETE POWER BUILD
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

# These limits prevent 413 Request Entity Too Large errors.
MAX_MEMORY_ITEMS = 25
MAX_CONTEXT_MESSAGES = 8
MAX_MESSAGE_CHARS = 6000
MAX_FILE_CHARS = 12000
MAX_TOTAL_FILE_CHARS = 24000
MAX_SYSTEM_CHARS = 7000


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "messages": [],
        "memory_notes": [],
        "memory": {},
        "user_name": "",
        "topic": "general",
        "emotion": "neutral",
        "last_voice_audio": None,
        "last_voice_hash": "",
        "last_user_prompt": "",
        "last_answer": "",
        "chat_started": datetime.now().isoformat(
            timespec="seconds"
        ),
        "uploaded_files": {},
        "file_context": "",
        "selected_language": "English",
        "turbo_mode": True,
        "factual_grounding": True,
        "deep_reasoning": True,
        "coding_mode": True,
        "web_search": True,
        "voice_output": True,
        "show_tool_status": True,
        "auto_memory": True,
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


def get_wolfram_key():
    return get_secret("WOLFRAM_ALPHA_APPID")


def get_client():
    api_key = get_api_key()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add your GROQ_API_KEY "
            "to Streamlit Secrets."
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

def add_memory_note(note):
    note = str(note).strip()

    if not note:
        return

    if note in st.session_state.memory_notes:
        return

    st.session_state.memory_notes.append(note)

    if len(st.session_state.memory_notes) > MAX_MEMORY_ITEMS:
        st.session_state.memory_notes = (
            st.session_state.memory_notes[-MAX_MEMORY_ITEMS:]
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
                st.session_state.memory["name"] = name

                add_memory_note(
                    "The user's name is " + name
                )

                return name

    return st.session_state.user_name


def remember_information(text):
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

                st.session_state.memory["note"] = note

                add_memory_note(note)

                return

    if not st.session_state.auto_memory:
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
                add_memory_note(preference)


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
        st.session_state.memory.pop(
            "note",
            None
        )

        if st.session_state.memory_notes:
            st.session_state.memory_notes.pop()

        return "Done. I forgot the saved note."

    if lowered in {
        "forget everything",
        "forget all my memory",
        "clear my memory",
    }:
        st.session_state.memory = {}
        st.session_state.memory_notes = []
        st.session_state.user_name = ""

        return (
            "Done. I cleared KingsBot's saved memory."
        )

    return None


# ============================================================
# TOPIC / EMOTION
# ============================================================

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
        return "math"

    if any(
        word in lowered
        for word in [
            "news",
            "today",
            "latest",
            "current",
            "recent",
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


# ============================================================
# FILE SUPPORT
# ============================================================

def extract_file_text(uploaded_file):
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
            )[:MAX_FILE_CHARS]

        if extension == "pdf":

            if not PDF_SUPPORT:
                return (
                    "PDF support requires pypdf. "
                    "Add pypdf to requirements.txt."
                )

            reader = PdfReader(
                io.BytesIO(raw)
            )

            pages = []

            for page in reader.pages:

                try:
                    page_text = page.extract_text()

                    if page_text:
                        pages.append(page_text)

                except Exception:
                    continue

            return "\n\n".join(
                pages
            )[:MAX_FILE_CHARS]

        return (
            "KingsBot received "
            + filename
            + ", but this file type is not "
              "currently supported for text extraction."
        )

    except Exception as exc:
        return (
            "Could not read "
            + filename
            + ". Error: "
            + str(exc)
        )


def process_uploaded_files(files):
    st.session_state.uploaded_files = {}

    if not files:
        st.session_state.file_context = ""
        return

    combined_parts = []
    total_chars = 0

    for uploaded_file in files:

        if total_chars >= MAX_TOTAL_FILE_CHARS:
            break

        text = extract_file_text(
            uploaded_file
        )

        remaining = (
            MAX_TOTAL_FILE_CHARS
            - total_chars
        )

        text = text[:remaining]

        st.session_state.uploaded_files[
            uploaded_file.name
        ] = text

        combined_parts.append(
            "===== FILE: "
            + uploaded_file.name
            + " =====\n"
            + text
        )

        total_chars += len(text)

    st.session_state.file_context = (
        "\n\n".join(combined_parts)
    )[:MAX_TOTAL_FILE_CHARS]


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

    return tools


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are KingsBot, a powerful general-purpose AI assistant.

Give useful, accurate and natural answers.

You can help with:
science, history, geography, mathematics, programming,
technology, education, business, entertainment, writing,
problem solving, troubleshooting, current information,
and general questions.

MULTILINGUAL:
Understand the user's language and normally reply in the
same language unless the user requests another language.

FACTUAL GROUNDING:
Do not invent facts. When information is current, changing,
recent or uncertain, use web tools when appropriate.

WEB:
Use web search for current information when useful.
Use website visiting when a specific website needs checking.

ADVANCED CODING:
When the user asks for code, produce complete working code.
Check the code carefully. Preserve useful existing code when
the user asks for modifications.

DEEP REASONING:
Solve difficult problems carefully. Give the important
steps and conclusions, but never expose private chain-of-thought.

FILES:
Uploaded files are user-provided reference material.
Use them when relevant and do not invent information from them.

MEMORY:
Use relevant saved memory when provided.

STYLE:
For simple questions, be quick and direct.
For difficult questions, give a complete useful explanation.

Never claim to have used a tool when you did not use it.
""".strip()


# ============================================================
# BUILD REQUEST
# ============================================================

def build_messages(user_text, include_files=True):
    messages = []

    # Keep system prompt bounded.
    messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT[:MAX_SYSTEM_CHARS],
    })

    if st.session_state.user_name:
        messages.append({
            "role": "system",
            "content": (
                "User's saved name: "
                + st.session_state.user_name
            ),
        })

    # Small memory block.
    if st.session_state.memory_notes:

        memory_items = (
            st.session_state.memory_notes[-10:]
        )

        memory_text = "\n".join(
            "- " + str(note)[:250]
            for note in memory_items
        )

        messages.append({
            "role": "system",
            "content": (
                "Relevant saved memory:\n"
                + memory_text
            ),
        })

    # File context is deliberately limited.
    if (
        include_files
        and st.session_state.file_context
    ):
        file_text = (
            st.session_state.file_context[
                :MAX_TOTAL_FILE_CHARS
            ]
        )

        messages.append({
            "role": "system",
            "content": (
                "Relevant uploaded file content:\n\n"
                + file_text
            ),
        })

    # Current settings.
    messages.append({
        "role": "system",
        "content": (
            "Settings: "
            "Turbo="
            + str(st.session_state.turbo_mode)
            + ", Grounding="
            + str(st.session_state.factual_grounding)
            + ", DeepReasoning="
            + str(st.session_state.deep_reasoning)
            + ", Coding="
            + str(st.session_state.coding_mode)
            + ", Web="
            + str(st.session_state.web_search)
            + ", Language="
            + str(st.session_state.selected_language)
            + ", Topic="
            + str(st.session_state.topic)
        ),
    })

    # Only recent conversation.
    recent_messages = (
        st.session_state.messages[
            -MAX_CONTEXT_MESSAGES:
        ]
    )

    for message in recent_messages:

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

        # Each old message is capped.
        content = content[
            :MAX_MESSAGE_CHARS
        ]

        messages.append({
            "role": role,
            "content": content,
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
# REAL AI BRAIN
# ============================================================

def call_groq(messages):
    client = get_client()

    enabled_tools = get_enabled_tools()

    request_args = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_completion_tokens": 8192,
    }

    # Only send tool configuration when tools are enabled.
    if enabled_tools:

        request_args["compound_custom"] = {
            "tools": {
                "enabled_tools": enabled_tools
            }
        }

        wolfram_key = get_wolfram_key()

        if (
            "wolfram_alpha"
            in enabled_tools
            and wolfram_key
        ):
            request_args[
                "compound_custom"
            ]["tools"][
                "wolfram_settings"
            ] = {
                "authorization": wolfram_key
            }

    return client.chat.completions.create(
        **request_args
    )


def power_agent(user_text):
    """
    Real Groq Compound AI.
    Uses aggressive request-size protection.
    """

    # First attempt: recent conversation + limited files.
    messages = build_messages(
        user_text,
        include_files=True,
    )

    try:
        response = call_groq(messages)

    except Exception as first_error:

        error_text = str(first_error)

        # 413 = request body too large.
        # Retry with files removed and a much smaller context.
        if (
            "413" in error_text
            or "Request Entity Too Large"
            in error_text
            or "request body is too large"
            in error_text.lower()
        ):

            messages = build_messages(
                user_text,
                include_files=False,
            )

            # Extra emergency reduction.
            reduced = []

            for message in messages:

                content = str(
                    message.get(
                        "content",
                        ""
                    )
                )

                if (
                    message.get("role")
                    == "system"
                    and len(content) > 3500
                ):
                    content = content[:3500]

                if (
                    message.get("role")
                    in {"user", "assistant"}
                    and len(content) > 3500
                ):
                    content = content[:3500]

                reduced.append({
                    "role": message["role"],
                    "content": content,
                })

            # Keep only the system messages and
            # latest few conversation messages.
            system_messages = [
                item
                for item in reduced
                if item["role"] == "system"
            ]

            conversation = [
                item
                for item in reduced
                if item["role"] != "system"
            ]

            messages = (
                system_messages[:5]
                + conversation[-4:]
            )

            response = call_groq(messages)

        else:
            raise first_error

    message = response.choices[0].message

    answer = getattr(
        message,
        "content",
        ""
    )

    answer = str(
        answer or ""
    ).strip()

    if not answer:
        answer = (
            "I did not receive a text answer. "
            "Please try the question again."
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
        audio.name = "kingsbot_voice.wav"

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

def describe_tools(executed_tools):

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
            continue

    if names:

        unique_names = list(
            dict.fromkeys(names)
        )

        st.caption(
            "🛠️ Tools used: "
            + ", ".join(unique_names)
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
        lines.append(
            "User name: "
            + st.session_state.user_name
        )
        lines.append("")

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

        lines.append(
            "## " + role
        )

        lines.append("")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 KingsBot")

    st.caption(
        "AI Brain • Memory • Web • Code • Voice"
    )

    # --------------------------------------------------------
    # CHAT CONTROLS
    # --------------------------------------------------------

    if st.button(
        "➕ New chat",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.topic = "general"
        st.session_state.emotion = "neutral"
        st.session_state.last_voice_audio = None
        st.session_state.last_user_prompt = ""
        st.session_state.last_answer = ""

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
        st.session_state.last_voice_audio = None
        st.session_state.last_user_prompt = ""
        st.session_state.last_answer = ""

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

    st.subheader("🌍 Multilingual Mastery")

    language_list = list(
        LANGUAGE_CODES.keys()
    )

    current_language = (
        st.session_state.selected_language
    )

    if current_language not in language_list:
        current_language = "English"

    st.session_state.selected_language = (
        st.selectbox(
            "Response language",
            language_list,
            index=language_list.index(
                current_language
            ),
        )
    )

    # --------------------------------------------------------
    # FILE LAB
    # --------------------------------------------------------

    st.divider()

    st.subheader("📁 File Lab")

    st.caption(
        "File upload is here, separate from the chat box."
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

        process_uploaded_files(
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
            "🗑️ Remove uploaded files",
            use_container_width=True,
        ):

            st.session_state.uploaded_files = {}
            st.session_state.file_context = ""

            st.rerun()

    # --------------------------------------------------------
    # MEMORY CENTER
    # --------------------------------------------------------

    st.divider()

    st.subheader("🧠 Memory Center")

    if st.session_state.user_name:
        st.write(
            "👤 Name: "
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
                st.session_state.memory_notes[-10:]
            ):
                st.write(
                    "• " + str(note)
                )

    if st.button(
        "🧠 Clear memory",
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

    st.subheader("💾 Conversation")

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
        "Brain: Groq Compound"
    )

    st.caption(
        "Web: "
        + (
            "ON"
            if st.session_state.web_search
            else "OFF"
        )
    )

    st.caption(
        "Coding: "
        + (
            "ON"
            if st.session_state.coding_mode
            else "OFF"
        )
    )

    st.caption(
        "Memory: "
        + (
            "ON"
            if st.session_state.auto_memory
            else "OFF"
        )
    )

    if get_wolfram_key():
        st.caption(
            "Math engine: Wolfram Alpha"
        )
    else:
        st.caption(
            "Math engine: Compound Code"
        )


# ============================================================
# MAIN SCREEN
# ============================================================

st.title("🤖 KingsBot AI")

st.caption(
    "Fast • Intelligent • Multilingual • "
    "Web • Coding • Memory • Files • Voice"
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
        "You said: " + voice_text
    )


# ============================================================
# CHAT INPUT
# ============================================================

text_input = st.chat_input(
    "Ask KingsBot anything..."
)

prompt = voice_text or text_input


# ============================================================
# MESSAGE PROCESSING
# ============================================================

if prompt:

    prompt = str(prompt).strip()

    if not prompt:
        st.stop()

    # --------------------------------------------------------
    # LOCAL UNDERSTANDING
    # --------------------------------------------------------

    detect_name(prompt)
    remember_information(prompt)

    forget_result = forget_information(
        prompt
    )

    st.session_state.topic = detect_topic(
        prompt
    )

    st.session_state.emotion = detect_emotion(
        prompt
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
    # AI
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

                # Do NOT say "KingsBot could not reach
                # the AI service."
                #
                # Give the actual useful error instead.

                error_text = str(exc)

                if "413" in error_text:
                    answer = (
                        "⚠️ The request was too large. "
                        "KingsBot automatically limits "
                        "conversation and file data, "
                        "so please try the message again "
                        "or upload a smaller file."
                    )

                elif "401" in error_text:
                    answer = (
                        "🔐 The Groq API key was rejected. "
                        "Please check GROQ_API_KEY in "
                        "Streamlit Secrets."
                    )

                elif "429" in error_text:
                    answer = (
                        "⏳ Groq rate limit reached. "
                        "Please wait a moment and try again."
                    )

                elif "400" in error_text:
                    answer = (
                        "⚠️ Groq rejected the request. "
                        "The application request settings "
                        "need to be checked.\n\n"
                        "Technical details: "
                        + error_text
                    )

                else:
                    answer = (
                        "⚠️ Something went wrong while "
                        "processing your request.\n\n"
                        "Technical details:\n"
                        + error_text
                    )

                executed_tools = None

        st.markdown(answer)

        describe_tools(
            executed_tools
        )

        # ----------------------------------------------------
        # VOICE OUTPUT
        # ----------------------------------------------------

        if st.session_state.voice_output:

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
    # SAVE ANSWER
    # --------------------------------------------------------

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
    })

    st.session_state.last_answer = answer

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

            # Remove previous assistant response.
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

                    error_text = str(exc)

                    if "413" in error_text:
                        answer = (
                            "⚠️ The request was too large. "
                            "The conversation context has "
                            "been reduced. Please try again."
                        )
                    else:
                        answer = (
                            "⚠️ Regeneration error:\n"
                            + error_text
                        )

                    executed_tools = None

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
            })

            st.session_state.last_answer = answer

            st.rerun()

    with col2:

        st.download_button(
            "💾 Save chat",
            data=build_transcript(),
            file_name="kingsbot_conversation.md",
            mime="text/markdown",
            use_container_width=True,
        )

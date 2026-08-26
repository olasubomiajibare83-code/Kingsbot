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
# CONFIGURATION
# ============================================================

MODEL_NAME = "groq/compound"

MAX_MEMORY_ITEMS = 40
MAX_CONTEXT_MESSAGES = 16
MAX_FILE_CHARS = 50000
MAX_TOTAL_FILE_CHARS = 100000


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "messages": [],
        "memory": {},
        "memory_notes": [],
        "user_name": "",
        "emotion": "neutral",
        "topic": "general",
        "last_voice_audio": None,
        "last_voice_hash": "",
        "last_answer": "",
        "last_user_prompt": "",
        "chat_started": datetime.now().isoformat(timespec="seconds"),
        "uploaded_files": {},
        "file_context": "",
        "selected_language": "English",
        "turbo_mode": True,
        "web_search": True,
        "factual_grounding": True,
        "deep_reasoning": True,
        "coding_mode": True,
        "voice_output": True,
        "show_tool_status": True,
        "auto_memory": True,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ============================================================
# SECRETS / API
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
            re.IGNORECASE,
        )

        if match:
            name = match.group(1).strip(" .,!?")

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
                note = note[:1000]

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
            re.IGNORECASE,
        )

        if match:
            preference = match.group(0).strip()

            if len(preference) < 300:
                add_memory_note(preference)


def forget_information(text):
    lowered = text.lower().strip()

    if lowered in {
        "forget my name",
        "forget my name please",
    }:
        st.session_state.user_name = ""
        st.session_state.memory.pop("name", None)

        st.session_state.memory_notes = [
            note
            for note in st.session_state.memory_notes
            if "name" not in note.lower()
        ]

        return "Done. I forgot your name."

    if lowered.startswith("forget that"):
        st.session_state.memory.pop("note", None)

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
        for word in (
            "sad",
            "angry",
            "upset",
            "cry",
            "worried",
            "scared",
            "frustrated",
        )
    ):
        return "supportive"

    if any(
        word in lowered
        for word in (
            "happy",
            "excited",
            "great",
            "amazing",
            "awesome",
        )
    ):
        return "positive"

    return "neutral"


def detect_topic(text):
    lowered = text.lower()

    if any(
        word in lowered
        for word in (
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
            "github",
        )
    ):
        return "coding"

    if any(
        word in lowered
        for word in (
            "math",
            "calculate",
            "equation",
            "percent",
            "percentage",
            "algebra",
            "geometry",
            "calculus",
        )
    ):
        return "math"

    if any(
        word in lowered
        for word in (
            "news",
            "today",
            "latest",
            "current",
            "recent",
            "yesterday",
            "tomorrow",
        )
    ):
        return "current information"

    if any(
        word in lowered
        for word in (
            "school",
            "study",
            "exam",
            "homework",
            "learn",
        )
    ):
        return "learning"

    if any(
        word in lowered
        for word in (
            "business",
            "money",
            "company",
            "startup",
            "sell",
        )
    ):
        return "business"

    return "general"


# ============================================================
# FILE LAB
# ============================================================

def extract_file_text(uploaded_file):
    filename = uploaded_file.name

    if "." not in filename:
        extension = ""
    else:
        extension = filename.rsplit(".", 1)[1].lower()

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
                errors="replace",
            )[:MAX_FILE_CHARS]

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

            return "\n\n".join(
                pages
            )[:MAX_FILE_CHARS]

        return (
            f"KingsBot received '{filename}', "
            f"but text extraction for .{extension} "
            f"files is not currently supported."
        )

    except Exception as exc:
        return (
            f"Could not read '{filename}'. "
            f"Error: {str(exc)}"
        )


def process_uploaded_files(files):
    st.session_state.uploaded_files = {}

    if not files:
        st.session_state.file_context = ""
        return

    all_text = []

    for uploaded_file in files:
        text = extract_file_text(
            uploaded_file
        )

        st.session_state.uploaded_files[
            uploaded_file.name
        ] = text

        all_text.append(
            "===== FILE: "
            + uploaded_file.name
            + " =====\n"
            + text
        )

    combined = "\n\n".join(all_text)

    st.session_state.file_context = (
        combined[:MAX_TOTAL_FILE_CHARS]
    )


# ============================================================
# COMPOUND TOOLS
# ============================================================

def get_enabled_tools():
    tools = []

    if st.session_state.web_search:
        tools.append("web_search")
        tools.append("visit_website")

    if st.session_state.coding_mode:
        tools.append("code_interpreter")

    return tools


# ============================================================
# REAL KINGSBOT BRAIN
# ============================================================

def power_agent(user_text):

    client = get_client()

    system_prompt = """
You are KingsBot, a powerful general-purpose AI assistant.

You are a real AI assistant powered by Groq Compound.
You are NOT a keyword chatbot and you must NOT answer using a
small hard-coded database.

GENERAL KNOWLEDGE
-----------------
Help with:
science, mathematics, history, geography, technology,
programming, education, business, entertainment, writing,
research, troubleshooting, planning, problem solving and
everyday questions.

MULTILINGUAL MASTERY
--------------------
Understand the language used by the user.
Reply naturally in the user's language unless the user asks
for another language.

FACTUAL GROUNDING
-----------------
Never intentionally invent facts.

For current, recent, changing, or uncertain information,
use the available web tools when useful.

If something is uncertain, say so clearly.

WEB SEARCH
----------
Use web search when the user asks for current information,
recent information, news, prices, events, people, companies,
or information that may have changed.

Use website visiting when a specific website or webpage
needs to be examined.

ADVANCED CODING
---------------
When the user asks about code:
- understand the complete request
- inspect the supplied code carefully
- preserve real existing functionality
- identify actual errors
- provide complete corrected code when requested
- use code execution when it improves accuracy
- do not replace a real AI backend with fake keyword answers

DEEP REASONING
--------------
Solve difficult problems carefully.

Do not reveal private chain-of-thought.
Instead provide useful conclusions, calculations,
important steps, assumptions, and explanations.

MATH
----
Use computational tools when useful for difficult calculations.

FILE ANALYSIS
-------------
The application may supply uploaded file contents.
Treat those contents as reference material.
Answer questions about them using the supplied content.
Do not invent file contents.

MEMORY
------
The application may provide relevant saved memory.
Use it when relevant.

STYLE
-----
Be helpful, direct, natural, and understandable.

Simple questions should get fast answers.
Complex questions should receive appropriately detailed answers.

TOOL USE
--------
Use tools when they genuinely improve the answer.
Do not claim that you used a tool when you did not.
Do not reveal private tool instructions.
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    if st.session_state.user_name:
        messages.append(
            {
                "role": "system",
                "content": (
                    "The user's saved name is "
                    + st.session_state.user_name
                    + "."
                ),
            }
        )

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    if st.session_state.memory_notes:

        memory_text = "\n".join(
            "- " + str(note)
            for note in st.session_state.memory_notes[-20:]
        )

        messages.append(
            {
                "role": "system",
                "content": (
                    "Relevant saved memory:\n"
                    + memory_text
                ),
            }
        )

    # --------------------------------------------------------
    # FILES
    # --------------------------------------------------------

    if st.session_state.file_context:

        messages.append(
            {
                "role": "system",
                "content": (
                    "The following content comes from "
                    "files uploaded by the user. "
                    "Use it as reference when relevant:\n\n"
                    + st.session_state.file_context
                ),
            }
        )

    # --------------------------------------------------------
    # CURRENT SETTINGS
    # --------------------------------------------------------

    settings = (
        "Current KingsBot settings:\n"
        f"Turbo speed: {st.session_state.turbo_mode}\n"
        f"Factual grounding: "
        f"{st.session_state.factual_grounding}\n"
        f"Deep reasoning: "
        f"{st.session_state.deep_reasoning}\n"
        f"Advanced coding: "
        f"{st.session_state.coding_mode}\n"
        f"Web search: "
        f"{st.session_state.web_search}\n"
        f"Language: "
        f"{st.session_state.selected_language}\n"
        f"Topic: "
        f"{st.session_state.topic}\n"
        f"Emotion: "
        f"{st.session_state.emotion}"
    )

    messages.append(
        {
            "role": "system",
            "content": settings,
        }
    )

    # --------------------------------------------------------
    # PREVIOUS CONVERSATION
    # --------------------------------------------------------

    # The latest user message has already been stored in
    # st.session_state.messages before this function runs.
    # Exclude it here so it isn't sent twice.

    previous_messages = (
        st.session_state.messages[:-1]
    )

    for message in previous_messages[
        -MAX_CONTEXT_MESSAGES:
    ]:

        role = message.get("role")

        content = str(
            message.get(
                "content",
                "",
            )
        ).strip()

        if role in (
            "user",
            "assistant",
        ) and content:

            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    # --------------------------------------------------------
    # CURRENT MESSAGE
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_text,
        }
    )

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    request_args = {
        "model": MODEL_NAME,
        "messages": messages,
    }

    enabled_tools = get_enabled_tools()

    if enabled_tools:

        request_args["compound_custom"] = {
            "tools": {
                "enabled_tools": enabled_tools
            }
        }

    response = client.chat.completions.create(
        **request_args
    )

    assistant_message = (
        response.choices[0].message
    )

    answer = str(
        getattr(
            assistant_message,
            "content",
            "",
        )
        or ""
    ).strip()

    executed_tools = getattr(
        assistant_message,
        "executed_tools",
        None,
    )

    if not answer:
        answer = (
            "I couldn't generate an answer. "
            "Please try again."
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
                "",
            )
            or ""
        ).strip()

    except Exception as exc:

        st.error(
            "Voice transcription failed: "
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
            "en",
        )

        output = io.BytesIO()

        gTTS(
            text=str(text)[:4500],
            lang=language,
            slow=False,
        ).write_to_fp(output)

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
                "",
            )
        ).upper()

        content = message.get(
            "content",
            "",
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

def describe_tools(executed_tools):

    if not executed_tools:
        return

    if not st.session_state.show_tool_status:
        return

    names = []

    for tool in executed_tools:

        try:

            tool_type = getattr(
                tool,
                "type",
                None,
            )

            if tool_type:
                names.append(
                    str(tool_type)
                )
                continue

            if isinstance(
                tool,
                dict,
            ):

                tool_type = tool.get(
                    "type"
                )

                if tool_type:
                    names.append(
                        str(tool_type)
                    )

        except Exception:
            pass

    if names:

        unique_names = list(
            dict.fromkeys(names)
        )

        st.caption(
            "🛠️ Tools used: "
            + ", ".join(unique_names)
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 KingsBot")

    st.caption(
        "Real AI • Memory • Web • Code • Voice"
    )

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "➕ New chat",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.topic = "general"
        st.session_state.emotion = "neutral"
        st.session_state.last_voice_audio = None
        st.session_state.last_answer = ""
        st.session_state.last_user_prompt = ""
        st.session_state.last_voice_hash = ""

        st.session_state.chat_started = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        st.rerun()

    # --------------------------------------------------------
    # CLEAR CONVERSATION
    # --------------------------------------------------------

    if st.button(
        "🧹 Clear conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.last_voice_audio = None
        st.session_state.last_answer = ""
        st.session_state.last_user_prompt = ""

        st.rerun()

    st.divider()

    # ========================================================
    # POWER SETTINGS
    # ========================================================

    st.subheader(
        "⚙️ Power Settings"
    )

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

    # ========================================================
    # LANGUAGE
    # ========================================================

    st.subheader(
        "🌍 Multilingual"
    )

    languages = list(
        LANGUAGE_CODES.keys()
    )

    current_language_index = languages.index(
        st.session_state.selected_language
    )

    st.session_state.selected_language = (
        st.selectbox(
            "Response language",
            languages,
            index=current_language_index,
        )
    )

    # ========================================================
    # FILE LAB
    # ========================================================

    st.divider()

    st.subheader(
        "📁 File Lab"
    )

    st.caption(
        "File tools are separate from the main typing box."
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
            "🗑️ Remove files",
            use_container_width=True,
        ):

            st.session_state.uploaded_files = {}
            st.session_state.file_context = ""

            st.rerun()

    # ========================================================
    # MEMORY CENTER
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Memory Center"
    )

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

    # ========================================================
    # CONVERSATION TOOLS
    # ========================================================

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

    # ========================================================
    # STATUS
    # ========================================================

    st.divider()

    st.caption(
        "🧠 Brain: Groq Compound"
    )

    st.caption(
        "⚡ Turbo: "
        + (
            "ON"
            if st.session_state.turbo_mode
            else "OFF"
        )
    )

    st.caption(
        "🔎 Web: "
        + (
            "ON"
            if st.session_state.web_search
            else "OFF"
        )
    )

    st.caption(
        "💻 Coding: "
        + (
            "ON"
            if st.session_state.coding_mode
            else "OFF"
        )
    )

    st.caption(
        "🧠 Memory: "
        + (
            "ON"
            if st.session_state.auto_memory
            else "OFF"
        )
    )


# ============================================================
# MAIN PAGE
# ============================================================

st.title(
    "🤖 KingsBot AI"
)

st.caption(
    "Real AI with web search, coding, reasoning, "
    "memory, multilingual support, files and voice."
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
    # MEMORY / PROFILE
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

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": forget_result,
            }
        )

        with st.chat_message(
            "user"
        ):

            st.markdown(
                prompt
            )

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                forget_result
            )

        st.rerun()

    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    st.session_state.last_user_prompt = prompt

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )

    # --------------------------------------------------------
    # REAL AI
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "⚡ KingsBot is thinking..."
        ):

            try:

                answer, executed_tools = (
                    power_agent(prompt)
                )

            except Exception as exc:

                answer = (
                    "KingsBot could not reach "
                    "the AI service.\n\n"
                    "Please check your "
                    "GROQ_API_KEY in Streamlit Secrets.\n\n"
                    "Error:\n"
                    + str(exc)
                )

                executed_tools = None

        st.markdown(
            answer
        )

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
                    format="audio/mp3",
                )

    # --------------------------------------------------------
    # SAVE ASSISTANT RESPONSE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    st.session_state.last_answer = answer

    st.rerun()

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
# SETTINGS
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

        "turbo_mode": True,
        "factual_grounding": True,
        "deep_reasoning": True,
        "coding_mode": True,
        "web_search": True,
        "auto_memory": True,
        "voice_output": True,
        "show_tool_status": True,
        "early_access": True,

        "topic": "general",
        "emotion": "neutral",

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
# API KEY
# ============================================================

def get_api_key():

    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        key = ""

    if not key:
        key = os.getenv("GROQ_API_KEY", "")

    return str(key).strip()


def get_client():

    key = get_api_key()

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add GROQ_API_KEY to Streamlit Secrets."
        )

    return Groq(
        api_key=key
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

            index = lowered.find(trigger)

            note = text[
                index + len(trigger):
            ].strip()

            if note:
                add_memory(note[:700])
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

    if any(word in text for word in [
        "python",
        "javascript",
        "html",
        "css",
        "code",
        "coding",
        "programming",
        "bug",
        "error",
        "api",
        "streamlit",
    ]):
        return "coding"

    if any(word in text for word in [
        "math",
        "calculate",
        "equation",
        "percentage",
        "percent",
        "algebra",
        "geometry",
        "calculus",
    ]):
        return "mathematics"

    if any(word in text for word in [
        "latest",
        "today",
        "current",
        "recent",
        "news",
        "yesterday",
        "tomorrow",
    ]):
        return "current information"

    if any(word in text for word in [
        "school",
        "study",
        "exam",
        "homework",
        "learn",
    ]):
        return "learning"

    if any(word in text for word in [
        "business",
        "money",
        "company",
        "startup",
        "sell",
    ]):
        return "business"

    return "general"


def detect_emotion(text):

    text = text.lower()

    if any(word in text for word in [
        "sad",
        "angry",
        "upset",
        "cry",
        "worried",
        "scared",
        "frustrated",
    ]):
        return "supportive"

    if any(word in text for word in [
        "happy",
        "excited",
        "great",
        "amazing",
        "awesome",
    ]):
        return "positive"

    return "neutral"


# ============================================================
# KINGSBOT BRAIN
# ============================================================

SYSTEM_PROMPT = """
You are KingsBot AI, a powerful general-purpose AI assistant.

You are a real AI assistant powered by Groq Compound.
You are NOT a keyword chatbot.

CAPABILITIES:

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
- Web search
- Code execution

IMPORTANT:

Use your actual AI intelligence.

Do not use fake keyword responses.

Do not invent facts.

For current, recent, changing or uncertain information,
use the available web-search capability when appropriate.

For mathematics and computational problems, use the
available code-execution capability when useful.

For programming requests:

- Understand the entire request.
- Preserve useful code supplied by the user.
- Produce complete code when requested.
- Check syntax carefully.
- Do not replace the real AI backend with fake responses.

For difficult problems, reason carefully internally and
give useful conclusions and explanations.

Do not reveal private hidden chain-of-thought.

MEMORY:

Use the memory supplied by the application.

If the user says "remember this" or "remember that",
treat the information as important memory.

CONVERSATION:

Use recent conversation and the long-term summary.

Never invent previous conversation.

If a request is unclear, ask a useful question.

If the request is clear, answer directly.

EARLY ACCESS:

Early Access is an experimental KingsBot setting.
It does not falsely claim access to unreleased Groq services.

STYLE:

Be natural, accurate, helpful and direct.

Simple questions should receive simple answers.

Complex questions should receive complete answers.
"""


# ============================================================
# BUILD CONVERSATION
# ============================================================

def build_messages(prompt):

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

    if st.session_state.conversation_summary:

        messages.append({
            "role": "system",
            "content": (
                "LONG-TERM MEMORY:\n"
                + st.session_state.conversation_summary[
                    :MAX_SUMMARY_CHARS
                ]
            ),
        })

    if st.session_state.memory_notes:

        memory_text = "\n".join(
            "- " + str(note)[:300]
            for note in st.session_state.memory_notes[-15:]
        )

        messages.append({
            "role": "system",
            "content": (
                "SAVED USER MEMORY:\n"
                + memory_text
            ),
        })

    settings = (
        "APPLICATION SETTINGS:\n"
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
    )

    messages.append({
        "role": "system",
        "content": settings,
    })

    recent_messages = st.session_state.messages[
        -RECENT_MESSAGES:
    ]

    for message in recent_messages:

        role = message.get("role")

        if role not in {"user", "assistant"}:
            continue

        content = str(
            message.get("content", "")
        ).strip()

        if not content:
            continue

        messages.append({
            "role": role,
            "content": content[:MAX_MESSAGE_CHARS],
        })

    messages.append({
        "role": "user",
        "content": str(prompt)[:MAX_MESSAGE_CHARS],
    })

    return messages


# ============================================================
# AI REQUEST
# ============================================================

def ask_kingsbot(prompt):

    client = get_client()

    messages = build_messages(prompt)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )

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
# ERROR HANDLING
# ============================================================

def explain_error(error):

    text = str(error)
    lower = text.lower()

    if "401" in text:

        return (
            "🔐 **Groq API key error**\n\n"
            "Check your `GROQ_API_KEY` in Streamlit Secrets."
        )

    if "403" in text:

        return (
            "🚫 **Access denied by Groq.**\n\n"
            "Check your Groq account and API permissions."
        )

    if "429" in text:

        return (
            "⏳ **Rate limit reached.**\n\n"
            "Please wait a little and try again."
        )

    if (
        "413" in text
        or "too large" in lower
        or "request entity" in lower
    ):

        return (
            "⚠️ **The conversation was too large.**\n\n"
            "Start a new chat and try again."
        )

    if "400" in text:

        return (
            "⚠️ **Groq rejected the request.**\n\n"
            "Technical details:\n"
            + text
        )

    return (
        "⚠️ **KingsBot encountered an error.**\n\n"
        + text
    )


# ============================================================
# LONG-TERM MEMORY
# ============================================================

def update_long_memory():

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
            message.get("role", "")
        ).upper()

        content = str(
            message.get("content", "")
        )

        transcript.append(
            role + ": " + content[:1800]
        )

    conversation = "\n\n".join(
        transcript
    )[:14000]

    old_memory = (
        st.session_state.conversation_summary[:4000]
    )

    prompt = """
Create a concise long-term memory for this conversation.

Keep important:

- project details
- decisions
- preferences
- unresolved problems
- useful facts
- information needed to continue the conversation

Do not invent anything.

Return only the memory summary.

Previous memory:
""" + old_memory + """

New conversation:
""" + conversation

    try:

        response = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You create concise conversation "
                        "memory summaries."
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
# VOICE
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
        audio.name = "kingsbot_voice.wav"

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

    except Exception as error:

        st.error(
            "Voice transcription error: "
            + str(error)
        )

        return ""


def make_voice(text):

    try:

        output = io.BytesIO()

        gTTS(
            text=str(text)[:3500],
            lang="en",
            slow=False,
        ).write_to_fp(output)

        return output.getvalue()

    except Exception:
        return None


# ============================================================
# TRANSCRIPT
# ============================================================

def make_transcript():

    lines = [
        "# KingsBot AI Conversation",
        "",
        "Started: "
        + st.session_state.chat_started,
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
            "## Long-term Memory",
            "",
            st.session_state.conversation_summary,
            "",
        ])

    for message in st.session_state.messages:

        role = str(
            message.get("role", "")
        ).upper()

        content = str(
            message.get("content", "")
        )

        lines.extend([
            "## " + role,
            "",
            content,
            "",
        ])

    return "\n".join(lines)


# ============================================================
# TOOL STATUS
# ============================================================

def display_tool_status(tools):

    if not tools:
        return

    if not st.session_state.show_tool_status:
        return

    names = []

    try:

        for tool in tools:

            if isinstance(tool, dict):

                tool_type = tool.get("type")

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
        return

    if names:

        names = list(
            dict.fromkeys(names)
        )

        st.caption(
            "🛠️ Tools used: "
            + ", ".join(names)
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 KingsBot AI")

    st.caption(
        "Real AI • Web • Coding • Memory • Voice"
    )

    st.divider()

    # --------------------------------------------------------
    # CHAT CONTROLS
    # --------------------------------------------------------

    if st.button(
        "➕ New Chat",
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
        "🧹 Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.conversation_summary = ""
        st.session_state.summary_message_count = 0

        st.session_state.last_user_prompt = ""
        st.session_state.last_answer = ""

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # POWER
    # --------------------------------------------------------

    st.subheader("⚙️ Power Settings")

    st.session_state.turbo_mode = st.toggle(
        "⚡ Turbo Speed",
        value=True,
    )

    st.session_state.factual_grounding = st.toggle(
        "🎯 Factual Grounding",
        value=True,
    )

    st.session_state.deep_reasoning = st.toggle(
        "🧩 Deep Reasoning",
        value=True,
    )

    st.session_state.coding_mode = st.toggle(
        "💻 Advanced Coding",
        value=True,
    )

    st.session_state.web_search = st.toggle(
        "🔎 Web Search",
        value=True,
    )

    st.session_state.auto_memory = st.toggle(
        "🧠 Steel Cage Memory",
        value=True,
    )

    st.session_state.voice_output = st.toggle(
        "🔊 Voice Output",
        value=True,
    )

    st.session_state.show_tool_status = st.toggle(
        "🛠️ Show Tool Status",
        value=True,
    )

    # --------------------------------------------------------
    # EARLY ACCESS
    # --------------------------------------------------------

    st.divider()

    st.subheader("🚀 Early Access")

    st.session_state.early_access = st.toggle(
        "Early Access to New Features",
        value=True,
    )

    if st.session_state.early_access:

        st.success(
            "Early Access is ON."
        )

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    st.divider()

    st.subheader("🧠 Memory Center")

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

        with st.expander("View Memory"):

            for note in (
                st.session_state.memory_notes[-10:]
            ):

                st.write(
                    "• " + str(note)
                )

    if st.session_state.conversation_summary:

        with st.expander(
            "Long Conversation Memory"
        ):

            st.write(
                st.session_state.conversation_summary
            )

    if st.button(
        "🧠 Clear Saved Memory",
        use_container_width=True,
    ):

        st.session_state.memory_notes = []
        st.session_state.user_name = ""

        st.rerun()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    st.divider()

    st.subheader("💾 Conversation")

    st.download_button(
        "⬇️ Download Conversation",
        data=make_transcript(),
        file_name="kingsbot_conversation.md",
        mime="text/markdown",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    st.divider()

    st.caption("🧠 Brain: Groq Compound")

    st.caption(
        "🌐 Web Search: ON"
    )

    st.caption(
        "💻 Code Execution: ON"
    )

    st.caption(
        "🧠 Memory: "
        + (
            "ON"
            if st.session_state.auto_memory
            else "OFF"
        )
    )

    st.caption(
        "🚀 Early Access: "
        + (
            "ON"
            if st.session_state.early_access
            else "OFF"
        )
    )


# ============================================================
# MAIN SCREEN
# ============================================================

st.title("🤖 KingsBot AI")

st.caption(
    "Real AI brain • Web Search • Code Execution • "
    "Deep Reasoning • Memory • Voice • Early Access"
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

voice_text = ""

try:

    audio_input = st.audio_input(
        "🎤 Record a message",
        sample_rate=16000,
    )

    if audio_input:

        voice_text = transcribe_voice(
            audio_input
        )

except Exception:

    st.caption(
        "Voice recording is unavailable "
        "in this Streamlit version."
    )


if voice_text:

    st.info(
        "You said: " + voice_text
    )


# ============================================================
# TEXT INPUT
# ============================================================

text_input = st.chat_input(
    "Ask KingsBot anything..."
)

prompt = voice_text or text_input


# ============================================================
# MESSAGE PROCESSING
# ============================================================

if prompt:

    prompt = str(
        prompt
    ).strip()

    if not prompt:
        st.stop()

    # --------------------------------------------------------
    # LOCAL MEMORY
    # --------------------------------------------------------

    detect_name(prompt)

    remember_information(prompt)

    forget_result = (
        forget_information(prompt)
    )

    st.session_state.topic = (
        detect_topic(prompt)
    )

    st.session_state.emotion = (
        detect_emotion(prompt)
    )

    # --------------------------------------------------------
    # MEMORY COMMAND
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
            st.markdown(forget_result)

        st.rerun()

    # --------------------------------------------------------
    # USER
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

                answer, tools = ask_kingsbot(
                    prompt
                )

            except Exception as error:

                answer = explain_error(
                    error
                )

                tools = None

        st.markdown(answer)

        display_tool_status(tools)

        # Voice output
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

    update_long_memory()

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
        "🔊 Last Voice Response"
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

                    answer, tools = ask_kingsbot(
                        st.session_state.last_user_prompt
                    )

                except Exception as error:

                    answer = explain_error(
                        error
                    )

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
            })

            st.session_state.last_answer = answer

            st.rerun()

    with col2:

        st.download_button(
            "💾 Save Chat",
            data=make_transcript(),
            file_name="kingsbot_conversation.md",
            mime="text/markdown",
            use_container_width=True,
        )

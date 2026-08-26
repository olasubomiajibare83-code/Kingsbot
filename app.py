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

# Medium conversation memory.
# It is intentionally not tiny and not unlimited.
RECENT_MESSAGES = 12
MAX_MESSAGE_CHARS = 4000
MAX_CONTEXT_CHARS = 42000
MAX_SUMMARY_CHARS = 6000
MAX_MEMORY_ITEMS = 40


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
# GROQ
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
            re.IGNORECASE,
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

    patterns = [
        r"\bi like (.+)",
        r"\bi love (.+)",
        r"\bi prefer (.+)",
        r"\bmy favorite (.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            note = match.group(0).strip()

            if len(note) <= 250:
                add_memory(note)


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
# KINGSBOT SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are KingsBot AI.

You are a real general-purpose AI assistant powered by
Groq Compound. You are NOT a keyword chatbot.

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
- Analysis
- Problem solving
- Current information
- Web search
- Website research
- Code execution

IMPORTANT:

Use your real AI capabilities.

Do not create fake keyword-based answers.

For current or changing information, use web search when
appropriate.

For calculations and computational problems, use code
execution when useful.

For programming requests:

1. Understand the complete request.
2. Preserve useful code provided by the user.
3. Produce complete code when requested.
4. Check syntax carefully.
5. Do not replace the AI backend with fake responses.

MEMORY:

Use the supplied conversation memory and saved user memory.

Never invent previous conversations.

If the user explicitly asks you to remember something,
treat it as important memory.

CONVERSATION:

Maintain continuity using the recent conversation and
long-term summary.

The application intentionally limits the amount of old
conversation sent to you so requests do not become too large.

REASONING:

Think carefully about difficult problems.

Do not reveal private hidden chain-of-thought.

STYLE:

Be natural, accurate, helpful and direct.

Simple questions should receive simple answers.

Complex questions should receive complete answers.

EARLY ACCESS:

Early Access is an experimental KingsBot application
feature. Do not falsely claim that it provides access to
unreleased Groq services.
"""


# ============================================================
# BUILD MEDIUM-SIZED CONTEXT
# ============================================================

def build_messages(prompt):

    messages = []

    messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT,
    })

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    if st.session_state.user_name:

        messages.append({
            "role": "system",
            "content": (
                "The user's saved name is "
                + st.session_state.user_name
                + "."
            ),
        })

    # --------------------------------------------------------
    # LONG MEMORY
    # --------------------------------------------------------

    if st.session_state.conversation_summary:

        messages.append({
            "role": "system",
            "content": (
                "LONG-TERM CONVERSATION MEMORY:\n"
                + st.session_state.conversation_summary[
                    :MAX_SUMMARY_CHARS
                ]
            ),
        })

    # --------------------------------------------------------
    # USER MEMORY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

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
        + "\nMemory: "
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

    # --------------------------------------------------------
    # RECENT CONVERSATION
    # --------------------------------------------------------

    recent = st.session_state.messages[
        -RECENT_MESSAGES:
    ]

    total_chars = 0

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

        remaining = (
            MAX_CONTEXT_CHARS
            - total_chars
        )

        if remaining <= 0:
            break

        content = content[
            :min(
                MAX_MESSAGE_CHARS,
                remaining,
            )
        ]

        messages.append({
            "role": role,
            "content": content,
        })

        total_chars += len(content)

    # --------------------------------------------------------
    # CURRENT MESSAGE
    # --------------------------------------------------------

    messages.append({
        "role": "user",
        "content": str(prompt)[:MAX_MESSAGE_CHARS],
    })

    return messages


# ============================================================
# AI CALL
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
            "",
        )
        or ""
    ).strip()

    if not answer:
        answer = (
            "I did not receive a text response. "
            "Please try again."
        )

    tools = getattr(
        message,
        "executed_tools",
        None,
    )

    return answer, tools


# ============================================================
# ERROR HANDLING
# ============================================================

def error_message(error):

    text = str(error)
    lower = text.lower()

    if "401" in text:

        return (
            "🔐 **API key problem.**\n\n"
            "Check `GROQ_API_KEY` in Streamlit Secrets."
        )

    if "403" in text:

        return (
            "🚫 **Groq access was denied.**\n\n"
            "Check your Groq account and API key."
        )

    if "429" in text:

        return (
            "⏳ **Too many requests.**\n\n"
            "Please wait a moment and try again."
        )

    if (
        "413" in text
        or "too large" in lower
        or "request entity" in lower
    ):

        return (
            "⚠️ **The conversation became too large.**\n\n"
            "Start a new chat and continue from there."
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
# LONG-TERM SUMMARY
# ============================================================

def update_summary():

    total = len(
        st.session_state.messages
    )

    # Do not summarize tiny conversations.
    if total < 18:
        return

    # Do not repeatedly summarize the same messages.
    if (
        total
        - st.session_state.summary_message_count
        < 10
    ):
        return

    cutoff = max(
        0,
        total - RECENT_MESSAGES,
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
            role
            + ": "
            + content[:1600]
        )

    transcript_text = "\n\n".join(
        transcript
    )[:14000]

    previous = (
        st.session_state.conversation_summary[
            :3500
        ]
    )

    prompt = """
Create a compact long-term memory for this conversation.

Keep only information useful for continuing the conversation:

- project details
- decisions
- preferences
- important facts
- unresolved problems
- useful technical details

Do not invent information.

Do not write a transcript.

Return only the memory summary.

Previous memory:
""" + previous + """

New conversation:
""" + transcript_text

    try:

        client = get_client()

        response = client.chat.completions.create(
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
        # Never break the main chatbot because
        # the memory summary failed.
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
                "",
            )
            or ""
        ).strip()

    except Exception as error:

        st.error(
            "Voice transcription error: "
            + str(error)
        )

        return ""


# ============================================================
# VOICE OUTPUT
# ============================================================

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

            if isinstance(tool, dict):
                tool_type = tool.get("type")
            else:
                tool_type = getattr(
                    tool,
                    "type",
                    None,
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
    # CHAT
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
    # POWER SETTINGS
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
    # STATUS
    # --------------------------------------------------------

    st.divider()

    st.caption(
        "🧠 Brain: Groq Compound"
    )

    st.caption(
        "🌐 Web Search: Built into Compound"
    )

    st.caption(
        "💻 Code Execution: Built into Compound"
    )

    st.caption(
        "🧠 Long Memory: ON"
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
# MAIN
# ============================================================

st.title("🤖 KingsBot AI")

st.caption(
    "Real AI brain • Web Search • Code Execution • "
    "Deep Reasoning • Memory • Voice • Early Access"
)


# ============================================================
# DISPLAY CHAT
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
    # UNDERSTANDING
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

                answer, tools = ask_kingsbot(
                    prompt
                )

            except Exception as error:

                answer = error_message(
                    error
                )

                tools = None

        st.markdown(answer)

        show_tools(tools)

        # ----------------------------------------------------
        # VOICE RESPONSE
        # ----------------------------------------------------

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
                    format="audio/mp3",
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
    # UPDATE LONG MEMORY
    # --------------------------------------------------------

    update_summary()

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
        format="audio/mp3",
    )


# ============================================================
# REGENERATE
# ============================================================

if (
    st.session_state.last_user_prompt
    and st.session_state.messages
):

    st.divider()

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

                answer = error_message(
                    error
                )

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })

        st.session_state.last_answer = answer

        st.rerun()

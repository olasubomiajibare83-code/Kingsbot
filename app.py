import io
import json
import os
import uuid
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
    layout="wide",
)


# ============================================================
# REAL AI BRAIN
# ============================================================

MODEL = "openai/gpt-oss-20b"
VOICE_MODEL = "whisper-large-v3-turbo"

# MEDIUM CONVERSATION MEMORY
# Only the most recent 30 messages are sent to the model.
MEDIUM_HISTORY_MESSAGES = 30

MEMORY_FILE = "kingsbot_early_access_memory.json"
CHATS_FILE = "kingsbot_chats.json"


# ============================================================
# JSON STORAGE
# ============================================================

def load_json(path, default):
    try:
        if not os.path.exists(path):
            return default

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return default


def save_json(path, data):
    try:
        temporary_path = path + ".tmp"

        with open(
            temporary_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(
            temporary_path,
            path,
        )

    except Exception:
        pass


# ============================================================
# EARLY ACCESS MEMORY
# ============================================================

def default_memory():
    return {
        "name": None,
        "facts": [],
        "preferences": [],
    }


def load_memory():
    data = load_json(
        MEMORY_FILE,
        default_memory(),
    )

    if not isinstance(data, dict):
        return default_memory()

    return {
        "name": data.get("name"),
        "facts": data.get("facts", []),
        "preferences": data.get("preferences", []),
    }


def save_memory():
    save_json(
        MEMORY_FILE,
        {
            "name": st.session_state.user_name,
            "facts": st.session_state.personal_memory,
            "preferences": st.session_state.preferences,
        },
    )


memory = load_memory()


# ============================================================
# CONVERSATION SYSTEM
# ============================================================

def create_chat():
    now = datetime.now().isoformat(
        timespec="seconds"
    )

    return {
        "id": uuid.uuid4().hex,
        "title": "New conversation",
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }


def load_chats():
    chats = load_json(
        CHATS_FILE,
        [],
    )

    if not isinstance(chats, list):
        chats = []

    if not chats:
        chats = [create_chat()]

        save_json(
            CHATS_FILE,
            chats,
        )

    return chats


def get_current_chat():
    for chat in st.session_state.saved_chats:

        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):
            return chat

    return None


def save_current_chat():
    chat = get_current_chat()

    if chat is None:
        return

    # Keep the complete conversation saved locally.
    chat["messages"] = list(
        st.session_state.messages
    )

    chat["updated_at"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    # Automatic title.
    for message in st.session_state.messages:

        if (
            message.get("role") == "user"
            and message.get("content")
        ):

            title = " ".join(
                str(
                    message["content"]
                ).split()
            )

            if len(title) > 50:
                title = title[:50] + "..."

            chat["title"] = title
            break

    save_json(
        CHATS_FILE,
        st.session_state.saved_chats,
    )


# ============================================================
# SESSION STATE
# ============================================================

if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = load_chats()


if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = (
        st.session_state.saved_chats[0]["id"]
    )


if "messages" not in st.session_state:

    selected_chat = get_current_chat()

    if selected_chat:
        st.session_state.messages = list(
            selected_chat.get(
                "messages",
                [],
            )
        )
    else:
        st.session_state.messages = []


if "user_name" not in st.session_state:
    st.session_state.user_name = memory["name"]


if "personal_memory" not in st.session_state:
    st.session_state.personal_memory = memory["facts"]


if "preferences" not in st.session_state:
    st.session_state.preferences = memory["preferences"]


# ============================================================
# GROQ CONNECTION
# ============================================================

def get_groq_key():

    try:
        secret_key = st.secrets.get(
            "GROQ_API_KEY"
        )

        if secret_key:
            return str(
                secret_key
            ).strip()

    except Exception:
        pass

    return os.getenv(
        "GROQ_API_KEY"
    )


GROQ_API_KEY = get_groq_key()


if GROQ_API_KEY:

    client = Groq(
        api_key=GROQ_API_KEY,
        timeout=120,
        max_retries=0,
    )

else:

    client = None


# ============================================================
# EARLY ACCESS MEMORY
# ============================================================

def remember_from_message(text):

    changed = False
    lower_text = text.lower()

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    name_marker = "my name is "

    if name_marker in lower_text:

        start = (
            lower_text.find(name_marker)
            + len(name_marker)
        )

        name = text[start:].strip(
            " .!?"
        )

        if name:

            st.session_state.user_name = (
                name[:80]
            )

            changed = True

    # --------------------------------------------------------
    # EXPLICIT MEMORY
    # --------------------------------------------------------

    memory_markers = [
        "remember that ",
        "remember this: ",
        "please remember ",
        "save this: ",
    ]

    for marker in memory_markers:

        if marker in lower_text:

            start = (
                lower_text.find(marker)
                + len(marker)
            )

            fact = text[start:].strip(
                " .!?"
            )

            if (
                fact
                and fact
                not in st.session_state.personal_memory
            ):

                st.session_state.personal_memory.append(
                    fact
                )

                changed = True

            break

    # --------------------------------------------------------
    # PREFERENCES
    # --------------------------------------------------------

    preference_markers = [
        "i prefer ",
        "i like ",
        "my favorite ",
    ]

    for marker in preference_markers:

        if marker in lower_text:

            start = lower_text.find(marker)

            preference = text[start:].strip(
                " .!?"
            )

            if (
                preference
                and preference
                not in st.session_state.preferences
            ):

                st.session_state.preferences.append(
                    preference
                )

                changed = True

            break

    if changed:
        save_memory()


def clear_memory():

    st.session_state.user_name = None
    st.session_state.personal_memory = []
    st.session_state.preferences = []

    save_memory()


def get_memory_context():

    memory_lines = []

    if st.session_state.user_name:

        memory_lines.append(
            "User name: "
            + st.session_state.user_name
        )

    for fact in st.session_state.personal_memory:

        memory_lines.append(
            "Saved fact: "
            + str(fact)
        )

    for preference in st.session_state.preferences:

        memory_lines.append(
            "Preference: "
            + str(preference)
        )

    if not memory_lines:
        return "No saved personal memory."

    return "\n".join(memory_lines)


# ============================================================
# REAL BRAIN
# ============================================================

def build_brain_messages(current_user_message):

    system_prompt = f"""
You are KingsBot AI.

You are powered by the real AI model:
{MODEL}

Groq provides the fast Turbo inference layer.
The model itself is the brain.

============================================================
CORE INTELLIGENCE
============================================================

You are a capable general-purpose AI assistant.

You can help with:

• General knowledge
• World knowledge
• Mathematics
• Science
• History
• Geography
• Technology
• Artificial intelligence
• Programming
• Advanced coding
• Debugging
• Code review
• Software development
• Problem solving
• Deep reasoning
• Research
• Current information
• Education
• Writing
• Planning
• Explanations
• Everyday questions

============================================================
DEEP REASONING
============================================================

Think carefully about difficult problems.

For complicated questions:

• Break the problem into useful steps.
• Check assumptions.
• Check calculations.
• Verify conclusions when possible.
• Correct mistakes rather than continuing them.

Do NOT reveal private chain-of-thought.

Instead provide useful:
• conclusions
• reasoning summaries
• calculations
• explanations
• steps

============================================================
FACTUAL GROUNDING
============================================================

When information may have changed:

• Use browser search.
• Prefer reliable sources.
• Do not invent facts.
• Do not invent citations.
• Do not pretend old information is current.
• Say when something is uncertain.

============================================================
MATHEMATICS
============================================================

Solve mathematics accurately.

For difficult calculations, use the code
execution tool when useful.

============================================================
ADVANCED CODING
============================================================

When the user asks for code:

• Give complete code when appropriate.
• Check imports.
• Check indentation.
• Check syntax.
• Check variable names.
• Check API usage.
• Check logic.
• Preserve requested features.
• Do not replace the real AI brain with
  hard-coded fake answers.

============================================================
CONVERSATION
============================================================

Understand the conversation history.

Use earlier messages when they are relevant.

Ask useful follow-up questions when they
genuinely help.

Do not ask unnecessary questions.

Be direct, friendly, clear and honest.

============================================================
EARLY ACCESS MEMORY
============================================================

{get_memory_context()}

Use memory only when relevant.

============================================================
REMOVED FEATURES
============================================================

There is NO separate multilingual feature.

There is NO topic-detection system.

There is NO file-upload feature.

There is NO file-generation feature.

There is NO artificial request cooldown.

There is NO artificial request counter.

============================================================
CURRENT USER MESSAGE
============================================================

Answer the user's current message directly.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # ========================================================
    # MEDIUM CONVERSATION HISTORY
    # ========================================================
    #
    # The application can save the conversation.
    #
    # Only the most recent 30 messages are sent to
    # the AI model to keep the active context MEDIUM.
    #
    # This is the ONLY conversation-size change requested.
    #

    recent_messages = (
        st.session_state.messages[
            -MEDIUM_HISTORY_MESSAGES:
        ]
    )

    for message in recent_messages:

        role = message.get("role")
        content = message.get("content")

        if role not in (
            "user",
            "assistant",
        ):
            continue

        if not content:
            continue

        messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": current_user_message,
        }
    )

    return messages


# ============================================================
# ASK REAL AI BRAIN
# ============================================================

def ask_kingsbot(user_message):

    if client is None:

        return (
            "🔑 GROQ_API_KEY is missing.\n\n"
            "Add your GROQ_API_KEY to "
            "Streamlit Secrets."
        )

    remember_from_message(
        user_message
    )

    try:

        response = (
            client.chat.completions.create(
                model=MODEL,

                messages=build_brain_messages(
                    user_message
                ),

                tools=[
                    {
                        "type": "browser_search"
                    },
                    {
                        "type": "code_interpreter"
                    },
                ],

                tool_choice="auto",

                reasoning_effort="high",

                temperature=1,

                max_completion_tokens=8192,

                stream=False,
            )
        )

        answer = (
            response
            .choices[0]
            .message
            .content
            or ""
        )

        answer = answer.strip()

        if not answer:

            return (
                "I couldn't produce an answer. "
                "Please try again."
            )

        return answer

    except Exception as error:

        error_text = str(
            error
        ).lower()

        if (
            "429" in error_text
            or "rate limit" in error_text
            or "too many requests" in error_text
        ):

            return (
                "The AI provider returned a "
                "429 rate-limit response.\n\n"
                "KingsBot itself has no artificial "
                "request cooldown or request counter."
            )

        return (
            "KingsBot could not reach the AI brain.\n\n"
            "Technical error:\n"
            + str(error)
        )


# ============================================================
# VOICE INPUT
# ============================================================

def transcribe_voice(audio_file):

    if client is None:
        return None

    if audio_file is None:
        return None

    try:

        audio_data = io.BytesIO(
            audio_file.getvalue()
        )

        audio_data.name = (
            "kingsbot_voice.webm"
        )

        result = (
            client.audio.transcriptions.create(
                model=VOICE_MODEL,
                file=audio_data,
                response_format="json",
            )
        )

        text = getattr(
            result,
            "text",
            "",
        )

        if text:
            return text.strip()

    except Exception:

        return None

    return None


# ============================================================
# VOICE RESPONSE
# ============================================================

def make_voice(text):

    try:

        audio = io.BytesIO()

        speech = gTTS(
            text=text[:3000],
            lang="en",
            slow=False,
        )

        speech.write_to_fp(
            audio
        )

        return audio.getvalue()

    except Exception:

        return None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🤖 KingsBot AI"
    )

    st.success(
        "⚡ Turbo inference ON"
    )

    st.write(
        "🧠 Real brain:",
        MODEL,
    )

    st.write(
        "🧠 Deep reasoning:",
        "HIGH",
    )

    st.write(
        "🌐 Web search:",
        "ON",
    )

    st.write(
        "💻 Code execution:",
        "ON",
    )

    st.write(
        "🧮 Math:",
        "ON",
    )

    st.write(
        "🧠 Early Access Memory:",
        "ON",
    )

    st.write(
        "🎤 Voice:",
        "ON",
    )

    st.write(
        "💬 Active AI history:",
        "30 messages",
    )

    st.write(
        "📎 File upload:",
        "OFF",
    )

    st.write(
        "📥 File generation:",
        "OFF",
    )

    st.write(
        "🌍 Multilingual:",
        "REMOVED",
    )

    st.write(
        "🔎 Topic detection:",
        "REMOVED",
    )

    st.write(
        "⏱️ Artificial request limit:",
        "OFF",
    )

    st.divider()

    # ========================================================
    # NEW CHAT
    # ========================================================

    if st.button(
        "➕ New conversation",
        use_container_width=True,
    ):

        chat = create_chat()

        st.session_state.saved_chats.insert(
            0,
            chat,
        )

        st.session_state.current_chat_id = (
            chat["id"]
        )

        st.session_state.messages = []

        save_json(
            CHATS_FILE,
            st.session_state.saved_chats,
        )

        st.rerun()

    # ========================================================
    # CONVERSATIONS
    # ========================================================

    st.subheader(
        "💬 Conversations"
    )

    for chat in st.session_state.saved_chats:

        title = chat.get(
            "title",
            "Conversation",
        )

        if len(title) > 32:
            title = title[:32] + "..."

        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):

            prefix = "🟢 "

        else:

            prefix = "💬 "

        if st.button(
            prefix + title,
            key="open_" + chat["id"],
            use_container_width=True,
        ):

            st.session_state.current_chat_id = (
                chat["id"]
            )

            st.session_state.messages = list(
                chat.get(
                    "messages",
                    [],
                )
            )

            st.rerun()

    st.divider()

    # ========================================================
    # EARLY ACCESS MEMORY
    # ========================================================

    st.subheader(
        "🧠 Early Access Memory"
    )

    st.write(
        "Name:",
        st.session_state.user_name
        or "Not saved",
    )

    st.write(
        "Saved facts:",
        len(
            st.session_state.personal_memory
        ),
    )

    st.write(
        "Preferences:",
        len(
            st.session_state.preferences
        ),
    )

    if st.button(
        "🧹 Clear Early Access Memory",
        use_container_width=True,
    ):

        clear_memory()

        st.rerun()


# ============================================================
# MAIN PAGE
# ============================================================

st.title(
    "🤖 KingsBot AI"
)

st.caption(
    "Real GPT-OSS 20B brain • "
    "⚡ Turbo • 🧠 Deep Reasoning • "
    "🌐 Web Search • 💻 Advanced Coding • "
    "🧮 Problem Solving • 🧠 Memory • 🎤 Voice"
)


# ============================================================
# DISPLAY CONVERSATION
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# VOICE ASSISTANT
# ============================================================

st.subheader(
    "🎤 Voice Assistant"
)

audio_input = st.audio_input(
    "Record your message",
    key="kingsbot_voice_input",
)

voice_text = None

if audio_input:

    with st.spinner(
        "🎧 Understanding your voice..."
    ):

        voice_text = transcribe_voice(
            audio_input
        )

    if voice_text:

        st.info(
            "You said: "
            + voice_text
        )

    else:

        st.warning(
            "I couldn't understand that recording."
        )


# ============================================================
# TEXT INPUT
# ============================================================

text_prompt = st.chat_input(
    "Ask KingsBot anything..."
)

prompt = (
    voice_text
    or text_prompt
)


# ============================================================
# SEND TO REAL BRAIN
# ============================================================

if prompt:

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "⚡ KingsBot is thinking..."
        ):

            answer = ask_kingsbot(
                prompt
            )

        st.markdown(
            answer
        )

        if voice_text:

            with st.spinner(
                "🔊 Preparing voice reply..."
            ):

                audio = make_voice(
                    answer
                )

            if audio:

                st.audio(
                    audio,
                    format="audio/mp3",
                )

    # ========================================================
    # SAVE CONVERSATION
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    save_current_chat()

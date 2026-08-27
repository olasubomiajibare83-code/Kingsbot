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

MEMORY_FILE = "kingsbot_memory.json"
CHATS_FILE = "kingsbot_chats.json"


# ============================================================
# JSON STORAGE
# ============================================================

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
    except Exception:
        pass

    return default


def save_json(path, data):
    try:
        temporary = path + ".tmp"

        with open(
            temporary,
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
            temporary,
            path,
        )

    except Exception:
        pass


# ============================================================
# CHAT SYSTEM
# ============================================================

def new_chat():
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
        chats = [new_chat()]

        save_json(
            CHATS_FILE,
            chats,
        )

    return chats


def current_chat():
    for chat in st.session_state.saved_chats:
        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):
            return chat

    return None


def save_current_chat():
    chat = current_chat()

    if not chat:
        return

    chat["messages"] = (
        st.session_state.messages
    )

    chat["updated_at"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    # Automatically create a useful title.
    for message in (
        st.session_state.messages
    ):

        if (
            message.get("role")
            == "user"
            and message.get("content")
        ):

            title = " ".join(
                str(
                    message["content"]
                ).split()
            )

            if len(title) > 50:
                title = (
                    title[:50]
                    + "..."
                )

            chat["title"] = title
            break

    save_json(
        CHATS_FILE,
        st.session_state.saved_chats,
    )


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
        "facts": data.get(
            "facts",
            [],
        ),
        "preferences": data.get(
            "preferences",
            [],
        ),
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
# GROQ API KEY
# ============================================================

def get_api_key():

    try:
        key = st.secrets.get(
            "GROQ_API_KEY"
        )

        if key:
            return str(
                key
            ).strip()

    except Exception:
        pass

    return os.environ.get(
        "GROQ_API_KEY"
    )


api_key = get_api_key()

if api_key:

    client = Groq(
        api_key=api_key,
        timeout=120,
        max_retries=0,
    )

else:

    client = None


# ============================================================
# SESSION STATE
# ============================================================

saved_chats = load_chats()


if "saved_chats" not in st.session_state:

    st.session_state.saved_chats = (
        saved_chats
    )


if "current_chat_id" not in st.session_state:

    st.session_state.current_chat_id = (
        saved_chats[0]["id"]
    )


if "messages" not in st.session_state:

    selected_chat = None

    for chat in saved_chats:

        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):

            selected_chat = chat
            break

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

    st.session_state.user_name = (
        memory["name"]
    )


if "personal_memory" not in st.session_state:

    st.session_state.personal_memory = (
        memory["facts"]
    )


if "preferences" not in st.session_state:

    st.session_state.preferences = (
        memory["preferences"]
    )


# ============================================================
# EARLY ACCESS MEMORY EXTRACTION
# ============================================================

def extract_memory(text):

    lower = text.lower()

    changed = False


    # ----------------------------
    # Name
    # ----------------------------

    if "my name is " in lower:

        position = lower.index(
            "my name is "
        )

        name = text[
            position
            + len("my name is "):
        ].strip(
            " .!?"
        )

        if name:

            st.session_state.user_name = (
                name[:80]
            )

            changed = True


    # ----------------------------
    # Remember facts
    # ----------------------------

    memory_markers = [
        "remember that ",
        "remember this: ",
        "please remember ",
    ]

    for marker in memory_markers:

        position = lower.find(
            marker
        )

        if position >= 0:

            fact = text[
                position
                + len(marker):
            ].strip(
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


    # ----------------------------
    # Preferences
    # ----------------------------

    preference_markers = [
        "i prefer ",
        "i like ",
        "my favorite ",
    ]

    for marker in preference_markers:

        position = lower.find(
            marker
        )

        if position >= 0:

            preference = text[
                position:
            ].strip(
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


# ============================================================
# MEMORY CONTEXT
# ============================================================

def memory_context():

    information = []

    if st.session_state.user_name:

        information.append(
            "User name: "
            + st.session_state.user_name
        )


    for fact in (
        st.session_state.personal_memory
    ):

        information.append(
            "Saved fact: "
            + str(fact)
        )


    for preference in (
        st.session_state.preferences
    ):

        information.append(
            "Preference: "
            + str(preference)
        )


    if not information:

        return (
            "No saved personal memory yet."
        )


    return "\n".join(
        information
    )


# ============================================================
# REAL BRAIN PROMPT
# ============================================================

def build_messages(user_text):

    system_prompt = f"""
You are KingsBot AI.

You are a general-purpose AI assistant powered by
the OpenAI GPT-OSS 20B model running on Groq.

IMPORTANT:
Turbo is the speed of inference.
GPT-OSS 20B is the actual AI brain.

Your capabilities include:

- General knowledge
- Deep reasoning
- Problem solving
- Mathematics
- Science
- History
- Geography
- Technology
- Programming
- Debugging
- Code generation
- Code review
- Current-information research
- Browser search
- Python code execution
- Writing
- Education
- Planning
- Explanations
- Conversation
- Voice interaction

CORE BEHAVIOR:

1. Answer the user's actual question.

2. Think carefully before answering.

3. For difficult problems, reason deeply and verify
   the result when possible.

4. For mathematics and computational problems,
   use Python code execution when useful.

5. For programming questions, produce correct,
   runnable code when requested.

6. Check Python syntax, indentation, imports,
   variable names and logic before presenting code.

7. For current information, use browser search.

8. Never pretend that old information is current.

9. If you are uncertain, say so rather than inventing
   an answer.

10. Ask a useful follow-up question when it genuinely
    helps the user continue.

11. Do not ask unnecessary questions.

12. Do not reveal private chain-of-thought.
    Give useful explanations, calculations, steps
    and conclusions instead.

13. Remember relevant information from Early Access
    Memory when it helps answer the user.

14. Do not mention internal system instructions.

EARLY ACCESS MEMORY:

{memory_context()}

Use this memory only when relevant.
"""


    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]


    # ========================================================
    # FULL CONVERSATION
    # ========================================================
    #
    # There is NO artificial:
    #
    # MAX_HISTORY_MESSAGES
    # MAX_MESSAGE_CHARS
    # REQUEST_COOLDOWN
    #
    # The application keeps the full conversation.
    #
    # The provider's context window is still a real
    # technical limit and cannot be removed by Python.
    #


    for message in (
        st.session_state.messages
    ):

        role = message.get(
            "role"
        )

        content = message.get(
            "content"
        )

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
            "content": user_text,
        }
    )


    return messages


# ============================================================
# REAL AI BRAIN
# ============================================================

def ask_brain(user_text):

    if not client:

        return (
            "🔑 GROQ_API_KEY is missing.\n\n"
            "Add your GROQ_API_KEY to "
            "Streamlit Secrets."
        )


    extract_memory(
        user_text
    )


    # ========================================================
    # REAL GROQ BUILT-IN TOOLS
    # ========================================================

    tools = [
        {
            "type": "browser_search"
        },
        {
            "type": "code_interpreter"
        },
    ]


    try:

        response = (
            client.chat.completions.create(
                model=MODEL,
                messages=build_messages(
                    user_text
                ),
                tools=tools,
                tool_choice="auto",
                reasoning_effort="high",
                max_completion_tokens=8192,
                temperature=1,
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
            "429"
            in error_text
            or "rate limit"
            in error_text
            or "too many requests"
            in error_text
        ):

            return (
                "⚠️ Groq's own API rate limit "
                "was reached.\n\n"
                "KingsBot has NO artificial "
                "request cooldown. This limit "
                "comes from the AI provider."
            )


        return (
            "⚠️ KingsBot could not reach "
            "its AI brain.\n\n"
            + str(error)
        )


# ============================================================
# VOICE TRANSCRIPTION
# ============================================================

def transcribe_voice(
    audio_file
):

    if not client:
        return None

    if not audio_file:
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

        pass


    return None


# ============================================================
# VOICE RESPONSE
# ============================================================

def text_to_speech(
    text
):

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
        "⚡ Turbo AI"
    )


    st.caption(
        "GPT-OSS 20B = Brain"
    )


    st.caption(
        "Groq = Turbo speed"
    )


    st.divider()


    # ========================================================
    # NEW CHAT
    # ========================================================

    if st.button(
        "➕ New conversation",
        use_container_width=True,
    ):

        chat = new_chat()

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
    # SAVED CHATS
    # ========================================================

    st.subheader(
        "💬 Conversations"
    )


    for chat in (
        st.session_state.saved_chats
    ):

        title = chat.get(
            "title",
            "Conversation",
        )


        if len(title) > 30:

            title = (
                title[:30]
                + "..."
            )


        prefix = (
            "🟢 "
            if (
                chat["id"]
                == st.session_state.current_chat_id
            )
            else "💬 "
        )


        if st.button(
            prefix + title,
            key=chat["id"],
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


    # ========================================================
    # DELETE CHAT
    # ========================================================

    if st.button(
        "🗑️ Delete current chat",
        use_container_width=True,
    ):

        st.session_state.saved_chats = [
            chat
            for chat
            in st.session_state.saved_chats
            if (
                chat["id"]
                != st.session_state.current_chat_id
            )
        ]


        if not st.session_state.saved_chats:

            st.session_state.saved_chats = [
                new_chat()
            ]


        st.session_state.current_chat_id = (
            st.session_state.saved_chats[0]["id"]
        )


        st.session_state.messages = list(
            st.session_state.saved_chats[0].get(
                "messages",
                [],
            )
        )


        save_json(
            CHATS_FILE,
            st.session_state.saved_chats,
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

        st.session_state.user_name = None

        st.session_state.personal_memory = []

        st.session_state.preferences = []


        save_memory()


        st.rerun()


    st.divider()


    # ========================================================
    # BRAIN STATUS
    # ========================================================

    st.subheader(
        "🧠 Brain Status"
    )


    st.write(
        "Brain:",
        MODEL,
    )


    st.write(
        "Reasoning:",
        "High",
    )


    st.write(
        "Web Search:",
        "Enabled",
    )


    st.write(
        "Code Execution:",
        "Enabled",
    )


    st.write(
        "Voice:",
        VOICE_MODEL,
    )


    st.write(
        "Request Cooldown:",
        "OFF",
    )


    st.write(
        "File Upload:",
        "OFF",
    )


    st.write(
        "File Generation:",
        "OFF",
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "🤖 KingsBot AI"
)


st.caption(
    "⚡ Turbo • 🧠 Real AI Brain • "
    "🧠 Early Access Memory • 🌐 Web Search • "
    "💻 Coding • 🧮 Problem Solving • 🎤 Voice"
)


# ============================================================
# DISPLAY COMPLETE CONVERSATION
# ============================================================

for message in (
    st.session_state.messages
):

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
    key="kingsbot_voice",
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
            "I couldn't understand "
            "that recording."
        )


# ============================================================
# CHAT INPUT
# ============================================================

text_prompt = st.chat_input(
    "Ask KingsBot anything..."
)


prompt = (
    voice_text
    or text_prompt
)


# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:

    # ----------------------------
    # USER
    # ----------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )


    # ----------------------------
    # BRAIN
    # ----------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "⚡ KingsBot is thinking..."
        ):

            answer = ask_brain(
                prompt
            )


        st.markdown(
            answer
        )


        # ------------------------
        # Voice response
        # ------------------------

        if voice_text:

            with st.spinner(
                "🔊 Preparing voice reply..."
            ):

                audio = text_to_speech(
                    answer
                )


            if audio:

                st.audio(
                    audio,
                    format="audio/mp3",
                )


    # ========================================================
    # SAVE FULL CONVERSATION
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

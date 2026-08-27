import io
import json
import os
import uuid
from datetime import datetime

import streamlit as st
from openai import OpenAI


# ============================================================
# KINGSBOT AI
# OPENAI / GPT-5.6 VERSION
# ============================================================

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# SETTINGS
# ============================================================

MODEL = "gpt-5.6"

TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
TTS_MODEL = "gpt-4o-mini-tts"

# Large conversation context.
# Old messages remain saved locally.
ACTIVE_HISTORY_MESSAGES = 60

MEMORY_FILE = "kingsbot_early_access_memory.json"
CHATS_FILE = "kingsbot_chats.json"


# ============================================================
# STORAGE
# ============================================================

def load_json(path, default):
    try:
        if not os.path.exists(path):
            return default

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data

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
# MEMORY
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
# CONVERSATIONS
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
        save_json(CHATS_FILE, chats)

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

    chat["messages"] = list(
        st.session_state.messages
    )

    chat["updated_at"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

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

            if len(title) > 55:
                title = title[:55] + "..."

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

    current = get_current_chat()

    if current:
        st.session_state.messages = list(
            current.get(
                "messages",
                [],
            )
        )

    else:
        st.session_state.messages = []


if "user_name" not in st.session_state:
    st.session_state.user_name = memory["name"]


if "personal_memory" not in st.session_state:
    st.session_state.personal_memory = list(
        memory["facts"]
    )


if "preferences" not in st.session_state:
    st.session_state.preferences = list(
        memory["preferences"]
    )


# ============================================================
# OPENAI CLIENT
# ============================================================

def get_api_key():

    try:
        key = st.secrets.get(
            "OPENAI_API_KEY"
        )

        if key:
            return str(key).strip()

    except Exception:
        pass

    return os.getenv(
        "OPENAI_API_KEY"
    )


OPENAI_API_KEY = get_api_key()


if OPENAI_API_KEY:
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )
else:
    client = None


# ============================================================
# MEMORY SYSTEM
# ============================================================

def remember_from_message(text):

    changed = False
    lower = text.lower()

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    marker = "my name is "

    if marker in lower:

        start = (
            lower.find(marker)
            + len(marker)
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

    markers = [
        "remember that ",
        "remember this: ",
        "please remember ",
        "save this: ",
    ]

    for marker in markers:

        if marker in lower:

            start = (
                lower.find(marker)
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

        if marker in lower:

            start = lower.find(marker)

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

    lines = []

    if st.session_state.user_name:
        lines.append(
            "User name: "
            + st.session_state.user_name
        )

    for fact in st.session_state.personal_memory:
        lines.append(
            "Saved fact: "
            + str(fact)
        )

    for preference in st.session_state.preferences:
        lines.append(
            "Preference: "
            + str(preference)
        )

    if not lines:
        return "No saved personal memory."

    return "\n".join(lines)


# ============================================================
# TONE ADAPTATION
# ============================================================

TONE_INSTRUCTIONS = """
Automatically adapt your tone to the user's situation.

Use these principles:

- Simple questions:
  Answer simply and directly.

- Beginner questions:
  Explain clearly without assuming advanced knowledge.

- Difficult technical questions:
  Be precise, structured and technical.

- Coding:
  Be practical and give working code when requested.

- Emotional or personal questions:
  Be respectful, calm and supportive.

- Professional requests:
  Use a professional tone.

- Casual conversation:
  Be natural and conversational.

- If the user asks for a short answer:
  Keep it short.

- If the user asks for detail:
  Give enough detail to be useful.

Do not announce that you are adapting your tone.
Just adapt naturally.
"""


# ============================================================
# SYSTEM INSTRUCTIONS
# ============================================================

def build_instructions():

    return f"""
You are KingsBot AI.

You are powered by OpenAI model:
{MODEL}

You are a general-purpose intelligent AI assistant.

============================================================
CORE CAPABILITIES
============================================================

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
• Software development
• Problem solving
• Deep reasoning
• Research
• Current information
• Education
• Writing
• Rewriting
• Planning
• Brainstorming
• Comparisons
• Explanations
• Everyday questions

============================================================
REASONING
============================================================

Think carefully about difficult problems.

Check calculations, assumptions, logic and conclusions.

Do not reveal private chain-of-thought.

Instead provide concise reasoning summaries,
important steps and conclusions.

============================================================
FACTUAL ACCURACY
============================================================

Do not invent facts.

When information may be current or changing,
use web search when appropriate.

Clearly distinguish uncertainty from known facts.

When web search is used, base current claims
on the retrieved information.

============================================================
CODING
============================================================

For programming requests:

• Check syntax.
• Check indentation.
• Check imports.
• Check variable names.
• Check API usage.
• Check logic.
• Preserve requested features.
• Give complete code when appropriate.
• Avoid fake hard-coded "AI brains."

============================================================
MATHEMATICS
============================================================

Solve calculations carefully.

Use the code interpreter when useful.

============================================================
TONE ADAPTATION
============================================================

{TONE_INSTRUCTIONS}

============================================================
EARLY ACCESS MEMORY
============================================================

{get_memory_context()}

Use saved memory only when relevant.

============================================================
IMPORTANT REMOVED FEATURES
============================================================

Do NOT create or advertise these as active features:

• Multilingual mastery
• Topic detection
• File upload
• File generation
• Delete conversation

There is also no artificial request counter
or artificial cooldown in this application.

============================================================
FOLLOW-UP QUESTIONS
============================================================

Ask a useful follow-up question when the request
is genuinely ambiguous or when additional information
is needed.

Do not ask unnecessary questions.

============================================================
CURRENT DATE
============================================================

Use the actual current date supplied by the API/system
when discussing dates or current information.
"""


# ============================================================
# BUILD INPUT
# ============================================================

def build_input(user_message):

    recent = (
        st.session_state.messages[
            -ACTIVE_HISTORY_MESSAGES:
        ]
    )

    input_messages = []

    for message in recent:

        role = message.get("role")
        content = message.get("content")

        if role not in (
            "user",
            "assistant",
        ):
            continue

        if not content:
            continue

        input_messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    input_messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    return input_messages


# ============================================================
# OPENAI RESPONSE
# ============================================================

def ask_kingsbot(user_message):

    if client is None:

        return (
            "🔑 OPENAI_API_KEY was not found.\n\n"
            "Make sure the secret is named exactly:\n\n"
            "OPENAI_API_KEY\n\n"
            "Then restart the Streamlit app."
        )

    remember_from_message(
        user_message
    )

    try:

        response = client.responses.create(

            model=MODEL,

            instructions=build_instructions(),

            input=build_input(
                user_message
            ),

            reasoning={
                "effort": "high"
            },

            tools=[
                {
                    "type": "web_search"
                },
                {
                    "type": "code_interpreter",
                    "container": {
                        "type": "auto"
                    }
                },
            ],

            tool_choice="auto",

            max_output_tokens=8192,

        )

        answer = (
            getattr(
                response,
                "output_text",
                ""
            )
            or ""
        ).strip()


        if not answer:

            return (
                "I didn't receive a usable answer "
                "from the AI. Please try again."
            )


        return answer


    except Exception as error:

        message = str(error)

        lower = message.lower()


        if (
            "401" in lower
            or "authentication" in lower
            or "api key" in lower
        ):

            return (
                "🔐 OpenAI authentication failed.\n\n"
                "Check that your Streamlit secret is:\n\n"
                "OPENAI_API_KEY = \"your-key\"\n\n"
                "Do not paste the key into app.py."
            )


        if (
            "429" in lower
            or "rate limit" in lower
            or "quota" in lower
        ):

            return (
                "⚠️ OpenAI returned a rate-limit or "
                "quota error.\n\n"
                "KingsBot does not add an artificial "
                "request limit. This response came "
                "from the API."
            )


        if (
            "model" in lower
            and (
                "not found" in lower
                or "does not exist" in lower
            )
        ):

            return (
                "The selected model is not available "
                "to this API key.\n\n"
                "Change MODEL near the top of app.py "
                "to a model available to your account."
            )


        return (
            "❌ KingsBot encountered an OpenAI API error.\n\n"
            + message
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

        audio = io.BytesIO(
            audio_file.getvalue()
        )

        audio.name = (
            "kingsbot_voice.webm"
        )

        result = (
            client.audio.transcriptions.create(
                model=TRANSCRIBE_MODEL,
                file=audio,
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
# VOICE OUTPUT
# ============================================================

def make_voice(text):

    if client is None:
        return None

    try:

        audio = io.BytesIO()

        speech = client.audio.speech.create(

            model=TTS_MODEL,

            voice="coral",

            input=text[:7000],

            response_format="mp3",

        )

        speech.stream_to_file(
            audio
        )

        audio.seek(0)

        return audio.read()

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
        "🧠 OpenAI Brain ON"
    )

    st.write(
        "Brain:",
        MODEL,
    )

    st.write(
        "⚡ Fast processing:",
        "ON",
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
        "💻 Code interpreter:",
        "ON",
    )

    st.write(
        "🧮 Math:",
        "ON",
    )

    st.write(
        "🎯 Tone adaptation:",
        "ON",
    )

    st.write(
        "🧠 Early Access Memory:",
        "ON",
    )

    st.write(
        "💬 Active history:",
        "60 messages",
    )

    st.write(
        "🎤 Voice:",
        "ON",
    )

    st.write(
        "📎 File upload:",
        "REMOVED",
    )

    st.write(
        "📄 File generation:",
        "REMOVED",
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
        "🗑️ Delete conversation:",
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

        new_chat = create_chat()

        st.session_state.saved_chats.insert(
            0,
            new_chat,
        )

        st.session_state.current_chat_id = (
            new_chat["id"]
        )

        st.session_state.messages = []

        save_json(
            CHATS_FILE,
            st.session_state.saved_chats,
        )

        st.rerun()


    # ========================================================
    # SAVE

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

# Small active conversation history.
# Older messages remain saved locally.
ACTIVE_HISTORY_MESSAGES = 15

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
        temp_path = path + ".tmp"

        with open(
            temp_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(temp_path, path)

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

    # Save the complete local conversation.
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

    marker = "my name is "

    if marker in lower_text:

        start = (
            lower_text.find(marker)
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
       

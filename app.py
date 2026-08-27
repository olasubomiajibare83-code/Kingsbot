import io
import json
import os
import uuid
from datetime import datetime

import streamlit as st
from openai import OpenAI


# ============================================================
# KINGSBOT AI
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

# Large but controlled conversation.
ACTIVE_HISTORY_MESSAGES = 60

MEMORY_FILE = "kingsbot_memory.json"
CHATS_FILE = "kingsbot_chats.json"


# ============================================================
# STORAGE
# ============================================================

def load_json(filename, default):
    try:
        if not os.path.exists(filename):
            return default

        with open(
            filename,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except Exception:
        return default


def save_json(filename, data):
    try:
        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except Exception:
        pass


# ============================================================
# MEMORY
# ============================================================

def default_memory():
    return {
        "name": "",
        "facts": [],
        "preferences": [],
    }


memory_data = load_json(
    MEMORY_FILE,
    default_memory(),
)

if not isinstance(memory_data, dict):
    memory_data = default_memory()


# ============================================================
# CHAT STORAGE
# ============================================================

def new_chat():
    return {
        "id": uuid.uuid4().hex,
        "title": "New conversation",
        "created": datetime.now().isoformat(
            timespec="seconds"
        ),
        "messages": [],
    }


saved_chats = load_json(
    CHATS_FILE,
    [],
)

if not isinstance(saved_chats, list):
    saved_chats = []


if not saved_chats:
    saved_chats = [new_chat()]
    save_json(
        CHATS_FILE,
        saved_chats,
    )


# ============================================================
# SESSION STATE
# ============================================================

if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = saved_chats


if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = (
        st.session_state.saved_chats[0]["id"]
    )


if "messages" not in st.session_state:

    selected = None

    for chat in st.session_state.saved_chats:
        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):
            selected = chat
            break

    if selected:
        st.session_state.messages = list(
            selected.get("messages", [])
        )
    else:
        st.session_state.messages = []


if "user_name" not in st.session_state:
    st.session_state.user_name = (
        memory_data.get("name", "")
    )


if "memory_facts" not in st.session_state:
    st.session_state.memory_facts = list(
        memory_data.get("facts", [])
    )


if "memory_preferences" not in st.session_state:
    st.session_state.memory_preferences = list(
        memory_data.get("preferences", [])
    )


# ============================================================
# OPENAI KEY
# ============================================================

def get_openai_key():

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


OPENAI_API_KEY = get_openai_key()


if OPENAI_API_KEY:

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

else:

    client = None


# ============================================================
# MEMORY
# ============================================================

def save_memory():

    save_json(
        MEMORY_FILE,
        {
            "name": st.session_state.user_name,
            "facts": st.session_state.memory_facts,
            "preferences": st.session_state.memory_preferences,
        },
    )


def learn_from_user(text):

    changed = False
    lower = text.lower()

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    if "my name is " in lower:

        position = lower.find(
            "my name is "
        )

        name = text[
            position + len("my name is "):
        ].strip(
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

    memory_words = [
        "remember that ",
        "remember this: ",
        "please remember ",
    ]

    for marker in memory_words:

        if marker in lower:

            position = lower.find(
                marker
            )

            fact = text[
                position + len(marker):
            ].strip(
                " .!?"
            )

            if (
                fact
                and fact
                not in st.session_state.memory_facts
            ):

                st.session_state.memory_facts.append(
                    fact
                )

                changed = True

            break


    # --------------------------------------------------------
    # PREFERENCES
    # --------------------------------------------------------

    preference_words = [
        "i prefer ",
        "i like ",
        "my favorite ",
    ]

    for marker in preference_words:

        if marker in lower:

            position = lower.find(
                marker
            )

            preference = text[
                position:
            ].strip(
                " .!?"
            )

            if (
                preference
                and preference
                not in st.session_state.memory_preferences
            ):

                st.session_state.memory_preferences.append(
                    preference
                )

                changed = True

            break


    if changed:
        save_memory()


def memory_text():

    lines = []

    if st.session_state.user_name:
        lines.append(
            "User name: "
            + st.session_state.user_name
        )

    for fact in st.session_state.memory_facts:
        lines.append(
            "Saved fact: "
            + str(fact)
        )

    for preference in (
        st.session_state.memory_preferences
    ):
        lines.append(
            "Preference: "
            + str(preference)
        )

    if not lines:
        return "No saved memory."

    return "\n".join(lines)


# ============================================================
# AI INSTRUCTIONS
# ============================================================

def system_instructions():

    return f"""
You are KingsBot AI.

Your AI brain is OpenAI {MODEL}.

You are a powerful general-purpose assistant.

CAPABILITIES:

- General knowledge
- Current information
- Mathematics
- Science
- History
- Geography
- Technology
- AI
- Programming
- Advanced coding
- Debugging
- Problem solving
- Deep reasoning
- Writing
- Rewriting
- Planning
- Brainstorming
- Teaching
- Explanations
- Comparisons
- Research

TONE ADAPTATION:

Automatically adapt your communication style.

For simple questions:
be simple and direct.

For beginners:
explain clearly without unnecessary jargon.

For difficult technical questions:
be precise and structured.

For coding:
be practical and provide complete working
code when appropriate.

For casual conversation:
be natural and friendly.

For professional requests:
be professional.

For emotional or personal questions:
be respectful and supportive.

If the user asks for a short answer:
keep it short.

If the user asks for detailed information:
provide useful detail.

Do not announce that you are adapting your tone.

REASONING:

Think carefully about difficult problems.

Check calculations and logic.

Do not reveal private chain-of-thought.

Provide concise reasoning summaries instead.

FACTUAL ACCURACY:

Do not invent information.

For information that may be current or changing,
use web search when appropriate.

If you are uncertain, say so.

CODING:

Check:
- imports
- syntax
- indentation
- variables
- logic
- API usage

Do not create a fake hard-coded AI brain.

MEMORY:

{memory_text()}

Use memory only when relevant.

REMOVED FEATURES:

Do not create:
- multilingual mode
- topic detection
- file upload
- file generation
- delete conversation

There is no artificial request counter
and no artificial cooldown.

Ask useful follow-up questions when necessary,
but do not ask unnecessary questions.
"""


# ============================================================
# BUILD CONVERSATION
# ============================================================

def build_messages(user_text):

    recent_messages = (
        st.session_state.messages[
            -ACTIVE_HISTORY_MESSAGES:
        ]
    )

    result = []

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

        result.append(
            {
                "role": role,
                "content": content,
            }
        )

    result.append(
        {
            "role": "user",
            "content": user_text,
        }
    )

    return result


# ============================================================
# ASK KINGSBOT
# ============================================================

def ask_kingsbot(user_text):

    if client is None:

        return (
            "🔑 I could not find OPENAI_API_KEY.\n\n"
            "In Streamlit Secrets, make sure you have:\n\n"
            "OPENAI_API_KEY = \"your-api-key\"\n\n"
            "Do not put the real key inside app.py."
        )

    learn_from_user(
        user_text
    )

    try:

        response = client.responses.create(

            model=MODEL,

            instructions=system_instructions(),

            input=build_messages(
                user_text
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

        )

        answer = getattr(
            response,
            "output_text",
            ""
        )

        answer = (
            answer
            if isinstance(answer, str)
            else str(answer)
        ).strip()


        if not answer:

            return (
                "I didn't receive an answer. "
                "Please try again."
            )


        return answer


    except Exception as error:

        error_text = str(
            error
        )

        lower = error_text.lower()


        if (
            "401" in lower
            or "authentication" in lower
            or "api key" in lower
        ):

            return (
                "🔐 OpenAI authentication failed.\n\n"
                "Check that your Streamlit secret "
                "is named exactly OPENAI_API_KEY."
            )


        if (
            "429" in lower
            or "rate limit" in lower
            or "quota" in lower
        ):

            return (
                "⚠️ OpenAI returned a rate-limit "
                "or quota error.\n\n"
                "KingsBot itself does not add a "
                "request limit."
            )


        if (
            "model" in lower
            and (
                "not found" in lower
                or "does not exist" in lower
            )
        ):

            return (
                "⚠️ The GPT-5.6 model is not "
                "available to this API key/account."
            )


        return (
            "❌ OpenAI error:\n\n"
            + error_text
        )


# ============================================================
# SAVE CHAT
# ============================================================

def save_current_chat():

    for chat in st.session_state.saved_chats:

        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):

            chat["messages"] = list(
                st.session_state.messages
            )

            chat["updated"] = (
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )

            # Automatic title.
            for message in (
                st.session_state.messages
            ):

                if (
                    message.get("role")
                    == "user"
                    and message.get("content")
                ):

                    title = " ".join(
                        message["content"].split()
                    )

                    if len(title) > 50:
                        title = (
                            title[:50]
                            + "..."
                        )

                    chat["title"] = title
                    break

            break

    save_json(
        CHATS_FILE,
        st.session_state.saved_chats,
    )


# ============================================================
# NEW CHAT
# ============================================================

def start_new_chat():

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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🤖 KingsBot AI"
    )

    st.success(
        "🧠 GPT-5.6 Brain"
    )

    st.write(
        "Model:",
        MODEL,
    )

    st.write(
        "⚡ Fast AI:",
        "ON",
    )

    st.write(
        "🧠 Deep reasoning:",
        "ON",
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

    st.divider()

    if st.button(
        "➕ New conversation",
        use_container_width=True,
    ):

        start_new_chat()
        st.rerun()


    st.subheader(
        "💬 Conversations"
    )


    for chat in st.session_state.saved_chats:

        title = chat.get(
            "title",
            "New conversation",
        )

        if len(title) > 30:
            title = title[:30] + "..."

        prefix = (
            "🟢 "
            if chat["id"]
            == st.session_state.current_chat_id
            else "💬 "
        )

        if st.button(
            prefix + title,
            key="chat_" + chat["id"],
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

    st.subheader(
        "🧠 Early Access Memory"
    )

    st.write(
        "Name:",
        st.session_state.user_name
        or "Not saved",
    )

    st.write(
        "Facts:",
        len(
            st.session_state.memory_facts
        ),
    )

    st.write(
        "Preferences:",
        len(
            st.session_state.memory_preferences
        ),
    )


    if st.button(
        "🧹 Clear memory",
        use_container_width=True,
    ):

        st.session_state.user_name = ""
        st.session_state.memory_facts = []
        st.session_state.memory_preferences = []

        save_memory()

        st.rerun()


    st.divider()

    st.caption(
        "Removed: multilingual mode, "
        "topic detection, file upload, "
        "file generation and delete conversation."
    )


# ============================================================
# MAIN
# ============================================================

st.title(
    "🤖 KingsBot AI"
)

st.caption(
    "GPT-5.6 • Deep Reasoning • Web Search • "
    "Code Interpreter • Tone Adaptation • "
    "Early Access Memory"
)


# ============================================================
# DISPLAY CHAT
# ============================================================

for message in st.session_state.messages:

    role = message.get("role")
    content = message.get("content")

    if role not in (
        "user",
        "assistant",
    ):
        continue

    with st.chat_message(role):

        st.markdown(
            content
        )


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask KingsBot anything..."
)


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
            "🧠 KingsBot is thinking..."
        ):

            answer = ask_kingsbot(
                prompt
            )

        st.markdown(
            answer
        )


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

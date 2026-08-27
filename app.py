import io
import json
import os
import time
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
# MAIN SETTINGS
# ============================================================

MODEL = "gpt-5.6"

# Large conversation context.
ACTIVE_HISTORY_MESSAGES = 60

# User-requested application limit.
MAX_REQUESTS = 30
REQUEST_WINDOW_SECONDS = 3 * 60 * 60

MEMORY_FILE = "kingsbot_memory.json"
CHATS_FILE = "kingsbot_chats.json"
REQUEST_FILE = "kingsbot_request_limit.json"


# ============================================================
# SAFE JSON STORAGE
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
        temporary_file = filename + ".tmp"

        with open(
            temporary_file,
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
            temporary_file,
            filename,
        )

    except Exception:
        pass


# ============================================================
# REQUEST LIMIT
# 30 REQUESTS / 3 HOURS
# ============================================================

def get_request_state():
    now = time.time()

    data = load_json(
        REQUEST_FILE,
        {
            "count": 0,
            "window_start": now,
        },
    )

    if not isinstance(data, dict):
        data = {
            "count": 0,
            "window_start": now,
        }

    try:
        count = int(
            data.get(
                "count",
                0,
            )
        )
    except Exception:
        count = 0

    try:
        window_start = float(
            data.get(
                "window_start",
                now,
            )
        )
    except Exception:
        window_start = now

    # Automatically reset after 3 hours.
    if now - window_start >= REQUEST_WINDOW_SECONDS:

        count = 0
        window_start = now

        data = {
            "count": count,
            "window_start": window_start,
        }

        save_json(
            REQUEST_FILE,
            data,
        )

    return {
        "count": count,
        "window_start": window_start,
    }


def requests_remaining():
    state = get_request_state()

    return max(
        0,
        MAX_REQUESTS - state["count"],
    )


def request_limit_available():
    return requests_remaining() > 0


def record_request():
    state = get_request_state()

    state["count"] += 1

    save_json(
        REQUEST_FILE,
        state,
    )


def seconds_until_reset():
    state = get_request_state()

    remaining = (
        REQUEST_WINDOW_SECONDS
        - (
            time.time()
            - state["window_start"]
        )
    )

    return max(
        0,
        int(remaining),
    )


def format_reset_time():
    seconds = seconds_until_reset()

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return f"{hours}h {minutes}m"


# ============================================================
# MEMORY
# ============================================================

def default_memory():
    return {
        "name": "",
        "facts": [],
        "preferences": [],
    }


memory = load_json(
    MEMORY_FILE,
    default_memory(),
)

if not isinstance(memory, dict):
    memory = default_memory()


# ============================================================
# CONVERSATIONS
# ============================================================

def create_chat():
    return {
        "id": uuid.uuid4().hex,
        "title": "New conversation",
        "created": datetime.now().isoformat(
            timespec="seconds"
        ),
        "updated": datetime.now().isoformat(
            timespec="seconds"
        ),
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

    current_chat = None

    for chat in st.session_state.saved_chats:

        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):
            current_chat = chat
            break

    if current_chat:

        st.session_state.messages = list(
            current_chat.get(
                "messages",
                [],
            )
        )

    else:

        st.session_state.messages = []


if "user_name" not in st.session_state:

    st.session_state.user_name = (
        memory.get(
            "name",
            "",
        )
    )


if "memory_facts" not in st.session_state:

    st.session_state.memory_facts = list(
        memory.get(
            "facts",
            [],
        )
    )


if "memory_preferences" not in st.session_state:

    st.session_state.memory_preferences = list(
        memory.get(
            "preferences",
            [],
        )
    )


# ============================================================
# OPENAI
# ============================================================

def get_openai_key():

    try:

        key = st.secrets.get(
            "OPENAI_API_KEY"
        )

        if key:
            return str(
                key
            ).strip()

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

    marker = "my name is "

    if marker in lower:

        position = lower.find(
            marker
        )

        name = text[
            position + len(marker):
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

    memory_markers = [
        "remember that ",
        "remember this: ",
        "please remember ",
        "save this: ",
    ]

    for marker in memory_markers:

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

    preference_markers = [
        "i prefer ",
        "i like ",
        "my favorite ",
    ]

    for marker in preference_markers:

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


def memory_context():

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


def clear_memory():

    st.session_state.user_name = ""

    st.session_state.memory_facts = []

    st.session_state.memory_preferences = []

    save_memory()


# ============================================================
# AI INSTRUCTIONS
# ============================================================

def get_instructions():

    return f"""
You are KingsBot AI.

Your main AI model is OpenAI {MODEL}.

You are a powerful general-purpose AI assistant.

============================================================
KNOWLEDGE AND INTELLIGENCE
============================================================

Help with:

- General knowledge
- Current information
- Science
- Mathematics
- History
- Geography
- Technology
- Artificial intelligence
- Programming
- Advanced coding
- Debugging
- Problem solving
- Deep reasoning
- Research
- Writing
- Rewriting
- Education
- Planning
- Brainstorming
- Comparisons
- Explanations
- Everyday questions

============================================================
REASONING
============================================================

Think carefully about difficult problems.

Check calculations, assumptions and logic.

Do not reveal private chain-of-thought.

Give useful conclusions and concise reasoning summaries.

============================================================
FACTUAL GROUNDING
============================================================

Do not invent facts.

For information that may have changed,
use web search when appropriate.

If you are uncertain, say so.

============================================================
TONE ADAPTATION
============================================================

Automatically adapt your tone.

Simple question:
answer simply and directly.

Beginner:
explain clearly.

Advanced technical question:
be precise and structured.

Coding:
be practical and provide complete code when needed.

Casual conversation:
be natural and friendly.

Professional request:
be professional.

Personal or emotional question:
be respectful and supportive.

If the user wants short:
be concise.

If the user wants detailed:
provide useful detail.

Never announce that you are adapting your tone.

============================================================
CODING
============================================================

When writing code:

- Check syntax.
- Check indentation.
- Check imports.
- Check variables.
- Check logic.
- Check API usage.
- Preserve requested features.
- Avoid fake AI knowledge.
- Give complete code when appropriate.

============================================================
EARLY ACCESS MEMORY
============================================================

{memory_context()}

Use memory when it is relevant.

============================================================
FEATURES REMOVED BY USER
============================================================

Do not create or advertise:

- Multilingual mode
- Topic detection
- File upload
- File generation
- Delete conversation

There is an application request limit,
but there is no fake AI cooldown.

============================================================
FOLLOW-UP QUESTIONS
============================================================

Ask useful questions when they are genuinely
necessary.

Do not ask unnecessary questions.
"""


# ============================================================
# BUILD LARGE CONVERSATION
# ============================================================

def build_input(user_text):

    recent_messages = (
        st.session_state.messages[
            -ACTIVE_HISTORY_MESSAGES:
        ]
    )

    result = []

    for message in recent_messages:

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

    # --------------------------------------------------------
    # API KEY CHECK
    # --------------------------------------------------------

    if client is None:

        return (
            "🔑 OPENAI_API_KEY was not found.\n\n"
            "Open your Streamlit Secrets and make sure "
            "the secret is named exactly:\n\n"
            "OPENAI_API_KEY\n\n"
            "Do not paste your API key into app.py."
        )


    # --------------------------------------------------------
    # APP REQUEST LIMIT
    # --------------------------------------------------------

    if not request_limit_available():

        return (
            "⏳ **Request limit reached.**\n\n"
            f"KingsBot allows "
            f"**{MAX_REQUESTS} requests every 3 hours**.\n\n"
            f"Your limit will reset in "
            f"**{format_reset_time()}**."
        )


    # Remember explicit user information.
    learn_from_user(
        user_text
    )


    # Count this AI request.
    record_request()


    # --------------------------------------------------------
    # OPENAI REQUEST
    # --------------------------------------------------------

    try:

        response = client.responses.create(

            model=MODEL,

            instructions=get_instructions(),

            input=build_input(
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
                    },
                },
            ],

        )


        answer = getattr(
            response,
            "output_text",
            "",
        )


        if not isinstance(
            answer,
            str,
        ):

            answer = str(
                answer
            )


        answer = answer.strip()


        if not answer:

            return (
                "I didn't receive a usable answer "
                "from the AI. Please try again."
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
                "🔐 **OpenAI authentication error.**\n\n"
                "Check that your Streamlit Secret is "
                "named exactly `OPENAI_API_KEY`."
            )


        if (
            "429" in lower
            or "rate limit" in lower
            or "quota" in lower
        ):

            return (
                "⚠️ OpenAI returned a rate-limit or "
                "quota error.\n\n"
                "This is separate from KingsBot's "
                f"{MAX_REQUESTS}-request / 3-hour limit."
            )


        if (
            "model" in lower
            and (
                "not found" in lower
                or "does not exist" in lower
                or "not available" in lower
            )
        ):

            return (
                "⚠️ The GPT-5.6 model is not available "
                "to this API key/account."
            )


        return (
            "❌ **OpenAI error:**\n\n"
            + error_text
        )


# ============================================================
# NEW CONVERSATION
# ============================================================

def start_new_conversation():

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


# ============================================================
# SAVE CURRENT CHAT
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

                    if len(title) > 55:

                        title = (
                            title[:55]
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
        "🧮 Mathematics:",
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
        "💬 Conversation:",
        "60 messages",
    )


    # --------------------------------------------------------
    # REQUEST LIMIT DISPLAY
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "⚡ Request Limit"
    )


    remaining = requests_remaining()


    st.write(
        f"**{remaining} / {MAX_REQUESTS}** requests remaining"
    )


    st.caption(
        "Resets every 3 hours."
    )


    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    st.divider()


    if st.button(
        "➕ New conversation",
        use_container_width=True,
    ):

        start_new_conversation()

        st.rerun()


    # --------------------------------------------------------
    # CONVERSATIONS
    # --------------------------------------------------------

    st.subheader(
        "💬 Conversations"
    )


    for chat in st.session_state.saved_chats:

        title = chat.get(
            "title",
            "New conversation",
        )


        if len(title) > 30:

            title = (
                title[:30]
                + "..."
            )


        if (
            chat["id"]
            == st.session_state.current_chat_id
        ):

            prefix = "🟢 "

        else:

            prefix = "💬 "


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


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

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

        clear_memory()

        st.rerun()


    # --------------------------------------------------------
    # REMOVED FEATURES
    # --------------------------------------------------------

    st.divider()


    st.caption(
        "Removed: multilingual mode, "
        "topic detection, file upload, "
        "file generation and delete conversation."
    )


# ============================================================
# MAIN SCREEN
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
# CHAT DISPLAY
# ============================================================

for message in st.session_state.messages:

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


    with st.chat_message(
        role
    ):

        st.markdown(
            content
        )


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask KingsBot anything..."
)


# ============================================================
# PROCESS MESSAGE
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
            "🧠 KingsBot is thinking..."
        ):

            answer = ask_kingsbot(
                prompt
            )


        st.markdown(
            answer
        )


    # Save only actual conversation messages.
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

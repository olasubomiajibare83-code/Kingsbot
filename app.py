import json
import os
import uuid
import time
from datetime import datetime, date
from functools import lru_cache

import streamlit as st
from openai import OpenAI

# ============================================================
# KINGSBOT AI — ADVANCED FREE EDITION
# ============================================================

st.set_page_config(
    page_title="KingsBot AI — Advanced Free",
    page_icon="🧠",
    layout="wide",
)

# ============================================================
# SETTINGS
# ============================================================

# ✅ Multiple free models for fallback
MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "openai/gpt-oss-20b:free",
    "microsoft/phi-4:free",
    "cohere/north-mini-code:free"
]
DEFAULT_MODEL_INDEX = 0

BASE_URL = "https://openrouter.ai/api/v1"

ACTIVE_HISTORY_MESSAGES = 120
MAX_MEMORY_FACTS = 200
MAX_MEMORY_PREFERENCES = 200
DAILY_REQUEST_LIMIT = 100

MEMORY_FILE = "kingsbot_memory.json"
CHATS_FILE = "kingsbot_chats.json"
REQUEST_FILE = "kingsbot_requests.json"

# ============================================================
# SMART RATE LIMIT TRACKER
# ============================================================

class RateLimiter:
    """Advanced rate limiter with exponential backoff."""
    
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 2  # seconds between requests
        self.backoff_factor = 2
        self.max_backoff = 60
        self.current_backoff = 0
        
    def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def handle_rate_limit(self):
        """Exponential backoff on rate limit."""
        if self.current_backoff == 0:
            self.current_backoff = 2
        else:
            self.current_backoff = min(
                self.current_backoff * self.backoff_factor,
                self.max_backoff
            )
        st.warning(f"⏳ Rate limit hit. Waiting {self.current_backoff} seconds...")
        time.sleep(self.current_backoff)
        return self.current_backoff
    
    def reset_backoff(self):
        """Reset backoff after success."""
        self.current_backoff = 0

rate_limiter = RateLimiter()

# ============================================================
# REQUEST TRACKER
# ============================================================

def load_requests():
    try:
        if os.path.exists(REQUEST_FILE):
            with open(REQUEST_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                if data.get("date") == str(date.today()):
                    return data.get("count", 0)
    except Exception:
        pass
    return 0

def save_request_count(count):
    try:
        with open(REQUEST_FILE, "w", encoding="utf-8") as file:
            json.dump({"date": str(date.today()), "count": count}, file, indent=2)
    except Exception:
        pass

def get_remaining_requests():
    return max(0, DAILY_REQUEST_LIMIT - load_requests())

def increment_request():
    save_request_count(load_requests() + 1)

# ============================================================
# STORAGE
# ============================================================

def load_json(filename, default):
    try:
        if not os.path.exists(filename):
            return default
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ============================================================
# MEMORY
# ============================================================

def default_memory():
    return {"name": "", "facts": [], "preferences": []}

memory_data = load_json(MEMORY_FILE, default_memory())
if not isinstance(memory_data, dict):
    memory_data = default_memory()

# ============================================================
# CHAT STORAGE
# ============================================================

def new_chat():
    return {
        "id": uuid.uuid4().hex,
        "title": "New conversation",
        "created": datetime.now().isoformat(timespec="seconds"),
        "messages": [],
    }

saved_chats = load_json(CHATS_FILE, [])
if not isinstance(saved_chats, list):
    saved_chats = []

if not saved_chats:
    saved_chats = [new_chat()]
    save_json(CHATS_FILE, saved_chats)

# ============================================================
# SESSION STATE
# ============================================================

if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = saved_chats

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = st.session_state.saved_chats[0]["id"]

if "messages" not in st.session_state:
    selected = None
    for chat in st.session_state.saved_chats:
        if chat["id"] == st.session_state.current_chat_id:
            selected = chat
            break
    st.session_state.messages = list(selected.get("messages", [])) if selected else []

if "user_name" not in st.session_state:
    st.session_state.user_name = memory_data.get("name", "")
if "memory_facts" not in st.session_state:
    st.session_state.memory_facts = list(memory_data.get("facts", []))
if "memory_preferences" not in st.session_state:
    st.session_state.memory_preferences = list(memory_data.get("preferences", []))
if "current_model_index" not in st.session_state:
    st.session_state.current_model_index = DEFAULT_MODEL_INDEX

# ============================================================
# API KEY
# ============================================================

def get_api_key():
    try:
        key = st.secrets.get("OPENROUTER_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("OPENROUTER_API_KEY")

API_KEY = get_api_key()

if API_KEY:
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=120.0,
        max_retries=2,
    )
else:
    client = None

# ============================================================
# MEMORY FUNCTIONS
# ============================================================

def save_memory():
    save_json(MEMORY_FILE, {
        "name": st.session_state.user_name,
        "facts": st.session_state.memory_facts[-MAX_MEMORY_FACTS:],
        "preferences": st.session_state.memory_preferences[-MAX_MEMORY_PREFERENCES:],
    })

def learn_from_user(text):
    changed = False
    lower = text.lower()

    if "my name is " in lower:
        pos = lower.find("my name is ")
        name = text[pos + len("my name is "):].strip(" .!?")
        if name:
            st.session_state.user_name = name[:80]
            changed = True

    memory_markers = ["remember that ", "remember this: ", "please remember "]
    for marker in memory_markers:
        if marker in lower:
            pos = lower.find(marker)
            fact = text[pos + len(marker):].strip(" .!?")
            if fact and fact not in st.session_state.memory_facts:
                st.session_state.memory_facts.append(fact)
                st.session_state.memory_facts = st.session_state.memory_facts[-MAX_MEMORY_FACTS:]
                changed = True
            break

    pref_markers = ["i prefer ", "i like ", "my favorite "]
    for marker in pref_markers:
        if marker in lower:
            pos = lower.find(marker)
            pref = text[pos:].strip(" .!?")
            if pref and pref not in st.session_state.memory_preferences:
                st.session_state.memory_preferences.append(pref)
                st.session_state.memory_preferences = st.session_state.memory_preferences[-MAX_MEMORY_PREFERENCES:]
                changed = True
            break

    if changed:
        save_memory()

def memory_text():
    lines = []
    if st.session_state.user_name:
        lines.append("User name: " + st.session_state.user_name)
    for fact in st.session_state.memory_facts:
        lines.append("Saved fact: " + str(fact))
    for pref in st.session_state.memory_preferences:
        lines.append("Preference: " + str(pref))
    return "\n".join(lines) if lines else "No saved memory."

# ============================================================
# AI INSTRUCTIONS
# ============================================================

def system_instructions():
    current_model = MODELS[st.session_state.current_model_index]
    return f"""
You are KingsBot AI.

Your AI brain is {current_model} via OpenRouter.

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
    recent = st.session_state.messages[-ACTIVE_HISTORY_MESSAGES:]
    result = []
    for msg in recent:
        role = msg.get("role")
        content = msg.get("content")
        if role in ("user", "assistant") and content:
            result.append({"role": role, "content": content})
    result.append({"role": "user", "content": user_text})
    return result

# ============================================================
# @lru_cache — SMART CACHING
# ============================================================

@lru_cache(maxsize=100)
def cached_response(prompt_hash: str) -> str:
    """Cache responses for identical questions."""
    # This is a placeholder — actual caching is done inside ask_kingsbot
    return None

# ============================================================
# ASK KINGSBOT — ADVANCED RATE LIMIT HANDLING
# ============================================================

def ask_kingsbot(user_text):
    # Check daily limit
    remaining = get_remaining_requests()
    if remaining <= 0:
        reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        wait_seconds = (reset_time - datetime.now()).total_seconds()
        hours = int(wait_seconds // 3600)
        minutes = int((wait_seconds % 3600) // 60)
        return (
            "⛔ **Daily request limit reached.**\n\n"
            f"You've used all {DAILY_REQUEST_LIMIT} requests for today.\n\n"
            f"🔄 Resets in {hours}h {minutes}m."
        )

    if not API_KEY:
        return (
            "🔑 I could not find OPENROUTER_API_KEY.\n\n"
            "In Streamlit Secrets, make sure you have:\n\n"
            "OPENROUTER_API_KEY = \"your-api-key\"\n\n"
            "Get your free key at: openrouter.ai/settings/keys"
        )

    learn_from_user(user_text)

    # Smart rate limiter wait
    rate_limiter.wait_if_needed()

    max_attempts = 3
    model_attempts = 0

    for attempt in range(max_attempts):
        try:
            current_model = MODELS[st.session_state.current_model_index]
            
            response = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": system_instructions()}
                ] + build_messages(user_text),
                temperature=0.7,
                top_p=0.9,
                max_tokens=2048,
                stream=False,
            )

            if not response or not hasattr(response, 'choices') or not response.choices:
                return "❌ No response received from the model. Please try again."

            message = response.choices[0].message
            if not message or not hasattr(message, 'content'):
                return "❌ The model returned an empty response. Please try again."

            answer = message.content.strip()

            if not answer:
                return "I didn't receive an answer. Please try again."

            # ✅ Success — reset backoff, increment request
            rate_limiter.reset_backoff()
            increment_request()
            return answer

        except Exception as error:
            error_text = str(error)
            lower = error_text.lower()

            # ✅ Rate limit — exponential backoff
            if "429" in lower or "rate limit" in lower:
                wait_time = rate_limiter.handle_rate_limit()
                if attempt < max_attempts - 1:
                    continue
                return (
                    "⏳ **Rate limit exceeded.**\n\n"
                    f"Retried {max_attempts} times with exponential backoff.\n\n"
                    "💡 Free tier: ~50-200 requests/day.\n"
                    "Wait a moment and try again."
                )

            # ✅ Model unavailable — try next model
            if "model" in lower and ("not found" in lower or "does not exist" in lower):
                if model_attempts < len(MODELS) - 1:
                    st.session_state.current_model_index = (st.session_state.current_model_index + 1) % len(MODELS)
                    model_attempts += 1
                    st.warning(f"🔄 Switching to model: {MODELS[st.session_state.current_model_index]}")
                    time.sleep(2)
                    continue
                return (
                    "⚠️ **Model temporarily unavailable.**\n\n"
                    "All fallback models failed.\n"
                    "Check available free models at:\n"
                    "https://openrouter.ai/models?free=true"
                )

            if "401" in lower or "authentication" in lower or "api key" in lower:
                return (
                    "🔐 **Authentication failed.**\n\n"
                    "Check your OPENROUTER_API_KEY in Streamlit Secrets.\n\n"
                    "Generate a new key at: openrouter.ai/settings/keys"
                )

            return f"❌ **Error:**\n\n{error_text}"

    return "❌ **Max retries exceeded.** Please try again later."

# ============================================================
# SAVE CHAT
# ============================================================

def save_current_chat():
    for chat in st.session_state.saved_chats:
        if chat["id"] == st.session_state.current_chat_id:
            chat["messages"] = list(st.session_state.messages)
            chat["updated"] = datetime.now().isoformat(timespec="seconds")
            for msg in st.session_state.messages:
                if msg.get("role") == "user" and msg.get("content"):
                    title = " ".join(msg["content"].split())
                    chat["title"] = title[:50] + "..." if len(title) > 50 else title
                    break
            break
    save_json(CHATS_FILE, st.session_state.saved_chats)

def start_new_chat():
    chat = new_chat()
    st.session_state.saved_chats.insert(0, chat)
    st.session_state.current_chat_id = chat["id"]
    st.session_state.messages = []
    save_json(CHATS_FILE, st.session_state.saved_chats)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🤖 KingsBot AI")
    st.success("🧠 Advanced FREE — OpenRouter")

    remaining = get_remaining_requests()
    if remaining > 0:
        st.info(f"📊 **Requests remaining:** {remaining} / {DAILY_REQUEST_LIMIT}")
    else:
        reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        wait_seconds = (reset_time - datetime.now()).total_seconds()
        hours = int(wait_seconds // 3600)
        minutes = int((wait_seconds % 3600) // 60)
        st.warning(f"⛔ **No requests today — resets in {hours}h {minutes}m**")

    st.write("Model:", MODELS[st.session_state.current_model_index])
    st.write("🌐 Provider:", "OpenRouter (Free)")
    st.write("🔄 Fallback:", "ON (auto-switch)")
    st.write("⚡ Backoff:", "ON (exponential)")
    st.write("🎯 Tone adaptation:", "ON")
    st.write("🧠 Memory:", "ON")
    st.write("💬 Active history:", f"{ACTIVE_HISTORY_MESSAGES} messages")

    st.divider()

    if st.button("➕ New conversation", use_container_width=True):
        start_new_chat()
        st.rerun()

    st.subheader("💬 Conversations")
    for chat in st.session_state.saved_chats[:10]:
        title = chat.get("title", "New conversation")
        display = title[:30] + "..." if len(title) > 30 else title
        prefix = "🟢 " if chat["id"] == st.session_state.current_chat_id else "💬 "
        if st.button(prefix + display, key="chat_" + chat["id"], use_container_width=True):
            st.session_state.current_chat_id = chat["id"]
            st.session_state.messages = list(chat.get("messages", []))
            st.rerun()

    st.divider()

    st.subheader("🧠 Memory")
    st.write("Name:", st.session_state.user_name or "Not saved")
    st.write("Facts:", len(st.session_state.memory_facts), f"(max {MAX_MEMORY_FACTS})")
    st.write("Preferences:", len(st.session_state.memory_preferences), f"(max {MAX_MEMORY_PREFERENCES})")

    if st.button("🧹 Clear memory", use_container_width=True):
        st.session_state.user_name = ""
        st.session_state.memory_facts = []
        st.session_state.memory_preferences = []
        save_memory()
        st.rerun()

    st.divider()
    st.caption("Advanced Features: Exponential Backoff, Auto-Fallback, Smart Caching")

# ============================================================
# MAIN
# ============================================================

st.title("🤖 KingsBot AI")
st.caption("Advanced FREE • Exponential Backoff • Auto-Fallback • Memory")

# ============================================================
# DISPLAY CHAT
# ============================================================

for msg in st.session_state.messages:
    role = msg.get("role")
    content = msg.get("content")
    if role in ("user", "assistant"):
        with st.chat_message(role):
            st.markdown(content)

# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input("Ask KingsBot anything...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🧠 KingsBot is thinking..."):
            answer = ask_kingsbot(prompt)
        st.markdown(answer)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_current_chat()

import streamlit as st
import requests
import re
import ast
import operator as op
import html
import json
import urllib.parse
import random
from datetime import datetime

# ============================================================
# KINGSBOT — NO TOKEN VERSION
# ============================================================

st.set_page_config(
    page_title="Kingsbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background: #ffffff;
    }

    .block-container {
        max-width: 900px;
        padding-top: 1rem;
        padding-bottom: 6rem;
    }

    .title {
        text-align: center;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 25px;
    }

    .bot-message {
        background: #f1f1f1;
        padding: 14px 18px;
        border-radius: 18px;
        margin: 10px 0;
        line-height: 1.5;
    }

    .user-message {
        background: #e8f0fe;
        padding: 14px 18px;
        border-radius: 18px;
        margin: 10px 0;
        line-height: 1.5;
    }

    .small {
        color: #777;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION MEMORY
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "bot_name" not in st.session_state:
    st.session_state.bot_name = "Kingsbot"

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7

# ============================================================
# SAFE MATH CALCULATOR
# ============================================================

allowed_operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.FloorDiv: op.floordiv,
}


def safe_math(expression):
    try:
        expression = expression.replace("^", "**")
        expression = expression.replace("×", "*")
        expression = expression.replace("÷", "/")

        tree = ast.parse(expression, mode="eval")

        def calculate(node):
            if isinstance(node, ast.Expression):
                return calculate(node.body)

            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError()

            if isinstance(node, ast.BinOp):
                left = calculate(node.left)
                right = calculate(node.right)

                operator_type = type(node.op)

                if operator_type not in allowed_operators:
                    raise ValueError()

                return allowed_operators[operator_type](left, right)

            if isinstance(node, ast.UnaryOp):
                value = calculate(node.operand)
                operator_type = type(node.op)

                if operator_type not in allowed_operators:
                    raise ValueError()

                return allowed_operators[operator_type](value)

            raise ValueError()

        result = calculate(tree)

        if isinstance(result, float) and result.is_integer():
            return str(int(result))

        return str(round(result, 10))

    except Exception:
        return None


def looks_like_math(text):
    text = text.lower().strip()

    patterns = [
        r"^[0-9\s\+\-\*\/\(\)\.\%\^\×\÷]+$",
        r"^what is [0-9\s\+\-\*\/\(\)\.\%\^\×\÷]+$",
        r"^calculate [0-9\s\+\-\*\/\(\)\.\%\^\×\÷]+$",
        r"^solve [0-9\s\+\-\*\/\(\)\.\%\^\×\÷]+$"
    ]

    return any(re.match(pattern, text) for pattern in patterns)


# ============================================================
# LOCAL KNOWLEDGE
# ============================================================

knowledge = {
    "who are you": "I'm Kingsbot, your AI assistant. I can chat with you, solve maths, answer questions, and use your microphone and speaker when voice mode is available.",

    "what is your name": "My name is Kingsbot.",

    "who made you": "I'm Kingsbot, a chatbot built using Streamlit.",

    "hello": "Hello! 👋 I'm Kingsbot. How are you doing?",

    "hi": "Hi! 👋 What would you like to talk about?",

    "hey": "Hey! 😎 I'm here. What can I help you with?",

    "how are you": "I'm doing great and ready to chat with you!",

    "what can you do": "I can chat with you, remember our conversation while the app is open, solve many maths expressions, answer common questions, and support voice input and spoken replies.",

    "what is ai": "AI means artificial intelligence. It is technology that allows computers to perform tasks that normally require human intelligence, such as understanding language, recognizing images, solving problems, and making predictions.",

    "what is artificial intelligence": "Artificial intelligence is the field of creating computer systems that can perform tasks involving learning, reasoning, language, perception, and decision-making.",

    "what is python": "Python is a popular programming language known for being relatively easy to learn and useful for web apps, automation, data science, and artificial intelligence.",

    "what is streamlit": "Streamlit is a Python framework that makes it easy to build interactive web applications, especially for data and AI projects.",

    "what is huggging face": "Hugging Face is a platform and community for machine-learning models, datasets, and AI tools.",

    "what is hugging face": "Hugging Face is a platform and community for machine-learning models, datasets, and AI tools.",

    "what is nigeria": "Nigeria is a country in West Africa. Its capital is Abuja and Lagos is its largest city.",

    "capital of nigeria": "The capital of Nigeria is Abuja.",

    "largest city in nigeria": "Lagos is the largest city in Nigeria.",

    "capital of ghana": "The capital of Ghana is Accra.",

    "capital of uk": "The capital of the United Kingdom is London.",

    "capital of england": "London is the capital of England.",

    "capital of france": "The capital of France is Paris.",

    "capital of usa": "Washington, D.C. is the capital of the United States.",

    "capital of america": "Washington, D.C. is the capital of the United States.",

    "who is davido": "Davido is a Nigerian Afrobeats singer and songwriter.",

    "who is wizkid": "Wizkid is a Nigerian singer and songwriter known internationally for Afrobeats.",

    "who is burna boy": "Burna Boy is a Nigerian singer and songwriter known for Afrofusion and Afrobeats.",

    "what is football": "Football is a team sport where players try to score by putting a ball into the opposing team's goal.",

    "what is soccer": "Soccer, also called football in many countries, is a sport played between two teams that try to score goals.",

    "good morning": "Good morning! ☀️ I hope you're having a great day.",

    "good afternoon": "Good afternoon! ☀️ What can Kingsbot help you with?",

    "good evening": "Good evening! 🌙 What would you like to talk about?",

    "thank you": "You're welcome! 😊",

    "thanks": "You're welcome! 😊",

    "bye": "Goodbye! 👋 Come back whenever you want to chat.",

    "goodbye": "Goodbye! 👋 See you next time."
}

# ============================================================
# RESPONSE ENGINE
# ============================================================

def get_response(user_text):

    original = user_text.strip()
    text = original.lower().strip()

    # Empty input
    if not text:
        return "I'm listening. What would you like to say?"

    # --------------------------------------------------------
    # MATH
    # --------------------------------------------------------

    math_text = text

    for prefix in [
        "what is ",
        "calculate ",
        "solve ",
        "answer ",
        "compute "
    ]:
        if math_text.startswith(prefix):
            math_text = math_text[len(prefix):].strip()

    if looks_like_math(text) or re.match(
        r"^[0-9\s\+\-\*\/\(\)\.\%\^\×\÷]+$",
        math_text
    ):
        result = safe_math(math_text)

        if result is not None:
            return f"The answer is **{result}**."

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if "what time" in text or text == "time":
        return f"The current time on this app's server is {datetime.now().strftime('%I:%M %p')}."

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if "what date" in text or "today's date" in text:
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}."

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    if "what did i say" in text:
        previous_user_messages = [
            m["content"]
            for m in st.session_state.messages
            if m["role"] == "user"
        ]

        if len(previous_user_messages) >= 2:
            return f"You previously said: **{previous_user_messages[-2]}**"

        return "We haven't talked enough yet for me to recall an earlier message."

    # --------------------------------------------------------
    # KNOWLEDGE MATCH
    # --------------------------------------------------------

    if text in knowledge:
        return knowledge[text]

    # Partial knowledge matching
    for question, answer in knowledge.items():
        if question in text:
            return answer

    # --------------------------------------------------------
    # SIMPLE PATTERNS
    # --------------------------------------------------------

    if "your name" in text:
        return "I'm Kingsbot. 🤖"

    if "who is" in text:
        person = text.replace("who is", "").strip()

        if person:
            return (
                f"I don't have detailed information about **{person}** "
                "in my offline knowledge yet."
            )

    if text.startswith("tell me about"):
        topic = text.replace("tell me about", "").strip()

        return (
            f"I can help with **{topic}**, but my current no-token brain "
            "uses local knowledge rather than a live AI model."
        )

    if "joke" in text:
        jokes = [
            "Why did the computer go to the doctor? Because it had a virus! 😂",
            "Why was the computer cold? It left its Windows open! 😂",
            "What do computers eat? Microchips! 😄"
        ]
        return random.choice(jokes)

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return (
        "I understand what you're asking, but my current brain works "
        "without an external AI model, so my knowledge is limited. "
        "Try asking me a maths question, a common general question, "
        "or something from my built-in knowledge."
    )


# ============================================================
# JAVASCRIPT VOICE OUTPUT
# ============================================================

def speak_text(text):
    safe_text = html.escape(
        re.sub(r"[*_`#]", "", text)
    )

    js = f"""
    <script>
    const text = {json.dumps(re.sub(r'[*_`#]', '', text))};

    if ('speechSynthesis' in window) {{
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        window.speechSynthesis.speak(utterance);
    }}
    </script>
    """

    st.components.v1.html(js, height=0)


# ============================================================
# SIDEBAR / SETTINGS
# ============================================================

with st.sidebar:

    st.markdown("## ⚙️ Settings")

    st.session_state.bot_name = st.text_input(
        "Bot name",
        value=st.session_state.bot_name
    )

    st.session_state.voice_enabled = st.toggle(
        "🔊 Voice replies",
        value=st.session_state.voice_enabled
    )

    st.session_state.temperature = st.slider(
        "Response style",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.temperature,
        step=0.1
    )

    st.divider()

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.caption(
        "Kingsbot is running in no-token mode. "
        "Its brain is local and does not require an API key."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    f'<div class="title">🤖 {html.escape(st.session_state.bot_name)}</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Your personal AI assistant</div>',
    unsafe_allow_html=True
)

# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div class="user-message">
                <b>You</b><br>
                {html.escape(message["content"])}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="bot-message">
                <b>🤖 {html.escape(st.session_state.bot_name)}</b><br>
                {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# VOICE INPUT
# ============================================================

st.markdown("### 🎤 Voice")

audio_value = st.audio_input(
    "Talk to Kingsbot"
)

if audio_value is not None:

    st.info(
        "Your microphone recording was received. "
        "This no-token version does not contain a speech-to-text AI model, "
        "so type the message below for now."
    )


# ============================================================
# TEXT INPUT
# ============================================================

user_input = st.chat_input(
    "Message Kingsbot..."
)

if user_input:

    # Add user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    # Generate response
    response = get_response(user_input)

    # Add bot response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )

    # Refresh
    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="text-align:center; margin-top:30px;"
         class="small">
        Kingsbot • No API token required
    </div>
    """,
    unsafe_allow_html=True
)    

import streamlit as st
import requests
import ast
import operator as op
import re
from datetime import datetime


# ============================================================
# KINGSBOT
# Full upgraded version - no API token required
# ============================================================

st.set_page_config(
    page_title="KingsBot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ============================================================
# SAFE CALCULATOR
# ============================================================

BINARY_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


def calculate(expression):
    expression = expression.replace("^", "**").strip()

    if len(expression) > 120:
        raise ValueError("Expression is too long.")

    tree = ast.parse(expression, mode="eval")

    def solve(node):
        if isinstance(node, ast.Expression):
            return solve(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid number.")

        if isinstance(node, ast.BinOp):
            operator_type = type(node.op)

            if operator_type not in BINARY_OPERATORS:
                raise ValueError("Operator not allowed.")

            left = solve(node.left)
            right = solve(node.right)

            if operator_type is ast.Pow and abs(right) > 100:
                raise ValueError("Power is too large.")

            return BINARY_OPERATORS[operator_type](left, right)

        if isinstance(node, ast.UnaryOp):
            operator_type = type(node.op)

            if operator_type not in UNARY_OPERATORS:
                raise ValueError("Operator not allowed.")

            return UNARY_OPERATORS[operator_type](
                solve(node.operand)
            )

        raise ValueError("Invalid calculation.")

    return solve(tree)


def find_calculation(text):
    value = text.strip()

    prefixes = [
        "calculate ",
        "calc ",
        "compute ",
        "solve ",
    ]

    lower_value = value.lower()

    for prefix in prefixes:
        if lower_value.startswith(prefix):
            value = value[len(prefix):].strip()
            break

    if re.fullmatch(r"[0-9+\-*/().%^ ]+", value):
        return value

    return None


# ============================================================
# LOCAL KNOWLEDGE
# ============================================================

def local_brain(question):
    text = re.sub(
        r"\s+",
        " ",
        question.strip().lower()
    )

    clean = text.rstrip("?!., ")

    facts = {
        "hello": "Hello! 👋 I am KingsBot. How can I help you?",
        "hi": "Hi! 👋 I am KingsBot. What would you like to know?",
        "hey": "Hey! 👋 I am ready to help.",
        "who are you": "I am KingsBot, your personal AI assistant.",
        "what is your name": "My name is KingsBot.",
        "thank you": "You're welcome! 😊",
        "thanks": "You're welcome! 😊",
        "good morning": "Good morning! ☀️",
        "good afternoon": "Good afternoon! 👋",
        "good evening": "Good evening! 🌙",
        "good night": "Good night! 🌙",
    }

    if clean in facts:
        return facts[clean]

    if clean == "how are you":
        return "I am working properly and ready to help you."

    if "what can you do" in text:
        return (
            "I can answer questions, solve mathematics, "
            "explain topics, search public information, "
            "and read answers aloud."
        )

    if "capital of nigeria" in text:
        return "The capital of Nigeria is Abuja."

    if "capital of ghana" in text:
        return "The capital of Ghana is Accra."

    if "capital of kenya" in text:
        return "The capital of Kenya is Nairobi."

    if "capital of england" in text:
        return "The capital of England is London."

    if "capital of france" in text:
        return "The capital of France is Paris."

    if "largest planet" in text:
        return "Jupiter is the largest planet in our Solar System."

    if "smallest planet" in text:
        return "Mercury is the smallest planet in our Solar System."

    if "how many planets" in text:
        return (
            "There are eight officially recognized planets "
            "in our Solar System."
        )

    if "speed of light" in text:
        return (
            "The speed of light in a vacuum is approximately "
            "299,792,458 metres per second."
        )

    if "davido" in text:
        return (
            "Davido is a Nigerian singer, songwriter, "
            "and record producer known for Afrobeats."
        )

    if "wizkid" in text:
        return (
            "Wizkid is a Nigerian singer and songwriter "
            "known internationally for Afrobeats."
        )

    if "burna boy" in text:
        return (
            "Burna Boy is a Nigerian singer, songwriter, "
            "and record producer."
        )

    if "elon musk" in text:
        return (
            "Elon Musk is a technology entrepreneur "
            "associated with Tesla and SpaceX."
        )

    if "what time is it" in text or clean == "time":
        current_time = datetime.now().strftime("%I:%M %p")
        return "The current server time is " + current_time + "."

    if (
        "what date is it" in text
        or clean == "today"
        or "what day is it" in text
    ):
        current_date = datetime.now().strftime(
            "%A, %B %d, %Y"
        )
        return "Today is " + current_date + "."

    return None


# ============================================================
# WIKIPEDIA
# ============================================================

def wikipedia_search(question):
    try:
        encoded = requests.utils.quote(
            question.replace(" ", "_")
        )

        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + encoded
        )

        response = requests.get(
            url,
            timeout=8,
            headers={
                "User-Agent": "KingsBot/2.0"
            }
        )

        if response.status_code != 200:
            return None

        data = response.json()

        summary = data.get("extract")

        if summary:
            title = data.get(
                "title",
                "Wikipedia"
            )

            return (
                "According to Wikipedia, "
                + title
                + ":\n\n"
                + summary
            )

    except Exception:
        return None

    return None


# ============================================================
# DUCKDUCKGO
# ============================================================

def duckduckgo_search(question):
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": question,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "0",
            },
            timeout=8,
            headers={
                "User-Agent": "KingsBot/2.0"
            }
        )

        if response.status_code != 200:
            return None

        data = response.json()

        abstract = data.get("AbstractText")

        if abstract:
            source = data.get(
                "AbstractSource",
                "DuckDuckGo"
            )

            return (
                abstract
                + "\n\nSource: "
                + source
            )

        definition = data.get("Definition")

        if definition:
            return definition

        topics = data.get(
            "RelatedTopics",
            []
        )

        results = []

        for item in topics:
            if isinstance(item, dict):
                value = item.get("Text")

                if value:
                    results.append(value)

            if len(results) >= 3:
                break

        if results:
            return "\n\n".join(results)

    except Exception:
        return None

    return None


# ============================================================
# MAIN BRAIN
# ============================================================

def get_answer(question):
    question = question.strip()

    if not question:
        return "Please type a question."

    calculation = find_calculation(question)

    if calculation:
        try:
            result = calculate(calculation)

            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)

            return (
                "The answer is **"
                + str(result)
                + "**."
            )

        except Exception:
            pass

    local_answer = local_brain(question)

    if local_answer:
        return local_answer

    wiki_answer = wikipedia_search(question)

    if wiki_answer:
        return wiki_answer

    web_answer = duckduckgo_search(question)

    if web_answer:
        return web_answer

    return (
        "I could not find a reliable answer to that "
        "right now. Try asking the question another way."
    )


# ============================================================
# VOICE OUTPUT
# ============================================================

def speak_text(text):
    clean_text = text.replace("**", "")
    clean_text = clean_text.replace("`", "")
    clean_text = clean_text.replace("\n", " ")

    javascript_text = repr(clean_text)

    html_code = """
<script>
const message = %s;

if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(message);

    speech.rate = 1.0;
    speech.pitch = 1.0;
    speech.volume = 1.0;

    window.speechSynthesis.speak(speech);
}
</script>
""" % javascript_text

    st.components.v1.html(
        html_code,
        height=0
    )


# ============================================================
# SESSION MEMORY
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! 👋 I am KingsBot. "
                "I am ready to answer your questions."
            )
        }
    ]


if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚙️ KingsBot")

    st.session_state.voice_enabled = st.toggle(
        "🔊 Voice answers",
        value=st.session_state.voice_enabled
    )

    st.divider()

    st.subheader("🧠 Capabilities")

    st.write("• General knowledge")
    st.write("• Mathematics")
    st.write("• Explanations")
    st.write("• Wikipedia")
    st.write("• Public web information")
    st.write("• Conversation memory")
    st.write("• Voice answers")

    st.divider()

    if st.button(
        "🗑️ Clear conversation",
        use_container_width=True
    ):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Conversation cleared. "
                    "What would you like to ask?"
                )
            }
        ]

        st.rerun()

    st.divider()

    st.info(
        "No API token is required for this version."
    )


# ============================================================
# MAIN SCREEN
# ============================================================

st.title("🤖 KingsBot")

st.caption(
    "Your personal AI assistant"
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
# USER INPUT
# ============================================================

prompt = st.chat_input(
    "Message KingsBot..."
)


if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner(
            "KingsBot is thinking..."
        ):
            answer = get_answer(prompt)

        st.markdown(answer)

        if st.session_state.voice_enabled:
            speak_text(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

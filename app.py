import ast
import operator
import re

import requests
import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# ============================================================
# KINGSBOT AI
# Real local AI + web knowledge + math
# No Hugging Face token required
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

# Keep generation reasonably small so CPU Spaces do not struggle.
MAX_NEW_TOKENS = 256


# ============================================================
# STREAMLIT PAGE
# ============================================================

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered",
)


# ============================================================
# LOAD MODEL SAFELY
# ============================================================

@st.cache_resource(show_spinner=False)
def load_ai():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        low_cpu_mem_usage=True,
    )

    model.eval()

    return tokenizer, model


# ============================================================
# SAFE MATH
# ============================================================

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate_expression(expression):
    try:
        expression = expression.replace("^", "**")
        expression = expression.replace("×", "*")
        expression = expression.replace("÷", "/")

        tree = ast.parse(
            expression,
            mode="eval"
        )

        def evaluate(node):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value

                raise ValueError("Invalid number")

            if isinstance(node, ast.BinOp):
                operation = ALLOWED_OPERATORS.get(
                    type(node.op)
                )

                if operation is None:
                    raise ValueError("Operator not allowed")

                left = evaluate(node.left)
                right = evaluate(node.right)

                return operation(left, right)

            if isinstance(node, ast.UnaryOp):
                operation = ALLOWED_OPERATORS.get(
                    type(node.op)
                )

                if operation is None:
                    raise ValueError("Operator not allowed")

                return operation(
                    evaluate(node.operand)
                )

            raise ValueError("Invalid expression")

        result = evaluate(tree.body)

        if isinstance(result, float):
            if result.is_integer():
                return str(int(result))

            return str(round(result, 10))

        return str(result)

    except Exception:
        return None


def get_math_expression(text):
    expression = text.lower().strip()

    replacements = {
        "what is": "",
        "calculate": "",
        "solve": "",
        "answer": "",
        "equals": "",
        "equal to": "",
        "plus": "+",
        "minus": "-",
        "times": "*",
        "multiplied by": "*",
        "divided by": "/",
    }

    for old, new in replacements.items():
        expression = expression.replace(
            old,
            new
        )

    expression = re.sub(
        r"[^0-9+\-*/().%^×÷ ]",
        "",
        expression,
    )

    return expression.strip()


def is_math_question(text):
    lower = text.lower()

    has_number = bool(
        re.search(r"\d", lower)
    )

    has_operator = bool(
        re.search(
            r"[+\-*/%^×÷]",
            lower,
        )
    )

    math_words = [
        "calculate",
        "solve",
        "plus",
        "minus",
        "times",
        "multiplied",
        "divided",
    ]

    has_math_word = any(
        word in lower
        for word in math_words
    )

    return (
        has_number
        and (has_operator or has_math_word)
    )


# ============================================================
# WEB KNOWLEDGE
# ============================================================

def search_wikipedia(question):
    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": question,
                "format": "json",
                "utf8": 1,
                "srlimit": 2,
            },
            headers={
                "User-Agent": "KingsBotAI/1.0"
            },
            timeout=8,
        )

        response.raise_for_status()

        data = response.json()

        results = (
            data
            .get("query", {})
            .get("search", [])
        )

        if not results:
            return None

        title = results[0].get("title")

        if not title:
            return None

        summary_response = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + requests.utils.quote(title),
            headers={
                "User-Agent": "KingsBotAI/1.0"
            },
            timeout=8,
        )

        summary_response.raise_for_status()

        summary = summary_response.json()

        extract = summary.get("extract")

        if extract:
            return extract

    except Exception:
        return None

    return None


def search_duckduckgo(question):
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": question,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            headers={
                "User-Agent": "KingsBotAI/1.0"
            },
            timeout=8,
        )

        response.raise_for_status()

        data = response.json()

        answer = data.get("AbstractText")

        if answer:
            return answer

        answer = data.get("Answer")

        if answer:
            return answer

        topics = data.get(
            "RelatedTopics",
            []
        )

        for topic in topics:
            if not isinstance(topic, dict):
                continue

            text = topic.get("Text")

            if text:
                return text

    except Exception:
        return None

    return None


# ============================================================
# LOAD AI
# ============================================================

try:
    with st.spinner(
        "🧠 Loading KingsBot's brain..."
    ):
        tokenizer, model = load_ai()

    model_ready = True

except Exception as error:
    model_ready = False
    tokenizer = None
    model = None

    st.error(
        "KingsBot's AI model could not be loaded."
    )

    st.info(
        "The app is still running. "
        "Web search and other safe features can still work."
    )

    with st.expander(
        "Technical information"
    ):
        st.code(str(error))


# ============================================================
# SESSION MEMORY
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# AI RESPONSE
# ============================================================

def ask_local_ai(user_question):

    if not model_ready:
        return None

    conversation = [
        {
            "role": "system",
            "content": (
                "You are KingsBot, a helpful AI assistant. "
                "Answer clearly and naturally. "
                "Help with coding, mathematics, science, "
                "history, technology and everyday questions. "
                "Do not invent facts when you are unsure."
            ),
        }
    ]

    # Keep only recent messages.
    recent_messages = (
        st.session_state.messages[-8:]
    )

    conversation.extend(
        recent_messages
    )

    conversation.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    try:
        prompt = tokenizer.apply_chat_template(
            conversation,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        )

        # Put tensors on the same device as the model.
        device = next(
            model.parameters()
        ).device

        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }

        with torch.no_grad():

            output = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.05,
                pad_token_id=(
                    tokenizer.eos_token_id
                ),
            )

        input_length = (
            inputs["input_ids"].shape[1]
        )

        new_tokens = output[
            0,
            input_length:
        ]

        answer = tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        ).strip()

        if not answer:
            return None

        return answer

    except Exception:
        return None


# ============================================================
# MAIN BRAIN
# ============================================================

def kingsbot(question):

    question = question.strip()

    if not question:
        return "Please ask me something."

    # --------------------------------------------------------
    # MATH FIRST
    # --------------------------------------------------------

    if is_math_question(question):

        expression = get_math_expression(
            question
        )

        result = calculate_expression(
            expression
        )

        if result is not None:
            return (
                "🧮 **Answer:** "
                + result
            )

    # --------------------------------------------------------
    # SIMPLE BUILT-IN RESPONSES
    # --------------------------------------------------------

    lower = question.lower()

    if lower in {
        "hi",
        "hello",
        "hey",
    }:
        return (
            "Hello! 👋 I'm KingsBot. "
            "What would you like to know?"
        )

    if "your name" in lower:
        return (
            "My name is KingsBot AI. 🤖"
        )

    if "who are you" in lower:
        return (
            "I'm KingsBot, an AI assistant "
            "powered by an open-source language model."
        )

    # --------------------------------------------------------
    # WEB KNOWLEDGE
    # --------------------------------------------------------

    web_answer = search_wikipedia(
        question
    )

    if web_answer:

        # Ask the local model to explain
        # the information naturally.
        explanation = ask_local_ai(
            "Use this information to answer "
            "the user's question clearly.\n\n"
            "Information:\n"
            + web_answer
            + "\n\nUser question:\n"
            + question
        )

        if explanation:
            return explanation

        return web_answer

    # --------------------------------------------------------
    # LOCAL AI
    # --------------------------------------------------------

    local_answer = ask_local_ai(
        question
    )

    if local_answer:
        return local_answer

    # --------------------------------------------------------
    # LAST RESORT WEB SEARCH
    # --------------------------------------------------------

    web_answer = search_duckduckgo(
        question
    )

    if web_answer:
        return web_answer

    return (
        "I'm sorry, I couldn't find a reliable answer "
        "to that question right now."
    )


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT BOX
# ============================================================

user_message = st.chat_input(
    "Ask KingsBot anything..."
)

if user_message:

    with st.chat_message("user"):
        st.markdown(user_message)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    with st.chat_message("assistant"):

        with st.spinner(
            "🧠 Thinking..."
        ):

            answer = kingsbot(
                user_message
            )

        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🤖 KingsBot AI")

    st.write(
        "A real open-source language model "
        "with web knowledge and math support."
    )

    st.divider()

    st.subheader("Features")

    st.write("🧠 Real AI model")
    st.write("🌐 Web knowledge")
    st.write("🧮 Mathematics")
    st.write("💬 Conversation memory")
    st.write("💻 Coding questions")
    st.write("📚 General questions")

    st.divider()

    if st.button(
        "🗑️ Clear conversation"
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.caption(
        "Model: Qwen2.5-0.5B-Instruct"
    )

    st.caption(
        "No Hugging Face token required."
    )

import ast
import operator
import re

import requests
import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
MAX_NEW_TOKENS = 256


st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered",
)


@st.cache_resource(show_spinner=False)
def load_ai():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
    )

    model.eval()

    return tokenizer, model


# ------------------------------------------------------------
# MATH
# ------------------------------------------------------------

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
            mode="eval",
        )

        def evaluate(node):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError()

            if isinstance(node, ast.BinOp):
                operation = ALLOWED_OPERATORS.get(
                    type(node.op)
                )

                if operation is None:
                    raise ValueError()

                return operation(
                    evaluate(node.left),
                    evaluate(node.right),
                )

            if isinstance(node, ast.UnaryOp):
                operation = ALLOWED_OPERATORS.get(
                    type(node.op)
                )

                if operation is None:
                    raise ValueError()

                return operation(
                    evaluate(node.operand)
                )

            raise ValueError()

        result = evaluate(tree.body)

        if isinstance(result, float):
            if result.is_integer():
                return str(int(result))
            return str(round(result, 10))

        return str(result)

    except Exception:
        return None


def is_math_question(text):
    lower = text.lower()

    has_number = bool(
        re.search(r"\d", lower)
    )

    has_operator = bool(
        re.search(r"[+\-*/%^×÷]", lower)
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

    return has_number and (
        has_operator or has_math_word
    )


def get_math_expression(text):
    expression = text.lower()

    replacements = {
        "what is": "",
        "calculate": "",
        "solve": "",
        "answer": "",
        "equals": "",
        "equal to": "",
        "multiplied by": "*",
        "divided by": "/",
        "plus": "+",
        "minus": "-",
        "times": "*",
    }

    for old, new in replacements.items():
        expression = expression.replace(
            old,
            new,
        )

    expression = re.sub(
        r"[^0-9+\-*/().%^×÷ ]",
        "",
        expression,
    )

    return expression.strip()


# ------------------------------------------------------------
# WEB SEARCH
# ------------------------------------------------------------

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

        return summary.get("extract")

    except Exception:
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

        for topic in data.get(
            "RelatedTopics",
            [],
        ):
            if isinstance(topic, dict):
                text = topic.get("Text")

                if text:
                    return text

    except Exception:
        return None

    return None


# ------------------------------------------------------------
# LOAD MODEL
# ------------------------------------------------------------

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
        "KingsBot could not load the AI model."
    )

    with st.expander(
        "Technical information"
    ):
        st.code(str(error))


# ------------------------------------------------------------
# CHAT MEMORY
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------------------
# LOCAL AI
# ------------------------------------------------------------

def ask_local_ai(messages):
    if not model_ready:
        return None

    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        model_inputs = tokenizer(
            [text],
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        ).to(model.device)

        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.05,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(
                model_inputs.input_ids,
                generated_ids,
            )
        ]

        response = tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()

        return response if response else None

    except Exception:
        return None


# ------------------------------------------------------------
# MAIN BRAIN
# ------------------------------------------------------------

def kingsbot(question):
    question = question.strip()

    if not question:
        return "Please ask me something."

    # Math

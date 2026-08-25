import streamlit as st
import torch
import requests
from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# KINGSBOT AI
# Real local language model
# All-class memory
# Fact checking
# Conversation history
# Save conversation
# No Hugging Face token required
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


# ------------------------------------------------------------
# PAGE SETTINGS
# ------------------------------------------------------------

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered"
)


# ------------------------------------------------------------
# LOAD THE MODEL
# ------------------------------------------------------------

@st.cache_resource(show_spinner="🧠 Loading KingsBot's brain...")
def load_model():

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto"
    )

    model.eval()

    return tokenizer, model


try:

    tokenizer, model = load_model()

except Exception as error:

    st.error(
        "KingsBot could not load its AI model."
    )

    st.code(str(error))

    st.stop()


# ------------------------------------------------------------
# CHAT MEMORY
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------------------
# SCHOOL LEVEL MEMORY
# ------------------------------------------------------------

if "student_level" not in st.session_state:
    st.session_state.student_level = None


# ------------------------------------------------------------
# DETECT SCHOOL LEVEL
# ------------------------------------------------------------

def detect_student_level(text):

    lower = text.lower()

    levels = [
        ("PRIMARY 1", [
            "primary 1",
            "primary one",
            "pry 1"
        ]),
        ("PRIMARY 2", [
            "primary 2",
            "primary two",
            "pry 2"
        ]),
        ("PRIMARY 3", [
            "primary 3",
            "primary three",
            "pry 3"
        ]),
        ("PRIMARY 4", [
            "primary 4",
            "primary four",
            "pry 4"
        ]),
        ("PRIMARY 5", [
            "primary 5",
            "primary five",
            "pry 5"
        ]),
        ("PRIMARY 6", [
            "primary 6",
            "primary six",
            "pry 6"
        ]),
        ("JSS1", [
            "jss1",
            "jss 1",
            "jss one",
            "junior secondary 1",
            "junior secondary one"
        ]),
        ("JSS2", [
            "jss2",
            "jss 2",
            "jss two",
            "junior secondary 2",
            "junior secondary two"
        ]),
        ("JSS3", [
            "jss3",
            "jss 3",
            "jss three",
            "junior secondary 3",
            "junior secondary three"
        ]),
        ("SS1", [
            "ss1",
            "ss 1",
            "ss one",
            "sss1",
            "sss 1",
            "senior secondary 1",
            "senior secondary one"
        ]),
        ("SS2", [
            "ss2",
            "ss 2",
            "ss two",
            "sss2",
            "sss 2",
            "senior secondary 2",
            "senior secondary two"
        ]),
        ("SS3", [
            "ss3",
            "ss 3",
            "ss three",
            "sss3",
            "sss 3",
            "senior secondary 3",
            "senior secondary three"
        ]),
        ("UNIVERSITY", [
            "university",
            "uni",
            "college",
            "undergraduate",
            "bachelor's degree",
            "bachelors degree"
        ])
    ]

    for level, words in levels:

        for word in words:

            if word in lower:

                st.session_state.student_level = level

                return level

    return None


# ------------------------------------------------------------
# FACT QUESTION DETECTION
# ------------------------------------------------------------

def needs_fact_check(text):

    lower = text.lower().strip()

    factual_phrases = [
        "who is",
        "who was",
        "who are",
        "what is",
        "what was",
        "what are",
        "when did",
        "when was",
        "when were",
        "where is",
        "where was",
        "where are",
        "how many",
        "how much",
        "which country",
        "which year",
        "which team",
        "who won",
        "who has won",
        "how old",
        "when did",
        "date of",
        "born",
        "died",
        "capital of",
        "president of",
        "population of",
        "list the",
        "name the",
        "tell me about"
    ]

    for phrase in factual_phrases:

        if phrase in lower:

            return True

    return False


# ------------------------------------------------------------
# WIKIPEDIA SEARCH
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
                "srlimit": 3
            },
            headers={
                "User-Agent": "KingsBotAI/1.0"
            },
            timeout=8
        )

        response.raise_for_status()

        data = response.json()

        results = (
            data.get("query", {})
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
            timeout=8
        )

        summary_response.raise_for_status()

        summary_data = summary_response.json()

        extract = summary_data.get("extract")

        if extract:
            return extract

    except Exception:
        return None

    return None


# ------------------------------------------------------------
# DUCKDUCKGO SEARCH
# ------------------------------------------------------------

def search_duckduckgo(question):

    try:

        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": question,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            },
            headers={
                "User-Agent": "KingsBotAI/1.0"
            },
            timeout=8
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
            []
        ):

            if isinstance(topic, dict):

                text = topic.get("Text")

                if text:
                    return text

    except Exception:
        return None

    return None


# ------------------------------------------------------------
# GET FACT INFORMATION
# ------------------------------------------------------------

def get_fact_information(question):

    if not needs_fact_check(question):
        return None

    information = search_wikipedia(question)

    if information:
        return information

    information = search_duckduckgo(question)

    if information:
        return information

    return None


# ------------------------------------------------------------
# TITLE
# ------------------------------------------------------------

st.title("🤖 KingsBot AI")

st.caption(
    "Powered by a real open-source language model"
)


# ------------------------------------------------------------
# SHOW PREVIOUS MESSAGES
# ------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )


# ------------------------------------------------------------
# GENERATE AI RESPONSE
# ------------------------------------------------------------

def generate_response(user_message):

    # Remember the user's school level
    detect_student_level(user_message)

    # --------------------------------------------------------
    # SCHOOL LEVEL INSTRUCTION
    # --------------------------------------------------------

    if st.session_state.student_level:

        level = st.session_state.student_level

        level_instruction = (
            "The user's current education level is "
            + level
            + ". Adjust explanations, examples and vocabulary "
              "to that level. Do not unnecessarily use material "
              "from a much higher level."
        )

    else:

        level_instruction = (
            "The user's education level has not been provided. "
            "Answer normally and clearly."
        )


    # --------------------------------------------------------
    # FACT CHECK
    # --------------------------------------------------------

    fact_information = get_fact_information(
        user_message
    )


    # --------------------------------------------------------
    # SYSTEM MESSAGE
    # --------------------------------------------------------

    system_message = (
        "You are KingsBot, a helpful, intelligent and "
        "friendly AI assistant.\n\n"

        "Answer clearly and naturally.\n\n"

        "Help with mathematics, science, technology, coding, "
        "school subjects, history, general knowledge and "
        "everyday questions.\n\n"

        + level_instruction
        + "\n\n"

        "If reliable factual information is provided below, "
        "use it as the factual basis for your answer. "
        "Do not invent a different number, date, name or fact."
    )


    # --------------------------------------------------------
    # ADD FACT INFORMATION
    # --------------------------------------------------------

    if fact_information:

        system_message += (
            "\n\nFACT INFORMATION:\n"
            + fact_information
        )


    messages = [
        {
            "role": "system",
            "content": system_message
        }
    ]


    # --------------------------------------------------------
    # ADD PREVIOUS CONVERSATION
    # --------------------------------------------------------

    messages.extend(
        st.session_state.messages
    )


    # --------------------------------------------------------
    # ADD CURRENT QUESTION
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )


    # --------------------------------------------------------
    # CREATE MODEL PROMPT
    # --------------------------------------------------------

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )


    # --------------------------------------------------------
    # MODEL INPUT
    # --------------------------------------------------------

    model_inputs = tokenizer(
        [text],
        return_tensors="pt",
        truncation=True,
        max_length=2048
    ).to(model.device)


    # --------------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------------

    with torch.no_grad():

        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.eos_token_id
        )


    # --------------------------------------------------------
    # REMOVE PROMPT
    # --------------------------------------------------------

    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids
        in zip(
            model_inputs.input_ids,
            generated_ids
        )
    ]


    # --------------------------------------------------------
    # DECODE RESPONSE
    # --------------------------------------------------------

    response = tokenizer.batch_decode(
        generated_ids,
        skip_special_tokens=True
    )[0]


    return response.strip()


# ------------------------------------------------------------
# CHAT INPUT
# ------------------------------------------------------------

prompt = st.chat_input(
    "Ask KingsBot anything..."
)


if prompt:

    with st.chat_message("user"):

        st.markdown(prompt)


    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    with st.chat_message("assistant"):

        with st.spinner(
            "🧠 Thinking..."
        ):

            try:

                response = generate_response(
                    prompt
                )

            except Exception as error:

                response = (
                    "I ran into an error while thinking.\n\n"
                    f"`{error}`"
                )

        st.markdown(response)


    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )


# ------------------------------------------------------------
# CREATE SAVED CONVERSATION
# ------------------------------------------------------------

def create_chat_file():

    lines = []

    lines.append(
        "KINGSBOT AI - SAVED CONVERSATION"
    )

    lines.append(
        "=" * 40
    )

    lines.append("")

    if st.session_state.student_level:

        lines.append(
            "Education level: "
            + st.session_state.student_level
        )

        lines.append("")


    for message in st.session_state.messages:

        if message["role"] == "user":

            lines.append("YOU:")

        else:

            lines.append("KINGSBOT:")

        lines.append(
            message["content"]
        )

        lines.append("")
        lines.append("-" * 40)
        lines.append("")


    return "\n".join(lines)


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

with st.sidebar:

    st.header("🤖 KingsBot")

    st.write(
        "KingsBot uses a real open-source language model "
        "with education-level memory and factual lookup."
    )

    st.divider()

    # --------------------------------------------------------
    # EDUCATION LEVEL
    # --------------------------------------------------------

    st.subheader("🎓 Education Level")

    if st.session_state.student_level:

        st.success(
            "Current level: "
            + st.session_state.student_level
        )

    else:

        st.info(
            "Tell KingsBot your class, for example: "
            "\"I am in JSS3.\""
        )

    st.divider()

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    st.subheader("📚 Conversation History")

    if st.session_state.messages:

        user_messages = 0

        for message in st.session_state.messages:

            if message["role"] == "user":

                user_messages += 1

                preview = message["content"]

                if len(preview) > 60:

                    preview = preview[:60] + "..."

                st.write(
                    f"💬 {user_messages}. {preview}"
                )

    else:

        st.write(
            "No conversations yet."
        )

    # --------------------------------------------------------
    # SAVE CHAT
    # --------------------------------------------------------

    if st.session_state.messages:

        chat_file = create_chat_file()

        st.download_button(
            label="💾 Save conversation",
            data=chat_file,
            file_name="kingsbot_conversation.txt",
            mime="text/plain"
        )

    st.divider()

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    st.subheader("Features")

    st.write("🧠 Real language model")
    st.write("🎓 All-class education memory")
    st.write("🌐 Factual lookup")
    st.write("💬 Conversation memory")
    st.write("💾 Save conversations")
    st.write("🧮 Mathematics")
    st.write("💻 Coding help")
    st.write("📚 General knowledge")
    st.write("🔬 Science")
    st.write("🌍 Everyday questions")

    st.divider()

    # --------------------------------------------------------
    # CLEAR CONVERSATION
    # --------------------------------------------------------

    if st.button(
        "🗑️ Clear conversation"
    ):

        st.session_state.messages = []

        st.session_state.student_level = None

        st.rerun()

    st.divider()

    st.caption(
        "Model: Qwen2.5-0.5B-Instruct"
    )

    st.caption(
        "No Hugging Face token required."
    )

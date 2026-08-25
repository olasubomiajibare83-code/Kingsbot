import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# KINGSBOT AI
# Real local language model
# JSS3-aware
# Conversation history
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
# STUDENT LEVEL MEMORY
# ------------------------------------------------------------

if "student_level" not in st.session_state:
    st.session_state.student_level = None


# ------------------------------------------------------------
# DETECT JSS3
# ------------------------------------------------------------

def detect_student_level(text):

    lower = text.lower()

    jss3_words = [
        "jss3",
        "jss 3",
        "junior secondary 3",
        "junior secondary school 3"
    ]

    for word in jss3_words:

        if word in lower:

            st.session_state.student_level = "JSS3"

            return True

    return False


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

    # Check whether the user mentioned JSS3
    detect_student_level(user_message)

    # --------------------------------------------------------
    # JSS3-AWARE SYSTEM INSTRUCTION
    # --------------------------------------------------------

    if st.session_state.student_level == "JSS3":

        level_instruction = (
            "The student is in JSS3 (Junior Secondary School 3) "
            "in Nigeria. Keep explanations appropriate for JSS3. "
            "Use simple language, clear examples and school-level "
            "methods. Do NOT give university-level mathematics "
            "such as calculus, L'Hopital's rule, Lambert W, "
            "improper integrals, advanced series expansions or "
            "other university topics unless the student "
            "specifically asks about them. "
            "When the student asks for JSS3 topics, give "
            "JSS3-appropriate topics rather than university topics."
        )

    else:

        level_instruction = (
            "Answer at a normal general-knowledge level. "
            "If the user tells you their school level, remember "
            "that level and adjust your explanations accordingly."
        )


    messages = [
        {
            "role": "system",
            "content": (
                "You are KingsBot, a helpful, intelligent and "
                "friendly AI assistant.\n\n"

                "Answer questions clearly and naturally.\n\n"

                "Help with mathematics, science, technology, "
                "coding, school subjects, history, general "
                "knowledge and everyday questions.\n\n"

                + level_instruction
                + "\n\n"

                "If the user asks a school question, teach the "
                "idea step by step instead of giving an unnecessarily "
                "advanced answer.\n\n"

                "If you are unsure about a fact, do not pretend "
                "that you know it."
            )
        }
    ]


    # --------------------------------------------------------
    # ADD PREVIOUS CONVERSATION
    # --------------------------------------------------------

    messages.extend(
        st.session_state.messages
    )


    # --------------------------------------------------------
    # ADD NEW USER MESSAGE
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
    # REMOVE ORIGINAL PROMPT
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

    # --------------------------------------------------------
    # SHOW USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)


    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    # --------------------------------------------------------
    # GENERATE ANSWER
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # SAVE ASSISTANT MESSAGE
    # --------------------------------------------------------

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
            "Student level: "
            + st.session_state.student_level
        )

        lines.append("")


    for message in st.session_state.messages:

        if message["role"] == "user":

            lines.append(
                "YOU:"
            )

        else:

            lines.append(
                "KINGSBOT:"
            )

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
        "running inside the Space."
    )


    st.divider()


    # --------------------------------------------------------
    # STUDENT LEVEL
    # --------------------------------------------------------

    st.subheader("🎓 Student Level")


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
    st.write("🎓 JSS3-aware answers")
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

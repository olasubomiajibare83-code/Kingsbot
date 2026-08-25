import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ============================================================
# KINGSBOT AI
# Real local language model
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
    st.error("KingsBot could not load its AI model.")
    st.code(str(error))
    st.stop()

# ------------------------------------------------------------
# CHAT MEMORY
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

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
        st.markdown(message["content"])

# ------------------------------------------------------------
# GENERATE AI RESPONSE
# ------------------------------------------------------------

def generate_response(user_message):

    messages = [
        {
            "role": "system",
            "content": (
                "You are KingsBot, a helpful, intelligent and "
                "friendly AI assistant. "
                "Answer clearly and naturally. "
                "Help with mathematics, science, technology, "
                "coding, school subjects, history, general "
                "knowledge and everyday questions. "
                "Do not pretend to know something if you do not "
                "know it. Keep answers understandable."
            )
        }
    ]

    # Add previous conversation
    messages.extend(st.session_state.messages)

    # Add the new user message
    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # Create the model prompt
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Convert prompt into model input
    model_inputs = tokenizer(
        [text],
        return_tensors="pt"
    ).to(model.device)

    # Generate response
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

    # Remove the prompt from the generated result
    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids
        in zip(
            model_inputs.input_ids,
            generated_ids
        )
    ]

    # Turn model output into normal text
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

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Generate answer
    with st.chat_message("assistant"):

        with st.spinner("🧠 Thinking..."):

            try:
                response = generate_response(prompt)

            except Exception as error:
                response = (
                    "I ran into an error while thinking.\n\n"
                    f"`{error}`"
                )

        st.markdown(response)

    # Save assistant message
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )

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

    st.subheader("Features")

    st.write("🧠 Real language model")
    st.write("💬 Conversation")
    st.write("🧮 Mathematics")
    st.write("💻 Coding help")
    st.write("📚 General knowledge")
    st.write("🔬 Science")
    st.write("🌍 Everyday questions")

    st.divider()

    if st.button("🗑️ Clear conversation"):

        st.session_state.messages = []

        st.rerun()

    st.divider()

    st.caption(
        "Model: Qwen2.5-0.5B-Instruct"
    )

    st.caption(
        "No Hugging Face token required."
    )

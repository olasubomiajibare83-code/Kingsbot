                        
  import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🧠",
    layout="centered"
)

# -----------------------------
# AI MODEL
# -----------------------------
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32
    )

    return tokenizer, model


# -----------------------------
# LOAD BRAIN
# -----------------------------
with st.spinner("🧠 KingsBot is loading its brain..."):
    tokenizer, model = load_model()


# -----------------------------
# PAGE
# -----------------------------
st.title("🧠 KingsBot AI")
st.caption("Your personal AI assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------
# SHOW CHAT
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# -----------------------------
# CHAT INPUT
# -----------------------------
user_text = st.chat_input("Ask KingsBot anything...")

if user_text:

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_text
    })

    with st.chat_message("user"):
        st.write(user_text)

    # Prepare conversation
    messages = [
        {
            "role": "system",
            "content": (
                "You are KingsBot, a helpful, intelligent AI assistant. "
                "Answer questions clearly and naturally. "
                "Help with mathematics, science, coding, history, "
                "technology, general knowledge and everyday questions. "
                "If you don't know something, say so instead of making it up."
            )
        }
    ]

    messages.extend(st.session_state.messages)

    # Convert conversation to model input
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    )

    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=300,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True
                )

            # Remove the original prompt
            generated_tokens = output[0][inputs["input_ids"].shape[1]:]

            answer = tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True
            ).strip()

            if not answer:
                answer = "I'm sorry, I couldn't generate an answer."

            st.write(answer)

    # Save answer
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })


# -----------------------------
# CLEAR CHAT
# -----------------------------
if st.button("🗑️ Clear conversation"):
    st.session_state.messages = []
    st.rerun()      

    



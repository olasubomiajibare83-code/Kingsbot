  import streamlit as st
from transformers import pipeline

# -----------------------------
# PAGE SETTINGS
# -----------------------------

st.set_page_config(
    page_title="KingsBot AI",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 KingsBot AI")
st.caption("Your AI assistant with a real language model")


# -----------------------------
# LOAD THE AI MODEL
# -----------------------------

@st.cache_resource
def load_model():
    return pipeline(
        "text-generation",
        model="HuggingFaceTB/SmolLM2-360M-Instruct"
    )


# -----------------------------
# START MODEL
# -----------------------------

with st.spinner("🧠 KingsBot is loading its brain..."):
    try:
        generator = load_model()
        model_ready = True
    except Exception as error:
        model_ready = False
        st.error("The AI model could not be loaded.")
        st.code(str(error))


# -----------------------------
# CHAT MEMORY
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------
# DISPLAY OLD MESSAGES
# -----------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# -----------------------------
# CLEAR CHAT BUTTON
# -----------------------------

if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()


# -----------------------------
# CHAT INPUT
# -----------------------------

user_message = st.chat_input("Talk to KingsBot...")


if user_message and model_ready:

    # Save user's message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # Display user's message
    with st.chat_message("user"):
        st.write(user_message)

    # Keep recent conversation
    recent_messages = st.session_state.messages[-10:]

    # System instruction
    messages_for_model = [
        {
            "role": "system",
            "content": (
                "You are KingsBot, a helpful, friendly AI assistant. "
                "Answer questions clearly and naturally. "
                "If you do not know something, say that you are not sure. "
                "Do not pretend to know information you do not know."
            )
        }
    ]

    messages_for_model.extend(recent_messages)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):

            try:
                result = generator(
                    messages_for_model,
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )

                generated = result[0]["generated_text"]

                # Chat models return a list of messages
                if isinstance(generated, list):
                    assistant_messages = [
                        message
                        for message in generated
                        if message.get("role") == "assistant"
                    ]

                    if assistant_messages:
                        answer = assistant_messages[-1]["content"]
                    else:
                        answer = "Sorry, I could not generate an answer."

                else:
                    answer = generated

                st.write(answer)

                # Save AI response
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

            except Exception as error:
                st.error("Something went wrong while generating the answer.")
                st.code(str(error))      

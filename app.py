import streamlit as st
from huggingface_hub import InferenceClient

# -----------------------------
# PAGE
# -----------------------------

st.set_page_config(
    page_title="My AI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 My AI")
st.caption("Your personal AI assistant")


# -----------------------------
# HUGGING FACE CONNECTION
# -----------------------------

try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except Exception:
    st.error("HF_TOKEN has not been added to your Streamlit Secrets.")
    st.stop()


client = InferenceClient(
    api_key=HF_TOKEN,
    provider="auto"
)


# -----------------------------
# AI PERSONALITY
# -----------------------------

SYSTEM_PROMPT = """
You are My AI, a powerful and friendly general-purpose AI assistant.

You can help with:

- General knowledge
- Mathematics
- Science
- History
- Geography
- Programming
- Computer science
- Writing
- Rewriting
- Summarization
- Translation
- Learning
- Explanations
- Brainstorming
- Problem solving
- AI development
- Website development
- Games and game development
- Creative ideas

Rules:

1. Give useful and accurate answers.
2. Explain difficult things simply when appropriate.
3. Show mathematical working when useful.
4. Write clean, understandable code.
5. Never pretend to know current information if you cannot verify it.
6. If you don't know something, say so.
7. Do not invent sources or facts.
8. Remember the conversation provided in the chat history.
9. Be friendly and helpful.
"""


# -----------------------------
# MEMORY
# -----------------------------

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.header("🤖 My AI")

    if st.button(
        "🆕 New chat",
        use_container_width=True
    ):

        st.session_state.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        st.rerun()


    st.divider()

    st.write("### Abilities")

    st.write("🧠 AI conversation")
    st.write("🧮 Mathematics")
    st.write("💻 Programming")
    st.write("📚 Learning")
    st.write("✍️ Writing")
    st.write("🌍 General knowledge")
    st.write("🧠 Conversation memory")


# -----------------------------
# SHOW HISTORY
# -----------------------------

for message in st.session_state.messages:

    if message["role"] == "system":
        continue

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# -----------------------------
# USER MESSAGE
# -----------------------------

user_message = st.chat_input(
    "Message My AI..."
)


if user_message:

    # Show user message

    with st.chat_message("user"):

        st.markdown(user_message)


    # Save user message

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )


    # Generate AI response

    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        full_response = ""


        try:

            response = client.chat.completions.create(

                model="deepseek-ai/DeepSeek-V3-0324",

                messages=st.session_state.messages,

                max_tokens=2048,

                temperature=0.7,

                stream=True
            )


            for chunk in response:

                if not chunk.choices:
                    continue

                token = chunk.choices[0].delta.content

                if token:

                    full_response += token

                    response_placeholder.markdown(
                        full_response + "▌"
                    )


            response_placeholder.markdown(
                full_response
            )


        except Exception as error:

            full_response = (
                "I couldn't connect to the AI model.\n\n"
                "Error: " + str(error)
            )

            response_placeholder.error(
                full_response
            )


    # Save AI response

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )

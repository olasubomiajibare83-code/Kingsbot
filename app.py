import streamlit as st
import requests
import html
import base64


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="My AI",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #212121;
        color: white;
    }

    .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    .title {
        text-align: center;
        font-size: 38px;
        font-weight: 700;
        color: #10a37f;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #999;
        margin-bottom: 30px;
    }

    .user-box {
        background: #343541;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
    }

    .ai-box {
        background: #2a2a2a;
        border-left: 4px solid #10a37f;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HUGGING FACE TOKEN
# ============================================================

try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except Exception:
    HF_TOKEN = ""


# ============================================================
# AI MODEL
# ============================================================

MODEL = "deepseek-ai/DeepSeek-V3-0324"

CHAT_URL = "https://router.huggingface.co/v1/chat/completions"

WHISPER_URL = (
    "https://router.huggingface.co/"
    "hf-inference/models/openai/whisper-large-v3"
)


# ============================================================
# AI SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are My AI.

You are a helpful, intelligent, friendly general-purpose AI assistant.

You can help with:

- General knowledge
- Mathematics
- Science
- History
- Geography
- Programming
- Computer science
- Website development
- AI development
- Game development
- Writing
- Rewriting
- Summarizing
- Translation
- Learning
- Explanations
- Brainstorming
- Problem solving
- Creative work
- Everyday questions

Behavior:

1. Give accurate and useful answers.
2. Never intentionally invent facts.
3. If you are uncertain, say that you are uncertain.
4. Solve mathematics carefully.
5. Show mathematical steps when useful.
6. Write clean, working code.
7. Explain difficult subjects clearly.
8. Remember information from the conversation supplied to you.
9. Be friendly and natural.
10. Do not claim to have searched the internet unless a search tool was actually used.
11. If the user asks for current information and you do not have live web access, say that clearly.
"""


# ============================================================
# SESSION MEMORY
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


# ============================================================
# LAST AI RESPONSE
# ============================================================

if "last_ai_response" not in st.session_state:
    st.session_state.last_ai_response = ""


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 My AI")

    st.write("Your personal AI assistant")

    st.divider()

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

        st.session_state.last_ai_response = ""

        st.rerun()


    st.divider()

    st.subheader("Abilities")

    st.write("🧠 Real AI")
    st.write("🧮 Mathematics")
    st.write("💻 Programming")
    st.write("📚 Learning")
    st.write("✍️ Writing")
    st.write("🎤 Voice input")
    st.write("🔊 Voice output")


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="title">🤖 My AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Talk to your AI assistant'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# AI REQUEST FUNCTION
# ============================================================

def ask_ai(messages):

    if not HF_TOKEN:

        return (
            "⚠️ My AI is not connected yet.\n\n"
            "Please add your Hugging Face token as "
            "HF_TOKEN in your app Secrets."
        )


    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }


    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }


    try:

        response = requests.post(
            CHAT_URL,
            headers=headers,
            json=payload,
            timeout=120
        )


        if response.status_code != 200:

            return (
                "❌ The AI service returned an error.\n\n"
                f"HTTP {response.status_code}\n\n"
                f"{response.text}"
            )


        data = response.json()


        choices = data.get("choices", [])


        if not choices:

            return (
                "❌ The AI returned no answer."
            )


        message = choices[0].get(
            "message",
            {}
        )


        answer = message.get(
            "content",
            ""
        )


        if not answer:

            return (
                "❌ The AI returned an empty answer."
            )


        return answer


    except requests.exceptions.Timeout:

        return (
            "⏳ The AI took too long to respond. "
            "Please try again."
        )


    except requests.exceptions.RequestException as error:

        return (
            "❌ I couldn't connect to the AI service.\n\n"
            f"{error}"
        )


    except Exception as error:

        return (
            "❌ Something went wrong.\n\n"
            f"{error}"
        )


# ============================================================
# DISPLAY CHAT
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "system":
        continue


    if message["role"] == "user":

        safe_text = html.escape(
            message["content"]
        )

        st.markdown(
            f"""
            <div class="user-box">
                <b>👤 You</b><br><br>
                {safe_text}
            </div>
            """,
            unsafe_allow_html=True
        )


    elif message["role"] == "assistant":

        safe_text = html.escape(
            message["content"]
        )

        st.markdown(
            f"""
            <div class="ai-box">
                <b>🤖 My AI</b><br><br>
                {safe_text}
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# TEXT CHAT
# ============================================================

user_message = st.chat_input(
    "Message My AI..."
)


if user_message:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )


    with st.spinner("🧠 Thinking..."):

        answer = ask_ai(
            st.session_state.messages
        )


    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


    st.session_state.last_ai_response = answer

    st.rerun()


# ============================================================
# VOICE INPUT
# ============================================================

st.divider()

st.subheader("🎤 Talk to My AI")

audio = st.audio_input(
    "Press the microphone and speak",
    sample_rate=16000,
    key="voice_input"
)


if audio:

    st.audio(audio)


    if not HF_TOKEN:

        st.warning(
            "⚠️ Add HF_TOKEN to your Secrets first."
        )

    else:

        if st.button(
            "🧠 Understand my voice",
            key="process_voice"
        ):

            with st.spinner(
                "🎧 Understanding your voice..."
            ):

                try:

                    audio_bytes = audio.getvalue()


                    headers = {
                        "Authorization":
                            f"Bearer {HF_TOKEN}"
                    }


                    speech_response = requests.post(
                        WHISPER_URL,
                        headers=headers,
                        data=audio_bytes,
                        timeout=120
                    )


                    if speech_response.status_code != 200:

                        st.error(
                            "❌ Speech recognition failed.\n\n"
                            + speech_response.text
                        )

                    else:

                        speech_data = (
                            speech_response.json()
                        )


                        spoken_text = (
                            speech_data
                            .get("text", "")
                            .strip()
                        )


                        if not spoken_text:

                            st.warning(
                                "I couldn't understand "
                                "the recording."
                            )

                        else:

                            st.success(
                                "You said: "
                                + spoken_text
                            )


                            st.session_state.messages.append(
                                {
                                    "role": "user",
                                    "content": spoken_text
                                }
                            )


                            with st.spinner(
                                "🧠 My AI is thinking..."
                            ):

                                answer = ask_ai(
                                    st.session_state.messages
                                )


                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": answer
                                }
                            )


                            st.session_state.last_ai_response = (
                                answer
                            )


                            st.rerun()


                except requests.exceptions.Timeout:

                    st.error(
                        "⏳ Voice processing timed out."
                    )


                except requests.exceptions.RequestException as error:

                    st.error(
                        "❌ Network error:\n\n"
                        + str(error)
                    )


                except Exception as error:

                    st.error(
                        "❌ Voice error:\n\n"
                        + str(error)
                    )


# ============================================================
# VOICE OUTPUT
# ============================================================

if st.session_state.last_ai_response:

    st.divider()

    st.subheader("🔊 My AI can speak")

    if st.button(
        "🔊 Speak latest answer",
        key="speak_answer"
    ):

        text = st.session_state.last_ai_response

        escaped_text = (
            text
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("$", "\\$")
        )


        speech_html = f"""
        <script>

        const text = `{escaped_text}`;

        if ("speechSynthesis" in window) {{

            window.speechSynthesis.cancel();

            const speech =
                new SpeechSynthesisUtterance(text);

            speech.lang = "en-US";
            speech.rate = 1;
            speech.pitch = 1;

            window.speechSynthesis.speak(speech);

        }}

        </script>
        """


        st.components.v1.html(
            speech_html,
            height=1
        )


        st.success(
            "🔊 Speaking..."
        )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "My AI • Real AI model + voice input + voice output"
)

import streamlit as st
import torch
import requests
import re
import io

from transformers import AutoTokenizer, AutoModelForCausalLM
import speech_recognition as sr
from gtts import gTTS


# ============================================================
# KINGSBOT AI
# Real local language model
# Voice assistant
# Memory
# EQ / sentiment
# Tone adaptation
# Education-level adaptation
# Conversation saving
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
# SESSION MEMORY
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "student_level" not in st.session_state:
    st.session_state.student_level = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "personal_memory" not in st.session_state:
    st.session_state.personal_memory = []

if "last_emotion" not in st.session_state:
    st.session_state.last_emotion = "neutral"


# ------------------------------------------------------------
# EDUCATION LEVEL DETECTION
# ------------------------------------------------------------

def detect_student_level(text):

    lower = text.lower()

    levels = [
        ("PRIMARY 1", ["primary 1", "primary one", "pry 1"]),
        ("PRIMARY 2", ["primary 2", "primary two", "pry 2"]),
        ("PRIMARY 3", ["primary 3", "primary three", "pry 3"]),
        ("PRIMARY 4", ["primary 4", "primary four", "pry 4"]),
        ("PRIMARY 5", ["primary 5", "primary five", "pry 5"]),
        ("PRIMARY 6", ["primary 6", "primary six", "pry 6"]),
        ("JSS1", ["jss1", "jss 1", "jss one",
                  "junior secondary 1"]),
        ("JSS2", ["jss2", "jss 2", "jss two",
                  "junior secondary 2"]),
        ("JSS3", ["jss3", "jss 3", "jss three",
                  "junior secondary 3"]),
        ("SS1", ["ss1", "ss 1", "ss one",
                  "sss1", "sss 1", "senior secondary 1"]),
        ("SS2", ["ss2", "ss 2", "ss two",
                  "sss2", "sss 2", "senior secondary 2"]),
        ("SS3", ["ss3", "ss 3", "ss three",
                  "sss3", "sss 3", "senior secondary 3"]),
        ("UNIVERSITY", [
            "university",
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
# NAME MEMORY
# ------------------------------------------------------------

def detect_name(text):

    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\bcall me ([A-Za-z][A-Za-z '\-]{1,40})",
        r"\byou can call me ([A-Za-z][A-Za-z '\-]{1,40})"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            name = match.group(1).strip()

            if name:

                st.session_state.user_name = name
                return name

    return None


# ------------------------------------------------------------
# PERSONAL MEMORY
# ------------------------------------------------------------

def remember_information(text):

    lower = text.lower()

    phrases = [
        "remember that",
        "remember this",
        "please remember",
        "keep this in mind"
    ]

    for phrase in phrases:

        if phrase in lower:

            position = lower.find(phrase)

            memory = text[
                position + len(phrase):
            ].strip(" :,-")

            if memory and memory not in st.session_state.personal_memory:

                st.session_state.personal_memory.append(
                    memory
                )

                return memory

    return None


# ------------------------------------------------------------
# ETHICAL FORGETTING
# ------------------------------------------------------------

def handle_forgetting(text):

    lower = text.lower()

    if (
        "forget everything" in lower
        or "forget all my memory" in lower
        or "delete everything you remember" in lower
    ):

        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []

        return (
            "Done. I cleared the personal information "
            "I had saved."
        )

    if (
        "forget my name" in lower
        or "delete my name" in lower
    ):

        st.session_state.user_name = None

        return "Done. I forgot your saved name."

    if (
        "forget my class" in lower
        or "forget my education level" in lower
    ):

        st.session_state.student_level = None

        return "Done. I forgot your saved education level."

    return None


# ------------------------------------------------------------
# EMOTION DETECTION
# ------------------------------------------------------------

def detect_emotion(text):

    lower = text.lower()

    if any(word in lower for word in [
        "angry",
        "mad",
        "annoyed",
        "you are wrong",
        "useless"
    ]):
        return "frustrated"

    if any(word in lower for word in [
        "sad",
        "crying",
        "upset",
        "hurt"
    ]):
        return "sad"

    if any(word in lower for word in [
        "confused",
        "don't understand",
        "do not understand",
        "explain again"
    ]):
        return "confused"

    if any(word in lower for word in [
        "worried",
        "scared",
        "afraid",
        "nervous"
    ]):
        return "worried"

    if any(word in lower for word in [
        "happy",
        "great",
        "awesome",
        "good",
        "thanks",
        "thank you",
        "yesss"
    ]):
        return "happy"

    return "neutral"


# ------------------------------------------------------------
# TONE ADAPTATION
# ------------------------------------------------------------

def tone_instruction(emotion):

    if emotion == "frustrated":
        return (
            "Be calm, respectful and direct. "
            "Do not argue with the user."
        )

    if emotion == "sad":
        return (
            "Be warm, kind and supportive."
        )

    if emotion == "confused":
        return (
            "Use simple language and explain "
            "the answer step by step."
        )

    if emotion == "worried":
        return (
            "Be reassuring and give clear practical steps."
        )

    if emotion == "happy":
        return (
            "Use a friendly and positive tone."
        )

    return (
        "Use a natural, friendly and clear tone."
    )


# ------------------------------------------------------------
# FACT LOOKUP
# ------------------------------------------------------------

def get_fact(question):

    try:

        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": question,
                "format": "json",
                "utf8": 1,
                "srlimit": 1
            },
            headers={
                "User-Agent": "KingsBotAI/1.0"
            },
            timeout=6
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "query",
            {}
        ).get(
            "search",
            []
        )

        if not results:
            return None

        title = results[0].get("title")

        if not title:
            return None

        summary = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + requests.utils.quote(title),
            headers={
                "User-Agent": "KingsBotAI/1.0"
            },
            timeout=6
        )

        summary.raise_for_status()

        return summary.json().get("extract")

    except Exception:

        return None


# ------------------------------------------------------------
# GENERATE RESPONSE
# ------------------------------------------------------------

def generate_response(user_message):

    forgotten = handle_forgetting(
        user_message
    )

    if forgotten:

        return forgotten, "High"

    detect_name(user_message)

    detect_student_level(user_message)

    remember_information(
        user_message
    )

    emotion = detect_emotion(
        user_message
    )

    st.session_state.last_emotion = emotion

    if st.session_state.student_level:

        education_instruction = (
            "The user is studying at "
            + st.session_state.student_level
            + ". Adapt the difficulty to this level. "
            "Do not give university-level material to a "
            "younger student unless they specifically ask "
            "for advanced material."
        )

    else:

        education_instruction = (
            "The user's education level is unknown. "
            "Use an appropriate general explanation."
        )

    memory_lines = []

    if st.session_state.user_name:

        memory_lines.append(
            "User name: "
            + st.session_state.user_name
        )

    if st.session_state.student_level:

        memory_lines.append(
            "Education level: "
            + st.session_state.student_level
        )

    for item in st.session_state.personal_memory[-10:]:

        memory_lines.append(
            "Remembered information: "
            + item
        )

    memory_text = "\n".join(memory_lines)

    system_prompt = (
        "You are KingsBot, a helpful, intelligent and "
        "friendly AI assistant.\n\n"

        "Answer questions clearly and naturally.\n\n"

        "Help with mathematics, science, technology, coding, "
        "school subjects, history, general knowledge and "
        "everyday questions.\n\n"

        + education_instruction
        + "\n\n"

        + tone_instruction(emotion)
        + "\n\n"

        "When solving problems, reason carefully and explain "
        "important steps. Do not invent facts. If you are "
        "uncertain, say so.\n\n"
    )

    if memory_text:

        system_prompt += (
            "USER MEMORY:\n"
            + memory_text
            + "\n\n"
        )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(
        st.session_state.messages[-12:]
    )

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    model_inputs = tokenizer(
        [prompt_text],
        return_tensors="pt",
        truncation=True,
        max_length=2048
    ).to(model.device)

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

    new_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(
            model_inputs.input_ids,
            generated_ids
        )
    ]

    response = tokenizer.batch_decode(
        new_ids,
        skip_special_tokens=True
    )[0].strip()

    if not response:

        response = (
            "I couldn't generate an answer. "
            "Please try again."
        )

    return response, "Medium"


# ------------------------------------------------------------
# SPEECH TO TEXT
# ------------------------------------------------------------

def speech_to_text(audio_file):

    recognizer = sr.Recognizer()

    try:

        audio_bytes = audio_file.getvalue()

        audio_source = sr.AudioFile(
            io.BytesIO(audio_bytes)
        )

        with audio_source as source:

            audio_data = recognizer.record(
                source
            )

        text = recognizer.recognize_google(
            audio_data,
            language="en-US"
        )

        return text

    except Exception:

        return None


# ------------------------------------------------------------
# TEXT TO SPEECH
# ------------------------------------------------------------

def text_to_speech(text):

    try:

        audio_buffer = io.BytesIO()

        tts = gTTS(
            text=text[:3000],
            lang="en",
            slow=False
        )

        tts.write_to_fp(
            audio_buffer
        )

        audio_buffer.seek(0)

        return audio_buffer.getvalue()

    except Exception:

        return None


# ------------------------------------------------------------
# SAVED CONVERSATION
# ------------------------------------------------------------

def create_chat_file():

    lines = [
        "KINGSBOT AI - SAVED CONVERSATION",
        "=" * 40,
        ""
    ]

    if st.session_state.user_name:

        lines.append(
            "Name: "
            + st.session_state.user_name
        )

        lines.append("")

    if st.session_state.student_level:

        lines.append(
            "Education level: "
            + st.session_state.student_level
        )

        lines.append("")

    for memory in st.session_state.personal_memory:

        lines.append(
            "Memory: "
            + memory
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
# TITLE
# ------------------------------------------------------------

st.title("🤖 KingsBot AI")

st.caption(
    "Real AI • Memory • Voice • EQ • Tone Adaptation"
)


# ------------------------------------------------------------
# DISPLAY CONVERSATION
# ------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ------------------------------------------------------------
# VOICE INPUT
# ------------------------------------------------------------

st.subheader("🎤 Talk to KingsBot")

audio_file = st.audio_input(
    "Tap the microphone and speak"
)

if audio_file is not None:

    with st.spinner(
        "🎧 Understanding your voice..."
    ):

        voice_prompt = speech_to_text(
            audio_file
        )

    if voice_prompt:

        st.success(
            "You said: " + voice_prompt
        )

        prompt = voice_prompt

    else:

        st.error(
            "I couldn't understand the recording. "
            "Please try again."
        )

        prompt = None

else:

    prompt = st.chat_input(
        "Ask KingsBot anything..."
    )


# ------------------------------------------------------------
# PROCESS MESSAGE
# ------------------------------------------------------------

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

                response, confidence = (
                    generate_response(
                        prompt
                    )
                )

            except Exception as error:

                response = (
                    "I ran into an error while thinking.\n\n"
                    + str(error)
                )

                confidence = "Unknown"

        st.markdown(response)

        st.caption(
            "Confidence estimate: "
            + confidence
        )

        with st.spinner(
            "🔊 Preparing voice..."
        ):

            voice = text_to_speech(
                response
            )

        if voice:

            st.audio(
                voice,
                format="audio/mp3"
            )

        else:

            st.warning(
                "Voice output could not be created, "
                "but the text answer is available."
            )

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
        "Anyone can talk to KingsBot using the microphone."
    )

    st.divider()

    st.subheader("🧠 Memory")

    if st.session_state.user_name:

        st.write(
            "👤 Name: "
            + st.session_state.user_name
        )

    if st.session_state.student_level:

        st.write(
            "🎓 Level: "
            + st.session_state.student_level
        )

    st.write(
        "📝 Saved memories: "
        + str(
            len(
                st.session_state.personal_memory
            )
        )
    )

    st.divider()

    st.subheader("❤️ EQ")

    st.write(
        "Current emotion: "
        + st.session_state.last_emotion
    )

    st.divider()

    st.subheader("🎭 Tone Adaptation")

    if st.session_state.last_emotion == "frustrated":

        st.write("Calm + direct")

    elif st.session_state.last_emotion == "sad":

        st.write("Warm + supportive")

    elif st.session_state.last_emotion == "confused":

        st.write("Simple + step-by-step")

    elif st.session_state.last_emotion == "worried":

        st.write("Reassuring + practical")

    elif st.session_state.last_emotion == "happy":

        st.write("Friendly + positive")

    else:

        st.write("Natural + friendly")

    st.divider()

    st.subheader("💾 Conversation")

    if st.session_state.messages:

        chat_file = create_chat_file()

        st.download_button(
            "💾 Save conversation",
            data=chat_file,
            file_name="kingsbot_conversation.txt",
            mime="text/plain"
        )

    else:

        st.write(
            "No conversation yet."
        )

    st.divider()

    st.subheader("Features")

    st.write("🧠 Real language model")
    st.write("🎤 Voice input")
    st.write("🔊 Voice output")
    st.write("❤️ EQ / sentiment")
    st.write("🎭 Tone adaptation")
    st.write("🧠 Personalized memory")
    st.write("🧹 Ethical forgetting")
    st.write("🎓 Primary to University")
    st.write("💬 Conversation memory")
    st.write("💾 Save conversations")

    st.divider()

    if st.button(
        "🗑️ Clear conversation"
    ):

        st.session_state.messages = []
        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []
        st.session_state.last_emotion = "neutral"

        st.rerun()

    st.divider()

    st.caption(
        "Model: Qwen2.5-0.5B-Instruct"
    )

    st.caption(
        "No Hugging Face token required."
    )

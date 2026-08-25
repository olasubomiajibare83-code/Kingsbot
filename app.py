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
# EQ / sentiment
# Personalized memory
# Ethical forgetting
# All education levels
# Pattern recognition
# Proactive guidance
# Confidence indicator
# Tone adaptation
# Fact lookup
# Conversation memory
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
# LOAD MODEL
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

if "last_confidence" not in st.session_state:
    st.session_state.last_confidence = "Medium"


# ------------------------------------------------------------
# EDUCATION LEVEL
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
            "undergraduate",
            "college",
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
# ETHICAL FORGETTING
# ------------------------------------------------------------

def handle_forgetting(text):

    lower = text.lower()

    if (
        "forget everything" in lower
        or "forget all my memory" in lower
        or "forget all my information" in lower
        or "delete everything you remember" in lower
    ):

        st.session_state.user_name = None
        st.session_state.student_level = None
        st.session_state.personal_memory = []

        return (
            "Done. I cleared the personal information "
            "I had stored for this conversation."
        )

    if (
        "forget my name" in lower
        or "delete my name" in lower
        or "don't remember my name" in lower
    ):

        st.session_state.user_name = None

        return "Done. I forgot your saved name."

    if (
        "forget my class" in lower
        or "forget my education level" in lower
        or "delete my class" in lower
    ):

        st.session_state.student_level = None

        return (
            "Done. I forgot your saved education level."
        )

    return None


# ------------------------------------------------------------
# PERSONAL MEMORY
# ------------------------------------------------------------

def remember_user_information(text):

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

            memory_text = text[
                position + len(phrase):
            ].strip(" :,-")

            if memory_text:

                if memory_text not in (
                    st.session_state.personal_memory
                ):

                    st.session_state.personal_memory.append(
                        memory_text
                    )

                return memory_text

    return None


# ------------------------------------------------------------
# EMOTION DETECTION
# ------------------------------------------------------------

def detect_emotion(text):

    lower = text.lower()

    frustrated_words = [
        "angry",
        "mad",
        "annoyed",
        "annoying",
        "useless",
        "stupid",
        "you failed",
        "you are wrong"
    ]

    sad_words = [
        "sad",
        "cry",
        "crying",
        "upset",
        "hurt",
        "terrible"
    ]

    confused_words = [
        "confused",
        "don't understand",
        "do not understand",
        "i don't get",
        "explain again",
        "what does this mean"
    ]

    worried_words = [
        "worried",
        "scared",
        "afraid",
        "nervous"
    ]

    happy_words = [
        "happy",
        "great",
        "awesome",
        "good",
        "nice",
        "love",
        "thank you",
        "thanks",
        "yesss"
    ]

    for word in frustrated_words:

        if word in lower:
            return "frustrated"

    for word in sad_words:

        if word in lower:
            return "sad"

    for word in confused_words:

        if word in lower:
            return "confused"

    for word in worried_words:

        if word in lower:
            return "worried"

    for word in happy_words:

        if word in lower:
            return "happy"

    return "neutral"


# ------------------------------------------------------------
# TONE ADAPTATION
# ------------------------------------------------------------

def get_tone_instruction(emotion):

    if emotion == "frustrated":

        return (
            "The user seems frustrated. Be calm, respectful "
            "and direct. Do not argue."
        )

    if emotion == "sad":

        return (
            "The user seems sad. Be warm, kind and supportive."
        )

    if emotion == "confused":

        return (
            "The user seems confused. Use simpler language "
            "and explain the idea step by step."
        )

    if emotion == "worried":

        return (
            "The user seems worried. Be reassuring and "
            "give clear practical steps."
        )

    if emotion == "happy":

        return (
            "The user seems happy. Use a friendly and "
            "positive tone."
        )

    return (
        "Use a natural, friendly and clear tone."
    )


# ------------------------------------------------------------
# PATTERN RECOGNITION
# ------------------------------------------------------------

def detect_patterns():

    patterns = []

    user_messages = [
        message["content"].lower()
        for message in st.session_state.messages
        if message["role"] == "user"
    ]

    if len(user_messages) >= 3:

        coding_count = sum(
            1
            for text in user_messages
            if (
                "code" in text
                or "python" in text
                or "app" in text
            )
        )

        school_count = sum(
            1
            for text in user_messages
            if (
                "school" in text
                or "jss" in text
                or "ss1" in text
                or "ss2" in text
                or "ss3" in text
            )
        )

        if coding_count >= 2:

            patterns.append(
                "The user frequently asks about coding or apps."
            )

        if school_count >= 2:

            patterns.append(
                "The user frequently asks school-related questions."
            )

    return patterns


# ------------------------------------------------------------
# FACT CHECK DETECTION
# ------------------------------------------------------------

def needs_fact_check(text):

    lower = text.lower()

    phrases = [
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
        "which country",
        "which year",
        "which team",
        "who won",
        "who has won",
        "how old",
        "capital of",
        "president of",
        "population of"
    ]

    for phrase in phrases:

        if phrase in lower:
            return True

    return False


# ------------------------------------------------------------
# WIKIPEDIA LOOKUP
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

        return summary_data.get("extract")

    except Exception:

        return None


# ------------------------------------------------------------
# DUCKDUCKGO LOOKUP
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

                topic_text = topic.get("Text")

                if topic_text:
                    return topic_text

    except Exception:

        return None

    return None


# ------------------------------------------------------------
# FACT INFORMATION
# ------------------------------------------------------------

def get_fact_information(question):

    if not needs_fact_check(question):

        return None

    result = search_wikipedia(question)

    if result:

        return result

    return search_duckduckgo(question)


# ------------------------------------------------------------
# CONFIDENCE
# ------------------------------------------------------------

def get_confidence(
    fact_information,
    emotion
):

    if fact_information:

        return "High"

    if emotion in [
        "frustrated",
        "sad",
        "confused",
        "worried"
    ]:

        return "Medium"

    return "Medium"


# ------------------------------------------------------------
# MEMORY
# ------------------------------------------------------------

def build_memory():

    memory = []

    if st.session_state.user_name:

        memory.append(
            "User's name: "
            + st.session_state.user_name
        )

    if st.session_state.student_level:

        memory.append(
            "User's education level: "
            + st.session_state.student_level
        )

    for item in st.session_state.personal_memory[-10:]:

        memory.append(
            "User asked KingsBot to remember: "
            + item
        )

    return "\n".join(memory)


# ------------------------------------------------------------
# GENERATE AI RESPONSE
# ------------------------------------------------------------

def generate_response(user_message):

    forget_response = handle_forgetting(
        user_message
    )

    if forget_response:

        return (
            forget_response,
            "High",
            "neutral"
        )

    detect_name(user_message)

    detect_student_level(user_message)

    remember_user_information(
        user_message
    )

    emotion = detect_emotion(
        user_message
    )

    st.session_state.last_emotion = emotion

    tone_instruction = get_tone_instruction(
        emotion
    )

    patterns = detect_patterns()

    fact_information = get_fact_information(
        user_message
    )

    confidence = get_confidence(
        fact_information,
        emotion
    )

    if st.session_state.student_level:

        level_instruction = (
            "The user's education level is "
            + st.session_state.student_level
            + ". Adapt explanations and examples to "
              "that level."
        )

    else:

        level_instruction = (
            "The user's education level is unknown. "
            "Answer at a normal general level."
        )

    system_message = (
        "You are KingsBot, a helpful and friendly AI assistant.\n\n"

        "Answer clearly and naturally.\n\n"

        "Help with mathematics, science, technology, coding, "
        "school subjects, history, general knowledge and "
        "everyday questions.\n\n"

        + level_instruction
        + "\n\n"

        + tone_instruction
        + "\n\n"

        "Remember useful information the user has told you "
        "during this conversation.\n\n"

        "For difficult problems, work through the important "
        "steps carefully and give a clear explanation. "
        "Do not pretend to be certain when you are unsure."
    )

    memory = build_memory()

    if memory:

        system_message += (
            "\n\nUSER MEMORY:\n"
            + memory
        )

    if patterns:

        system_message += (
            "\n\nCONVERSATION PATTERNS:\n"
            + "\n".join(patterns)
        )

    if fact_information:

        system_message += (
            "\n\nFACT INFORMATION:\n"
            + fact_information
        )

    system_message += (
        "\n\nPROACTIVE HELP:\n"
        "If the user appears stuck, give one useful next step."
    )

    messages = [
        {
            "role": "system",
            "content": system_message
        }
    ]

    messages.extend(
        st.session_state.messages
    )

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    model_inputs = tokenizer(
        [text],
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

    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids
        in zip(
            model_inputs.input_ids,
            generated_ids
        )
    ]

    response = tokenizer.batch_decode(
        generated_ids,
        skip_special_tokens=True
    )[0].strip()

    if not response:

        response = (
            "I couldn't generate a response. "
            "Please try again."
        )

    return response, confidence, emotion


# ------------------------------------------------------------
# VOICE: SPEECH TO TEXT
# ------------------------------------------------------------

def transcribe_audio(audio_file):

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
            audio_data
        )

        return text

    except sr.UnknownValueError:

        return None

    except sr.RequestError:

        return None

    except Exception:

        return None


# ------------------------------------------------------------
# VOICE: TEXT TO SPEECH
# ----

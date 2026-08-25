import streamlit as st
import torch
import requests
import re
from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# KINGSBOT AI
# Real local language model
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
# NAME DETECTION
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

    forget_everything = [
        "forget everything",
        "forget all my memory",
        "forget all my information",
        "delete everything you remember"
    ]

    forget_name = [
        "forget my name",
        "delete my name",
        "don't remember my name"
    ]

    forget_class = [
        "forget my class",
        "forget my education level",
        "delete my class"
    ]

    for phrase in forget_everything:

        if phrase in lower:

            st.session_state.user_name = None
            st.session_state.student_level = None
            st.session_state.personal_memory = []

            return (
                "Done. I cleared the personal information "
                "KingsBot had stored for this conversation."
            )

    for phrase in forget_name:

        if phrase in lower:

            st.session_state.user_name = None

            return (
                "Done. I forgot your saved name."
            )

    for phrase in forget_class:

        if phrase in lower:

            st.session_state.student_level = None

            return (
                "Done. I forgot your saved education level."
            )

    return None


# ------------------------------------------------------------
# PERSONAL MEMORY DETECTION
# ------------------------------------------------------------

def remember_user_information(text):

    lower = text.lower()

    remember_phrases = [
        "remember that",
        "remember this",
        "please remember",
        "keep this in mind"
    ]

    for phrase in remember_phrases:

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
# EMOTION / SENTIMENT LOGIC
# ------------------------------------------------------------

def detect_emotion(text):

    lower = text.lower()

    angry_words = [
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
        "depressed",
        "upset",
        "hurt",
        "terrible"
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
        "yesss",
        "yes!"
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
        "nervous",
        "problem",
        "help me"
    ]

    for word in angry_words:

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
            "The user seems frustrated. Stay calm, respectful "
            "and helpful. Do not argue. Give a direct solution."
        )

    if emotion == "sad":

        return (
            "The user seems sad. Respond warmly and respectfully. "
            "Do not be overly dramatic."
        )

    if emotion == "confused":

        return (
            "The user seems confused. Explain the answer more "
            "simply and use an easy example."
        )

    if emotion == "worried":

        return (
            "The user seems worried. Be reassuring and give "
            "clear practical steps."
        )

    if emotion == "happy":

        return (
            "The user seems happy. You can use a friendly "
            "and positive tone."
        )

    return (
        "Use a natural, friendly and clear tone."
    )


# ------------------------------------------------------------
# PATTERN RECOGNITION
# ------------------------------------------------------------

def detect_patterns():

    patterns = []

    if not st.session_state.messages:
        return patterns

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
# FACT QUESTION DETECTION
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
        "how much",
        "which country",
        "which year",
        "which team",
        "who won",
        "who has won",
        "how old",
        "capital of",
        "president of",
        "population of",
        "list the",
        "name the"
    ]

    for phrase in phrases:

        if phrase in lower:
            return True

    return False


# ------------------------------------------------------------
# WIKIPEDIA FACT LOOKUP
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
# DUCKDUCKGO FACT LOOKUP
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
# CONFIDENCE ESTIMATION
# ------------------------------------------------------------

def get_confidence(fact_information, emotion):

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
# MEMORY SUMMARY
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

    if st.session_state.personal_memory:

        for item in st.session_state.personal_memory[-10:]:

            memory.append(
                "User asked KingsBot to remember: "
                + item
            )

    return "\n".join(memory)


# ------------------------------------------------------------
# GENERATE RESPONSE
# ------------------------------------------------------------

def generate_response(user_message):

    # --------------------------------------------------------
    # MEMORY OPERATIONS
    # --------------------------------------------------------

    forget_response = handle_forgetting(
        user_message
    )

    if forget_response:

        return forget_response

    detect_name(user_message)

    detect_student_level(user_message)

    remember_user_information(
        user_message
    )

    # --------------------------------------------------------
    # EMOTION
    # --------------------------------------------------------

    emotion = detect_emotion(
        user_message
    )

    st.session_state.last_emotion = emotion

    tone_instruction = get_tone_instruction(
        emotion
    )

    # --------------------------------------------------------
    # PATTERNS
    # --------------------------------------------------------

    patterns = detect_patterns()

    # --------------------------------------------------------
    # FACT LOOKUP
    # --------------------------------------------------------

    fact_information = get_fact_information(
        user_message
    )

    confidence = get_confidence(
        fact_information,
        emotion
    )

    # --------------------------------------------------------
    # EDUCATION LEVEL
    # --------------------------------------------------------

    if st.session_state.student_level:

        level_instruction = (
            "The user's education level is "
            + st.session_state.student_level
            + ". Adapt explanations and examples to that "
              "level. Do not unnecessarily use much higher "
              "level material."
        )

    else:

        level_instruction = (
            "The user's education level is unknown. "
            "Answer at a normal general level."
        )

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    memory = build_memory()

    # --------------------------------------------------------
    # SYSTEM INSTRUCTION
    # --------------------------------------------------------

    system_message = (
        "You are KingsBot, a helpful and friendly AI assistant.\n\n"

        "Answer naturally and clearly.\n\n"

        "Help with mathematics, science, technology, coding, "
        "school subjects, history, general knowledge and "
        "everyday questions.\n\n"

        + level_instruction
        + "\n\n"

        + tone_instruction
        + "\n\n"

        "Remember useful information the user has told you "
        "during this conversation.\n\n"

        "When solving a difficult problem, work through the "
        "problem carefully and give the user a clear explanation "
        "of the important steps. Do not claim certainty when "
        "you are unsure.\n\n"

        "If factual information is supplied below, use it as "
        "evidence and do not invent different dates, names or "
        "numbers."
    )

    # --------------------------------------------------------
    # ADD PERSONAL MEMORY
    # --------------------------------------------------------

    if memory:

        system_message += (
            "\n\nUSER MEMORY:\n"
            + memory
        )

    # --------------------------------------------------------
    # ADD PATTERNS
    # --------------------------------------------------------

    if patterns:

        system_message += (
            "\n\nUSEFUL CONVERSATION PATTERNS:\n"
            + "\n".join(patterns)
        )

    # --------------------------------------------------------
    # ADD FACTS
    # --------------------------------------------------------

    if fact_information:

        system_message += (
            "\n\nFACT INFORMATION FROM LOOKUP:\n"
            + fact_information
        )

    # --------------------------------------------------------
    # ADD PROACTIVE GUIDANCE
    # --------------------------------------------------------

    system_message += (
        "\n\nPROACTIVE GUIDANCE:\n"
        "If the user appears stuck, suggest one useful next "
        "step. Do not overwhelm the user with unnecessary "
        "suggestions."
    )

    # --------------------------------------------------------
    # CREATE MESSAGE LIST
    # --------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": system_message
        }
    ]

    # --------------------------------------------------------
    # CONVERSATION MEMORY
    # --------------------------------------------------------

    messages.extend(
        st.session_state.messages
    )

    # --------------------------------------------------------
    # CURRENT QUESTION
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # --------------------------------------------------------
    # CHAT TEMPLATE
    # --------------------------------------------------------

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # --------------------------------------------------------
    # TOKENIZE
    # --------------------------------------------------------

    model_inputs = tokenizer(
        [text],
        return_tensors="pt",
        truncation=True,
        max_length=2048
    ).to(model.device)

    # --------------------------------------------------------
    # GENERATE
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
    # REMOVE INPUT PROMPT
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
    # DECODE
    # --------------------------------------------------------

    response = tokenizer.batch_decode(
        generated_ids,
        skip_special_tokens=True
    )[0].strip()

    if not response:

        response = (
            "I couldn't generate a response. "
            "Please try asking the question again."
        )

    return response, confidence, emotion


# ------------------------------------------------------------
# TITLE
# ------------------------------------------------------------

st.title("🤖 KingsBot AI")

st.caption(
    "Real local AI with memory, EQ and learning-level adaptation"
)


# ------------------------------------------------------------
# SHOW OLD CONVERSATION
# ------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )


# ------------------------------------------------------------
# CHAT INPUT
# ------------------------------------------------------------

prompt = st.chat_input(
    "Ask KingsBot anything..."
)


if prompt:

    # --------------------------------------------------------
    # SHOW USER
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "🧠 Thinking..."
        ):

            try:

                response, confidence, emotion = (
                    generate_response(prompt)
                )

            except Exception as error:

                response = (
                    "I ran into an error while thinking.\n\n"
                    f"`{error}`"
                )

                confidence = "Unknown"

                emotion = "neutral"

        st.markdown(response)

        # Show confidence only when useful
        st.caption(
            "Confidence estimate: "
            + confidence
        )

    # --------------------------------------------------------
    # SAVE CONVERSATION
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )


# ------------------------------------------------------------
# CREATE SAVED CHAT
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

    if st.session_state.personal_memory:

        lines.append(
            "Personal memory:"
        )

        for item in st.session_state.personal_memory:

            lines.append(
                "- " + item
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
        "A real AI assistant with memory, EQ, "
        "fact lookup and education-level adaptation."
    )

    st.divider()

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

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

    if st.session_state.personal_memory:

        st.write(
            "📝 Saved memories: "
            + str(
                len(
                    st.session_state.personal_memory
                )
            )
        )

    if (
        not st.session_state.user_name
        and not st.session_state.student_level
        and not st.session_state.personal_memory
    ):

        st.info(
            "KingsBot has not learned personal "
            "information yet."
        )

    st.divider()

    # --------------------------------------------------------
    # EMOTION
    # --------------------------------------------------------

    st.subheader("❤️ EQ")

    st.write(
        "Current detected tone: "
        + st.session_state.last_emotion
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

                    preview = (
                        preview[:60]
                        + "..."
                    )

                st.write(
                    f"💬 {user_messages}. {preview}"
                )

    else:

        st.write(
            "No conversations yet."
        )

    # --------------------------------------------------------
    # SAVE CONVERSATION
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
    st.write("❤️ EQ / sentiment")
    st.write("🎭 Tone adaptation")
    st.write("🧠 Personalized memory")
    st.write("🧹 Ethical forgetting")
    st.write("🎓 Primary → University")
    st.write("🔎 Pattern recognition")
    st.write("🧭 Proactive guidance")
    st.write("📊 Confidence estimate")
    st.write("🌐 Fact lookup")
    st.write("💬 Conversation memory")
    st.write("💾 Save conversations")
    st.write("🧮 Mathematics")
    st.write("💻 Coding help")
    st.write("🔬 Science")
    st.write("🌍 General knowledge")

    st.divider()

    # --------------------------------------------------------
    # CLEAR EVERYTHING
    # --------------------------------------------------------

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

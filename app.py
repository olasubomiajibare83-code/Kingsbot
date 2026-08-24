import streamlit as st
import requests

st.title("Kingsbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# MASSIVE LOCAL FACT BANK (Works instantly, NEVER crashes)
def get_fact(question):
    q = question.lower().strip()

    # Presidents
    if "president of nigeria" in q: return "The current President of Nigeria is Bola Ahmed Tinubu."
    if "president of usa" in q or "president of america" in q: return "The current President of the USA is Joe Biden."

    # Capitals
    if "capital of nigeria" in q: return "The capital of Nigeria is Abuja."
    if "capital of lagos" in q: return "Lagos is a state, but the capital is Ikeja."
    if "capital of usa" in q: return "The capital of the USA is Washington D.C."
    if "capital of uk" in q: return "The capital of the UK is London."
    if "capital of france" in q: return "The capital of France is Paris."
    if "capital of japan" in q: return "The capital of Japan is Tokyo."

    # Science
    if "water" in q: return "Water is H2O."
    if "photosynthesis" in q: return "Photosynthesis is how plants make food."
    if "gravity" in q: return "Gravity pulls objects to the Earth."
    if "dna" in q: return "DNA is the blueprint of life."

    # People
    if "davido" in q: return "Davido is a famous Nigerian Afrobeats singer."
    if "wizkid" in q: return "Wizkid is a Grammy-winning Nigerian singer."
    if "messi" in q: return "Messi is an Argentine football legend."

    # Math (Simple)
    try:
        if "+" in q:
            parts = q.split("+")
            num1 = int(''.join(filter(str.isdigit, parts[0])))
            num2 = int(''.join(filter(str.isdigit, parts[1])))
            return f"The answer is {num1 + num2}"
        if "-" in q:
            parts = q.split("-")
            num1 = int(''.join(filter(str.isdigit, parts[0])))
            num2 = int(''.join(filter(str.isdigit, parts[1])))
            return f"The answer is {num1 - num2}"
    except:
        pass

    # Fallback
    return "The AI server is busy, but I am still here! Ask me about presidents, capitals, or math!"

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 1. Try the AI API
    try:
        response = requests.post(
            "https://ai.hackclub.com/chat/completions",
            json={"messages": [{"role": "user", "content": prompt}]},
            timeout=10
        )
        data = response.json()
        if "choices" in data:
            bot_reply = data["choices"][0]["message"]["content"]
        else:
            bot_reply = get_fact(prompt) or "The AI server is busy. Let me try to answer from my local facts!"
    except:
        bot_reply = get_fact(prompt) or "The AI server is busy. Let me try to answer from my local facts!"
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

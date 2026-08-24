import streamlit as st
import requests

st.title("Kingsbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Local Fact Bank (Works instantly, NEVER crashes)
def get_fact(question):
    q = question.lower().strip()
    if "president of nigeria" in q: return "The current President of Nigeria is Bola Ahmed Tinubu."
    if "capital of nigeria" in q: return "The capital of Nigeria is Abuja."
    if "capital of usa" in q: return "The capital of the USA is Washington D.C."
    if "capital of france" in q: return "The capital of France is Paris."
    if "water" in q: return "Water is H2O."
    if "davido" in q: return "Davido is a famous Nigerian Afrobeats singer."
    return None

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

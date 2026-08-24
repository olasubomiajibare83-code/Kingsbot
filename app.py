import streamlit as st
import requests

st.title("Kingsbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": "Bearer sk-or-v1-xxxxxxxxxxxxxxxx"},
            json={
                "model": "qwen/qwen-2.5-72b-instruct",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        data = response.json()
        bot_reply = data["choices"][0]["message"]["content"]
    except:
        bot_reply = "The real brain is taking a moment. Please try again in 15 seconds."
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

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
    
    # Call the FREE, no-sign-up-required API
    response = requests.post("https://ai.hackclub.com/chat/completions", 
                             json={"messages": [{"role": "user", "content": prompt}]})
    
    data = response.json()
    bot_reply = data["choices"][0]["message"]["content"]
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

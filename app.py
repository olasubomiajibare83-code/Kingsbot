import streamlit as st
import requests

st.titlenn("Kingsbot")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.?.messages.append({"role": "user", "content": prompt})
    
    # Call the REAL AI brain (100% Free, works in Nigeria)
    try:
        response = requests.get(f"https://text.pollinations.ai/{prompt}")
        bot_reply = response.text
    except:
        bot_reply = "The AI server is taking a break. Please try again in 10 seconds."
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

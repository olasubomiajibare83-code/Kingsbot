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
    
    # Use the FREE, instant browser API
    try:
        response = requests.get(f"https://api.duckduckgo.com/?q={prompt}&format=json")
        data = response.json()
        bot_reply = data.get("AbstractText", "I don't know that yet. Try asking me a specific fact!")
    except:
        bot_reply = "The server is busy. Please try again in 10 seconds."
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

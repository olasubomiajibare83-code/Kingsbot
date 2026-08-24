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
    
    # Call the REAL AI without any keys
    try:
        response = requests.get(f"https://text.pollinations.ai/{prompt}")
        bot_reply = response.text
    except:
        bot_reply = "The AI is taking a moment. Please try again in 10 seconds."
    
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    
    # Speak the answer out loud
    audio_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={bot_reply}&tl=en&client=tw-ob"
    st.audio(audio_url, format="audio/mp3")

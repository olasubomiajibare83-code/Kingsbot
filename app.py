import streamlit as st
import requests

st.title("Kingsbot")

# Play sound when the bot speaks
st.markdown("""
<style>
    .stAudio { display: none; }
</style>
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything or type... "):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Use the free, instant, reliable API
    try:
        response = requests.get(f"https://api.duckduckgo.com/?q={prompt}&format=json")
        data = response.json()
        bot_reply = data.get("AbstractText", "I don't know that yet. Try asking me a specific fact!")
    except:
        bot_reply = "The server is busy. Please try again in 10 seconds."
    
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    
    # 1. Turn the reply into a voice file
    audio_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={bot_reply}&tl=en&client=tw-ob"
    
    # 2. Play the voice file for the user
    st.audio(audio_url, format="audio/mp3")

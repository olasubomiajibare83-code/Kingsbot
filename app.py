import streamlit as st
import requests

st.title("Kingsbot")

# This correctly hides the audio player
st.markdown("""
<style>
    [data-testid="stAudio"] { display: none; }
</style>
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- VOICE INPUT (Speak to the bot) ---
st.write("### 🎤 Speak to Kingsbot")

voice_text = st.text_input("Type here if you don't want to use voice:")

# --- TEXT INPUT ---
prompt = st.chat_input("Ask me anything...")

# If user typed or used voice
if voice_text:
    prompt = voice_text
    st.session_state.voice_input = ""

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Use the reliable DuckDuckGo API
    try:
        response = requests.get(f"https://api.duckduckgo.com/?q={prompt}&format=json")
        data = response.json()
        bot_reply = data.get("AbstractText", "I don't know that yet. Try asking me a specific fact!")
    except:
        bot_reply = "The server is busy. Please try again in 10 seconds."
    
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    
    # --- VOICE OUTPUT (The bot speaks back) ---
    audio_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={bot_reply}&tl=en&client=tw-ob"
    st.audio(audio_url, format="audio/mp3")

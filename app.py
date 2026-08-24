import streamlit as st
import requests

# Your FREE Gemini API Key (I will show you how to get it after this!)
API_KEY = "PASTE_YOUR_GEMINI_KEY_HERE"

st.title("Kingsbot")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Call the FREE Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    try:
        bot_reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        bot_reply = "Sorry, I hit a small error."
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

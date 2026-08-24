import streamlit as st
import requests

st.title("Kingsbot - Llama 3.2")

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    
    # The API payload for a lightweight model
    response = requests.post(
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        headers={"Content-Type": "application/json"},
        json={"inputs": prompt}
    )
    
    bot_reply = response.json()[0]["generated_text"]
    st.chat_message("assistant").markdown(bot_reply)

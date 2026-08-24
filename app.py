import streamlit as st
import requests

st.title("Kingsbot")

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    
    # Call the REAL AI brain (100% Free)
    try:
        response = requests.get(f"https://text.pollinations.ai/{prompt}")
        bot_reply = response.text
    except:
        bot_reply = "The AI server is taking a break. Please try again in 10 seconds."
    
    st.chat_message("assistant").markdown(bot_reply)

import streamlit as st
from transformers import pipeline

# This is the REAL brain that fits in the memory
chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium")

st.title("Kingsbot")

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    
    response = chatbot(prompt, max_new_tokens=100)[0]['generated_text']
    
    st.chat_message("assistant").markdown(response)

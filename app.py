import streamlit as st
from transformers import pipeline

# This is the REAL, UNLIMITED AI brain
chatbot = pipeline("text-generation", model="distilgpt2")

st.title("Kingsbot")

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    
    # The AI computes the answer internally, no busy server!
    response = chatbot(prompt, max_new_tokens=100)[0]['generated_text']
    
    st.chat_message("assistant").markdown(response)

import streamlit as st
from transformers import pipeline

# Use the REAL mathematical neural network weights
chatbot = pipeline("text-generation", model="distilgpt2")

st.title("Kingsbot")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # The Neural Network generates the response using math
    response = chatbot(prompt, max_new_tokens=100)[0]['generated_text']
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

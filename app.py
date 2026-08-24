import streamlit as st
from transformers import pipeline

# Load the Zephyr model - It is free, smart, and knows general knowledge!
chatbot = pipeline("text-generation", model="HuggingFaceH4/zephyr-7b-beta")

st.title("Kingsbot")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate response
    response = chatbot(prompt, max_new_tokens=150)[0]['generated_text']
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

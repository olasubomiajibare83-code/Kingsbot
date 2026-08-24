import streamlit as st
from transformers import pipeline

# Load the SUPER SMART Llama 3.1 model
chatbot = pipeline("text-generation", model="meta-llama/Llama-3.2-1B-Instruct")

st.title("Kingsbot")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Use the instruct model properly
    messages = [{"role": "user", "content": prompt}]
    response = chatbot(messages, max_new_tokens=150)[0]['generated_text'][-1]['content']
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

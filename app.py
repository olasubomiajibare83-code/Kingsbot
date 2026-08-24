import streamlit as st
from transformers import pipeline

# The smarter model that speaks clear English
chatbot = pipeline("text-generation", model="gpt2")

st.title("Kingsbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # The AI is instructed to answer briefly and in English only
    full_prompt = f"Answer the following question in one short sentence in English. Question: {prompt} Answer:"
    
    response = chatbot(full_prompt, max_new_tokens=50, do_sample=False)[0]['generated_text']
    
    # Remove the instruction part from the response
    bot_reply = response.replace(full_prompt, "").strip()
    
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

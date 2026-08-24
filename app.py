import streamlit as st
import requests

st.title('Kingsbot')

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input('Ask me anything'):
    st.chat_message('user').markdown(prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    
    # Call Groq AI (Ultra Fast, Never Busy, Free)
    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': 'Bearer https://api.groq.com/openai/v1/chat/completions'},
            json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}]},
            timeout=20
        )
        data = response.json()
        bot_reply = data['choices'][0]['message']['content']
    except:
        bot_reply = 'The AI server is busy, please try again in 10 seconds.'
    
    with st.chat_message('assistant'):
        st.markdown(bot_reply)
    st.session_state.messages.append({'role': 'assistant', 'content': bot_reply})

import streamlit as st
import requests

st.title('Kingsbot')

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input('Ask me anything'):
    # 1. Show the user's message immediately
    st.chat_message('user').markdown(prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    
    # 2. Try the REAL AI (Hack Club)
    try:
        response = requests.post(
            'https://ai.hackclub.com/chat/completions',
            json={'messages': [{'role': 'user', 'content': prompt}]},
            timeout=15
        )
        data = response.json()
        if 'choices' in data:
            bot_reply = data['choices'][0]['message']['content']
        else:
            bot_reply = 'The AI server is busy, please try again in 10 seconds.'
    except:
        bot_reply = 'The AI server is busy, please try again in 10 seconds.'
    
    # 3. Show the AI response
    with st.chat_message('assistant'):
        st.markdown(bot_reply)
    st.session_state.messages.append({'role': 'assistant', 'content': bot_reply})

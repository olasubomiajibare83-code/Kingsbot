import streamlit as st
import requests

st.title('Kingsbot')

if prompt := st.chat_input('Ask me anything'):
    st.chat_message('user').markdown(prompt)
    
    try:
        response = requests.post(
            'https://ai.hackclub.com/chat/completions',
            json={'messages': [{'role': 'user', 'content': prompt}]},
            timeout=10
        )
        data = response.json()
        bot_reply = data['choices'][0]['message']['content']
    except:
        bot_reply = 'Hi, how may i help you.'
    
    st.chat_message('assistant').markdown(bot_reply)

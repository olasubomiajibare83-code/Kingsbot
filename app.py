import streamlit as st
import requests

st.title('Kingsbot')

if prompt := st.chat_input('Ask me anything'):
    st.chat_message('user').markdown(prompt)
    
    try:
        response = requests.get(f'https://text.pollinations.ai/{prompt}')
        bot_reply = response.text
    except:
        bot_reply = 'I am having trouble connecting to the server. Please try again in 10 seconds.'
    
    st.chat_message('assistant').markdown(bot_reply)

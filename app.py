import streamlit as st
import requests
import json
import time
from datetime import datetime

# ============================================================
# PAGE SETTINGS
# ============================================================
st.set_page_config(
    page_title="KingsBot AI — API Brain",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 KingsBot AI — Real Brain")
st.caption("Powered by AI • No Installation • Just API")

# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = "gpt-3.5-turbo"

# ============================================================
# SIDEBAR — API SETUP
# ============================================================
with st.sidebar:
    st.header("⚙️ API Settings")
    
    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    if api_key:
        st.session_state.api_key = api_key
    
    model = st.selectbox(
        "Select Model",
        ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    )
    st.session_state.model = model
    
    st.caption("Get your API key from: platform.openai.com")
    st.divider()
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# DISPLAY CONVERSATION
# ============================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ============================================================
# GENERATE RESPONSE (USES REAL AI)
# ============================================================
def generate_response(prompt):
    if not st.session_state.api_key:
        return "⚠️ Please enter your OpenAI API key in the sidebar."
    
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": "You are KingsBot, a helpful AI assistant."}
        ]
        messages.extend(st.session_state.messages[-10:])
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": st.session_state.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ API Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================================
# TEXT INPUT
# ============================================================
prompt = st.chat_input("Ask KingsBot anything...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            start = time.time()
            response = generate_response(prompt)
            elapsed = time.time() - start
            st.write(response)
            st.caption(f"⏱️ {elapsed:.2f}s • {st.session_state.model}")
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("🤖 KingsBot • Powered by OpenAI • No Installation Required")

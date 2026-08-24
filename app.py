import streamlit as st

st.title("Kingsbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def get_answer(question):
    q = question.lower().strip()
    
    # User greeting
    if q in ["hi", "hello", "hey"]:
        return "Hello! How can I help you today?"
    
    # Presidents
    if "president of nigeria" in q:
        return "The current President of Nigeria is Bola Ahmed Tinubu."
    if "president of usa" in q or "president of america" in q:
        return "The current President of the USA is Joe Biden."
        
    # Capitals
    if "capital of nigeria" in q:
        return "The capital of Nigeria is Abuja."
    if "capital of france" in q:
        return "The capital of France is Paris."
    if "capital of uk" in q:
        return "The capital of the UK is London."
        
    # Math
    try:
        # Simple math checking
        if "+" in q:
            parts = q.split("+")
            num1 = int(''.join(filter(str.isdigit, parts[0])))
            num2 = int(''.join(filter(str.isdigit, parts[1])))
            return f"The answer is {num1 + num2}"
        if "-" in q:
            parts = q.split("-")
            num1 = int(''.join(filter(str.isdigit, parts[0])))
            num2 = int(''.join(filter(str.isdigit, parts[1])))
            return f"The answer is {num1 - num2}"
        if "x" in q or "*" in q:
            parts = q.replace("x", "*").split("*")
            num1 = int(''.join(filter(str.isdigit, parts[0])))
            num2 = int(''.join(filter(str.isdigit, parts[1])))
            return f"The answer is {num1 * num2}"
    except:
        pass

    # Science
    if "water" in q:
        return "Water is H2O."
    if "photosynthesis" in q:
        return "Photosynthesis is how plants make food using sunlight."
    if "gravity" in q:
        return "Gravity pulls objects towards the Earth."
    if "dna" in q:
        return "DNA is the blueprint of life."

    # Fallback
    return "I don't know the answer to that yet. Try asking about presidents, capitals, math, or science."

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    bot_reply = get_answer(prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

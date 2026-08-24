import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer

# This model runs INSIDE the server. No keys, no crashes.
model_name = "Qwen/Qwen2.5-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

st.title("Kingsbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Ask the REAL Brain
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    model_inputs = tokenizer([text], return_tensors="pt")
    generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=100, do_sample=False)
    
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    # Clean the answer
    bot_reply = response.replace(text, "").strip() or response.strip()
    
    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

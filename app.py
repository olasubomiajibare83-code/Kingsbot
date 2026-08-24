import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load the real AI model
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
    
    # Format the prompt for the AI
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    # Generate the answer
    model_inputs = tokenizer([text], return_tensors="pt")
    generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=100, do_sample=False)
    
    # Decode ONLY the answer
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    # Clean the response to remove the prompt
    if text in response:
        bot_reply = response.replace(text, "").strip()
    else:
        bot_reply = response.strip()
    
    # If the system prompt accidentally got included, cut it off
    if "system" in bot_reply.lower()[:10]:
        bot_reply = bot_reply.split("assistant")[-1].strip()
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

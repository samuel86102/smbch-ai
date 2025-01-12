import streamlit as st

# from groq import Groq
from openai import OpenAI


# groq_api_key = "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"


# Read the system prompt from the external file
with open("sys_prompt.txt", "r", encoding="utf-8") as file:
    sys_prompt = file.read()


st.set_page_config(page_title="教會AI助手", page_icon="✝️")


# Show title and description.
st.title("✝️  教會AI助手 ")
st.write("測試階段，可以問教會資訊(資訊截至 2025/01/05 )")
st.write("可以產生小組成長題目")

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management


# Create an Groq client.
client = OpenAI(
    api_key="sk-c155cb6974f1429e879d54b117e3befb", base_url="https://api.deepseek.com"
)
# client = Groq(api_key=groq_api_key)
# model_name = "llama3-8b-8192"
# model_name = "gemma2-9b-it"
model_name = "deepseek-chat"

# Create a session state variable to store the chat messages. This ensures that the
# messages persist across reruns.

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": sys_prompt}
    ]  # Add the system prompt here


# Display the existing chat messages via `st.chat_message`, excluding the system prompt
for message in st.session_state.messages:
    if message["role"] != "system":  # Skip the system prompt
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# Create a chat input field to allow the user to enter a message. This will display
# automatically at the bottom of the page.
if prompt := st.chat_input("平安！我能協助你什麼？"):
    st.session_state.messages.append({"role": "user", "content": f"{prompt}"})
    st.chat_message("user").write(prompt)
    # response = client.chat.completions.create(model="llama3-8b-8192", messages=st.session_state.messages)
    response = client.chat.completions.create(
        model=model_name, messages=st.session_state.messages, stream=False
    )
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

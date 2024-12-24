import streamlit as st

from groq import Groq
groq_api_key = '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'


# Read the system prompt from the external file
with open('sys_prompt.txt', 'r', encoding='utf-8') as file:
    sys_prompt = file.read()


st.set_page_config(page_title="石浸AI助手", page_icon="✝️")


# Show title and description.
st.title("✝️  石浸AI助手 🤖 ")
st.write("測試階段，可以問教會資訊 / 下一季服事表，但不要狂問額度會用完")

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management


# Create an Groq client.
client = Groq(api_key = groq_api_key)

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
if prompt := st.chat_input("What is up?"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(model="llama3-8b-8192", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

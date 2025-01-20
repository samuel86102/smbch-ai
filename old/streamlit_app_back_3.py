import streamlit as st
from openai import OpenAI

# Read the system prompt from the external file
with open("sys_prompt.txt", "r", encoding="utf-8") as file:
    sys_prompt = file.read()

st.set_page_config(page_title="教會AI助手", page_icon="✝️")

# Show title and description.
st.title("✝️  教會AI助手 ")
st.warning("測試階段", icon="⚠️")

if st.button("慶祝！🥳"):
    st.balloons()


st.write("""
- 可以問教會資訊(資訊截至 2025/01/12)
- 可以產生小組成長題目
- 可以詢問如何讀聖經
""")

# Create an OpenAI client.
client = OpenAI(
    api_key="sk-c155cb6974f1429e879d54b117e3befb", base_url="https://api.deepseek.com"
)
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

    # Start streaming response
    response = client.chat.completions.create(
        model=model_name, messages=st.session_state.messages, stream=True
    )
    msg = ""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        for chunk in response:  # Stream the response chunks
            chunk_content = (
                chunk.choices[0].delta.content
                if hasattr(chunk.choices[0].delta, "content")
                else ""
            )
            msg += chunk_content
            message_placeholder.markdown(msg)  # Update content incrementally
    st.session_state.messages.append({"role": "assistant", "content": msg})

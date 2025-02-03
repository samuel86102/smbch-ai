import streamlit as st
from openai import OpenAI
from utils.process import *


st.set_page_config(page_title="教會AI助手", page_icon="✝️")

# Read the base system prompt
with open("sys_prompt.txt", "r", encoding="utf-8") as file:
    base_sys_prompt = file.read()

url = "https://docs.google.com/spreadsheets/d/1jBIFbMoAGu28sz2EXOkuGVQtgT8yY7l8GNJ3ZmctIYM/edit?gid=723640444#gid=723640444"
json_string = df_to_json(convert_google_sheet_url(url))

base_sys_prompt += f"\n---\n# 以下是這一季的服事表:{json_string}"
# base_sys_prompt = 'zh-tw'


# Export to a .txt file
with open("serve.txt", "w") as file:
    file.write(json_string)

print("File saved as serve.txt")


taiwan_now = current_time(offset=8)

base_sys_prompt += f"\n---\n# 目前時間:{taiwan_now}"


st.title("✝️ 教會AI助手 ")
# st.warning("測試階段", icon="⚠️")

if st.button("慶祝！🥳"):
    st.balloons()

st.write("""
- 可詢問：
  - 教會公開資訊、週報消息(截至 2025/01/26)
  - 小組成長題目
  - 2025 Q1 崇拜服事表
""")

# api_key = "sk-ee0f84386d5d4f38965621bc6019f0d9"
# base_url = "https://api.deepseek.com"
# model_name = "deepseek-chat"

api_key = "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"
base_url = "https://openrouter.ai/api/v1"
# model_name = "deepseek/deepseek-r1-distill-llama-70b"
model_name = "deepseek/deepseek-chat"

client = OpenAI(api_key=api_key, base_url=base_url)


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": base_sys_prompt}]

# Display existing messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


if prompt := st.chat_input("平安！我能協助你什麼？"):
    if prompt == "hi":
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        msg = "hey!"
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})

    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        response = client.chat.completions.create(
            model=model_name, messages=st.session_state.messages, stream=True
        )

        msg = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            for chunk in response:
                chunk_content = (
                    chunk.choices[0].delta.content
                    if hasattr(chunk.choices[0].delta, "content")
                    else ""
                )
                msg += chunk_content
                message_placeholder.markdown(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})

import streamlit as st
from openai import OpenAI
from utils.process import *


st.set_page_config(page_title="教會AI助手", page_icon="✝️")
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

# Read the base system prompt
with open("sys_prompt.txt", "r", encoding="utf-8") as file:
    base_sys_prompt = file.read()

url = "https://docs.google.com/spreadsheets/d/1jBIFbMoAGu28sz2EXOkuGVQtgT8yY7l8GNJ3ZmctIYM/edit?gid=723640444#gid=723640444"
json_service, json_person = process_service_roster(url)

service_info = json_service


on = st.toggle("服事表查詢模式")
if on:
    st.write("個人模式啟動")
    service_info = json_person


selected_model = st.selectbox(
    "LLM Model",
    (
        "meta-llama/llama-3.3-70b-instruct",
        "deepseek/deepseek-chat",
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-3.2-1b-instruct:free",
        "deepseek/deepseek-r1:free",
        "deepseek/deepseek-r1-distill-llama-70b:free",
        "deepseek/deepseek-r1-distill-qwen-32b",
        "deepseek/deepseek-r1-distill-qwen-1.5b",
        "deepseek/deepseek-r1-distill-llama-70b",
    ),
)


base_sys_prompt += f"\n---\n# 以下是這一季的服事表:{service_info}"


taiwan_now = current_time(offset=8)

base_sys_prompt += f"\n---\n# 目前時間:{taiwan_now}"


api_key = st.secrets["llm"]["api_key"]
base_url = st.secrets["llm"]["base_url"]
# model_name = "deepseek/deepseek-chat" # 0.49
# model_name = "meta-llama/llama-3.3-70b-instruct"  # 0.12
# model_name = "deepseek/deepseek-r1:free"
model_name = selected_model

client = OpenAI(api_key=api_key, base_url=base_url)


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": base_sys_prompt}]

# Display existing messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


if prompt := st.chat_input("平安！我能協助你什麼？"):
    if prompt == "test":
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        msg = "this is non-llm response"
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

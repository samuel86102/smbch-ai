import streamlit as st
from openai import OpenAI
import pandas as pd
import json

# from utils.process import *
from utils.process import process_service_roster, current_time

st.set_page_config(page_title="教會AI助手", page_icon="✝️")
st.markdown(
    """
    <style>
    .st-emotion-cache-janbn0 {
        flex-direction: row-reverse;
        text-align: right;
        border-radius: 1.5rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


st.title("✝️ 教會AI助手 ")
# st.warning("測試階段", icon="⚠️")

if st.button("慶祝！🥳"):
    st.balloons()

st.write("""
- 可詢問：
  - 教會公開資訊、週報消息(截至 2025/01/26)
  - 小組成長題目
""")

# Read the base system prompt
with open("sys_prompt.txt", "r", encoding="utf-8") as file:
    base_sys_prompt = file.read()

url = "https://docs.google.com/spreadsheets/d/1jBIFbMoAGu28sz2EXOkuGVQtgT8yY7l8GNJ3ZmctIYM/edit?gid=723640444#gid=723640444"
json_service, json_service_raw, json_person, json_person_raw = process_service_roster(
    url
)

service_info = json_service


df_service = pd.DataFrame(json.loads(json_service_raw))


def get_person_df(json_person_raw, name):
    person_dict = json.loads(json_person_raw)["data"][name]

    max_length = max(len(v) for v in person_dict.values())
    for key in person_dict:
        while len(person_dict[key]) < max_length:
            person_dict[key].append(None)  # Or use an empty string ""

    df_person = pd.DataFrame(person_dict)

    return df_person


# selected_model = st.selectbox(
#     "語言模型",
#     (
#         "deepseek/deepseek-chat",
#         "meta-llama/llama-3.3-70b-instruct",
#         "openai/gpt-4o-mini",
#         "meta-llama/llama-3.2-3b-instruct:free",
#         "meta-llama/llama-3.2-1b-instruct:free",
#         "deepseek/deepseek-r1:free",
#         "deepseek/deepseek-r1-distill-llama-70b:free",
#         "deepseek/deepseek-r1-distill-qwen-32b",
#         "deepseek/deepseek-r1-distill-qwen-1.5b",
#         "deepseek/deepseek-r1-distill-llama-70b",
#     ),
# )

selected = st.selectbox(
    "語言模型",
    (
        "openai/gpt-4o-mini;0.15",
        "deepseek/deepseek-chat;0.49",
        "meta-llama/llama-3.1-70b-instruct:free;0",
        "meta-llama/llama-3.2-3b-instruct:free;0.00",
        "meta-llama/llama-3.3-70b-instruct;0.12",
    ),
)

selected_model = selected.split(";")[0]


# base_sys_prompt += f"\n---\n# 以下是這一季的服事表:{service_info}"
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


# Display chat history
for message in st.session_state.messages:
    role, content = message["role"], message["content"]
    if role != "system":
        if isinstance(content, pd.DataFrame):  # Check if content is a DataFrame
            with st.chat_message(role):
                st.dataframe(content)  # Display DataFrame as a table
        else:
            with st.chat_message(role):
                st.write(content)  # Display plain text


# Display existing messages
# for message in st.session_state.messages:
#     if message["role"] != "system":
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])


if prompt := st.chat_input("平安！我能協助你什麼？"):
    if prompt == "test":
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        msg = "this is non-llm response"
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})

    elif prompt == "service":
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            st.write(f"收到指令 '{prompt}'，以下為本季服事表:\n")
            # st.dataframe(df_service)

            # Freeze top-left 3 columns and disable sorting for all columns
            column_config = {
                col: {"frozen": True}
                for col in df_service.columns[:3]  # Freeze the first 3 columns
            }

            st.data_editor(
                df_service,
                hide_index=True,  # Hide index
                column_config=column_config,  # Freeze first 3 columns
                disabled=df_service.columns.tolist(),  # Disable sorting & editing for all columns
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": df_service}
            )

    elif "service:" in prompt:
        name = prompt.split(":")[1]

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            st.write(f"收到指令 '{prompt}'，以下為本季 {name} 的服事表:\n")
            df_person = get_person_df(json_person_raw, name)
            st.dataframe(df_person, hide_index=True)
            # message_placeholder = st.empty()
            # message_placeholder.markdown(msg)
        st.session_state.messages.append({"role": "assistant", "content": df_person})

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

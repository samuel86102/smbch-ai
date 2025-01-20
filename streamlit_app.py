import streamlit as st
from openai import OpenAI
import pandas as pd
import re
import tiktoken
from datetime import datetime, timezone, timedelta


def get_current_input_tokens(messages, base_system_tokens):
    """Count tokens for the current input to API, avoiding duplicate system prompt counting."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    # Count system prompt only once
    conversation_tokens = sum(
        len(encoding.encode(message["content"])) + 4
        for message in messages[1:]  # Skip system prompt
    )
    return base_system_tokens + conversation_tokens + 2  # +2 for assistant prefix


def count_single_message_tokens(message):
    """Count tokens for a single message."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(encoding.encode(message)) + 4


def convert_google_sheet_url(url):
    pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?"
    replacement = (
        lambda m: f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?"
        + (f"gid={m.group(3)}&" if m.group(3) else "")
        + "format=csv"
    )
    new_url = re.sub(pattern, replacement, url)
    return new_url


def df_to_json(csv_url):
    df = pd.read_csv(csv_url, header=1)
    # df = df[df["季度"].isin(["Q1", "Q2", "Q3"])]
    df = df[df["季度"].isin(["Q1"])]
    df = df.iloc[:, 0:24]

    # Merge columns with "Vocal" in their name, ignoring NaN values
    df["Vocal"] = df.filter(like="Vocal").apply(
        lambda row: " ".join(row.dropna().astype(str)), axis=1
    )

    # Drop the original columns (optional)
    df = df.drop(columns=df.filter(like="Vocal.").columns)

    # df.to_csv("tmp.csv")

    json_output = df.to_json(orient="records", force_ascii=False)
    json_output = str(json_output).replace("null", "")
    # print(json_output)
    # input()
    return json_output


st.set_page_config(page_title="教會AI助手", page_icon="✝️")

# Read the base system prompt
with open("sys_prompt.txt", "r", encoding="utf-8") as file:
    base_sys_prompt = file.read()

url = "https://docs.google.com/spreadsheets/d/1jBIFbMoAGu28sz2EXOkuGVQtgT8yY7l8GNJ3ZmctIYM/edit?gid=723640444#gid=723640444"
json_string = df_to_json(convert_google_sheet_url(url))

base_sys_prompt += f"\n---\n# 以下是這一季的服事表:{json_string}"


# Define the UTC offset for Taiwan (UTC+8)
taiwan_offset = timedelta(hours=8)
# Get the current UTC time
utc_now = datetime.utcnow()
# Convert UTC time to Taiwan time by adding the UTC offset
taiwan_now = utc_now.replace(tzinfo=timezone.utc).astimezone(timezone(taiwan_offset))

base_sys_prompt += f"\n---\n# 目前時間:{taiwan_now}"

# Calculate base system prompt tokens once
if "base_system_tokens" not in st.session_state:
    st.session_state.base_system_tokens = count_single_message_tokens(base_sys_prompt)
    st.session_state.service_schedule_tokens = count_single_message_tokens(json_string)

st.title("✝️ 教會AI助手 ")
st.warning("測試階段", icon="⚠️")

if st.button("慶祝！🥳"):
    st.balloons()

st.write("""
- 可詢問：
  - 教會公開資訊、週報消息(截至 2025/01/12)
  - 小組成長題目
  - 如何讀聖經
  - 2025 Q1 崇拜服事表
""")

# Add a checkbox to toggle the visibility of token metrics
show_token_metrics = st.checkbox("顯示 Token 使用情況", value=False)

# Create columns for metrics
if show_token_metrics:
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Token Usage")
        system_tokens_placeholder = st.empty()
        conversation_tokens_placeholder = st.empty()
        current_message_tokens_placeholder = st.empty()

    with col2:
        st.write("### API Call")
        total_tokens_placeholder = st.empty()
        response_tokens_placeholder = st.empty()

client = OpenAI(
    api_key="sk-c155cb6974f1429e879d54b117e3befb", base_url="https://api.deepseek.com"
)
model_name = "deepseek-chat"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": base_sys_prompt}]

# Display existing messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Calculate initial token counts
conversation_tokens = sum(
    count_single_message_tokens(msg["content"]) for msg in st.session_state.messages[1:]
)

# Update displays
if show_token_metrics:
    system_tokens_placeholder.metric(
        "System Prompt Tokens (Fixed)",
        st.session_state.base_system_tokens,
        help="This is counted only once and reused in each API call",
    )
    conversation_tokens_placeholder.metric(
        "Conversation History Tokens",
        conversation_tokens,
        help="Accumulated tokens from previous messages",
    )
    current_message_tokens_placeholder.metric(
        "Current Message Tokens", 0, help="Tokens in your new message"
    )
    total_tokens_placeholder.metric(
        "Total API Call Tokens",
        st.session_state.base_system_tokens + conversation_tokens,
        help="Total tokens being sent to API",
    )
    response_tokens_placeholder.metric(
        "Response Tokens", 0, help="Tokens in the assistant's response"
    )

if prompt := st.chat_input("平安！我能協助你什麼？"):
    current_system_tokens = st.session_state.base_system_tokens

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Calculate new token counts
    new_message_tokens = count_single_message_tokens(prompt)
    conversation_tokens = sum(
        count_single_message_tokens(msg["content"])
        for msg in st.session_state.messages[1:]
    )
    total_tokens = current_system_tokens + conversation_tokens

    # Update displays
    if show_token_metrics:
        system_tokens_placeholder.metric(
            "System Prompt Tokens (Fixed)",
            current_system_tokens,
            delta=None
            if current_system_tokens == st.session_state.base_system_tokens
            else f"+{st.session_state.service_schedule_tokens} (服事表)",
        )
        conversation_tokens_placeholder.metric(
            "Conversation History Tokens", conversation_tokens - new_message_tokens
        )
        current_message_tokens_placeholder.metric(
            "Current Message Tokens", new_message_tokens
        )
        total_tokens_placeholder.metric("Total API Call Tokens", total_tokens)

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

            # Update response tokens in real-time
            if show_token_metrics:
                response_tokens = count_single_message_tokens(msg)
                response_tokens_placeholder.metric("Response Tokens", response_tokens)

    st.session_state.messages.append({"role": "assistant", "content": msg})

import streamlit as st
from openai import OpenAI
import pandas as pd
import re


def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?"

    # Replace function to construct the new URL for CSV export
    # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
    replacement = (
        lambda m: f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?"
        + (f"gid={m.group(3)}&" if m.group(3) else "")
        + "format=csv"
    )

    # Replace using regex
    new_url = re.sub(pattern, replacement, url)

    return new_url


def df_to_json(csv_url):
    # Read the CSV from the URL into a DataFrame
    df = pd.read_csv(csv_url, header=1)
    df = df[df["季度"].isin(["Q1", "Q2", "Q3"])]

    # Convert the DataFrame to a JSON string
    # json_output = df.to_json(orient="records", indent=4, force_ascii=False)
    json_output = df.to_json(orient="records", force_ascii=False)  # compact

    return json_output


st.set_page_config(page_title="教會AI助手", page_icon="✝️")


# Read the system prompt from the external file
with open("sys_prompt_2.txt", "r", encoding="utf-8") as file:
    sys_prompt = file.read()


url = "https://docs.google.com/spreadsheets/d/1jBIFbMoAGu28sz2EXOkuGVQtgT8yY7l8GNJ3ZmctIYM/edit?gid=723640444#gid=723640444"
# df = pd.read_csv(convert_google_sheet_url(url), header=1)
json_string = df_to_json(convert_google_sheet_url(url))


sys_prompt += f"---# 以下是這一季的服事表:{json_string}"


# Show title and description.
st.title("✝️  教會AI助手 ")
st.warning("測試階段", icon="⚠️")

if st.button("慶祝！🥳"):
    st.balloons()


st.write("""
- 可以問教會資訊(資訊截至 2025/01/12)
- 可以產生小組成長題目
- 可以詢問如何讀聖經
- 可以詢問 2025 Q1 服事表(可能不準確)
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

import pandas as pd
import json
import re
from datetime import datetime, timezone, timedelta

def current_time(offset=8):
    # Define the UTC offset for Taiwan (UTC+8)
    taiwan_offset = timedelta(hours=offset)
    # Get the current UTC time
    utc_now = datetime.now(timezone.utc)

    # Convert UTC time to Taiwan time by adding the UTC offset
    taiwan_now = utc_now.replace(tzinfo=timezone.utc).astimezone(timezone(taiwan_offset))
    return taiwan_now



# Google Sheet
def format_export_url(match):
    """Formats a Google Sheets URL to export it as CSV."""
    return (
        f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?"
        + (f"gid={match.group(3)}&" if match.group(3) else "")
        + "format=csv"
    )


def convert_google_sheet_url(url):
    pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?"
    new_url = re.sub(pattern, format_export_url, url)
    return new_url


# DataFrame
def personal_json(melted_df):
    # Create a JSON string for each person
    result = {}
    for person, group in melted_df.groupby("姓名"):
        grouped = (
            group.groupby("服事")["日期"].apply(list).to_dict()
        )  # Group dates by service item
        result[person] = {"姓名": person}  # Add person's name
        result[person].update(grouped)  # Add service items and dates

    # Convert the result to JSON strings for each person
    json_strings = [
        json.dumps(details, ensure_ascii=False) for person, details in result.items()
    ]
    return json_strings


def process_multi_value(df):
    columns_to_split = ["聖餐人員", "招待同工"]
    for column in columns_to_split:
        # Split the column by '/' and expand into multiple columns
        split_columns = df[column].str.split("/", expand=True)

        # Remove any leading or trailing spaces from the new columns
        split_columns = split_columns.apply(lambda x: x.str.strip())

        # Rename the columns appropriately
        split_columns.columns = [
            f"{column}.{i+1}" for i in range(split_columns.shape[1])
        ]

        # Concatenate the new columns with the original DataFrame
        df = pd.concat([df, split_columns], axis=1)

        # Drop the original column if no longer needed
        df = df.drop(columns=[column])

    return df


def df_preprocess(df):
    df = df[df["季度"].isin(["Q1"])]
    df = df.iloc[:, 0:24]
    df = process_multi_value(df)
    columns_to_melt = [
        "會前禱告",
        "自由敬拜",
        "主席",
        "講員",
        "主領",
        "Vocal",
        "Vocal.1",
        "Vocal.2",
        "Vocal.3",
        "聖餐人員.1",
        "聖餐人員.2",
        "聖餐人員.3",
        "招待同工.1",
        "招待同工.2",
        "招待同工.3",
        "鋼琴",
        "KB",
        "EG",
        "AG",
        "Bass",
        "鼓",
        "調音",
        "PTT",
    ]

    melted_df = pd.melt(
        df,
        id_vars=["日期"],  # Keep the 日期 column as it is
        value_vars=columns_to_melt,  # Only melt specific columns
        var_name="服事",  # New column for service items
        value_name="姓名",  # New column for names
    ).dropna()  # Remove rows with NaN values

    personal_info = personal_json(melted_df)

    # --------------------- #

    # Merge columns with "Vocal" in their name, ignoring NaN values
    df["Vocal"] = df.filter(like="Vocal").apply(
        lambda row: " ".join(row.dropna().astype(str)), axis=1
    )

    # Drop the original columns (optional)
    df = df.drop(columns=df.filter(like="Vocal.").columns)
    # df.to_csv("tmp.csv")

    return df, personal_info


def df_to_json(csv_url):
    df = pd.read_csv(csv_url, header=1)
    df, personal_info = df_preprocess(df)
    json_output = df.to_json(orient="records", force_ascii=False)
    json_output = str(json_output).replace(
        "null", ""
    )  # Remove null string to save tokens
    json_output += str(personal_info)
    return json_output

import pandas as pd
import json
import re
from datetime import datetime, timezone, timedelta
import tiktoken


def token_estimate(text):
    # Select the encoding based on the model
    encoding = tiktoken.get_encoding("cl100k_base")  # Used for GPT-4, GPT-3.5-turbo
    tokens = encoding.encode(text)
    print("Number of tokens:", len(tokens))
    return tokens


def current_time(offset=8):
    # Define the UTC offset for Taiwan (UTC+8)
    taiwan_offset = timedelta(hours=offset)
    # Get the current UTC time
    utc_now = datetime.now(timezone.utc)

    # Convert UTC time to Taiwan time by adding the UTC offset
    taiwan_now = utc_now.replace(tzinfo=timezone.utc).astimezone(
        timezone(taiwan_offset)
    )
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
def personal_json_old(melted_df):
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


def df_preprocess_old(df, Q=1):
    df = df[df["季度"].isin([f"Q{Q}"])]
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

    return df, personal_info


#
# def df_to_json(csv_url):
#     df = pd.read_csv(csv_url, header=1)
#     df, personal_info = df_preprocess(df)
#     json_output = df.to_json(orient="records", force_ascii=False)
#     json_output = str(json_output).replace(
#         "null", ""
#     )  # Remove null string to save tokens
#     json_output += str(personal_info)
#     return json_output


# =========


def convert_gsheet_url(url):
    """Converts a Google Sheets URL to its CSV export format."""
    pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?"

    def format_export_url(match):
        return (
            f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?"
            + (f"gid={match.group(3)}&" if match.group(3) else "")
            + "format=csv"
        )

    csv_url = re.sub(pattern, format_export_url, url)

    return csv_url


def csv_to_df(csv_url):
    return pd.read_csv(csv_url, header=1)


def df_to_json(df):
    schema = {
        "columns": list(df.columns),
        "description": "This dataset contains tabular data with the specified columns.",
    }

    json_output = {
        "schema": schema,
        "data": json.loads(df.to_json(orient="records", force_ascii=False)),
    }

    return json.dumps(json_output, ensure_ascii=False)  # Keep Unicode characters


def dict_to_json(dict):
    schema = {
        "names": list(dict.keys()),
        "description": "This dataset contains tabular data with the specified columns.",
    }

    json_output = {
        "schema": schema,
        "data": dict,
    }

    return json.dumps(json_output, ensure_ascii=False)  # Keep Unicode characters


def split_multi_value(df, columns_to_split):
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


def merge_multi_value(df, columns_to_merge):
    for column in columns_to_merge:
        # Merge columns with "Vocal" in their name, ignoring NaN values
        df[column] = df.filter(like=column).apply(
            lambda row: " ".join(row.dropna().astype(str)), axis=1
        )
        # Drop the original columns (optional)
        df = df.drop(columns=df.filter(like=f"{column}.").columns)

    return df


def df_melt(df):
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

    # Remove the ".*"
    melted_df["服事"] = melted_df["服事"].str.replace(r"\..*", "", regex=True)

    return melted_df


def personalize(melted_df, person="all"):
    # Create a JSON string for each person
    person_dict = {}
    for name, group in melted_df.groupby("姓名"):
        if name and name != "暫停一次":
            grouped = (
                group.groupby("服事")["日期"].apply(list).to_dict()
            )  # Group dates by service item
            person_dict[name] = grouped  # Add service items and dates
    if person == "all":
        return person_dict
    else:
        return person_dict[person]


def df_preprocess(df, Q, level):
    df = df[df["季度"].isin([f"Q{Q}"])]
    df = df.iloc[:, 0:24]  # Columns Boundary

    if level == "service":
        # Merge multi-value columns for saving tokens
        df = merge_multi_value(df, ["Vocal", "聖餐人員", "招待同工"])
    elif level == "person":
        # Split to isolated columns, for personal
        df = split_multi_value(df, ["聖餐人員", "招待同工"])
        df = df_melt(df)

    else:
        raise

    return df


def process_service_roster(raw_url):
    print("=== Convert Google Sheet to Csv URL ===")
    csv_url = convert_gsheet_url(raw_url)
    df_raw = csv_to_df(csv_url)

    # Service Level
    print("=== Service ===")
    print("=== Convert Csv URL to DataFrame ===")

    print("=== DataFrame Preprocessing ===")
    df_service = df_preprocess(df_raw, Q=1, level="service")

    df_service.to_csv("service.csv", index=False)

    print("=== Convert DataFrame to JSON STring ===")
    json_service = df_to_json(df_service).replace("null", "")
    # token_estimate(json_service)

    # Person Level
    print("=== Person ===")
    df_person = df_preprocess(df_raw, Q=1, level="person")
    # df_person.to_csv("person.csv", index=False)

    person_dict = personalize(df_person, person="all")
    json_person = dict_to_json(person_dict)
    # token_estimate(json_person)

    return json_service, json_person

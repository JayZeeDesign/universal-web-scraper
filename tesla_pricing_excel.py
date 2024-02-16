# pylint: skip-file

import csv
import time

import webql
from webql.web import ChromePlaywrightWebDriver as PlaywrightWebDriver
from dotenv import load_dotenv

load_dotenv()

CSV_FILE = "tmp/tesla_pricing.csv"
CHAT_URL = "https://app.slack.com/client/T06J6D3BYDR/C06HZT327JS"

COUNTRIES = {
    "Canada": "https://www.tesla.com/en_CA/models/design#overview",
    "France": "https://www.tesla.com/fr_FR/models/design#overview",
    "Korea": "https://www.tesla.com/ko_KR/models/design#overview",
    "UAE": "https://www.tesla.com/ar_AE/models/design#overview",
}

MODEL_S_QUERY = """
{
    model_s {
        delivery
        model_s_price
        mode_s_plaid_price
    }
}
"""

driver = PlaywrightWebDriver(headless=False)
user_session_extras = {
    "user_data_dir": "/Users/jasonzhou/Library/Application Support/Google/Chrome/agent_profile"
}
session = webql.start_session("", user_session_extras, web_driver=driver)


def _save_json_as_csv(json_data, file_name):
    csv_header = ["Country", "Delivery Date", "Model S Price", "Mode S Plaid Price"]
    csv_data = [csv_header]
    for country, data in json_data.items():
        if not data:
            continue
        model_s_data = data.get("model_s", {})
        delivery_date = model_s_data.get("delivery", "")
        model_s_price = model_s_data.get("model_s_price", "")
        mode_s_plaid_price = model_s_data.get("mode_s_plaid_price", "")
        csv_data.append([country, delivery_date, model_s_price, mode_s_plaid_price])

    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)


def _highlight(response):
    try:
        driver.prepare_highlight()
        driver.highlight(response.model_s.delivery)
        driver.highlight(response.model_s.model_s_price)
        driver.highlight(response.model_s.mode_s_plaid_price)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error highlighting: {e}")


def extract_region_data(country: str, region_url: str):
    """Extract region data for a given country as json"""
    print(f"Extracting region data for {country}")
    try:
        driver.open_url(region_url)
        response = session.query(MODEL_S_QUERY, lazy_load_pages_count=0)
        _highlight(response)
        data = response.to_data()
        print(f"Tesla pricing data for {country}: {data}")
        return data
    except Exception as _:
        return None


def extract_tesla_pricing_data():
    """Extract Tesla pricing data and save as csv"""
    tesla_data = {}
    for country, url in COUNTRIES.items():
        tesla_data[country] = extract_region_data(country, url)

    _save_json_as_csv(tesla_data, CSV_FILE)


def upload_to_google_sheet():
    """Upload Tesla pricing data to Google Sheet"""
    try:
        with open(CSV_FILE) as file:
            csv_data = file.readlines()
        driver.open_url("https://docs.google.com/spreadsheets/u/0/create")
        time.sleep(1)
        driver.paste_via_clipboard("".join(csv_data))
        time.sleep(1)
        session.query("{paste_format_btn}").paste_format_btn.click()
        time.sleep(1)
        session.query(
            "{split_text_to_columns_menuitem}"
        ).split_text_to_columns_menuitem.click()
        time.sleep(1)
        session.query("{rename_input}").rename_input.fill("Tesla Pricing")
        driver.press_key("Enter")
        time.sleep(2)

        return driver.get_current_url()
    except Exception as e:
        print(f"Error: {e}")


def share_on_chat(url, message):
    """Share the url on chat"""
    driver.open_url(CHAT_URL)
    time.sleep(1)
    session.query("{message_textbox}").message_textbox.fill(message)
    driver.paste_via_clipboard(url)
    time.sleep(1)
    driver.press_key("Enter")
    try:
        session.query("{attach_button}").attach_button.click()
        attach_file = session.query(
            "{upload_from_your_computer}"
        ).upload_from_your_computer
        driver.upload_file(attach_file, CSV_FILE)
        time.sleep(5)
        driver.press_key("Enter")
    except Exception as e:
        print(f"Upload file error: {e}")


if __name__ == "__main__":
    extract_tesla_pricing_data()
    google_sheet_url = upload_to_google_sheet()
    share_on_chat(google_sheet_url, "Here is the Tesla pricing data: ")
    time.sleep(100)
    session.stop()

import webql
from webql.web import ChromePlaywrightWebDriver as PlaywrightWebDriver
from dotenv import load_dotenv
import csv
import time

load_dotenv()

url = "catch.com.au"
product = "coffee machine"
file_name = "data/catch_products.csv"


# Set up the Playwright web driver and start a new webQL session
driver = PlaywrightWebDriver(headless=False)
user_session_extras = {"user_data_dir": "tmp/playwright_chrome_user_data"}
session = webql.start_session(url, user_session_extras, web_driver=driver)


# Helper function to save JSON data as CSV
def _save_json_as_csv(json_data, file_name):
    csv_header = [
        "product_name",
        "product_price",
        "product_rating",
        "number_of_reviews",
    ]
    csv_data = [csv_header]
    products = json_data.get("results", {}).get("products", [])
    for product in products:
        print(product)
        product_name = product.get("product_name", "")
        product_price = product.get("product_price", "")
        product_rating = product.get("product_rating", "")
        number_of_reviews = product.get("number_of_reviews", "")
        csv_data.append(
            [product_name, product_price, product_rating, number_of_reviews]
        )

    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)


HOME_QUERY = """
{
    search_box
    search_btn
}
"""

SEARCH_QUERY = """
{
    results {
        products[] {
            product_name
            product_price
            product_rating
            number_of_reviews
        }
    }
}
"""

# Run query on home page & go to search result
home_page = session.query(HOME_QUERY)
home_page.search_box.fill(product)
home_page.search_btn.click(force=True)

time.sleep(2)

search_results = session.query(SEARCH_QUERY)
print(search_results)

_save_json_as_csv(search_results.to_data(), file_name)

session.stop()

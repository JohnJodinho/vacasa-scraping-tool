from flask import (
    Flask, 
    jsonify, 
    request, 
    render_template, 
    send_file, 
    abort, 
    send_from_directory, 
    current_app,
    g
)
from werkzeug.utils import secure_filename
import logging

from get_lat_lng import get_lat_long
import time
import json
import re
from get_address import get_address_from_coords
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from get_csv import save_to_csv
import os 
from os import path
from scrape_location import *
from get_all_locations import *
import sys
import threading
import time




app = Flask(__name__)

status = 0
LOCATION_NAME = ""
log_messages = []
scraping_thread = None
stop_scraping = threading.Event()  # Event to signal scraping stop

data_directory = "location_extracted_data"  # Folder to store data files
os.makedirs(data_directory, exist_ok=True)  # Ensure data directory exists
logging.basicConfig(
    filename="app.log",  # Log file in the root directory
    level=logging.DEBUG,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Log message format
)

# Add a StreamHandler to also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
app.logger.addHandler(console_handler)

def custom_print(message):
    """Log a message and make it available to the front-end."""
    log_messages.append(message)
    app.logger.info(message)  # For debugging and server-side logging

def set_scraping_url(new_url):
    global SCRAPING_URL
    SCRAPING_URL = new_url

# Search functionality
def search_sitemap(filename="sitemap_data.json"):
    with open(filename, "r") as f:
        data = json.load(f)

    while True:
        full_url = SCRAPING_URL
        if full_url:
            app.logger.info(f"You entered: {full_url}")
            custom_print(f"You entered: {full_url}")
            return full_url
        else:
            app.logger.warning("Nothing entered. Please try again.")
            custom_print("Nothing entered. Please try again.")
            
# Main Function
def main_runner():
    sitemap_url = "https://www.vacasa.com/sitemap-places.xml"
    try:
        custom_print("Fetching sitemap...")
        app.logger.info("Fetching sitemap...")
        root = fetch_and_parse_xml(sitemap_url)
        custom_print("Processing sitemap...")
        app.logger.info("Processing sitemap...")
        data = process_sitemap(root)
        save_to_json(data)
        custom_print("Starting search...")
        url = search_sitemap()
        return url
    except Exception as e:
        custom_print(f"Error: {e}")
        app.logger.error(f"Error: {e}")
        sys.exit(1)



def return_property_url():
    global LOCATION_NAME
    url = main_runner()
    if url.startswith("https://www.vacasa.com"):
        for part in url.split("https://www.vacasa.com")[-1].split("/"):
            if part:
                part += "_"
                LOCATION_NAME = part
        return url
    elif url.startswith("/"):
        for part in url.split("/"):
            if part:
                part += "_"
                LOCATION_NAME = part
        return "https://www.vacasa.com/search?place=" + url
    


def extract_unit_ids(max_retries=6):
    url = return_property_url()
    unit_ids = []

    retry_count = 0
    backoff = 1  # Start with 1 second

    while retry_count < max_retries:
        try:
            with sync_playwright() as p:
                # Launch the browser
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                # Navigate to the URL
                custom_print(f"Attempting to navigate to {url}, try {retry_count + 1}")
                app.logger.info(f"Attempting to navigate to {url}, try {retry_count + 1}")
                page.goto(url, timeout=80000, wait_until="domcontentloaded")

                # Wait for the button to appear
                page.wait_for_selector('button.page-link.px-4.text-capitalize', timeout=60000)

                # Get the page content
                content = page.content()

                # Close the browser
                browser.close()
            break

        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                custom_print("Max retries reached. Exiting.")
                app.logger.error("Max retries reached. Exiting.")
                sys.exit(1)
            else:
                wait_time = backoff ** retry_count  # Exponential backoff
                custom_print(f"Retrying in {wait_time} seconds...")
                app.logger.warning(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    # Parse with Beautiful Soup
    soup = BeautifulSoup(content, 'html.parser')

    # Find script tags with type "text/javascript"
    script_tags = soup.find_all("script", {"type": "text/javascript"})

    # Extract "unit_ids" from script tags
    if script_tags:
        # print(f"Found {len(script_tags)} script tags.")
        for script_tag in script_tags:
            script_content = script_tag.string
            if script_content:  # Ensure the script has content
                # Use regex to match 'SearchResults' and extract 'unit_ids'
                search_results_match = re.search(
                    r'SearchResults:\s*\{[^}]*"unit_ids":\s*(\[[^\]]+\])', script_content
                )

                if search_results_match:
                    unit_ids_json = search_results_match.group(1)
                    unit_ids = json.loads(unit_ids_json)  # Convert JSON array to Python list
                    custom_print(f"Number of Unit IDs/properties to scrape: {len(unit_ids)}")
                    app.logger.info(f"Number of Unit IDs/properties to scrape: {len(unit_ids)}")
                    break
        else:
            custom_print("No unit IDs/properties found in location page.")
            app.logger.warning("No unit IDs/properties found in location page.")

    return unit_ids



def get_location_name():
    return LOCATION_NAME

def process_data():
    """Handles the main data processing logic."""
    global status
    all_data = []

    vacasa_unitIds = extract_unit_ids()
    custom_print(f"Extracted unit ids...{vacasa_unitIds}")
    app.logger.info(f"Extracted unit ids...{vacasa_unitIds}")
    name = get_location_name()
    # custom_print(f"Location name: {name}")
    all_lats_and_longs = get_lat_long(unit_ids_list=vacasa_unitIds)
    # custom_print(f"Extracted latitudes and longitudes...{all_lats_and_longs}")
    # json_file_name = f"location_extracted_data/{location_name}_properties.json"
    os.makedirs("location_extracted_data", exist_ok=True)
    # Load existing data if available
    try:
        with open(f"location_extracted_data/{name}_properties.json", "r") as f:
            all_data = json.load(f)
    except FileNotFoundError:
        pass
    state = 0
    for id_ in vacasa_unitIds:
        state += 1
        is_new = True
        if all_data:
            for dt in all_data:
                if dt["VACASA_LINK"] == f"https://www.vacasa.com/unit/{id_}":
                    is_new = False
        if is_new:
            try:
                status = int((vacasa_unitIds.index(id_)+1)/len(vacasa_unitIds)*100)
                lat, lng = get_coordinates(id_, all_lats_and_longs)
                extract_property_data(id_, lat, lng, name)
                custom_print(f"Extracted data from property with id {id_} in {name} ({state}/{len(vacasa_unitIds)})...")
                app.logger.info(f"Extracted data from property with id {id_} in {name} ({state}/{len(vacasa_unitIds)})...")
            except Exception as e:
                custom_print(f"Error extracting data from property with id {id_}: {e}")
                app.logger.error(f"Error extracting data from property with id {id_}: {e}")
                continue

    custom_print(f"Data extraction for {name} completed.")
    app.logger.info(f"Data extraction for {name} completed.")
    # custom_print("Saving to CSV...")
    # app.logger.info("Saving to CSV...")
    save_to_csv(name)
    custom_print("Scraping completed!")
    app.logger.info("Scraping completed!")

    custom_print("Downloading...")
    # Clean up temporary JSON file
    # file_path = f"{name}_properties.json"
    # custom_print("Cleaning up...")
    # app.logger.info("Cleaning up...")
    # if os.path.exists(file_path):
    #     os.remove(file_path)
    #     custom_print("Done!")
    #     app.logger.info("Done!")
    # else:
    #     custom_print("No temporary file to clean up.")
    #     app.logger.warning("No temporary file to clean up.")


@app.route('/')
def home():
    """Renders the main scraping tool UI and stops any ongoing scraping."""
    global log_messages, scraping_thread, stop_scraping

    # Signal the thread to stop and wait for it to finish
    if scraping_thread and scraping_thread.is_alive():
        stop_scraping.set()  # Signal the thread to stop
        scraping_thread.join()  # Wait for the thread to finish

    # Clear logs and files
    try:
        log_messages.clear()
        all_files = os.listdir("location_extracted_data")
        for file in all_files:
            file_path = os.path.join("location_extracted_data", file)
            os.remove(file_path)
    except Exception as e:
        print(f"Error during cleanup: {e}")

    # Reset the stop flag for future scraping
    stop_scraping.clear()

    return render_template('index.html')


@app.route('/start-scraping', methods=['POST'])
def start_scraping():
    """
    API endpoint to trigger the scraping process.
    Expects JSON data with a URL or location name.
    """
    global log_messages, scraping_thread, stop_scraping

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Invalid request. URL is required."}), 400

    url = data['url']

    # Start a new scraping thread
    if scraping_thread and scraping_thread.is_alive():
        return jsonify({"error": "Scraping is already in progress."}), 400

    def scraping_task():
        global log_messages
        try:
            log_messages.clear()
            all_files = os.listdir("location_extracted_data")
            if len(all_files) != 0:
                for file in all_files:
                    file_path = os.path.join("location_extracted_data", file)
                    os.remove(file_path)
        except Exception as e:
            print(f"Error: {e}")

        # Simulate scraping process
        try:
            process_data()
            return jsonify({"message": "Scraping completed successfully."}), 200
        except Exception as e:
            print(f"Error during scraping: {e}")
            return jsonify({"error": f"An error occurred during scraping:{e}"}), 500

    scraping_thread = threading.Thread(target=scraping_task)
    scraping_thread.start()

    return jsonify({"message": "Scraping started."}), 200

@app.route('/start-scraping', methods=['POST'])
def start_scraping():
    """
    API endpoint to trigger the scraping process.
    Expects JSON data with a URL or location name.
    """
    global log_messages
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Invalid request. URL is required."}), 400

    try:
        log_messages.clear()
        all_files = os.listdir("location_extracted_data")
        if len(all_files) != 0:
            for file in all_files:
                file_path = os.path.join("location_extracted_data", file)
                os.remove(file_path)
    except Exception as e:
        print(f"Error: {e}")

    # Simulate scraping process
    try:
        process_data()
        return jsonify({"message": "Scraping completed successfully."}), 200
    except Exception as e:
        print(f"Error during scraping: {e}")
        return jsonify({"error": f"An error occurred during scraping:{e}"}), 500

@app.route('/check_status', methods=['GET'])
def check_status():
    """
    API endpoint to check the status of the scraping process.
    """
    # print(f"Current status: {status}")
    return jsonify({"status": status}), 200

@app.route('/set_scraping_url', methods=['POST'])
def handle_set_scraping_url():
    """
    API endpoint to receive and update the scraping URL.
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"success": False, "error": "Invalid request. URL not provided."}), 400

    url = data['url']
    # Call the custom function to update the global variable
    set_scraping_url(url)

    return jsonify({"success": True, "message": "URL has been set successfully."}), 200

@app.route('/get-logs', methods=['GET'])
def get_logs():
    """Provide the current log messages to the front-end."""
    global log_messages
    return jsonify(log_messages)

@app.route('/download-file/<file_type>', methods=['GET'])
def download_file(file_type):
    """
    Endpoint to download JSON or CSV file.
    :param file_type: 'json' or 'csv'
    """
    try:
        if file_type not in ['json', 'csv']:
            return jsonify({"error": "Invalid file type requested."}), 400

        # Find the relevant file in the data directory
        file_extension = f".{file_type}"
        for file_name in os.listdir(data_directory):
            if file_name.endswith(file_extension):
                return send_from_directory(data_directory, file_name, as_attachment=True)

        return jsonify({"error": f"No {file_type} file found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = 8080
    app.run(debug=True)

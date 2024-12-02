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

import time
import json
import re
from get_address import get_address_from_coords
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from get_csv import save_to_csv
import os 
from os import path


import sys
import threading
import time
import gzip
import zlib

import requests
from flags import stop_scraping




app = Flask(__name__)

status = 0
LOCATION_NAME = ""
log_messages = []
scraping_thread = None
SCRAPING_URL = ""
can_delete = False


data_directory = "location_extracted_data"  # Folder to store data files
os.makedirs(data_directory, exist_ok=True)  # Ensure data directory exists
logging.basicConfig(
    filename="app.log",  # Log file in the root directory
    level=logging.DEBUG,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Log message format
)

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
    

def delete_location_files():
    """
    Deletes JSON and CSV files in the 'location_extracted_data' folder 
    that contain the specified location_name in their filenames.

    Parameters:
        location_name (str): The name of the location to match in filenames.

    If no matching files are found, it does nothing.
    """
    folder_path = "location_extracted_data"
    try:
        # List all files in the folder
        all_files = os.listdir(folder_path)
        
        # # Identify files matching the pattern
        # files_to_delete = [
        #     file for file in all_files
        #     if f"{location_name}_properties.json" == file or f"{location_name}_properties.csv" == file
        # ]
        
        # Delete matching files
        for file in all_files:
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)
            print(f"Deleted: {file_path}")
    except Exception as e:
        print(f"Error during file deletion: {e}")


# Main Function
def main_runner():
    sitemap_url = "https://www.vacasa.com/sitemap-places.xml"
    try:

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

def split_unitids_list(input_list):
    """
    Splits the input list into sublists of up to 24 items each.
    
    Args:
        input_list (list): The list to be split.
    
    Returns:
        dict: A dictionary containing the total number of items and the sublists.
    """
    # Check the length of the input list
    num_unit_ids = len(input_list)
    
    # If the list has less than 24 items, return it as is
    if num_unit_ids <= 24:
        return {
            "numUnitIDs": num_unit_ids,
            "spittedUnitIDs": [input_list]
        }
    
    # Split the list into sublists of 24 items
    spitted_unit_ids = [input_list[i:i + 24] for i in range(0, num_unit_ids, 24)]
    
    # Return the result as a dictionary
    return {
        "numUnitIDs": num_unit_ids,
        "spittedUnitIDs": spitted_unit_ids
    }


def extract_csrftoken_from_url(url, max_retries=5):
    """
    Extracts the 'csrftoken' from the cookies of a given URL.

    Args:
        url (str): The URL to send the request to.

    Returns:
        str: The csrftoken if found, else None.
    """
    for _ in range(max_retries):
        try:
            # Initialize a session to persist cookies
            with requests.Session() as session:
                # Make a GET request to the URL
                response = session.get(url, timeout=10)  # Set a timeout for the request
                
                # Check if the request was successful
                response.raise_for_status()

                # Extract the 'csrftoken' from the cookies
                csrftoken = session.cookies.get("csrftoken")
                
                if csrftoken:
                    print(f"Extracted csrftoken: {csrftoken}")
                    return csrftoken
                else:
                    print("csrftoken not found in cookies.")
                    
        except requests.exceptions.Timeout:
            print(f"Request to {url} timed out.")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request failed: {req_err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    return None






def fetch_vacasa_data(payload, csrftoken, x_csrftoken, referer):
    """
    Fetches JSON data from Vacasa API with retries and exponential backoff.

    Args:
        payload (dict): The payload to send in the POST request.

    Returns:
        dict or None: The JSON response as a dictionary, or None if the request fails.
    """
    url = "https://www.vacasa.com/api/unit-api/paging"
    headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "content-length": "350",
    "content-type": "application/json",
    "cookie": f"csrftoken={csrftoken};", #ajs_anonymous_id=ab86c1fb-fc0b-41e3-a428-8d9a8f086cb9; optimizelyEndUserId=oeu1731104797792r0.952189376908009; _gcl_au=1.1.999204061.1731104806; _ga=GA1.1.532686323.1731104811; _fbp=fb.1.1731104820827.518358646939556170; hubspotutk=4c2384586a22f30990c40966bebdec43; _hjSessionUser_169794=eyJpZCI6IjFmYjc4ZWVlLWU1YTAtNWVjMy04NDI1LTYwZmNkZTc3YjI0MiIsImNyZWF0ZWQiOjE3MzExMDQ4MTcyODAsImV4aXN0aW5nIjp0cnVlfQ==; ndp_session_id=3090a2f8-08eb-40bf-9bb8-1a62ffe8858d; tracker_device_is_opt_in=true; tracker_device=7816f9ee-76c8-4521-bc10-e6da6e795322; sessionid=ecbc9xqvc8lfplrz3rr6k8ibqj7jxrv1; OptanonConsent=isGpcEnabled=0&datestamp=Sun+Dec+01+2024+14%3A42%3A08+GMT%2B0100+(West+Africa+Standard+Time)&version=202407.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0004%3A1&AwaitingReconsent=false; _uetsid=12e0d390afea11efac2dc72955690c40; _uetvid=8e25e2109e2011ef92a9755b2bea4b11; _hjSession_169794=eyJpZCI6ImRjMzUyYTgzLTg5YmYtNDIzMC1hN2UxLTllNDU4YTA5NGFiMiIsImMiOjE3MzMwNjA1MzQ5NzcsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MX0=; __hstc=93626498.4c2384586a22f30990c40966bebdec43.1731104860062.1732965532856.1733060543191.28; __hssrc=1; __hssc=93626498.1.1733060543191; _ga_4JGS42DXPK=GS1.1.1733060527.35.1.1733061106.0.0.0; _ga_SZKD9D5EPS=GS1.1.1733060527.35.1.1733061106.33.0.0; _dd_s=rum=0&expire=1733062011478",
    "origin": "https://www.vacasa.com",
    "priority": "u=1, i",
    "referer": referer,
    "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-csrftoken": x_csrftoken,
    "x-requested-with": "XMLHttpRequest",
    }
    
    max_retries = 5
    backoff_factor = 1

    def decode_response(content, encoding):
        # if encoding == "gzip":
        #     return gzip.decompress(content)
        # elif encoding == "deflate":
        #     return zlib.decompress(content)
        # elif encoding == "br":
        #     return brotli.decompress(content)
        # elif encoding == "zstd":
        #     dctx = zstandard.ZstdDecompressor()
        #     return dctx.decompress(content)
        return content

    for attempt in range(max_retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                print("didn't get here")
                response = page.request.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload)
                )
                print(response)
                if response.ok:
                    encoding = response.headers.get("content-encoding", "").lower()
                    raw_content = response.body()
                    decoded_content = decode_response(raw_content, encoding)
                    return json.loads(decoded_content.decode('utf-8'))
        except Exception as e:
            
            time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff
            custom_print(f"Attempt {attempt + 1} failed: {e}")
        finally:
            try:
                if 'browser' in locals() and browser.is_connected():
                    browser.close()
            except Exception as close_error:
                print(f"Error during browser cleanup: {close_error}")

    return None

def construct_payload(page_num, total_units, unit_ids, slug, place, display_featured=False):
    return {
        "page_num": page_num,
        "total_units": total_units,
        "unit_ids": unit_ids,
        "slug": slug,
        "display_featured": display_featured,
        "place": place
    }




def process_pages(unit_ids):
    """
    Processes the pages of Vacasa data and extracts the unit IDs.

    Returns:
        list: A list of unit IDs extracted from the Vacasa data.
    """
    split_data = split_unitids_list(unit_ids)
    csrftoken = extract_csrftoken_from_url(SCRAPING_URL)
    if csrftoken is None:
        csrftoken = "0G7mL6lmfaiJeocrBesKNJ3Gh7qToIIfHd1xq6n2DnKIY2VeR4Ysd7KDkkrBWX8q"
    
    total_units = split_data["numUnitIDs"]
    slug = SCRAPING_URL.split("=")[-1]
    place = SCRAPING_URL.split("=")[-1]
    pages_ids = split_data["spittedUnitIDs"]
    all_responses = []
    for ids in pages_ids:
        page_num = pages_ids.index(ids)
        payload = construct_payload(page_num, total_units, ids, slug, place)
        if page_num == 0:
            reference = SCRAPING_URL
        else:
            reference  = f"https://www.vacasa.com/search?page={page_num}&place={slug}"
            
        response = fetch_vacasa_data(payload, csrftoken, csrftoken, reference)
        if response is not None:
            custom_print(f"Fetched data for page {page_num}.")
            all_responses.append(response)
        else:
            custom_print(f"Failed to fetch data for page {page_num}.")
    return all_responses
    
        


def extract_property_data(the_unit, location_name):
    property_data = {
        "UNIT ID": the_unit["unit_id"],
        "VACASA_LINK": the_unit["attributes"]["url"],
        "PROPERTY_NAME": f'{the_unit["attributes"]["name"]}- {the_unit["attributes"]["city_name"]}',
        "RATING": the_unit["attributes"]["review"]["avg_score"],
        "MAX OCCUPANCY": the_unit["attributes"]["max_occupancy"],
        "REVIEWS": the_unit["attributes"]["review"]["count"],
        "BEDROOMS": the_unit["attributes"]["bedrooms"],
        "BATHS": the_unit["attributes"]["bathrooms"]["total"],
        "PRICING": the_unit["attributes"]["price_display"],
        "ADDRESS": None
    }
    lat = the_unit["attributes"]["lat"]
    lng = the_unit["attributes"]["lng"]   
    if lat and lng:
        address = get_address_from_coords(lat, lng)
        
        property_data["ADDRESS"] = address

       
    # Load existing properties from the JSON file
    try:
        with open(f"location_extracted_data/{location_name}_properties.json", "r") as f:
            properties = json.load(f)
    except FileNotFoundError:
        properties = []

    # Append the current property data to the list
    properties.append(property_data)

    # Save the updated list of properties to the JSON file
    with open(f"location_extracted_data/{location_name}_properties.json", "w") as f:
        json.dump(properties, f, indent=4)



def process_data():
    """Handles the main data processing logic."""
    global status, can_delete
    print("Not here")
    all_data = []
    vacasa_unitIds = extract_unit_ids()
    pages_data = process_pages(vacasa_unitIds)
    # custom_print(f"Extracted unit ids...{vacasa_unitIds}")
    app.logger.info(f"Extracted unit ids...{vacasa_unitIds}")
    name = get_location_name()
    # custom_print(f"Location name: {name}")
    
    os.makedirs("location_extracted_data", exist_ok=True)
    # Load existing data if available
    try:
        with open(f"location_extracted_data/{name}_properties.json", "r") as f:
            all_data = json.load(f)
    except FileNotFoundError:
        pass

    if all_data:
        state = len(all_data)
    else:
        state = 0
    for data in pages_data:
        for unit in data["units"]:
            is_new = True
            if all_data:
                for dt in all_data:
                    if dt["VACASA_LINK"] == f'https://www.vacasa.com/unit/{unit["unit_id"]}':
                        is_new = False
            if is_new:
                try:
                    if stop_scraping.is_set():
                        custom_print("Scraping stopped during process!")
                        return  # Exit the task
                    
                    extract_property_data(unit, name)
                    state += 1
                    status = int(state/len(vacasa_unitIds)*100)
                    custom_print("Extracted data!")
                    custom_print(f'From property with id: {unit["unit_id"]} in {name} ({state}/{len(vacasa_unitIds)})...')
                    app.logger.info(f'Extracted data from property with id {unit["unit_id"]} in {name} ({state}/{len(vacasa_unitIds)})...')
                    if state == len(vacasa_unitIds):
                        can_delete = True
                except Exception as e:
                    custom_print(f'Error extracting data from property with id {unit["unit_id"]}: {e}')
                    app.logger.error(f'Error extracting data from property with id {unit["unit_id"]}: {e}')
                    continue

    custom_print(f"Data extraction for {name} completed.")
    app.logger.info(f"Data extraction for {name} completed.")
    # custom_print("Saving to CSV...")
    # app.logger.info("Saving to CSV...")
    save_to_csv(name)
    custom_print("Scraping completed!")
    app.logger.info("Scraping completed!")

    custom_print("Downloading...")
    can_delete = True
   

@app.route('/')
def home():
    """Renders the main scraping tool UI and stops any ongoing scraping."""
    global log_messages, scraping_thread

    # Signal the thread to stop and wait for it to finish
    if scraping_thread and scraping_thread.is_alive():
        stop_scraping.set()  # Signal the thread to stop
        scraping_thread = None

    # Clear logs and files
    loc_name = get_location_name()
    delete_location_files()
    try:
        log_messages.clear()
    except Exception as e:
        print(f"Error during cleanup: {e}")

    # Reset the stop flag for future scraping
    stop_scraping.clear()

    return render_template('index.html')
    

def scraping_task():
    global log_messages
    with app.app_context():
        loc_name = get_location_name()
        
        delete_location_files()
        try:
            log_messages.clear()
        except Exception as e:
            print(f"Error during cleanup: {e}")

        try:
            custom_print("Starting scraping...")
            process_data()
           
            return jsonify({"message": "Scraping completed successfully."}), 200
        except Exception as e:
            print(f"Error during scraping: {e}")
            return jsonify({"error": f"An error occurred during scraping: {e}"}), 500


@app.route('/start-scraping', methods=['POST'])
def start_scraping():
    """
    API endpoint to trigger the scraping process.
    Expects JSON data with a URL or location name.
    """
    global log_messages, scraping_thread

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Invalid request. URL is required."}), 400

    url = data['url']
    print(f"Starting scraping for URL: {url}")

    set_scraping_url(url)
    # Start a new scraping thread
    if scraping_thread and scraping_thread.is_alive():
        return jsonify({"error": "Scraping is already in progress."}), 400


    stop_scraping.clear()  # Ensure the flag is reset
    scraping_thread = threading.Thread(target=scraping_task)
    scraping_thread.start()

    return jsonify({"message": "Scraping started."}), 200

# @app.route('/stop-scraping', methods=['POST'])
# def stop_prompt_scraping():
#     """
#     API endpoint to stop the scraping process immediately
#     and redirect to the homepage.
#     """
#     global log_messages, scraping_thread

#     # Signal the thread to stop and wait for it to finish
#     if scraping_thread and scraping_thread.is_alive():
#         stop_scraping.set()  # Signal the thread to stop
        

#     try:
#          save_to_csv()

#     except Exception as e:
#         pass

#     # Reset the stop flag for future scraping
#     stop_scraping.clear()

#     return jsonify({"message": "Scraping stopped immediately."}), 200



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
        the_location = get_location_name()
        if the_location:
            file_extension = f".{file_type}"
            for file_name in os.listdir(data_directory):
                if file_name.endswith(file_extension) and file_name.find(the_location) != -1:
                    return send_from_directory(
                        data_directory,
                        file_name,
                        as_attachment=True,
                        download_name=file_name  # Specify the filename for the response
                    )

        return jsonify({"error": f"No {the_location} as {file_type} file found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = 8080
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

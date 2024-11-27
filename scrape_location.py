from get_lat_lng import get_lat_long
from app import extract_unit_ids, get_location_name
import time
import json
import re
from get_address import get_address_from_coords
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from get_csv import save_to_csv
import os 
from os import path
from flags import stop_scraping



def get_coordinates(check_id, all_lat_long):
    for item in all_lat_long:
        if stop_scraping.is_set():
            print("Scraping stopped during process!")
            return  # Exit the task
        if item["unit_id"] == check_id:

            return item["lat"], item["lng"]
    return (None, None)  # If no matching id is found

# Function to extract bedrooms and baths from the HTML
def extract_bedrooms_baths(soup):
    main_div = soup.find("div", class_="row d-flex flex-wrap justify-content-start")
    if not main_div:
        print("No bathroom and Bedroom data here")
        return None, None  # Return None if the main div is not found
    
    bedroom, bath = None, None
    
    for feature in main_div.find_all("span", class_="core-feature"):
        text = feature.get_text(strip=True).lower()
        if stop_scraping.is_set():
                    print("Scraping stopped during process!")
                    return  # Exit the task
        try:
            if 'bedroom' in text:
                bedroom = float(text.strip().split()[0])
                # print(f"Bedrooms: {bedroom}")
            elif 'bath' in text:
                bath = float(text.strip().split()[0])
                # print(f"Baths: {bath}")
        except ValueError as e:
            print(f"Error parsing bedroom or bath number: {e}")
        
        if bedroom is not None and bath is not None:
            break
    
    return bedroom, bath


def extract_property_data(unit_id, lat, lng, location_name):
    property_data = {
        "VACASA_LINK": f"https://www.vacasa.com/unit/{unit_id}",
        "PROPERTY_NAME": None,
        "REVIEWS": None,
        "RATINGS": None,
        "BEDROOMS": None,
        "BATHS": None,
        "BEDS": None,
        "PRICING": None,
        "AMENITIES": None,
        "ADDRESS": None
    }
    backoff = 1
    with sync_playwright() as p:
        while True:
            try:
                url = f"https://www.vacasa.com/unit/{unit_id}"
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=80000, wait_until="domcontentloaded")
                time.sleep(2)
                if stop_scraping.is_set():
                    print("Scraping stopped during process!")
                    return  # Exit the task
                # page.wait_for_load_state("load", timeout=60000)
                # Extract property name
                page.wait_for_selector("h3.unit-rate", timeout=60000)
                # Wait for specific selectors
                page.wait_for_selector('i.icon-shower.core-feature-icon', timeout=60000)
                page.wait_for_selector('div.d-flex.mb-1 img.bedroom-icon-size.mr-2', timeout=60000)
                page.wait_for_selector('div.d-flex.mb-1 p.description.m-0', timeout=60000)
                break
            except Exception as e:
                print(f"Failed to load page: {e}")
                backoff *= 2
                if backoff > 128:
                    break
                continue
                browser.close()
        
        if lat and lng:
            address = get_address_from_coords(lat, lng)
            if isinstance(address, dict):
                return address
            property_data["ADDRESS"] = address

        # Extract reviews and ratings
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        property_data["PROPERTY_NAME"] = soup.title.string.split("|")[0].strip()
    
        # Reviews
        reviews = soup.select_one("h2.type-heading-medium.align-middle.mx-8.mb-0")
        property_data["REVIEWS"] = int(reviews.text.strip().split()[0]) if reviews else 0
        
        # Ratings
        ratings = soup.select_one("span.avg_score.pl-2")
        property_data["RATINGS"] = float(ratings.text.strip()) if ratings else 0.0
        
       
        total_beds = 0

        # Find all bed description paragraphs within each bedroom box
        bedroom_boxes = soup.find_all("div", id="bed-room-box")
        for bedroom in bedroom_boxes:
            bed_descriptions = bedroom.find_all("p", class_="description m-0")
            for bed in bed_descriptions:
                # Extract the quantity of beds from the text (e.g., "1 king bed" or "2 twin bunk beds")
                match = re.search(r'(\d+)', bed.get_text())
                if match:
                    total_beds += float(match.group(1))  # Add the number of beds found
                    property_data["BEDS"] = total_beds
                # Find all spans with class "core-feature"
        bedroom, bath = extract_bedrooms_baths(soup)
        property_data["BEDROOMS"] = bedroom
        property_data["BATHS"] = bath
        
        # Pricing
        pricing = soup.select_one("h3.unit-rate")
        
        property_data["PRICING"] = (
            float(pricing.text.strip().replace("$", "").replace(",", "")) if pricing else 0
        )
        
        # Amenities
        amenities = soup.select("div.row.featured-amenities.py-3 h3.featured-amenity")
        property_data["AMENITIES"] = ", ".join(a.text.strip() for a in amenities)

        browser.close()

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

    return property_data

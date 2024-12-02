
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import random

import json
from geopy.geocoders import AzureMaps
import os
from dotenv import load_dotenv


USER_AGENTS_AZ = [
    "azuremapsExercis_1", "azuremapsExercis_2", "azuremapsExercis_3", 
    "azuremapsExercis_4", "azuremapsExercis_5", "azuremapsExercis_6",
    "azuremapsExercis_7", "azuremapsExercis_8", "azuremapsExercis_9",
    "azuremapsExercis_10",
]

# List of user agents to randomize requests
USER_AGENTS = [
    "geoapiExercis_1",
    "geoapiExercis_2",
    "geoapiExercis_3",
    "geoapiExercis_4",
    "geoapiExercis_5",
    "geoapiExercis_6",
    "geoapiExercis_7",
    "geoapiExercis_8",
    "geoapiExercis_9",
    "geoapiExercis_10",
]

# Load environment variables from .env file
load_dotenv()

# def get_address_from_coords(latitude, longitude, language="en"):
#     # Randomly select a user agent for each request
#     user_agent = random.choice(USER_AGENTS)
    
    
#     while True:
#         try:
#             if stop_scraping.is_set():
#                 print("Scraping stopped during process!")
#                 return  # Exit the task
#             # Try to get the geocode data
#             geolocator = Nominatim(user_agent=user_agent)
#             # Set up a rate limiter to ensure requests are spaced out
#             geocode = RateLimiter(geolocator.reverse, min_delay_seconds=2)
            
#             # Default values
#             max_retries = 10
#             base_delay = 2  # Initial delay in seconds
#             attempt = 0
#             default_value = ""

#             data = geocode((latitude, longitude), language=language).raw

#             # Safely extract each required field
#             house_number = data.get('address', {}).get('house_number', default_value)
#             road = data.get('address', {}).get('road', default_value)
#             hamlet = data.get('address', {}).get('hamlet', default_value)
#             city = data.get('address', {}).get('city', default_value)
#             state = data.get('address', {}).get('state', default_value)
#             zipcode = data.get('address', {}).get('postcode', default_value)

#             # Combine non-empty fields into a formatted address string
#             address_parts = [house_number, road, hamlet, city, state, zipcode]
#             address = ", ".join(part for part in address_parts if part)
#             return address
        
#         except Exception as e:
#             attempt += 1
#             if attempt > max_retries:
#                 raise RuntimeError(f"Failed to get address after {max_retries} retries: {e}")
#             delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
#             print(f"Attempt {attempt} with user agent '{user_agent}' failed. Retrying in {delay} seconds...")
#             time.sleep(delay)
#             # Optionally pick a new user agent for the next attempt
#             user_agent = random.choice(USER_AGENTS)
#             geolocator = Nominatim(user_agent=user_agent)




def get_address_from_coords(latitude, longitude, language="en"):
    """
    Reverse geocodes coordinates into an address using Azure Maps.
    
    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        subscription_key (str): Azure Maps subscription key.
        language (str): Language in which the address should be returned (default: "en").
    
    Returns:
        str: Formatted address or an empty string if no address is found.
    """

    # Access the subscription key
    subscription_key = os.getenv("SUBSCRIPTION_KEY")
    # Randomly select a user agent for each request
    user_agent = random.choice(USER_AGENTS_AZ)
    
    # Initialize Azure Maps geolocator
    geolocator = AzureMaps(subscription_key=subscription_key, user_agent=user_agent)
    geocode = RateLimiter(geolocator.reverse, min_delay_seconds=2)

    # Default values
    max_retries = 10
    base_delay = 2  # Initial delay in seconds
    attempt = 0
    default_value = ""

    while True:
        
        try:
            # Reverse geocode
            location = geocode((latitude, longitude), language=language).raw
            
            # Safely extract address components
            address_info = location.get('address', {})
            street_number = address_info.get('streetNumber', default_value)
            street_name = address_info.get('streetName', default_value)
            municipality = address_info.get('municipality', default_value)
            region = address_info.get('countrySubdivisionName', default_value)
            postal_code = address_info.get('postalCode', default_value)
            country = address_info.get('country', default_value)

            # Combine non-empty fields into a formatted address string
            address_parts = [
                street_number, street_name, municipality, 
                region, postal_code, country
            ]
            address = ", ".join(part for part in address_parts if part)
            return address
        
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                print(f"Error: Failed to get address after {max_retries} retries. {e}")
                return None

            delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
            print(f"Attempt {attempt} failed with user agent '{user_agent}'. Retrying in {delay} seconds...")
            time.sleep(delay)
            
            # Optionally change user agent on retry
            user_agent = random.choice(USER_AGENTS)
            geolocator = AzureMaps(subscription_key=subscription_key, user_agent=user_agent)
            geocode = RateLimiter(geolocator.reverse, min_delay_seconds=2)




def process_properties(file_path):
    """
    Process a JSON file to retrieve addresses for each property using Azure Maps.

    Args:
        file_path (str): Path to the JSON file containing property data.
        subscription_key (str): Azure Maps subscription key.
    """
    # Load the JSON data
    with open(file_path, 'r') as file:
        properties = json.load(file)

    # Loop through each property and process it
    for property_data in properties:
        unit_id = property_data.get("unit_id")
        latitude = property_data.get("lat")
        longitude = property_data.get("lng")

        # Skip if latitude or longitude is missing
        if latitude is None or longitude is None:
            print(f"Skipping unit ID {unit_id}: Missing coordinates.")
            continue

        # Retrieve address
        try:
            address = get_address_from_coords(latitude, longitude)
            if address:
                print(f"Unit ID: {unit_id}\nAddress: {address}\n")
            else:
                print(f"Unit ID: {unit_id}\nAddress: No address found.\n")
        except Exception as e:
            print(f"Unit ID: {unit_id}\nError: {e}\n")

# # Example usage
# file_path = "lat_and_long2.json"  # Path to your JSON file


# process_properties(file_path)

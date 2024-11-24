
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import random

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

def get_address_from_coords(latitude, longitude, language="en"):
    # Randomly select a user agent for each request
    user_agent = random.choice(USER_AGENTS)
    
    
    while True:
        try:
            # Try to get the geocode data
            geolocator = Nominatim(user_agent=user_agent)
            # Set up a rate limiter to ensure requests are spaced out
            geocode = RateLimiter(geolocator.reverse, min_delay_seconds=2)
            
            # Default values
            max_retries = 10
            base_delay = 2  # Initial delay in seconds
            attempt = 0
            default_value = ""

            data = geocode((latitude, longitude), language=language).raw

            # Safely extract each required field
            house_number = data.get('address', {}).get('house_number', default_value)
            road = data.get('address', {}).get('road', default_value)
            hamlet = data.get('address', {}).get('hamlet', default_value)
            city = data.get('address', {}).get('city', default_value)
            state = data.get('address', {}).get('state', default_value)
            zipcode = data.get('address', {}).get('postcode', default_value)

            # Combine non-empty fields into a formatted address string
            address_parts = [house_number, road, hamlet, city, state, zipcode]
            address = ", ".join(part for part in address_parts if part)
            return address
        
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise RuntimeError(f"Failed to get address after {max_retries} retries: {e}")
            delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
            print(f"Attempt {attempt} with user agent '{user_agent}' failed. Retrying in {delay} seconds...")
            time.sleep(delay)
            # Optionally pick a new user agent for the next attempt
            user_agent = random.choice(USER_AGENTS)
            geolocator = Nominatim(user_agent=user_agent)




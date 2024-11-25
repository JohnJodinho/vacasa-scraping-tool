from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
import sys


def get_scraping_url():
    return SCRAPING_URL


# Function to fetch and parse XML
def fetch_and_parse_xml(url):
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url, timeout=80000, wait_until="domcontentloaded")
            content = BeautifulSoup(page.content(), "html.parser")
            
        except Exception as e:
            print(f"Unexpected error while processing {vacasa_link}: {e}")
        except PlaywrightTimeoutError:
            print(f"Timeout error while processing {vacasa_link}")
        
        finally:
            return content
            browser.close()


# Function to process XML and structure into JSON
def process_sitemap(html_content):
    data = []
    urls = html_content.find_all("div", class_="folder")
    # <div xmlns="http://www.w3.org/1999/xhtml" class="folder" id="folder1"><div class="line"><span class="folder-button fold">
    for url in urls:
        url = url.find('span', string=lambda text: text and "https://" in text).text
        # <div xmlns="http://www.w3.org/1999/xhtml" class="line"><span class="html-tag">&lt;loc&gt;</span><span>https://www.vacasa.com/usa/Nedonna-Views/</span><span class="html-tag">&lt;/loc&gt;</span></div>
     
        loc = url.split("vacasa.com")[-1]
        # print(loc)
        loc = loc.strip("/")
        # print(loc)
        if "usa" in loc or "vacation-rentals" in loc:
            if "vacation-rentals" in loc:
                loc = loc.split("vacation-rentals/")[-1]
            # print(loc)
            parts = loc.split("/")
            country = parts[0]
            if len(parts) == 2:
                # Structure: Country and Location
                location = parts[1].replace("-", " ")
                data.append({"country": country, "location": location, "url": url})
            elif len(parts) == 3:
                # Structure: Country, Region/State/Province, City/Town
                region = parts[1].replace("-", " ")
                city = parts[2].replace("-", " ")
                data.append({"country": country, "region/state/province": region, "city/town": city, "url": url})
    return data

# Save data to JSON file
def save_to_json(data, filename="sitemap_data.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")






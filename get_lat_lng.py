from playwright.sync_api import sync_playwright
import gzip
import zlib
import json

def get_lat_long(unit_ids_list):
    with sync_playwright() as p:
        # Create a Playwright request context
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        request_context = context.request

        url = "https://www.vacasa.com/guest-com-api/get-locations"

        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "csrftoken=yFp01IJk1cq7WYkbvOk4xnU9o75kABCPlmyjLD2eEvRizzzJKVYkgOS11gKEvG3x;",
            "origin": "https://www.vacasa.com",
            "referer": "https://www.vacasa.com/search?place=usa/Tennessee/Nashville/",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "x-csrftoken": "sOtdxp7T2D11q0wsoAKGXeC3kX57zVKufvCwhkqNFWsc3BL0DHoWGFAVX6Kru0bc",
            "x-requested-with": "XMLHttpRequest"
        }

        # Example payload (replace with your actual payload)
        payload = {"unit_ids": unit_ids_list, "avail_start": None, "avail_end": None}

        try:
            # Perform a POST request
            response = request_context.post(url, headers=headers, data=json.dumps(payload))

            if response.status == 200:
                response_content = response.body()
                content_encoding = response.headers.get("content-encoding", "")
                
                if "gzip" in content_encoding:
                    response_data = gzip.decompress(response_content).decode("utf-8")
                elif "deflate" in content_encoding:
                    response_data = zlib.decompress(response_content, zlib.MAX_WBITS | 16).decode("utf-8")
                else:
                    response_data = response.json()
                
                return response_data
            else:
                print(f"Request failed with status code: {response.status}")
                return f"Failed with status code: {response.status}"

        except Exception as e:
            print(f"An error occurred: {e}")
            return f"Error: {e}"
        finally:
            browser.close()

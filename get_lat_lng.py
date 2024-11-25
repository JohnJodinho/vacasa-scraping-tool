import requests
import json

def get_lat_long(unit_ids_list: list):
    url = "https://www.vacasa.com/guest-com-api/get-locations"

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "cookie": "csrftoken=yFp01IJk1cq7WYkbvOk4xnU9o75kABCPlmyjLD2eEvRizzzJKVYkgOS11gKEvG3x; ajs_anonymous_id=ab86c1fb-fc0b-41e3-a428-8d9a8f086cb9; optimizelyEndUserId=oeu1731104797792r0.952189376908009; _gcl_au=1.1.999204061.1731104806; _ga=GA1.1.532686323.1731104811; _fbp=fb.1.1731104820827.518358646939556170; hubspotutk=4c2384586a22f30990c40966bebdec43; _hjSessionUser_169794=eyJpZCI6IjFmYjc4ZWVlLWU1YTAtNWVjMy04NDI1LTYwZmNkZTc3YjI0MiIsImNyZWF0ZWQiOjE3MzExMDQ4MTcyODAsImV4aXN0aW5nIjp0cnVlfQ==; ndp_session_id=3090a2f8-08eb-40bf-9bb8-1a62ffe8858d; tracker_device_is_opt_in=true; tracker_device=7816f9ee-76c8-4521-bc10-e6da6e795322; sessionid=w6edhhov59jin3gkr7tqay0tlqymd2tf; __hssrc=1; _ga_SZKD9D5EPS=GS1.1.1731551514.9.1.1731551549.25.0.0; _ga_4JGS42DXPK=GS1.1.1731551513.9.1.1731551551.0.0.0; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Nov+14+2024+03%3A32%3A40+GMT%2B0100+(West+Africa+Standard+Time)&version=202407.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0004%3A1&AwaitingReconsent=false; _hjSession_169794=eyJpZCI6IjkyYzMwNGQ3LTBkMmYtNDI5YS05NTYwLTNhNjgzOTg2ZmY3ZSIsImMiOjE3MzE1NTE1NjEyNTcsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _uetsid=2dd22850a1ec11efbb1657e7843ac3fb; _uetvid=8e25e2109e2011ef92a9755b2bea4b11; dicbo_id=%7B%22dicbo_fetch%22%3A1731551562502%7D; __hstc=93626498.4c2384586a22f30990c40966bebdec43.1731104860062.1731548474380.1731551568782.8; __hssc=93626498.1.1731551568782; _dd_s=rum=0&expire=1731552559867",
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
    payload = {"unit_ids":unit_ids_list,"avail_start":None,"avail_end":None}
    response = requests.post(url, headers=headers, json=payload)

    # Save response to a JSON file
    if response.status_code == 200:
        try:
            response_data = response.json()
            return response_data
            
        except json.JSONDecodeError:
            print("Failed to decode JSON response.")
            return "Failed to decode JSON response."
    else:
        print(f"Request failed with status code: {response.status_code}")
        return f"Failed with status code: {response.status_code}"



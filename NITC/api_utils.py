import requests
from functools import lru_cache
from .config import BEACON_URL, USERNAME, PASSWORD
from pybeacon import beacon_auth
from .time_utils import sydney_time_now
import pytz
import json

@lru_cache(maxsize=1)
def get_api_token(username=USERNAME, password=PASSWORD):
    token_data = beacon_auth.get_api_token(username, password, BEACON_URL)
    if token_data is None:
        print("Access token was not found")
        return None
    return token_data.get('accessToken')

# Function to search for a member by registration number
@lru_cache(maxsize=32)
def search_member_by_reg_num(registrationNumber):
    access_token = get_api_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    search_url = f"https://apitrainbeacon.ses.nsw.gov.au/Api/v1/People/search?registrationNumber={registrationNumber}"
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        person_id = data['Results'][0]['Id'] if data['Results'] else None
        return data, person_id
    else:
        return None, None



@lru_cache(maxsize=32)
def search_member_by_last_name_api(LastName):
    access_token = get_api_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    search_url = f"{BEACON_URL}/Api/v1/People/Search?LastName={LastName}"
    response = requests.get(search_url, headers=headers)
    return response_handling(response)

def response_handling(response):
    if response.status_code == 200:
        try:
            data = response.json()
            person_id = data['Results'][0]['Id'] if data['Results'] else None
            return data, person_id
        except ValueError as e:  # Includes JSONDecodeError
            print("Error decoding JSON:", e)
            return None, None
    else:
        print(f"Error: Status code {response.status_code}")
        return None, None

def send_api_payload(person_id, start_date, end_date, tag_ids, token):
    sydney_tz = pytz.timezone('Australia/Sydney')
    start_date_aware = sydney_tz.localize(start_date)
    end_date_aware = sydney_tz.localize(end_date)

    payload = {
        "Name": f"NITC - {start_date_aware.strftime('%d/%m/%Y')}",
        "Description": "",
        "TypeId": 1,
        "StartDate": start_date_aware.strftime('%Y-%m-%dT%H:%M:%S'),
        "EndDate": end_date_aware.strftime('%Y-%m-%dT%H:%M:%S'),
        "Participants": [
            {
                "Id": 0,
                "PersonId": person_id,
                "StartDate": start_date_aware.strftime('%Y-%m-%dT%H:%M:%S'),
                "EndDate": end_date_aware.strftime('%Y-%m-%dT%H:%M:%S'),
                "TypeId": 1
            }
        ],
        "TagIds": tag_ids
    }

    print(json.dumps(payload, indent=4))  # This will print the payload in a formatted manner for debugging


    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        "https://apitrainbeacon.ses.nsw.gov.au/Api/v1/NonIncident", json=payload, headers=headers)
    if response.status_code in [200, 201]:
        return {"status": "success", "message": "Check-out time captured and event created"}
    else:
        return {"status": "error", "message": f"Failed to post to API: {response.text}"}



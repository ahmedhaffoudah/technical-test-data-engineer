import requests
import json
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def fetch_data(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Checks for HTTP errors
        data = response.json()
        if not isinstance(data, (list, dict)):
            raise ValueError(f"Unexpected data format from {endpoint}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        raise

def save_data(data, filename):
    try:
        json.dumps(data)  # This validates that data is JSON-serializable
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join("data", f"{filename}_{timestamp}.json")
        os.makedirs("data", exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
    except TypeError as e:
        print(f"Data provided to save_data is not serializable: {e}")
        raise


if __name__ == "__main__":
    tracks_data = fetch_data("tracks")
    save_data(tracks_data, "tracks")

    users_data = fetch_data("users")
    save_data(users_data, "users")

    listen_history_data = fetch_data("listen_history")
    save_data(listen_history_data, "listen_history")

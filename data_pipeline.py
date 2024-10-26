import requests
import json
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def fetch_data(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url)
    response.raise_for_status()  # Check for request errors
    return response.json()

def save_data(data, filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("data", f"{filename}_{timestamp}.json")
    os.makedirs("data", exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    tracks_data = fetch_data("tracks")
    save_data(tracks_data, "tracks")

    users_data = fetch_data("users")
    save_data(users_data, "users")

    listen_history_data = fetch_data("listen_history")
    save_data(listen_history_data, "listen_history")

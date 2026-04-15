import requests
import json

# First login to get token
login_url = "https://college-concierge-backend.onrender.com/auth/login"
login_data = {
    "username": "student3@iiitn.ac.in",
    "password": "test123"
}

response = requests.post(login_url, data=login_data)
token = response.json().get("access_token")

# Create a club
club_url = "https://college-concierge-backend.onrender.com/clubs"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
club_data = {
    "name": "Coding Club",
    "description": "A club for coding enthusiasts"
}

response = requests.post(club_url, headers=headers, json=club_data)
print(response.json())
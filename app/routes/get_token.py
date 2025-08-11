import requests

# Replace these with your actual details
client_id = "1000.B15249FU7RNPV8PIQIN0YF0SYZ4VNL"
client_secret = "e13ba8af33d967569299cf00da967bb826813f77cc"
redirect_uri = "http://localhost:8000/callback"
auth_code = "1000.2eea145693641fb60880e9ca202fcdf9.08242a780c56f28e50bb6726c382c72d"

url = "https://accounts.zoho.in/oauth/v2/token"

data = {
    "grant_type": "authorization_code",
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "code": auth_code
}

response = requests.post(url, data=data)

# Prints the access and refresh token
print(response.json())

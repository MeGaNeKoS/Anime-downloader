import io
import json

from deps.gdrive import gdrive

__all__ = ['service']

with open("data/cred.json") as infile:
    client_secret = json.load(infile)

scopes = ["https://www.googleapis.com/auth/drive"]

try:
    with open("data/user.json", "r") as user_file:
        cred = json.load(user_file)
except (io.UnsupportedOperation, json.JSONDecodeError):
    cred = None

service = gdrive.Google(client_secret, scopes)
creds = service.service.auth(cred, run_server=False)
if isinstance(creds, str):

    token = input("Auth code: ")
    creds = service.service.auth_token(token)
with open("data/user.json", "w") as outfile:
    outfile.write(creds.to_json())


def login():
    return None

import json
import os

import requests
import requests.exceptions

jyp_token = os.environ["JPY_API_TOKEN"]
jyp_server = os.environ["JUPYTERHUB_API_URL"]

r = requests.get(f"{jyp_server}/user", headers={"Authorization": f"token {jyp_token}"})

try:
    r.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(repr(e))
else:
    print(json.dumps(r.json(), indent=2))

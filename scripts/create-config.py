import json
import os
import random
import time

import requests

api_url = "https://api.mullvad.net/www/relays/all/"
relay_list_filename = os.getenv("RELAY_FILE_LOCATION", "./tmp/relay_list.json")
relay_list_expiry = 60 * 60 * 24  # 24 hours
all_relays = {}

config_filename = os.getenv("CONFIG_LOCATION", "./tmp/config.conf")

private_key = os.getenv("PRIVATE_KEY")
address = os.getenv("ADDRESS")
dns = os.getenv("DNS", "10.64.0.1")
allowed_ips = os.getenv("ALLOWED_IPS", "0.0.0.0/0,::0/0")

if not private_key or not address:
    print("Missing required environment variables")
    exit(1)

countries = os.getenv("COUNTRIES", "Canada").split(",")

# Read from file if recent file exists
if os.path.exists(relay_list_filename):
    if os.path.getmtime(relay_list_filename) + relay_list_expiry < time.time():
        os.remove(relay_list_filename)
    else:
        with open(relay_list_filename, "r") as f:
            all_relays = json.load(f)

if not all_relays:
    response = requests.get(api_url)
    all_relays = response.json()
    with open(relay_list_filename, "w") as f:
        json.dump(all_relays, f)

relays = [relay for relay in all_relays 
            if relay["country_name"] in countries
            and relay["active"]
            and relay["type"] == "wireguard"]

# Choose a random relay
chosen_relay = relays[random.randrange(0, len(relays))]

public_key = chosen_relay["pubkey"]
endpoint = chosen_relay["ipv4_addr_in"]

generated_config = \
f"""[Interface]
PrivateKey = {private_key}
Address = {address}
DNS = {dns}

[Peer]
PublicKey = {public_key}
AllowedIPs = {allowed_ips}
Endpoint = {endpoint}:51820

[http]
BindAddress = 0.0.0.0:8888
"""

with open(config_filename, "w") as f:
    f.write(generated_config)

print(f"Created a config to connect to {chosen_relay['country_name']} ({chosen_relay['city_name']}) - {public_key}")
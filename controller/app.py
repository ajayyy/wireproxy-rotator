import os
import random
import signal
import subprocess
import sys
import time
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

import requests

app = FastAPI()
api_url = "https://api.mullvad.net/www/relays/all/"
relay_list_expiry = 60 * 60 * 24  # 24 hours
last_relays_fetch = 0

config_filename = os.getenv("CONFIG_LOCATION", "./tmp/config.conf")

private_key = os.getenv("PRIVATE_KEY")
address = os.getenv("ADDRESS")
dns = os.getenv("DNS", "10.64.0.1")
allowed_ips = os.getenv("ALLOWED_IPS", "0.0.0.0/0,::0/0")
wait_time = int(os.getenv("TIMEOUT", str(60 * 60))) # 1 hour
failure_check_time = int(os.getenv("FAIL_CHECK_TIME", str(60))) # 1 hour

if not private_key or not address:
    print("Missing required environment variables")
    exit(1)

countries = os.getenv("COUNTRIES", "Canada").split(",")

relays = []
def fetch_relays():
    global last_relays_fetch, relays

    last_relays_fetch = time.time()

    all_relays = requests.get(api_url).json()

    relays = [relay for relay in all_relays 
                if relay["country_name"] in countries
                and relay["active"]
                and relay["type"] == "wireguard"]

def pick_relay():
    if time.time() - last_relays_fetch > relay_list_expiry:
        fetch_relays()

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

    return relays[random.randrange(0, len(relays))]

proxy_process = None

def start_proxy():
    global proxy_process

    if proxy_process:
        proxy_process.terminate()
        signal.alarm(0)

    pick_relay()

    proxy_process = subprocess.Popen(["/usr/bin/wireproxy", "--config", "./config.conf"])
    signal.alarm(wait_time)

fail_count = 0
success_count = 0
last_reset = time.time()

def reset_if_needed():
    global fail_count, success_count, last_reset

    if time.time() - last_reset > failure_check_time:
        print(f"Fail count: {fail_count}, Success count: {success_count}")
        if fail_count > 5 and fail_count > success_count:
            # Try a new server
            start_proxy()

        fail_count = 0
        success_count = 0
        last_reset = time.time()

@app.post("/api/fail")
def fail() -> RedirectResponse:
    global fail_count
    fail_count += 1

    reset_if_needed()
    pass

@app.post("/api/success")
def success() -> RedirectResponse:
    global success_count
    success_count += 1

    reset_if_needed()
    pass

def signal_handler(_, __):
    if proxy_process:
        proxy_process.terminate()
    sys.exit(0)

def alarm_handler(_, __):
    start_proxy()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGALRM, alarm_handler)

# Init
start_proxy()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=8000, log_level="warning")
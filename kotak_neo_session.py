import os
import sys
import json
import pyotp
import socket

# Force IPv4 socket resolution globally to eliminate IPv6 dual-stack mismatch with Kotak API gateway
old_getaddrinfo = socket.getaddrinfo
def _force_ipv4(*args, **kwargs):
    return [r for r in old_getaddrinfo(*args, **kwargs) if r[0] == socket.AF_INET]
socket.getaddrinfo = _force_ipv4

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
KOTAK_SDK_DIR = r"C:\Users\Ridham\.gemini\antigravity-ide\scratch\Kotak-neo-api-v2"
for p in [BOT_DIR, KOTAK_SDK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from neo_api_client import NeoAPI

CONFIG_PATH = os.path.join(BOT_DIR, "kotak_config.json")
SESSION_CACHE_PATH = os.path.join(BOT_DIR, "shared_session.json")
SHARED_FALLBACK_CONFIG = os.path.join(KOTAK_SDK_DIR, "kotak_config.json")

def load_config():
    """Loads config from local config or environment variables (GitHub Actions secrets)."""
    cfg = {}
    target_config = CONFIG_PATH if os.path.exists(CONFIG_PATH) else SHARED_FALLBACK_CONFIG
    if os.path.exists(target_config):
        try:
            with open(target_config, "r") as f:
                cfg = json.load(f)
        except Exception:
            pass

    return {
        "consumer_key": os.environ.get("KOTAK_CONSUMER_KEY", cfg.get("consumer_key", "")),
        "mobile_number": os.environ.get("KOTAK_MOBILE_NUMBER", cfg.get("mobile_number", "")),
        "ucc": os.environ.get("KOTAK_UCC", cfg.get("ucc", "")),
        "mpin": os.environ.get("KOTAK_MPIN", cfg.get("mpin", "")),
        "totp_secret": os.environ.get("KOTAK_TOTP_SECRET", cfg.get("totp_secret", "")),
        "environment": os.environ.get("KOTAK_ENV", cfg.get("environment", "prod"))
    }

def get_kotak_session():
    """Returns an authenticated Kotak NeoAPI client session."""
    cfg = load_config()
    consumer_key = cfg["consumer_key"]
    mobile_number = cfg["mobile_number"]
    ucc = cfg["ucc"]
    mpin = cfg["mpin"]
    totp_secret = cfg["totp_secret"]

    client = NeoAPI(environment="prod", consumer_key=consumer_key)

    # 1. Check for valid cached session token
    if os.path.exists(SESSION_CACHE_PATH):
        try:
            with open(SESSION_CACHE_PATH, "r") as f:
                cache = json.load(f)
            
            if cache.get("edit_token") and cache.get("edit_sid"):
                client.configuration.view_token = cache.get("view_token")
                client.configuration.sid = cache.get("sid")
                client.configuration.edit_token = cache.get("edit_token")
                client.configuration.edit_sid = cache.get("edit_sid")
                client.configuration.edit_rid = cache.get("edit_rid")
                client.configuration.serverId = cache.get("serverId", "")
                client.configuration.data_center = cache.get("data_center", "E21")
                client.configuration.base_url = cache.get("base_url", "https://e21.kotaksecurities.com")
                return client
        except Exception as e:
            print(f"[-] Cached session invalid: {e}")

    # 2. Automated TOTP Generation & Login
    print("[*] Generating live TOTP and initiating login...")
    totp = pyotp.TOTP(totp_secret).now()
    
    otp_resp = client.totp_login(
        mobile_number=mobile_number,
        ucc=ucc,
        totp=totp
    )

    if not otp_resp or "error" in str(otp_resp).lower():
        raise RuntimeError(f"Failed OTP validation: {otp_resp}")

    val_resp = client.totp_validate(mpin=mpin)
    
    if not val_resp or "error" in str(val_resp).lower():
        raise RuntimeError(f"Failed MPIN session creation: {val_resp}")

    # Cache token for reuse
    try:
        cache_data = {
            "view_token": client.configuration.view_token,
            "sid": client.configuration.sid,
            "edit_token": client.configuration.edit_token,
            "edit_sid": client.configuration.edit_sid,
            "edit_rid": client.configuration.edit_rid,
            "serverId": client.configuration.serverId,
            "data_center": client.configuration.data_center,
            "base_url": client.configuration.base_url,
            "timestamp": client.configuration.edit_token[:10] if client.configuration.edit_token else ""
        }
        with open(SESSION_CACHE_PATH, "w") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"[-] Token caching note: {e}")

    return client

#!/usr/bin/env python3
import os
import logging
import requests
from flask import Flask, request, jsonify, make_response

# --- CONFIG ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://yDark.stormx.pw/index.cpp")
BACKEND_KEY = os.getenv("BACKEND_KEY", "dark")
FRONTEND_KEY = os.getenv("FRONTEND_KEY", "VeiledAssembly")
OWNER_HANDLE = os.getenv("OWNER_HANDLE", "@alphadgaf")
CONTACT_INFO = os.getenv("CONTACT_INFO", "@alphadgaf")
PORT = int(os.getenv("PORT", 5000))
BACKEND_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", 300))

# --- Flask app ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("frontend-proxy")

# --- Ownership / landing page ---
def ownership_message():
    return f"This API is owned by {OWNER_HANDLE}. Contact {CONTACT_INFO} on Telegram for membership or access.", 200

@app.route("/", strict_slashes=False)
def root():
    return ownership_message()

# --- Frontend API endpoint ---
@app.route("/index.cpp", strict_slashes=False)
def index():
    args = request.args.to_dict(flat=True)  # get all query parameters
    key = args.pop("key", "").strip()

    # Ownership check
    if key != FRONTEND_KEY:
        log.warning("Invalid frontend key from %s: %s", request.remote_addr, key)
        return ownership_message(), 401

    # No other parameters? Show ownership
    if not args:
        return ownership_message(), 200

    # Build backend URL with backend key and forwarded parameters
    backend_params = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in args.items())
    backend_url = f"{BACKEND_URL}?key={BACKEND_KEY}&{backend_params}"

    log.info("Forwarding request from %s to backend: %s", request.remote_addr, backend_url)

    try:
        resp = requests.get(backend_url, timeout=BACKEND_TIMEOUT, headers={"User-Agent": "frontend-proxy/1.0"})
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                data = resp.json()
            except:
                data = resp.text
        else:
            data = resp.text

        out = {"backend_status": resp.status_code, "data": data}
        r = make_response(jsonify(out), 200 if resp.status_code == 200 else 502)
        r.headers["X-Proxy-Backend-Status"] = str(resp.status_code)
        return r

    except requests.exceptions.RequestException as e:
        log.error("Backend request failed: %s", e)
        return jsonify({"error": "backend request failed"}), 502

# --- Health check ---
@app.route("/health", strict_slashes=False)
def health():
    return {"status": "ok"}

# --- Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)


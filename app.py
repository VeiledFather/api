#!/usr/bin/env python3
import os, time, logging
from urllib.parse import quote_plus
import requests
from flask import Flask, request, jsonify, make_response

# --- CONFIG ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://yDark.stormx.pw/index.cpp")
BACKEND_KEY = os.getenv("BACKEND_KEY", "dark")  # Hidden backend key
FRONTEND_KEY = os.getenv("FRONTEND_KEY", "VeiledAssembly")
OWNER_HANDLE = os.getenv("OWNER_HANDLE", "@alphadgaf")
CONTACT_INFO = os.getenv("CONTACT_INFO", "@alphadgaf")
PORT = int(os.getenv("PORT", "5000"))
BACKEND_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "300"))

# --- Flask app + logging ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("frontend-proxy")

# --- Landing page ---
@app.route("/", strict_slashes=False)
def root():
    return f"This API is owned by {OWNER_HANDLE}. Contact {CONTACT_INFO} on Telegram for membership or access.", 200

# --- Frontend API mimicking backend API ---
@app.route("/index.cpp", strict_slashes=False)
def index():
    key = request.args.get("key", "").strip()
    
    # Check frontend key
    if key != FRONTEND_KEY:
        return f"This API is owned by {OWNER_HANDLE}. Contact {CONTACT_INFO} on Telegram for membership or access.", 401

    # Collect all other query parameters and forward them
    params = {k: v for k, v in request.args.items() if k != "key"}

    if not params:
        # No query parameters given
        return f"This API is owned by {OWNER_HANDLE}. Contact {CONTACT_INFO} on Telegram for membership or access.", 200

    # Build backend URL
    backend_params = "&".join(f"{k}={quote_plus(v)}" for k, v in params.items())
    backend_url = f"{BACKEND_URL}?key={quote_plus(BACKEND_KEY)}&{backend_params}"

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    log.info("Request from %s forwarded to backend: %s", client_ip, backend_url)

    try:
        t0 = time.perf_counter()
        resp = requests.get(backend_url, timeout=BACKEND_TIMEOUT, headers={"User-Agent": "frontend-proxy/1.0"})
        elapsed = time.perf_counter() - t0
    except requests.exceptions.RequestException as e:
        log.warning("Backend request failed for %s: %s", params, e)
        return jsonify({"error": "backend request failed"}), 502

    # Return JSON if possible
    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            data = resp.json()
        except Exception:
            data = resp.text
    else:
        data = resp.text

    out = {"backend_status": resp.status_code, "data": data}
    r = make_response(jsonify(out), 200 if resp.status_code == 200 else 502)
    r.headers["X-Proxy-Time"] = f"{elapsed:.3f}"
    r.headers["X-Proxy-Backend-Status"] = str(resp.status_code)
    return r

# --- Health check ---
@app.route("/health", strict_slashes=False)
def health():
    return {"status": "ok", "ts": int(time.time())}

# --- Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

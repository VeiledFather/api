#!/usr/bin/env python3
import requests

# --- CONFIG ---
API_URL = "https://api-d38k.onrender.com/index.cpp"  # Replace with your Render URL if needed
FRONTEND_KEY = "VeiledAssembly"

print("Interactive Number Query Tool")
print("Press Ctrl+C to exit.\n")

while True:
    try:
        number = input("Enter number to query: ").strip()
        if not number:
            print("Number cannot be empty.")
            continue

        params = {
            "key": FRONTEND_KEY,
            "number": number
        }

        resp = requests.get(API_URL, params=params, timeout=30)
        try:
            data = resp.json()
        except:
            data = resp.text

        print("\n--- Response ---")
        print(data)
        print("----------------\n")

    except KeyboardInterrupt:
        print("\nExiting.")
        break
    except Exception as e:
        print("Error:", e)

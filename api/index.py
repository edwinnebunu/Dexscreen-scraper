from flask import Flask, jsonify, request
import json
import threading
import time
import datetime
from api.dex import DexBot, Api  # Ensure DexBot is correctly imported
import os

app = Flask(__name__)

# Use an environment variable for your API key (default value for testing)
API_KEY = "67eba790-f6b6-4035-995b-5de1df963478"

# Global variable and lock for storing the latest fetched data
latest_data = {}
data_lock = threading.Lock()

# Default filter (for example, filtering by Solana)
default_filter = "&filters[chainIds][0]=solana"

# Base URL for the DexScreener endpoint
BASE_URL = "wss://io.dexscreener.com/dex/screener/v5/pairs/h24/1?rankBy[key]=trendingScoreH6&rankBy[order]=desc"

def update_data_periodically():
    global latest_data
    while True:
        try:
            # Construct the URL by appending the default filter
            url = BASE_URL + default_filter
            print("Fetching data from URL:", url)
            new_bot = DexBot(Api, url)
            fetched_data = new_bot.format_token_data()  # This returns a JSON string
            parsed_data = json.loads(fetched_data)
            # Add a fetched_at timestamp in ISO format (UTC)
            parsed_data["fetched_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            with data_lock:
                latest_data = parsed_data
            print("Data updated at", parsed_data["fetched_at"])
        except Exception as e:
            print("Error updating data:", e)
        # Sleep for 30 seconds before fetching again
        time.sleep(30)

# Start the background thread when the app starts
threading.Thread(target=update_data_periodically, daemon=True).start()

@app.route('/')
def root():
    return "Welcome to our Data API v3!"

@app.route('/api/dex', methods=['GET'])
def api_dex():
    # Expect the API key in the request header "x-api-key"
    provided_key = request.headers.get("x-api-key")
    if provided_key != API_KEY:
        return jsonify({"error": "Unauthorized access"}), 403
    with data_lock:
        if latest_data:
            return app.response_class(json.dumps(latest_data), mimetype='application/json')
        else:
            return jsonify({"error": "Data not yet available v3"}), 503

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

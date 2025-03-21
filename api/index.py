from flask import Flask, jsonify
import json
import threading
import time
import datetime
from api.dex import DexBot, Api  # Ensure DexBot is correctly imported

app = Flask(__name__)

# Global variable and lock for storing the latest fetched data
latest_data = {}
data_lock = threading.Lock()

# Default filter to apply by default (for example, filtering by Solana)
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
    return "Welcome to our Data API v2!"

@app.route('/api/dex', methods=['GET'])
def api_dex():
    with data_lock:
        if latest_data:
            return app.response_class(json.dumps(latest_data), mimetype='application/json')
        else:
            return jsonify({"error": "Data not yet available"}), 503

if __name__ == '__main__':
    app.run(debug=True)

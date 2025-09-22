import os
import time
from flask import Flask, jsonify, request, send_from_directory
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables from a .env file if it exists
load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app)

# Fetch the API key from environment variables
API_KEY = os.getenv("FINNHUB_API_KEY")
print(f'API KEY is {API_KEY}')
FINNHUB_API_BASE_URL = "https://finnhub.io/api/v1"

@app.route('/')
def serve_index():
    """Serves the main HTML file for the frontend."""
    return send_from_directory('.', 'index.html')

@app.route('/api/timeseries')
def get_time_series():
    """Fetches and returns historical stock data from Finnhub."""
    # Get the symbol from the URL query parameters
    symbol = request.args.get('symbol', 'AAPL').upper()

    if not API_KEY:
        return jsonify({"error": "API key is missing. Please provide one or set it in your environment."}), 400

    # Define the time range for historical data (e.g., last 3 months)
    to_timestamp = int(time.time())
    from_timestamp = to_timestamp - (90 * 24 * 60 * 60) # 90 days ago

    url = f"{FINNHUB_API_BASE_URL}/stock/candle?symbol={symbol}&resolution=D&from={from_timestamp}&to={to_timestamp}&token={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        # Finnhub returns 'c' for close price, 't' for timestamp, 's' for status
        if data.get("s") != "ok":
            return jsonify({"error": data.get("error", f"An unknown error occurred with the Finnhub API for symbol {symbol}.")}), 400

        close_prices = data.get("c", [])
        timestamps = data.get("t", [])

        if not close_prices or not timestamps:
            return jsonify({"error": f"No data found for symbol {symbol}"}), 404
        
        # Format data for the frontend
        formatted_data = []
        for i in range(len(close_prices)):
            date_str = datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
            formatted_data.append({
                "x": date_str,
                "y": close_prices[i]
            })

        return jsonify(formatted_data)
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to retrieve data from Finnhub: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

from flask import Flask, jsonify, request, send_from_directory, abort
from datetime import datetime, timedelta
from flask_cors import CORS
from faker import Faker
import random

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app)

fake = Faker()

# Generate symbols fake data
num_symbols = 50
symbols = []
for _ in range(num_symbols):
    # Generate a fake company name and ticker symbol
    company_name = fake.company()
    symbol = "".join(word[0].upper() for word in company_name.split())
    
    # Ensure the symbol is not too short or long
    if 2 <= len(symbol) <= 5:
        symbols.append({
            "symbol": symbol,
            "description": company_name
        })

# Add a few well-known fake symbols for consistency
symbols.append({"symbol": "AAPL", "description": "Apple Inc."})
symbols.append({"symbol": "GOOG", "description": "Alphabet Inc."})
symbols.append({"symbol": "MSFT", "description": "Microsoft Corp."})
symbols.append({"symbol": "AMZN", "description": "Amazon.com, Inc."})
symbols.append({"symbol": "TSLA", "description": "Tesla, Inc."})

# Generate fake time series
# Start from a random, but consistent, base price
prices = []
for symbol in [s["symbol"] for s in symbols]:
    base_price = sum(ord(c) for c in symbol) * 1.5 + 50
    current_price = base_price + random.uniform(-10, 10)

    price_timeserie = []
    for i in range(90, 0, -1):
        # Simulate a random walk for the price
        change = random.uniform(-1.5, 1.5)
        current_price += change
        current_price = max(current_price, 0.01) # Price can't be negative

        price_timeserie.append(current_price)

    prices.append(price_timeserie)


@app.route('/')
def serve_index():
    """Serves the main HTML file for the frontend."""
    return send_from_directory('.', 'index.html')

@app.route('/api/timeseries')
def get_time_series():
    symbol = request.args.get('symbol').upper()
    
    symbol_index = next((i for i, s in enumerate(symbols) if s["symbol"] == symbol), None)
    if symbol_index is None: abort(400,f"Unknown symbol {symbol}")
    price_timeserie = prices[symbol_index]

    formatted_data = []

    for i in range(len(price_timeserie), 0, -1):
        date = datetime.now() - timedelta(days=i)
        formatted_data.append({
            "x": date.strftime('%Y-%m-%d'),
            "y": round(price_timeserie[i-1], 2)
        })

    return jsonify(formatted_data)

@app.route('/api/symbols')
def get_symbols():
    return jsonify(symbols)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

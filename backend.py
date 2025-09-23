import os
import time
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from kafka import KafkaConsumer
from threading import Thread
import logging
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# In-memory storage for the latest data from each symbol
# A deque will automatically discard the oldest item when it reaches its maximum length
stock_history = {}

def start_kafka_consumer():
    """Starts a Kafka consumer in a separate thread."""
    try:
        consumer = KafkaConsumer(
            'stock-data',
            bootstrap_servers='kafka:9092',
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='my-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        for message in consumer:
            data = message.value
            symbol = data.get('symbol')
            # Check if the symbol exists in our history, and if not, create a new deque
            if symbol not in stock_history:
                stock_history[symbol] = deque(maxlen=120)
            
            # Store the new data point, oldest data will be automatically removed
            stock_history[symbol].append(data)
            
            #logging.info(f"Received and stored data for: {symbol}")
    except Exception as e:
        logging.error(f"Error in Kafka consumer: {e}")

# Start the consumer in a background thread
consumer_thread = Thread(target=start_kafka_consumer)
consumer_thread.daemon = True
consumer_thread.start()

@app.route('/')
def serve_index():
    """Serves the main HTML file."""
    return send_from_directory('.', 'index.html')

@app.route('/api/timeseries')
def get_time_series():
    """Returns the latest data for a given symbol."""
    symbol = request.args.get('symbol').upper()
    data = stock_history.get(symbol)
    if data:
        # Convert the deque to a list before returning
        return jsonify(list(data))
    return jsonify({"error": "Data not found for symbol"}), 404

@app.route('/api/symbols')
def get_symbols():
    """Returns the list of available symbols from the latest data."""
    # Infer available symbols from the keys in our latest_data cache
    symbols = []
    for symbol, data in stock_history.items():
        symbols.append({
            "symbol": symbol,
            "description": data[0].get("description", "N/A")
        })
    logging.info(f"API to send {len(symbols)} symbols")
    return jsonify(symbols)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

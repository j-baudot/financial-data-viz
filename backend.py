import os
import time
import json
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import redis
import threading
import logging
import queue
from collections import deque

from symbols import SYMBOLS

# Init shared data
stock_history = {} # An in-memory dictionary to gather stocks time series over time
stock_history_lock = threading.Lock() # A lock to ensure stock_history management is thread safe
redis_client = redis.Redis(host='redis', port=6379, db=0) # A Redis server to manage events in thread safe queues

def get_stock_history_dequeue(symbol):
    with stock_history_lock:
        if symbol not in stock_history: stock_history[symbol] = deque(maxlen=120)
        return stock_history[symbol]
    
# Configure the flask main app
logging.basicConfig(level=logging.INFO)
app = Flask('financial-data-viz-backend')
CORS(app)

# Init the class for WebSockets usage
socketio = SocketIO(app,cors_allowed_origins="*")

# Kafka consumer thread where data stream is stored to Redis and front end is notified 
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
            redis_client.lpush(f'queue:{symbol}', json.dumps(data))
            socketio.emit('new_financial_data',data['timestamp'])

    except Exception as e:
        logging.error(f"Error in Kafka consumer: {e}")

# Kafka consumer thread startup
if __name__ == '__main__':
    consumer_thread = threading.Thread(target=start_kafka_consumer)
    consumer_thread.daemon = True
    consumer_thread.start()

# Stock symbols API
@app.route('/api/symbols')
def get_symbols():
    """Returns the list of available symbols from the latest data."""
    return jsonify(SYMBOLS)

# Stock prices time series API
@app.route('/api/timeseries')
def get_time_series():
    """Returns the latest data for a given symbol."""
    symbol = request.args.get('symbol')
    symbol_deque = get_stock_history_dequeue(symbol)

    while True:
        data = redis_client.rpop(f'queue:{symbol}')
        if data is None: break
        symbol_deque.append(json.loads(data))

    return jsonify(list(symbol_deque))

# Front-end route
@app.route('/')
def serve_index():
    """Serves the main HTML file."""
    return send_from_directory('.', 'index.html')

# Main Flask app startup
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

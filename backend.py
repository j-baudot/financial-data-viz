import os
import time
import json
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from kafka import KafkaConsumer
import redis
import threading
import logging
import queue
from collections import deque

from symbols import SYMBOLS

# Init shared data
stock_vals_lock = threading.Lock()
stock_history = {}
event_queue = queue.Queue()
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Configure logging and build main app
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)

# SSE for front-end data updates
@app.route('/events')
def sse_stream():
    def event_stream():
        while True:
            # Block until new data is available in the queue
            data = event_queue.get()
            yield f"data: {data}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

# Manage data history in-memory
def get_stock_history_dequeue(symbol):
    with stock_vals_lock:
        if symbol not in stock_history: stock_history[symbol] = deque(maxlen=120)
        return stock_history[symbol]

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
            #logging.info(f"Message received from Kafka Producer")
            data = message.value
            symbol = data.get('symbol')
            redis_client.lpush(f'queue:{symbol}', json.dumps(data))

            # Trigger SSE event
            event_queue.put(data['timestamp'])

    except Exception as e:
        logging.error(f"Error in Kafka consumer: {e}")

# Front-end
@app.route('/')
def serve_index():
    """Serves the main HTML file."""
    return send_from_directory('.', 'index.html')

# Symbols API
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
    logging.info(f'Dequeue of {symbol} as {len(symbol_deque)} elements initially')

    while True:
        data = redis_client.rpop(f'queue:{symbol}')
        if data is None: break
        symbol_deque.append(json.loads(data))

    logging.info(f'Dequeue of {symbol} as {len(symbol_deque)} elements finally')

    # Convert the deque to a list before returning
    return jsonify(list(symbol_deque))

if __name__ == '__main__':
    consumer_thread = threading.Thread(target=start_kafka_consumer)
    consumer_thread.daemon = True
    consumer_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5000)

import os
import time
import json
from datetime import datetime, timedelta
from faker import Faker
import random
from kafka import KafkaProducer
import logging
logging.basicConfig(level=logging.INFO)

from symbols import SYMBOLS

fake = Faker()
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',api_version=(2, 13, 0),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)



def generate_stock_data():
    """Generates a continuous stream of fake stock data."""
    # Create a consistent state for each symbol's price
    price_states = {}
    for s in SYMBOLS:
        random.seed(s['symbol'])
        base_price = sum(ord(c) for c in s['symbol']) * 1.5 + 50
        price_states[s['symbol']] = base_price + random.uniform(-10, 10)

    while True:
        timestamp = datetime.now()
        
        for s in SYMBOLS:
            # Simulate a random walk for the price
            random.seed(f"{s['symbol']}_{timestamp.minute}_{timestamp.second}")
            change = random.uniform(-0.5, 0.5)
            current_price = price_states[s['symbol']] + change
            current_price = max(current_price, 0.01)
            price_states[s['symbol']] = current_price
            
            data_point = {
                "symbol": s['symbol'],
                "timestamp": timestamp.isoformat(timespec='seconds'),
                "price": round(current_price, 2),
                "description": s['description']
            }
            
            # Send the data point to Kafka
            producer.send('stock-data', value=data_point)
            logging.info(f"Sent message to Kafka: {data_point}")

        # Sleep for 1 second to control the data flow
        time.sleep(1)

if __name__ == "__main__":
    generate_stock_data()

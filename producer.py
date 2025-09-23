import os
import time
import json
from datetime import datetime, timedelta
from faker import Faker
import random
from kafka import KafkaProducer

# Initialize Faker and Kafka Producer
fake = Faker()
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',api_version=(2, 13, 0),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Constants for data generation
SYMBOL_COUNT = 20
KNOWN_SYMBOLS = [
    {"symbol": "AAPL", "description": "Apple Inc."},
    {"symbol": "GOOG", "description": "Alphabet Inc."},
    {"symbol": "MSFT", "description": "Microsoft Corp."},
    {"symbol": "AMZN", "description": "Amazon.com, Inc."},
    {"symbol": "TSLA", "description": "Tesla, Inc."}
]

# Generate a consistent list of fake symbols
def get_fake_symbols():
    symbols = []
    for _ in range(SYMBOL_COUNT - len(KNOWN_SYMBOLS)):
        company_name = fake.company()
        symbol = "".join(word[0].upper() for word in company_name.split())
        symbols.append({"symbol": symbol, "description": company_name})
    return symbols + KNOWN_SYMBOLS

def generate_stock_data():
    """Generates a continuous stream of fake stock data."""
    # This list will persist for the duration of the producer's run
    symbols = get_fake_symbols()

    # Create a consistent state for each symbol's price
    price_states = {}
    for s in symbols:
        random.seed(s['symbol'])
        base_price = sum(ord(c) for c in s['symbol']) * 1.5 + 50
        price_states[s['symbol']] = base_price + random.uniform(-10, 10)

    while True:
        timestamp = datetime.now()
        
        for s in symbols:
            # Simulate a random walk for the price
            random.seed(f"{s['symbol']}_{timestamp.minute}_{timestamp.second}")
            change = random.uniform(-0.5, 0.5)
            current_price = price_states[s['symbol']] + change
            current_price = max(current_price, 0.01)
            price_states[s['symbol']] = current_price
            
            data_point = {
                "symbol": s['symbol'],
                "timestamp": timestamp.isoformat(),
                "price": round(current_price, 2),
                "description": s['description']
            }
            
            # Send the data point to Kafka
            producer.send('stock-data', value=data_point)
            print(f"Sent message to Kafka: {data_point}")

        # Sleep for 1 second to control the data flow
        time.sleep(1)

if __name__ == "__main__":
    generate_stock_data()

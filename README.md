# financial-data-viz

![Printscreen](ressources/printscreen.gif)

## Purpose
This repository is a toy project aimed at practicing data management pipelines.

For now on, it contains a single application which allow users to display live stock values in a web browser.

As access to financial APIs is not that straightforward, stocks names are fakes and associated values are generated using random walks - don't try to run predictive algorithm ;) .

## How to use it
1. Clone this repository
2. Run docker-compose up --build
3. Open http://127.0.0.1:5000 on your favorite web browser
4. Enjoy selecting your favorite stock symbol and see it's pricing evolving over time in a limited time window (120 seconds).

## Architecture
This python application uses Apache Kafka in a producer-consumer scheme.
The stream is generated on the producer, and captured by the consumer on the Flask backend.

A Redis server is used to store the events in a persistent and thread-safe way.

The front end is notified of any new data income through WebSockets.

## Caveats
For now on, events are stored on different Redis queues - one per stock symbol - and a stock timeserie is built from queues only when an API is called for a given stock symbol. This may result in long processing time  - and erroneous timeouts - when a user vizualize a stock during a long timespan then switch to another.


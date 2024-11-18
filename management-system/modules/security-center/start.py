from security_module.consumer import SecurityConsumer
from security_module.producer import SecurityProducer
import threading

def start_producer():
    producer = SecurityProducer()
    sample_event = {
        "driver_id": "driver_123",
        "location": (50.455, 30.525),
        "speed": 60,
    }
    producer.send_event(sample_event)
    producer.close()

def start_consumer():
    consumer = SecurityConsumer()
    try:
        consumer.start()
    finally:
        consumer.close()

if __name__ == "__main__":
    # Start both producer and consumer in separate threads for demo purposes
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    producer_thread = threading.Thread(target=start_producer)

    consumer_thread.start()
    producer_thread.start()

    producer_thread.join()

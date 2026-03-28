import threading
from app.vector.consumer import run_consumer


def start_rabbitmq_consumer():
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    print("RabbitMQ consumer thread started")


if __name__ == "__main__":
    start_rabbitmq_consumer()

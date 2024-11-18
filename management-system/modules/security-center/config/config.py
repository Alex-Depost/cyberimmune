# Configurations for security_module
import os

class Config:
    # RabbitMQ connection details
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "security_events")

    # Zone configuration
    RESTRICTED_ZONES = {
        "restricted_zone_1": {"center": (50.45, 30.52), "radius": 0.5},  # in km
        "restricted_zone_2": {"center": (50.60, 30.55), "radius": 0.7},
    }
    WARNING_DISTANCE = 0.5  # km
    DECELERATION_RATE = 5  # km/h per second

import unittest
from unittest.mock import patch, MagicMock
from security_module.producer import SecurityProducer


class TestSecurityProducerWithMock(unittest.TestCase):
    @patch("pika.BlockingConnection")
    def test_send_event_with_mock_rabbitmq(self, mock_connection):
        # Mock RabbitMQ connection and channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        # Create producer instance
        producer = SecurityProducer()

        # Test event
        test_event = {"driver_id": "driver_123", "location": (50.455, 30.525), "speed": 60}

        # Call send_event
        producer.send_event(test_event)

        # Assert the event is sent
        mock_channel.basic_publish.assert_called_once_with(
            exchange="",
            routing_key="security_events",
            body='{"driver_id": "driver_123", "location": [50.455, 30.525], "speed": 60}',
        )
        producer.close()

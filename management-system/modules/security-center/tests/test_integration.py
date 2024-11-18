import unittest
from unittest.mock import patch, MagicMock
from security_module.producer import SecurityProducer
from security_module.consumer import SecurityConsumer


class TestIntegrationWithMock(unittest.TestCase):
    @patch("pika.BlockingConnection")
    def test_producer_consumer_integration_with_mock(self, mock_connection):
        # Mock RabbitMQ connection and channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        # Create producer and send event
        producer = SecurityProducer()
        test_event = {"driver_id": "driver_123", "location": (50.455, 30.525), "speed": 60}
        producer.send_event(test_event)

        # Verify the event is sent to the mock channel
        mock_channel.basic_publish.assert_called_once()

        # Create consumer and simulate message processing
        with patch("security_module.consumer.TripSafetyController") as MockSafetyController:
            mock_safety = MockSafetyController.return_value
            mock_safety.warn_restricted_zone.return_value = True
            mock_safety.handle_zone_entry.return_value = True

            consumer = SecurityConsumer()
            consumer.on_message(mock_channel, None, None, '{"driver_id": "driver_123", "location": [50.455, 30.525], "speed": 60}')

            # Verify consumer processes the event
            mock_safety.warn_restricted_zone.assert_called_once()
            mock_safety.handle_zone_entry.assert_called_once()

        producer.close()
        consumer.close()

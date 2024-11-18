import unittest
from unittest.mock import patch, MagicMock
from security_module.consumer import SecurityConsumer


class TestSecurityConsumerWithMock(unittest.TestCase):
    @patch("pika.BlockingConnection")
    def test_on_message_with_mock_rabbitmq(self, mock_connection):
        # Mock RabbitMQ connection and channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        # Mock TripSafetyController to avoid real logic
        with patch("security_module.consumer.TripSafetyController") as MockSafetyController:
            mock_safety = MockSafetyController.return_value
            mock_safety.warn_restricted_zone.return_value = True
            mock_safety.handle_zone_entry.return_value = True

            # Create consumer instance
            consumer = SecurityConsumer()

            # Simulate incoming message
            test_event = '{"driver_id": "driver_123", "location": [50.455, 30.525], "speed": 60}'
            consumer.on_message(mock_channel, None, None, test_event)

            # Verify warnings and safety measures were called
            mock_safety.warn_restricted_zone.assert_called_once_with((50.455, 30.525))
            mock_safety.handle_zone_entry.assert_called_once_with(60, (50.455, 30.525), "driver_123")

        consumer.close()

import os
import sys
import requests
import time
import unittest

# Настройка путей для импорта
__location__ = os.path.dirname(os.path.abspath(__file__))
monitor_path = os.path.join(__location__, os.pardir, os.pardir, 'management-system', 'modules', 'monitor', 'module')
security_path = os.path.join(__location__, os.pardir, os.pardir, 'management-system', 'modules', 'security-center', 'module')

if not os.path.exists(monitor_path):
    print('failed to find monitor module in', monitor_path)
    exit(1)
else:
    sys.path.insert(1, monitor_path)
    from policies import policies, check_operation

if not os.path.exists(security_path):
    print('failed to find security-center module in', security_path)
    exit(1)
else:
    sys.path.insert(1, security_path)
    from safety_and_zone_control import ZoneConfig, TripSafetyController

# URL сервиса мобильного приложения
MOBILE_URL = 'http://0.0.0.0:8002'

# Клиент для тестирования
client = {"name": "Иван Иванов", "experience": 1}

# Переменные для генерации уникальных событий
event_id = 0


def next_event():
    """Генерация уникального идентификатора события."""
    global event_id
    event_id += 1
    return event_id


class TestClientTrip(unittest.TestCase):
    """Тесты базового сценария поездки клиента."""

    def test_full_func(self):
        """Тест базового сценария поездки клиента от аренды до завершения поездки."""
        # Этап 1: Предварительная регистрация автомобиля
        prepayment = requests.post(f'{MOBILE_URL}/cars', json=client)
        self.assertEqual(prepayment.status_code, 200)
        time.sleep(2)

        # Этап 2: Создание предоплаты
        response = requests.post(f'{MOBILE_URL}/prepayment', json=prepayment.json())
        self.assertEqual(response.status_code, 200)
        time.sleep(2)

        # Этап 3: Начало поездки
        car = requests.post(f'{MOBILE_URL}/start_drive', json=client)
        self.assertEqual(car.status_code, 200)
        time.sleep(5)  # Имитация времени поездки

        # Этап 4: Завершение поездки
        invoice = requests.post(f'{MOBILE_URL}/stop_drive', json=client)
        self.assertEqual(invoice.status_code, 200)
        time.sleep(2)

        # Этап 5: Финальная оплата
        response = requests.post(f'{MOBILE_URL}/final_pay', json=invoice.json())
        self.assertEqual(response.status_code, 200)

        # Проверка данных ответа
        data = response.json()
        self.assertIn('car', data)
        self.assertIn('created_at', data)
        self.assertIn('elapsed_time', data)
        self.assertIn('name', data)
        self.assertIn('final_amount', data)
        self.assertIn('tarif', data)


class TestPolicies(unittest.TestCase):
    """Тесты политик взаимодействия модулей."""

    def test_check_operation_true(self):
        """Тест успешной проверки политики."""
        result = check_operation(next_event(), {
            "source": policies[1]["src"],
            "deliver_to": policies[1]["dst"],
        })
        self.assertEqual(result, True)

    def test_check_operation_false(self):
        """Тест на нарушение политики."""
        result = check_operation(next_event(), {
            "source": "foo",
            "deliver_to": "bar",
        })
        self.assertEqual(result, False)

    def test_policy_combinations(self):
        """Множественные проверки политик."""
        ops = [
            ("com-mobile", "profile-client", True),
            ("profile-client", "manage-drive", True),
            ("manage-drive", "auth", False),
            ("receiver-car", "control-drive", True),
            ("control-drive", "sender-car", True),
            ("profile-client", "control-drive", False),
        ]
        for src, dst, expected in ops:
            result = check_operation(next_event(), {"source": src, "deliver_to": dst})
            self.assertEqual(result, expected)


class TestZoneControl(unittest.TestCase):
    """Тесты управления зонами и безопасности поездки."""

    def setUp(self):
        """Инициализация зон и контроллера."""
        self.zone_config = ZoneConfig()
        self.trip_control = TripSafetyController(self.zone_config)

    def test_zone_control_warnings(self):
        """Тест предупреждений при попадании в зоны."""
        location_in_zone = (50.455, 30.525)  # Внутри зоны
        location_out_of_zone = (55.0, 35.0)  # Вне зоны

        self.assertTrue(self.trip_control.warn_restricted_zone(location_in_zone))
        self.assertFalse(self.trip_control.warn_restricted_zone(location_out_of_zone))

    def test_zone_control_handling(self):
        """Тест обработки входа в запрещённые зоны."""
        location_in_zone = (50.455, 30.525)
        location_out_of_zone = (55.0, 35.0)

        # Тест корректной обработки в зоне
        self.assertTrue(self.trip_control.handle_zone_entry(50, location_in_zone, "driver_123"))

        # Тест корректной обработки вне зоны
        self.assertFalse(self.trip_control.handle_zone_entry(50, location_out_of_zone, "driver_123"))

    def test_trip_control_sequence(self):
        """Тест последовательной обработки действий с зонами."""
        car_data = {
            "speed": 80,
            "coordinates": (50.455, 30.525),
            "user": "Иван Иванов",
            "car_model": "Toyota Prius",
            "license_plate": "А123ВС77",
        }

        # Имитация корректного поведения
        self.assertTrue(self.trip_control.warn_restricted_zone(car_data["coordinates"]))
        self.assertTrue(self.trip_control.handle_zone_entry(car_data["speed"], car_data["coordinates"], car_data["license_plate"]))

        # Тест выхода из зоны
        car_data["coordinates"] = (55.0, 35.0)
        self.assertFalse(self.trip_control.warn_restricted_zone(car_data["coordinates"]))
        self.assertFalse(self.trip_control.handle_zone_entry(car_data["speed"], car_data["coordinates"], car_data["license_plate"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

import time
from collections import deque
from .support import SupportService

class Config:
    # Интервал сбора данных
    DATA_INTERVAL = 120  # каждые 2 минуты
    MAX_COORDINATE_TIMEOUT = 600  # 10 минут в секундах
    MAX_NO_DATA_TIMEOUT = 1800  # 30 минут в секундах

    # Географические параметры (для кэширования зон)
    TUNNEL_RADIUS = 2.0  # км
    ZONE_API_URL = "http://0.0.0.0/allowed_zones"
    CACHE_EXPIRY = 3600  # Время жизни кэша в секундах (1 час)


class CarMonitor:
    """Мониторинг состояния автомобиля."""

    def __init__(self):
        self.car_data = {}  # Данные об автомобилях
        self.data_log = {}  # История маршрутов (хранится как deque)
        self.zone_api = ZoneAPI()

    def update_car_data(self, car_id, data):
        """Обновление данных автомобиля."""
        self.car_data[car_id] = data
        if car_id not in self.data_log:
            self.data_log[car_id] = deque(maxlen=3)  # Храним последние 3 записи
        self.data_log[car_id].append(data)

    def check_missing_coordinates(self, car_id):
        """Проверка отсутствия координат."""
        if time.time() - self.car_data[car_id]["timestamp"] > Config.MAX_COORDINATE_TIMEOUT:
            last_route = list(self.data_log[car_id])[:2]  # Берем последние 2 записи
            SupportService.notify_missing_coordinates(self.car_data[car_id], last_route)

    def analyze_no_data(self, car_id):
        """Анализ на отсутствие данных более 30 минут."""
        car = self.car_data[car_id]
        if time.time() - car["timestamp"] > Config.MAX_NO_DATA_TIMEOUT:
            if self.is_possible_area(car):
                SupportService.notify_possible_area(car, self.is_possible_area(car))
            else:
                SupportService.notify_driver(car)

    def is_possible_area(self, car):
        """Проверка, может ли автомобиль быть в зоне по данным API."""
        zones = self.zone_api.get_zones()

        for area_type, locations in zones.items():
            for loc in locations:
                distance = ((car["coordinates"][0] - loc[0]) ** 2 + (car["coordinates"][1] - loc[1]) ** 2) ** 0.5
                if distance <= Config.TUNNEL_RADIUS:
                    return area_type
        return None

    def monitor_cars(self):
        """Периодический мониторинг всех автомобилей."""
        while True:
            for car_id, car_data in list(self.car_data.items()):
                self.check_missing_coordinates(car_id)
                self.analyze_no_data(car_id)
            time.sleep(Config.DATA_INTERVAL)


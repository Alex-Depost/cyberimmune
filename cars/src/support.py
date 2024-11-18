import logging
import requests
import time
from cachetools import TTLCache

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class SupportService:
    """Класс для обработки уведомлений службы поддержки."""

    @staticmethod
    def notify_missing_coordinates(car_data, last_route):
        """Уведомление о недоступности координат."""
        logging.info(f"Support notified: Missing coordinates for {car_data['license_plate']}. Last route: {last_route}")

    @staticmethod
    def notify_possible_area(car_data, area_type):
        """Уведомление о возможном туннеле, пароме или горной местности."""
        logging.info(f"Support notified: Possible {area_type} detected for {car_data['license_plate']}.")

    @staticmethod
    def notify_driver(car_data):
        """Отправка уведомления водителю."""
        logging.info(f"Driver notified: Please contact support for {car_data['license_plate']}.")
        
class ZoneAPI:
    """Работа с внешним API зон."""

    def __init__(self):
        # Кэш для хранения данных зон
        self.cache = TTLCache(maxsize=100, ttl=Config.CACHE_EXPIRY)

    def get_zones(self):
        """Получение зон из внешнего API."""
        if "zones" in self.cache:
            return self.cache["zones"]

        response = requests.get(Config.ZONE_API_URL)
        if response.status_code == 200:
            zones = response.json()
            self.cache["zones"] = zones
            return zones
        else:
            raise ConnectionError("Failed to fetch zones from API.")

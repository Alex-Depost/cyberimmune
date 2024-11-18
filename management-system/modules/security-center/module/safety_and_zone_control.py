# file: management_system/safety_and_zone_control.py

from typing import Dict, Any, Tuple
import time
from dataclasses import dataclass


@dataclass
class ZoneConfig:
    """Configuration for restricted zones and warnings."""

    def __init__(self):
        # Define restricted zones and corresponding safe deceleration rates
        self.restricted_zones = {
            # in km
            "restricted_zone_1": {"center": (50.45, 30.52), "radius": 0.5},
            "restricted_zone_2": {"center": (50.60, 30.55), "radius": 0.7},
        }
        self.warning_distance = 0.5  # Distance in km for warning
        self.deceleration_rate = 5  # Deceleration rate in km/h per second

    def is_in_zone(self, location: Tuple[float, float], zone: Dict) -> bool:
        """Check if a location is within a given restricted zone."""
        lat, lon = location
        zone_lat, zone_lon = zone["center"]
        distance = ((lat - zone_lat) ** 2 + (lon - zone_lon) ** 2) ** 0.5
        return distance <= zone["radius"]

    def is_near_zone(self, location: Tuple[float, float], zone: Dict) -> bool:
        """Check if a location is near a given restricted zone."""
        lat, lon = location
        zone_lat, zone_lon = zone["center"]
        distance = ((lat - zone_lat) ** 2 + (lon - zone_lon) ** 2) ** 0.5
        # If we're inside the zone or within the warning distance, return True
        return distance <= (zone["radius"] + self.warning_distance)


class TripSafetyController:
    """Controls trip safety, including warnings and restricted zone handling."""

    def __init__(self, zone_config: ZoneConfig):
        self.zone_config = zone_config

    def warn_restricted_zone(self, location: Tuple[float, float]):
        """Issue a warning if near a restricted zone."""
        for zone_name, zone in self.zone_config.restricted_zones.items():
            if self.zone_config.is_near_zone(location, zone):
                print(
                    f"[warning] Approaching restricted zone {zone_name}, "
                    f"location: {location}. Triggering warnings."
                )
                self.trigger_sound_warning()
                return True
        return False

    def trigger_sound_warning(self):
        """Trigger warning sounds in app and vehicle."""
        print("[info] Sound warning triggered: app notification and car signal")

    def handle_zone_entry(self, speed: int, location: Tuple[float, float], driver_id: str):
        """Gradually reduce speed and log entry if in a restricted zone."""
        for zone_name, zone in self.zone_config.restricted_zones.items():
            if self.zone_config.is_in_zone(location, zone):
                print(
                    f"[alert] Entered restricted zone {zone_name}, location: {location}. "
                    f"Reducing speed for safety."
                )
                self.log_driver_entry(driver_id, location, zone_name)
                self.gradual_speed_reduction(speed)
                return True
        return False

    def gradual_speed_reduction(self, current_speed: int):
        """Reduce speed gradually to ensure safety."""
        print("[info] Initiating gradual speed reduction.")
        while current_speed > 0:
            current_speed = max(
                current_speed - self.zone_config.deceleration_rate, 0)
            print(f"[info] Current speed: {current_speed} km/h")
            time.sleep(1)
        print("[info] Vehicle stopped or reached safe speed.")

    def log_driver_entry(self, driver_id: str, location: Tuple[float, float], zone_name: str):
        """Log driver details and restricted zone entry."""
        log_entry = (
            f"Driver {driver_id} entered restricted zone {zone_name}. "
            f"Location: {location}."
        )
        print(f"[log] {log_entry}")
        # Append to a log file for record-keeping
        with open("restricted_zone_log.txt", "a") as log_file:
            log_file.write(f"{log_entry}\n")


if __name__ == "__main__":
    zone_config = ZoneConfig()
    safety_controller = TripSafetyController(zone_config)

    # Simulated inputs
    current_location = (50.455, 30.525)
    current_speed = 60  # km/h
    driver_id = "driver_123"

    # Check for warnings and zone entry
    if safety_controller.warn_restricted_zone(current_location):
        print("[info] Warning issued to the driver.")
    if safety_controller.handle_zone_entry(current_speed, current_location, driver_id):
        print("[info] Restricted zone safety measures applied.")

from flask import Flask, jsonify, request
from pathlib import Path
import json
import random
import time
import requests
import os
import threading
from werkzeug.exceptions import HTTPException

MANAGMENT_URL = 'http://receiver-car:6070'

HOST = '0.0.0.0'
PORT = 8000
MODULE_NAME = os.getenv('MODULE_NAME')
app = Flask(__name__)

data = None
flag = True


class Car:
    def __init__(self, car_model, license_plate, has_air_conditioner=False, has_heater=False, has_navigator=False):
        self.speed = 0
        self.coordinates = (0, 0)
        self.occupied_by = None
        self.start_time = None
        self.car_model = car_model
        self.has_air_conditioner = has_air_conditioner
        self.has_heater = has_heater
        self.has_navigator = has_navigator
        self.is_running = False
        self.tariff = None
        self.license_plate = license_plate

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            return f"{self.car_model, self.license_plate} поездка началась."
        else:
            return f"{self.car_model, self.license_plate} поездка ещё идет."

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.speed = 0
            self.occupied_by = None
            return f"{self.car_model, self.license_plate} поездка завершена."
        else:
            return f"{self.car_model, self.license_plate} на парковке."

    def get_status(self):
        elapsed_time = 0
        if self.start_time is not None and self.is_running:
            elapsed_time = round(time.time() - self.start_time, 2)  # Время в секундах
        return {
            "car_model": self.car_model,
            "is_running": self.is_running,
            "speed": self.speed,
            "coordinates": self.coordinates,
            "occupied_by": self.occupied_by,
            "trip_time": elapsed_time,
            "has_air_conditioner": self.has_air_conditioner,
            "has_heater": self.has_heater,
            "has_navigator": self.has_navigator,
            "tariff ": self.tariff,
            "license_plate": self.license_plate
        }

    def update_coordinates(self, x, y):
        self.coordinates = (x, y)

    def set_speed(self, speed):
        if self.is_running:
            self.speed = speed
            return f"Скорость {self.car_model, self.license_plate} изменена на {self.speed} км/ч."
        else:
            return f"{self.car_model, self.license_plate} не парковке, скорость не может быть изменена."

    def occupy(self, person, tarif):
        self.occupied_by = person
        self.tariff = tarif
        return f"{self.car_model, self.license_plate} арендован {self.occupied_by}."


def simulate_drive(car):
    while car.is_running:
        new_speed = random.randint(10, 100)
        car.set_speed(new_speed)

        x_change = random.uniform(-2, 2)
        y_change = random.uniform(-2, 2)
        current_coordinates = car.coordinates
        new_coordinates = (current_coordinates[0] + x_change, current_coordinates[1] + y_change)
        car.update_coordinates(*new_coordinates)

        print(f"{car.car_model} Гос.Номер: {car.license_plate} Скорость: {car.speed:.2f} км/ч, Координаты: {car.coordinates}")
        status = car.get_status()
        requests.post(f'{MANAGMENT_URL}/telemetry/{car.car_model}', json={'status': status})
        time.sleep(1)


# Функция для загрузки автомобилей из JSON файла
def load_cars_from_json(file_path):
    with open(file_path, 'r') as file:
        cars_data = json.load(file)
        return [Car(**car) for car in cars_data]


BASE_DIR = Path(__file__).resolve().parent.parent
# Загружаем список автомобилей из файла
cars = load_cars_from_json(f'{BASE_DIR}/data/cars.json')


@app.route('/car/status/all', methods=['GET'])
def get_all_car_statuses():
    statuses = [car.get_status() for car in cars]
    requests.post(f'{MANAGMENT_URL}/car/status/all', json={'cars': statuses}) # Реализация разделения модуля коммуникации (ответы приходят на отдельный handler)
    return jsonify(statuses)


@app.route('/car/start/<string:car_model>', methods=['POST'])
def start_car(car_model):
    car = next((car for car in cars if car.car_model.lower() == car_model.lower()), None)
    if car:
        message = car.start()
        thread = threading.Thread(target=simulate_drive, args=(car,))
        thread.start()
        return jsonify({"message": message})
    else:
        return jsonify({"error": "Автомобиль не найден."}), 404


@app.route('/car/stop/<string:car_model>', methods=['POST'])
def stop_car(car_model):
    car = next((car for car in cars if car.car_model.lower() == car_model.lower()), None)
    if car:
        status = car.get_status()
        response = requests.post(f'{MANAGMENT_URL}/return/{car.occupied_by}', json={'status': status})
        if response.status_code == 200:
            message = car.stop()
            return jsonify({"message": message})
        else:
            message = car.stop()
            return jsonify({"message": message}), 404
    else:
        return jsonify({"error": "Автомобиль не найден."}), 404


@app.route('/emergency/<string:car_model>', methods=['POST'])
def emergency(car_model):
    car = next((car for car in cars if car.car_model.lower() == car_model.lower()), None)
    if car:
        message = car.stop()
        return jsonify({"message": message})
    else:
        return jsonify({"error": "Автомобиль не найден."}), 404


@app.route('/car/status/<string:car_model>', methods=['GET'])
def get_car_status(car_model):
    car = next((car for car in cars if car.car_model.lower() == car_model.lower()), None)
    if car:
        status = car.get_status()
        requests.post(f'{MANAGMENT_URL}/car/status', json={'status': status}) # Реализация разделения модуля коммуникации (ответы приходят на отдельный handler)
        return jsonify(status)
    else:
        return jsonify({"error": "Автомобиль не найден."}), 404

@app.route('/access/<string:person>', methods=['POST']) # Реализация разделения модуля коммуникации (ответы приходят на отдельный handler)
def access(person):
    global data
    global flag
    data = request.json
    flag = False # Реализация разделения модуля коммуникации
    return jsonify("ok")


@app.route('/car/occupy/<string:person>', methods=['POST'])
def occupy_car(person):
    global data
    global flag
    requests.post(f'{MANAGMENT_URL}/access/{person}')
    while flag:
        time.sleep(1) # Реализация разделения модуля коммуникации
    if data['access']:
        car_model = data['car']
        car = next((car for car in cars if car.car_model.lower() == car_model.lower()), None)
        if car and person is not None:
            tariff = data['tariff']
            message = car.occupy(person, tariff)
            flag = True
            return jsonify({"access": True, "car": car.car_model, "message": message})
        else:
            return jsonify({"access": False, "message": "Автомобиль не найден или не указан клиент."}), 404
    else:
        return jsonify({"access": False, "message": "Доступ до автомобиля не разрешен."}), 404


@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web():
    threading.Thread(target=lambda: app.run(
        host=HOST, port=PORT, debug=True, use_reloader=False
    )).start()

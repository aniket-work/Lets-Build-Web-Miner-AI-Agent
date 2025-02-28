import csv
import csv
from typing import List
from models.car import Car
from models.car import Car


def is_duplicate_car(car_identifier: str, seen_identifiers: set) -> bool:
    return car_identifier in seen_identifiers


def is_complete_car(car: dict, required_keys: list) -> bool:
    return all(key in car for key in required_keys)


def save_cars_to_csv(cars: List[dict], filename: str):
    if not cars:
        print("[INFO] No cars to save.")
        return

    fieldnames = list(Car.model_fields.keys())  # ['year', 'name', 'kilometers', 'price']
    print(f"[INFO] Saving cars to '{filename}' with fieldnames: {fieldnames}")

    successful_cars = []
    for idx, car in enumerate(cars, 1):
        try:
            # Remove the 'error' field and any other unexpected fields
            cleaned_car = {key: car[key] for key in fieldnames if key in car}
            successful_cars.append(cleaned_car)
            print(f"[INFO] Car {idx}/{len(cars)}: Cleaned car data: {cleaned_car}")
        except Exception as e:
            print(f"[ERROR] Car {idx}/{len(cars)}: Failed to clean car data: {e}. Original car: {car}. Skipping this car.")
            continue

    if not successful_cars:
        print("[INFO] No cars to save after cleaning.")
        return

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(successful_cars)
        print(f"[INFO] Saved {len(successful_cars)} cars to '{filename}'.")
    except Exception as e:
        print(f"[ERROR] Failed to save cars to '{filename}': {e}")

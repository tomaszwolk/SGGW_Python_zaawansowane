import json
import csv
import dataclasses
from typing import Protocol, List
from pathlib import Path

from src.domain import Adwokat


class AdwokatRepository(Protocol):
    def save(self, data: List[Adwokat]) -> None: ...


class JsonAdwokatRepository:
    def __init__(self, filepath: str | Path):
        self.filepath = filepath

    def save(self, data: List[Adwokat]) -> None:
        # Konwersja obiektów dataclass na słowniki
        # Używamy dataclasses.asdict
        dict_data = [dataclasses.asdict(adw) for adw in data]

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(dict_data, f, ensure_ascii=False, indent=4)
        print(f"[Storage] Zapisano {len(data)} rekordów do JSON: {self.filepath}")


class CsvAdwokatRepository:
    def __init__(self, filepath: str | Path):
        self.filepath = filepath

    def save(self, data: List[Adwokat]) -> None:
        if not data:
            return

        # Ustalamy nagłówki na podstawie pól pierwszego obiektu
        fieldnames = [
            "imie",
            "nazwisko",
            "status",
            "email",
            "nr_legitymacji",
            "miasto_izby",
            "kancelaria_nazwa",
            "kancelaria_adres",
        ]

        with open(self.filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for adw in data:
                # Spłaszczamy strukturę dla CSV
                row = {
                    "imie": adw.imie,
                    "nazwisko": adw.nazwisko,
                    "status": adw.status.value,
                    "email": adw.email,
                    "nr_legitymacji": adw.nr_legitymacji,
                    "miasto_izby": adw.izba.miasto if adw.izba else "",
                    "kancelaria_nazwa": adw.kancelaria.nazwa if adw.kancelaria else "",
                    "kancelaria_adres": adw.kancelaria.adres if adw.kancelaria else "",
                }
                writer.writerow(row)
        print(f"[Storage] Zapisano {len(data)} rekordów do CSV: {self.filepath}")

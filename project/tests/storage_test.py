import json
import csv
from src.domain import Adwokat, StatusAdwokata, IzbaAdwokacka
from src.storage import JsonAdwokatRepository, CsvAdwokatRepository
from pathlib import Path


def test_json_repository_save(tmp_path: Path):
    # Tworzymy tymczasową ścieżkę do pliku
    file_path = tmp_path / "test_output.json"

    # Przygotowujemy dane testowe
    data = [
        Adwokat(
            imie="Test",
            nazwisko="User",
            status=StatusAdwokata.AKTYWNY,
            izba=IzbaAdwokacka(miasto="TestCity"),
            link_szczegoly="url",
        )
    ]

    # Zapisujemy
    repo = JsonAdwokatRepository(str(file_path))
    repo.save(data)

    # Weryfikujemy czy plik istnieje i ma poprawną treść
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)
        assert len(content) == 1
        assert content[0]["nazwisko"] == "User"
        assert content[0]["status"] == "Wykonujący zawód"


def test_csv_repository_save(tmp_path: Path):
    file_path = tmp_path / "test_output.csv"

    data = [
        Adwokat(
            imie="Test",
            nazwisko="Nazwisko-Podwójne",
            status=StatusAdwokata.BYLY,
            izba=IzbaAdwokacka(miasto="Konstantynówka"),
            link_szczegoly="url",
        )
    ]

    repo = CsvAdwokatRepository(str(file_path))
    repo.save(data)

    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)

        assert "nazwisko" in header
        assert "Nazwisko-Podwójne" in row

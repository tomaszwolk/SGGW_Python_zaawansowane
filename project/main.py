import asyncio
import time
from src.scraper.engine import AdwokatScraper
from src.storage import JsonAdwokatRepository, CsvAdwokatRepository, AdwokatRepository

# Wybrane miasta
CITIES = ["Syców", "Wieliczka", "Ostrzeszów"]


async def main():
    print(f"Start scrapowania dla miast: {CITIES}")
    start_time = time.time()

    # Przy większej ilości concurrency niż 3, serwer zwraca HTTP 500
    scraper: AdwokatScraper = AdwokatScraper(concurrency=3)
    adwokaci = await scraper.scrape_cities(CITIES)

    end_time = time.time()
    duration = end_time - start_time

    print("\n=== PODSUMOWANIE POBIERANIA ===")
    print(f"Pobrano łącznie: {len(adwokaci)} adwokatów")
    print(f"Czas operacji: {duration:.2f} sek")

    # Zapis do pliku
    format_zapisu = "json"

    repo: AdwokatRepository
    if format_zapisu == "json":
        repo = JsonAdwokatRepository("adwokaci.json")
    elif format_zapisu == "csv":
        repo = CsvAdwokatRepository("adwokaci.csv")
    else:
        raise ValueError("Nieobsługiwany format zapisu")

    repo.save(adwokaci)


if __name__ == "__main__":
    asyncio.run(main())

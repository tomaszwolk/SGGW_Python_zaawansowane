import asyncio
import re
import random
import aiohttp
from bs4 import BeautifulSoup, Tag
from typing import List, Optional, Coroutine, Any

from src.domain import Adwokat
from src.scraper.builder import AdwokatBuilder

BASE_URL = "https://www.rejestradwokatow.pl"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/adwokat",
}


class AdwokatScraper:
    def __init__(self, concurrency: int = 5):
        self.semaphore = asyncio.Semaphore(concurrency)

    async def scrape_cities(self, cities: List[str]) -> List[Adwokat]:
        """Główna metoda orkiestrująca. Przyjmuje listę miast, zwraca listę adwokatów."""
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks: List[Coroutine[Any, Any, List[Adwokat]]] = []
            for city in cities:
                tasks.append(self._process_city(session, city))

            results = await asyncio.gather(*tasks)
            # Spłaszczenie listy list (flattening)
            return [adwokat for city_list in results for adwokat in city_list]

    async def _get_csrf_token(self, html: str) -> str:
        """
        Wyciąga token ukryty w kodzie JavaScript.
        Szukamy wzorca: tokenElement.val('HASH');
        """
        # Regex: Szukaj ciągu znaków wewnątrz ' ', który jest wewnątrz .val()
        match = re.search(r"tokenElement\.val\('([^']+)'\)", html)
        if match:
            return match.group(1)
        return ""

    async def _process_city(
        self, session: aiohttp.ClientSession, city: str
    ) -> List[Adwokat]:
        # 1. GET: Pobranie strony i tokena
        try:
            async with session.get(f"{BASE_URL}/adwokat") as resp:
                if resp.status != 200:
                    return []
                html_initial = await resp.text()

            token = await self._get_csrf_token(html_initial)
            if not token:
                print(
                    f"[{city}] Ostrzeżenie: Nie znaleziono tokena w JS (możliwa zmiana na stronie)."
                )

        except Exception as e:
            print(f"[{city}] Błąd sieciowy (GET): {e}")
            return []

        # 2. POST: Wyszukiwanie
        print(f"[{city}] Wyszukiwanie (Token: {token[:10]}...)...")
        url_post = f"{BASE_URL}/adwokat/wyszukaj"

        payload = {
            "recaptcha_response": "",
            "nazwisko": "",
            "imie": "",
            "imie2": "",
            "ulica": "",
            "miasto": city,
            "id_j": "0",
            "btn_wyszukaj": "Wyszukaj",
            "token": token,
        }

        try:
            async with session.post(url_post, data=payload) as response:
                html = await response.text()
        except Exception as e:
            print(f"[{city}] Błąd sieciowy (POST): {e}")
            return []

        # 3. Parsowanie tabeli
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.rejestr tbody tr")

        if not rows:
            print(f"[{city}] Brak wyników.")
            return []

        print(f"[{city}] Znaleziono {len(rows)} adwokatów. Pobieranie szczegółów...")

        # 4. Asynchroniczne pobieranie szczegółów
        lawyer_tasks = [self._process_single_lawyer(session, row) for row in rows]
        lawyers = await asyncio.gather(*lawyer_tasks)

        return [lawyer for lawyer in lawyers if lawyer is not None]

    async def _process_single_lawyer(
        self, session: aiohttp.ClientSession, row: Tag
    ) -> Optional[Adwokat]:
        full_link = "nieznany"
        try:
            cols = row.find_all("td")
            if len(cols) < 7:
                return None

            link_tag = cols[-1].find("a")
            if not link_tag or "href" not in link_tag.attrs:
                return None

            relative_link = link_tag["href"]
            if not isinstance(relative_link, str):
                return None
            full_link = (
                relative_link
                if relative_link.startswith("http")
                else f"{BASE_URL}{relative_link}"
            )

            # Przygotowanie danych do Buildera
            imie = cols[2].get_text(strip=True)
            nazwisko = cols[1].get_text(strip=True)
            miasto_izby = cols[5].get_text(strip=True)

            details_html = None

            # Logika retry
            max_retries = 4

            async with self.semaphore:
                for attempt in range(max_retries):
                    try:
                        # Losowe opóźnienie (0.5s - 1.5s)
                        await asyncio.sleep(random.uniform(0.5, 1.5))

                        # Używamy sesji przekazanej z góry
                        async with session.get(full_link) as response:
                            if response.status == 200:
                                details_html = await response.text()
                                break

                            elif response.status >= 500:
                                print(
                                    f"[Retry {attempt + 1}/{max_retries}] Błąd {response.status} dla {nazwisko}. Czekam..."
                                )
                                await asyncio.sleep(2 * (attempt + 1))
                                continue

                            else:
                                print(
                                    f"Błąd krytyczny {response.status} dla {full_link}"
                                )
                                return None

                    except aiohttp.ClientError as e:
                        print(
                            f"[Retry {attempt + 1}/{max_retries}] Błąd sieci {e} dla {nazwisko}"
                        )
                        await asyncio.sleep(1)

            if not details_html:
                print(f"Nie udało się pobrać szczegółów dla: {full_link}")
                return None

            # Budowanie obiektu
            builder = AdwokatBuilder()
            builder.set_basic_data(
                imie=imie, nazwisko=nazwisko, link=full_link, miasto_izby=miasto_izby
            )
            builder.set_html_details(details_html)

            return builder.build()

        except Exception as e:
            print(
                f"WYJĄTEK LOGICZNY przy adwokacie ({full_link}): {type(e).__name__}: {e}"
            )
            return None

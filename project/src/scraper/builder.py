import re
from typing import Optional, Any, cast
from bs4 import BeautifulSoup
from bs4.element import Tag
from src.domain import Adwokat, StatusAdwokata, Kancelaria, IzbaAdwokacka


class AdwokatBuilder:
    """
    Wzorzec Builder: Odpowiada za proces tworzenia obiektu Adwokat.
    Oddziela logikę parsowania HTML od samej klasy danych.
    """

    def __init__(self):
        self._adwokat_data: dict[
            str, Optional[str | IzbaAdwokacka | Kancelaria | list[str]]
        ] = {}
        self._html_details: Optional[BeautifulSoup] = None

    def set_basic_data(self, imie: str, nazwisko: str, link: str, miasto_izby: str):
        """Ustawia dane z tabeli głównej."""
        self._adwokat_data["imie"] = imie
        self._adwokat_data["nazwisko"] = nazwisko
        self._adwokat_data["link_szczegoly"] = link
        self._adwokat_data["izba"] = IzbaAdwokacka(miasto=miasto_izby)
        return self

    def set_html_details(self, html_content: str):
        """Ładuje HTML strony szczegółowej do parsowania."""
        self._html_details = BeautifulSoup(html_content, "html.parser")
        return self

    def _parse_legitymacja(self) -> Optional[str]:
        """Wyciąga nr legitymacji z <h3>(WRO/Adw/1033)</h3>"""
        if not self._html_details:
            return None

        target_h3: Optional[Tag] = None
        for tag in self._html_details.find_all("h3"):
            if tag.string and re.search(r"/adw/", tag.string.lower()):
                target_h3 = tag
                break
        if target_h3:
            text: str = target_h3.get_text(strip=True)
            return text.strip("()")
        return None

    def _parse_email(self) -> Optional[str]:
        """
        Wyciąga email z atrybutów data-ea i data-eb (ochrona przed botami).
        HTML: <div class="address_e" data-ea="jan" data-eb="domena.pl"></div>
        """
        if not self._html_details:
            return None

        email_div = self._html_details.select_one("div.address_e")
        if email_div:
            part_a = email_div.get("data-ea")
            part_b = email_div.get("data-eb")
            if part_a and part_b:
                return f"{part_a}@{part_b}"

        return None

    def _parse_status(self) -> StatusAdwokata:
        """Szuka diva ze statusem w nagłówku."""
        if not self._html_details:
            return StatusAdwokata.INNY

        # Szukamy: <span>Status:</span><div>Wykonujący zawód</div>
        status_label = None
        for span in self._html_details.find_all("span"):
            if span.string and "Status:" in span.string:
                status_label = span
                break
        if status_label and status_label.next_sibling:
            # next_sibling to ten div obok spana
            status_text = status_label.next_sibling.get_text(strip=True)
            return StatusAdwokata.from_text(status_text)

        return StatusAdwokata.INNY

    def _parse_kancelaria(self) -> Optional[Kancelaria]:
        """
        Najtrudniejsza część. Parsuje sekcję z adresem oddzielonym <br>.
        Szukamy w sekcji "MIEJSCE WYKONYWANIA ZAWODU".
        """
        if not self._html_details:
            return None

        # Szukamy kontenera, który ma nagłówek "MIEJSCE WYKONYWANIA ZAWODU"
        # szukamy H3 z ikonką mapy, a potem rodzica
        header = self._html_details.select_one("h3 > i.fa-map-marker-alt")
        if not header or not header.parent:
            return None

        # Wchodzimy wyżej do H3, a potem do diva obok (line_list_K)
        container = header.parent.find_next_sibling("div", class_="line_list_K")
        if not container:
            return None

        # Pobieramy pierwszy div wewnątrz listy (zakładamy, że to pierwsza kancelaria)
        address_div = container.select_one("div")
        if not address_div:
            return None

        # zamieniamy <br> na "|", żeby łatwo podzielić tekst
        text_content = address_div.get_text(separator="|", strip=True)
        lines = [line.strip() for line in text_content.split("|") if line.strip()]

        # Analiza linii (heurystyka):
        # 0: "Kancelaria" (ignorujemy)
        # 1: Nazwa Kancelarii (zazwyczaj)
        # Reszta: Adres

        if len(lines) < 3:
            return None  # Za mało danych

        # Pomijamy linię "Kancelaria" jeśli istnieje
        start_idx = 1 if lines[0].lower() == "kancelaria" else 0

        nazwa = lines[start_idx]
        # Łączymy resztę linii w adres (ulica + kod miasto), pomijając telefony i inne informacje
        adres_lines: list[str] = []
        break_points = ["Komórkowy", "Tel", "WWW", "Stacjonarny", "Fax"]
        for line in lines[start_idx + 1 :]:
            if any(break_point in line for break_point in break_points):
                break
            adres_lines.append(line)

        adres = ", ".join(adres_lines)

        return Kancelaria(nazwa=nazwa, adres=adres)

    def _parse_specjalizacje(self) -> list[str]:
        if not self._html_details:
            return []

        # Szukamy sekcji PREFEROWANA PRAKTYKA
        header = self._html_details.select_one("h3 > i.fa-clipboard-list-check")
        if not header or not header.parent:
            return []

        container = header.parent.find_next_sibling("div", class_="line_list_A")
        if not container:
            return []

        specs: list[str] = []
        for div in container.find_all("div"):
            text = div.get_text(strip=True)
            if text:
                specs.append(text)

        return specs

    def build(self) -> Adwokat:
        """Składa wszystko w całość."""
        # Walidacja czy mamy podstawy
        if "imie" not in self._adwokat_data:
            raise ValueError("Brak danych podstawowych! Użyj set_basic_data().")

        # Wyciągamy dane szczegółowe
        self._adwokat_data["nr_legitymacji"] = self._parse_legitymacja()
        self._adwokat_data["email"] = self._parse_email()
        self._adwokat_data["status"] = self._parse_status()
        self._adwokat_data["kancelaria"] = self._parse_kancelaria()
        self._adwokat_data["specjalizacje"] = self._parse_specjalizacje()

        # Pydantic sam zwaliduje typy przy tworzeniu obiektu
        return Adwokat(**cast(dict[str, Any], self._adwokat_data))

from enum import Enum
from typing import Optional
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass


class StatusAdwokata(str, Enum):
    AKTYWNY = "Wykonujący zawód"
    NIEWYKONUJACY = "Niewykonujący zawodu"
    BYLY = "Byli adwokaci"
    INNY = "Inny"  # Fallback

    @classmethod
    def from_text(cls, text: str) -> "StatusAdwokata":
        """Pomocnicza metoda do bezpiecznego mapowania tekstu ze strony."""
        try:
            return cls(text.strip())
        except ValueError:
            return cls.INNY


config = ConfigDict(str_strip_whitespace=True)


@dataclass(config=config)
class IzbaAdwokacka:
    miasto: str


@dataclass(config=config)
class Kancelaria:
    nazwa: str
    adres: str


@dataclass(config=config)
class Adwokat:
    imie: str
    nazwisko: str
    status: StatusAdwokata
    izba: IzbaAdwokacka
    link_szczegoly: str
    nr_legitymacji: Optional[str] = None
    email: Optional[str] = None
    kancelaria: Optional[Kancelaria] = None
    specjalizacje: list[str] = Field(default_factory=list)

    def __post_init__(self):
        self.imie = self.imie.title()
        self.nazwisko = self.nazwisko.title()

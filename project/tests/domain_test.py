from src.domain import Adwokat, IzbaAdwokacka, StatusAdwokata


def test_adwokat_name_capitalization():
    """Sprawdza czy imię i nazwisko są automatycznie zmieniane na Title Case."""
    adwokat = Adwokat(
        imie="malgorzata",
        nazwisko="maciaszek",
        status=StatusAdwokata.AKTYWNY,
        izba=IzbaAdwokacka(miasto="Wrocław"),
        link_szczegoly="https://fake-link.pl",
    )

    assert adwokat.imie == "Malgorzata"
    assert adwokat.nazwisko == "Maciaszek"


def test_status_adwokata_from_text():
    """Sprawdza czy StatusAdwokata.from_text() poprawnie mapuje tekst do Enuma."""
    assert StatusAdwokata.from_text("Wykonujący zawód") == StatusAdwokata.AKTYWNY
    assert (
        StatusAdwokata.from_text("Niewykonujący zawodu") == StatusAdwokata.NIEWYKONUJACY
    )
    assert StatusAdwokata.from_text("Byli adwokaci") == StatusAdwokata.BYLY
    assert StatusAdwokata.from_text("Inny") == StatusAdwokata.INNY
    assert StatusAdwokata.from_text("Błędny tekst") == StatusAdwokata.INNY

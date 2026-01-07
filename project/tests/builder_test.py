import pytest
from src.scraper.builder import AdwokatBuilder
from src.domain import StatusAdwokata


@pytest.fixture
def sample_html_details() -> str:
    return """
    <section>
        <h3>(WRO/Adw/1234)</h3>
        <div class="line_list_K">
            <div><span>Status:</span><div>Wykonujący zawód</div></div>
            <div>
                <span>Email:</span> 
                <div class="address_e" data-ea="jan" data-eb="domena.pl"></div>
            </div>
        </div>
    </section>

    <div class="mb_tabs_content">
        <div class="mb_tab_content special_one">
            <h3><i class="fas fa-map-marker-alt"></i></h3>
            <div class="line_list_K">
                <div>
                    <strong>Kancelaria</strong> <br>
                    Moja Kancelaria<br>
                    ul. Testowa 1 <br>
                    00-001 Miasto<br>
                    Komórkowy: 123456789 <br>               
                </div>
            </div>
            
            <h3><i class="fal fa-clipboard-list-check"></i></h3>
            <div class="line_list_A ">
                <div>Prawo karne</div>
                <div>Prawo cywilne</div>
            </div>
        </div>
    </div>
    """


def test_builder_full_process(sample_html_details: str):
    builder = AdwokatBuilder()
    builder.set_basic_data("Jan", "Kowalski", "https://example.com", "Wrocław")
    builder.set_html_details(sample_html_details)
    adwokat = builder.build()

    assert adwokat.imie == "Jan"
    assert adwokat.nazwisko == "Kowalski"
    assert adwokat.status == StatusAdwokata.AKTYWNY
    assert adwokat.izba.miasto == "Wrocław"
    assert adwokat.link_szczegoly == "https://example.com"
    assert adwokat.nr_legitymacji == "WRO/Adw/1234"
    assert adwokat.email == "jan@domena.pl"
    assert adwokat.kancelaria is not None
    assert adwokat.kancelaria.nazwa == "Moja Kancelaria"
    assert adwokat.kancelaria.adres == "ul. Testowa 1, 00-001 Miasto"
    assert adwokat.specjalizacje == ["Prawo karne", "Prawo cywilne"]


def test_builder_missing_data():
    builder = AdwokatBuilder()
    builder.set_basic_data("Ewa", "Nowakowska", "https://example2.com", "Syców")
    builder.set_html_details("<html></html>")
    adwokat = builder.build()

    assert adwokat.nr_legitymacji is None
    assert adwokat.email is None
    assert adwokat.kancelaria is None
    assert adwokat.specjalizacje == []

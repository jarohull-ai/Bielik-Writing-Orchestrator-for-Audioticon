import json
from pathlib import Path

from writing_agent.contract import classify_request
from writing_agent.router import route_request
from writing_agent.tools import continuity_checker, load_bible
from writing_agent.post_renderer import render

def test_contract_modes():
    assert classify_request("Skróć ten tekst").intent == "shorten"
    assert classify_request("Sprawdź fakt historyczny").mode == "factual"
    assert classify_request("Wymyśl miasto").mode == "creative"

def test_bible_is_loadable():
    bible = load_bible()
    assert {"premise", "characters", "world", "timeline", "locations", "terminology", "style_guide"} <= set(bible)

def test_continuity_detects_reverse_years():
    result = continuity_checker("Najpierw było 2022, a potem 2020.")
    assert result["status"] == "conflict"

def test_router_selects_tools():
    assert route_request("Skróć ten akapit")["tool"] == "model_generation"
    assert route_request("Skróć ten akapit")["result"]["requested_tool"] == "style_editor"
    assert route_request("Sprawdź ciągłość dat")["tool"] == "continuity_checker"

def test_output_modes_and_renderer():
    assert classify_request("Napisz scenę").output_mode == "TEXT_ONLY"
    assert classify_request("Przeanalizuj ton i styl tekstu").output_mode == "ANALYSIS_ONLY"
    assert classify_request("Napisz scenę i dodaj osobno uwagi redakcyjne.").output_mode == "TEXT_WITH_NOTES"
    assert classify_request("Zwróć wynik w formacie JSON.").output_mode == "STRUCTURED_JSON"
    cleaned = render("Ton: spokojny\nVoice: narracyjny\nBohater wszedł do pokoju.", "TEXT_ONLY")
    assert cleaned.cleaned and cleaned.text == "Bohater wszedł do pokoju."
    dialog = render("— Ton: spokojny — powiedziała Marta.", "TEXT_ONLY")
    assert not dialog.cleaned and dialog.text.startswith("— Ton:")
    heading = render("Ton\nBohater wrócił do domu.", "TEXT_ONLY")
    assert not heading.cleaned
    markdown = render("**Uwagi redakcyjne:** zachowano ton autora.\n\nAnna weszła do domu.", "TEXT_ONLY")
    assert markdown.cleaned and "Uwagi redakcyjne" not in markdown.text and "Anna" in markdown.text
    assert render("— Ton: spokojny — powiedziała Marta.", "TEXT_ONLY").cleaned is False
    assert render("**Rozdział pierwszy:**\nAnna weszła do domu.", "TEXT_ONLY").cleaned is False

def test_character_router_modes():
    generic = route_request("Wymyśl głównego bohatera powieści")
    assert generic["output_mode"] == "STRUCTURED_JSON"
    assert generic["result"]["operation"] == "character_new"
    named = route_request("Zaprojektuj postać: Lena, archiwistka")
    assert named["output_mode"] == "STRUCTURED_JSON"
    assert named["result"]["name"] == "Lena"
    assert named["result"]["status"] == "proposed"
    expanded = route_request("Rozwiń tę istniejącą postać z biblii projektu")
    assert expanded["result"]["operation"] == "character_expand"

if __name__ == "__main__":
    test_contract_modes(); test_bible_is_loadable(); test_continuity_detects_reverse_years(); test_router_selects_tools(); test_output_modes_and_renderer(); test_character_router_modes()
    print("writing_agent MVP v4.1 contract: 6/6")

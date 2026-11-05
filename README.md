# Bielik Writing Orchestrator for Audioticon

Agentowa warstwa sterująca dla lokalnego modelu Bielik, przeznaczona do pracy z polskim tekstem i reżyserią audiobooków.

To repozytorium nie zawiera modelu Bielik ani jego wag. Jest wrapperem/orchestracją, która dodaje kontrakty JSON, pamięć projektu, walidację i bezpieczny adapter do Audioticonu.

## Zakres

- Writing Agent dla polskiego tekstu;
- tryby `creative`, `factual` i `mixed`;
- `project_bible` z ochroną przed niezatwierdzonym zapisem;
- retry/fallback i detekcja uciętych odpowiedzi;
- `TEXT_ONLY`, `TEXT_WITH_NOTES`, `ANALYSIS_ONLY`, `STRUCTURED_JSON`;
- Audiobook Director w trybie `annotation-only`;
- ochrona tekstu źródłowego po stronie adaptera;
- walidacja segmentów, mówców, emocji, tempa, pitchu i pauz;
- propozycje zawsze pozostają `proposed` do ręcznej akceptacji.

## Architektura

```text
Bielik przez Ollama
        ↓
Writing Agent / Audiobook Director
        ↓
JSON contract
        ↓
validator
        ↓
ręczna akceptacja
        ↓
Audioticon
```

Audioticon jest osobnym projektem i nie jest modyfikowany przez to repozytorium.

## Wymagania

- Python 3.10+;
- Ollama, jeśli używany jest generator Bielik;
- lokalny model `bielik-4.5b-v3:q5` lub inny zgodny model wskazany przez `--model`;
- Audioticon jest opcjonalny i nie jest wymagany do uruchomienia validatora.

## Uruchomienie Writing Agenta

Z katalogu repozytorium:

```bash
python3 -m writing_agent.cli "Napisz krótką scenę spotkania" --mode creative
```

## Testy Audiobook Director

Fixture można zwalidować bez uruchamiania Bielika, TTS, DSP ani Audioticonu:

```bash
python3 benchmark/run_audiobook_director_fixture_v1.py
```

Propozycje Bielika działają w trybie `proposal_only` i wymagają lokalnej Ollamy:

```bash
python3 benchmark/run_audiobook_director_bielik_proposal_v1.py
```

## Zasady bezpieczeństwa

- model nie jest właścicielem tekstu źródłowego;
- odpowiedź JSON nie oznacza automatycznej akceptacji;
- zmiany tekstu są odrzucane przez validator;
- nieznany mówca wymaga pytania do autora;
- renderowanie nie jest uruchamiane automatycznie;
- wagi modelu pozostają poza repozytorium.

## Status v0.1

Projekt jest eksperymentalnym wrapperem dla Bielika. Najlepiej sprawdza się jako narzędzie do polskiego tekstu oraz propozycji reżyserii spokojnych, narracyjnych i szeptanych fragmentów audiobooka. Nie jest nowym checkpointem Bielika ani autonomicznym redaktorem literackim.

## Licencja

MIT. Model Bielik, Ollama i Audioticon podlegają własnym licencjom.

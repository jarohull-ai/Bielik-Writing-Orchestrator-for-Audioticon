# Bielik Writing Orchestrator for Audioticon

Lekki, lokalny wrapper dla modelu Bielik: Writing Agent oraz **Audiobook Director** dla polskiego tekstu. Repozytorium zawiera kontrakty JSON, pamięć projektu, walidatory i adapter do osobnego projektu Audioticon.

To nie jest nowy Bielik, dostrojony checkpoint ani autonomiczny redaktor literacki. Wagi Bielika nie są częścią tego repozytorium.

## Quick Start

Wymagania runtime: Python 3.10+ oraz standardowa biblioteka. Do testów potrzebny jest `pytest` (zob. `requirements-dev.txt`). Ollama i model są potrzebne wyłącznie do generowania propozycji Bielika.

Uruchomienie Writing Agenta:

```bash
python3 -m writing_agent.cli "Napisz krótką scenę spotkania" --mode creative
```

Uruchomienie pełnego zestawu lokalnego testu fixture (bez Bielika, Ollamy, TTS, DSP i Audioticonu):

```bash
python3 -m compileall -q writing_agent benchmark
python3 -m pytest -q
python3 benchmark/run_audiobook_director_fixture_v1.py
```

W środowisku deweloperskim zależność testową można zainstalować poleceniem `python3 -m pip install -r requirements-dev.txt`.

## Known environment issue

Na niektórych środowiskach uruchamianych przez wrapper/harness `git clone` może zakończyć się błędem:

```text
/usr/lib/git-core/git-remote-https: symbol lookup error:
/lib/x86_64-linux-gnu/libcurl-gnutls.so.4: undefined symbol:
nghttp2_option_set_no_rfc9113_leading_and_trailing_ws_validation
```

To konflikt bibliotek dynamicznych środowiska uruchomieniowego: odziedziczone `LD_LIBRARY_PATH` wskazuje pakietowaną wersję `libnghttp2`, która nie pasuje do systemowego `libcurl-gnutls`. Nie jest to problem modelu, wrappera ani zawartości repozytorium.

Bezpieczne, jednorazowe obejście dla samego procesu klonowania:

```bash
env -u LD_LIBRARY_PATH git clone https://github.com/jarohull-ai/Bielik-Writing-Orchestrator-for-Audioticon.git
```

Nie zmienia ono systemowych bibliotek ani skryptów projektu. Po klonowaniu należy uruchomić standardowy test offline z Quick Start. Jeśli `git clone` działa w zwykłym terminalu bez tego błędu, obejście nie jest potrzebne.

## Architecture

```text
source text
    ↓
Bielik proposal (proposal_only / annotation-only)
    ↓
JSON contract
    ↓
validator + text coverage checks
    ↓
manual approval
    ↓
separate Audioticon project
```

Writing Agent obsługuje tryby `creative`, `factual` i `mixed`, kontrakty `TEXT_ONLY`, `TEXT_WITH_NOTES`, `ANALYSIS_ONLY` i `STRUCTURED_JSON`, retry/fallback oraz `project_bible`. Audiobook Director dzieli tekst na segmenty, a Bielik proponuje wyłącznie metadane reżyserii: mówcę, emocję, tempo, pitch, pauzy i cue DSP.

Audioticon pozostaje osobnym projektem i nie jest modyfikowany ani uruchamiany przez validator.

## Safety Model

- Tekst źródłowy jest własnością adaptera; adnotacje nie zawierają pola `text`.
- Każdy wynik modelu ma status `proposed`; JSON nie oznacza akceptacji.
- Validator sprawdza hash, pełne pokrycie, kolejność, mówców, enumy i presety.
- `unknown` wymaga jawnego pytania do autora.
- Zmiana tekstu, nieznane pola i niekanoniczne wartości są odrzucane.
- Renderowanie nie uruchamia się automatycznie.
- Wagi Bielika, blob Ollamy, TTS i pliki audio nie są publikowane.

## Audiobook Director

Fixture można zwalidować offline:

```bash
python3 benchmark/run_audiobook_director_fixture_v1.py
```

Runner sprawdza fixture pozytywny oraz 10 celowo uszkodzonych wariantów. Nie uruchamia Bielika, TTS, DSP ani Audioticonu.

## Running Offline Fixture

Test offline nie wymaga modelu ani Ollamy. Wyniki generowane przez benchmark są artefaktami lokalnymi; repozytorium nie powinno zawierać audio ani wag.

```bash
python3 -m pytest -q
python3 benchmark/run_audiobook_director_fixture_v1.py
```

## Running Bielik Proposal Mode

Tryb propozycji wymaga działającej Ollamy i lokalnego modelu, domyślnie `bielik-4.5b-v3:q5`:

```bash
python3 benchmark/run_audiobook_director_bielik_proposal_v1.py
```

Brak Ollamy lub modelu jest problemem środowiska generatora, a nie testu validatora. Wynik nadal musi przejść walidację i pozostać `proposed`. Nie ma automatycznego przejścia do renderowania.

## Limitations

- Projekt nie modyfikuje wag Bielika i nie dostarcza modelu.
- Bielik jest wyspecjalizowanym polskim reżyserem propozycji audio, szczególnie dla narracji spokojnych, intymnych i szeptanych; nie jest modelem ogólnym.
- Ocena jakości emocji, tempa i głosu wymaga ręcznej decyzji.
- Audioticon nie jest zależnością tego repozytorium.
- Validator nie zastępuje ręcznej akceptacji ani pełnej oceny nagrania.

## Roadmap

### v0.1

- stabilny wrapper Writing Agent;
- Audiobook Director w trybie annotation-only;
- kontrakt, validator i adapter Audioticon;
- offline fixture z testami negatywnymi;
- dokumentacja i jawny model bezpieczeństwa.

### v0.2

- ręcznie zatwierdzone adnotacje;
- lepsze rozpoznawanie narratora;
- metryki jakości oraz profile emocji i tempa;
- bezpieczny pojedynczy render testowy po osobnej akceptacji.

### v0.3

- większy dataset korekt autora;
- porównanie modeli;
- ewentualny trening LoRA dopiero po zebraniu danych.

## Licencja

Kod tego repozytorium jest dostępny na licencji MIT. Model Bielik, Ollama i Audioticon podlegają własnym licencjom i nie są częścią tego wydania.

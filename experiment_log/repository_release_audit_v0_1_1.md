# Audyt wydania v0.1.1

Data: 2026-11-06  
Repozytorium: `jarohull-ai/Bielik-Writing-Orchestrator-for-Audioticon`

## Zakres zmian

Stabilizacja nie zmienia wag Bielika, Writing Agenta, Audiobook Directora ani kodu Audioticonu. Dodano wyłącznie:

- workflow offline GitHub Actions;
- trzy szablony GitHub Issues;
- badge i instrukcje CI w README;
- ten raport audytu.

CI nie uruchamia Ollamy, Bielika, TTS, DSP, Audioticonu ani renderowania audio.

## Testy lokalne

Wynik lokalny:

- `python3 -m compileall -q writing_agent benchmark`: PASS;
- `python3 -m pytest -q`: **18 passed**;
- `python3 benchmark/run_audiobook_director_fixture_v1.py`: **positive=PASS, negative=10/10**.

## GitHub Actions

Workflow: `.github/workflows/ci.yml`  
Run dla commita `de31a5988438b8a551bca3dd912f8b9f2b2ba67a`: **success**  
Run URL: https://github.com/jarohull-ai/Bielik-Writing-Orchestrator-for-Audioticon/actions/runs/42173138432

Pierwszy run ujawnił błąd konfiguracji cache `setup-python`: akcja szukała `requirements.txt` lub `pyproject.toml`. Poprawiono to przez jawne `cache-dependency-path: requirements-dev.txt`. Nie zmieniano kodu aplikacji.

Workflow uruchamia się dla:

- push do `main`;
- pull request do `main`;
- tagów `v*`.

## Świeży klon

Klon wykonano poleceniem:

```bash
env -u LD_LIBRARY_PATH git clone https://github.com/jarohull-ai/Bielik-Writing-Orchestrator-for-Audioticon.git
```

Globalna instalacja przez `python3 -m pip install` była zablokowana przez PEP 668 (`externally-managed-environment`). Nie użyto `--break-system-packages`; utworzono izolowane `.venv` i zainstalowano `requirements-dev.txt` w tym środowisku.

Wynik świeżego klonu:

- instalacja dependencies w `.venv`: PASS;
- kompilacja: PASS;
- pytest: **18 passed**;
- fixture: **PASS**;
- przypadki negatywne: **10/10**;
- skan sekretów, prywatnych ścieżek, wag, blobów i audio: PASS.

Problem `libcurl/libnghttp2` pozostaje udokumentowany w README; obejście `env -u LD_LIBRARY_PATH` nie zmienia systemowych bibliotek.

## Branch protection

`main` jest chroniona:

- wymagany pull request: **1 review**;
- wymagany status CI: `Compile, pytest and offline fixture`;
- wymagane aktualne testy przed merge: **tak**;
- enforce administrators: **tak**;
- force push: **wyłączony**;
- usuwanie `main`: **wyłączone**.

## Audyt publikacji

Potwierdzono brak:

- wag Bielika;
- blobów Ollama;
- plików audio;
- sekretów i prywatnych ścieżek;
- danych użytkownika;
- kodu Audioticonu.

README zawiera niezależny link do projektu Audioticon oraz wyjaśnia, że wynik Bielika pozostaje `proposed`, validator jest obowiązkową bramką, a renderowanie nie uruchamia się automatycznie.

## Decyzja

**READY_FOR_TAG** po udanym runie CI dla commita na `main` i po potwierdzeniu runu CI dla tagu `v0.1.1`.

Tag i release zostaną utworzone dopiero po spełnieniu obu warunków.

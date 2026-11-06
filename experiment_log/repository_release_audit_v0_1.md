# Audyt wydania repozytorium v0.1

Data audytu: 2026-11-06  
Repozytorium: `jarohull-ai/Bielik-Writing-Orchestrator-for-Audioticon`  
Commit zdalny audytowany z gałęzi `main`: `7a18442095e540ad0766457701cd8e2de5a3c3fb`

## Zakres

Audyt obejmował świeży eksport gałęzi `main`, zawartość repozytorium, dokumentację, reguły ignorowania plików, skany prywatnych artefaktów oraz testy offline. Standardowy `git clone` na tej maszynie zatrzymał się przed pobraniem na błędzie systemowej biblioteki `libcurl-gnutls`; do audytu użyto równoważnego archiwum źródłowego GitHub dla aktualnego commita z API. Nie modyfikowano wag Bielika ani kodu Audioticonu. Nie tworzono taga ani release’u.

README, `.gitignore`, `requirements-dev.txt` i ten raport należą do audytowanego zestawu release’owego na gałęzi `main`.

## Wyniki audytu zawartości

| Kontrola | Wynik |
|---|---|
| Wagi/model blobs (`gguf`, `safetensors`, `onnx`, `bin`, `blob`) | PASS — brak |
| Audio (`mp3`, `wav`, `m4b`, `ogg`, `flac`, `opus`) | PASS — brak |
| Prywatne ścieżki i dane lokalne | PASS — brak wykrytych absolutnych ścieżek użytkownika |
| Klucze, tokeny i sekrety | PASS — brak wykrytych wzorców |
| Licencja | PASS — `LICENSE`, MIT |
| `.gitignore` | PASS — wyklucza środowiska, cache, modele i audio; raporty Markdown pozostają możliwe do publikacji |
| Rozdzielenie Audioticonu | PASS — osobny projekt, brak jego kodu w repozytorium |
| Spójność zakresu | PASS — wrapper, Writing Agent, Audiobook Director, validator i adapter |

README został uporządkowany o sekcje Quick Start, Architecture, Safety Model, Audiobook Director, Running Offline Fixture, Running Bielik Proposal Mode, Limitations, Roadmap i License. Dodano `requirements-dev.txt` z jedyną zależnością testową `pytest`. Dokumentacja nie przedstawia projektu jako nowego modelu, autonomicznego redaktora ani systemu bez nadzoru.

## Diagnostyka świeżego klonu

Środowisko audytu:

- Git `2.43.0`;
- glibc `2.39`;
- systemowy `libcurl-gnutls.so.4`;
- systemowy `libnghttp2.so.14` dostarcza wymagany symbol;
- `git-lfs` nie jest wymagany i nie jest używany przez drzewo repozytorium.

Pierwsza próba zwykłego klonu odtworzyła błąd:

```text
/usr/lib/git-core/git-remote-https: symbol lookup error:
/lib/x86_64-linux-gnu/libcurl-gnutls.so.4: undefined symbol:
nghttp2_option_set_no_rfc9113_leading_and_trailing_ws_validation
```

Diagnoza `ldd` wykazała, że odziedziczone `LD_LIBRARY_PATH` kierowało loader do pakietowanej przez harness wersji `libnghttp2.so.14`, niezgodnej z systemowym `libcurl-gnutls`. Po usunięciu tej zmiennej wyłącznie dla procesu Git:

```bash
env -u LD_LIBRARY_PATH git clone https://github.com/jarohull-ai/Bielik-Writing-Orchestrator-for-Audioticon.git
```

klon zakończył się kodem `0`. Obejście nie modyfikuje systemu, repozytorium ani skryptów projektu i zostało opisane w README. Nie wykryto Git LFS ani plików wymagających LFS.

## Testy z czystego checkoutu

Wykonane polecenia:

```bash
python3 -m compileall -q writing_agent benchmark
python3 -m pytest -q
python3 benchmark/run_audiobook_director_fixture_v1.py
```

Wynik po świeżym klonie wykonanym powyższym, udokumentowanym obejściem:

- `compileall`: PASS;
- `pytest`: **18 passed**;
- fixture pozytywny: **PASS**;
- fixture negatywny: **10/10** wykrytych uszkodzeń;
- TTS, DSP i Audioticon: **0 uruchomień** podczas testu offline;
- Bielik/Ollama: **0 użyć** podczas testu fixture.

## Testy zależne od modelu

`benchmark/run_audiobook_director_bielik_proposal_v1.py` jest runnerem zależnym od działającej Ollamy i lokalnego modelu. Nie traktuję jego niewykonania jako awarii validatora. README rozdziela ten tryb od gwarantowanego testu offline.

## Zmiany w tej stabilizacji

1. Rozszerzono README o instrukcję uruchomienia, architekturę, ograniczenia, bezpieczeństwo i roadmapę.
2. Doprecyzowano `.gitignore`, aby blokował lokalne artefakty modeli/audio, ale nie ukrywał raportów Markdown.
3. Dodano `requirements-dev.txt` dla powtarzalnego uruchamiania testów.
4. Dodano ten raport audytu.

Nie zmieniano kodu produkcyjnego, kontraktów, validatora, wag Bielika ani Audioticonu.

## Ocena v0.1

**READY_FOR_TAG.** Testy offline, fixture, skany zawartości i świeży klon przeszły po jawnym, bezpiecznym obejściu problemu loadera bibliotek. Obejście nie zmienia kodu projektu ani systemu. Pozostaje tylko osobne potwierdzenie właściciela repozytorium przed utworzeniem taga oraz ewentualne uruchomienie testu propozycji Bielika w środowisku z Ollamą.

Propozycja taga: `v0.1.0`. Tag i release **nie zostały utworzone**.

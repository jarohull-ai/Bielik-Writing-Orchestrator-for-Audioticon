# Changelog

## [v0.1.1] — 2026-11-06

Stabilizacja repozytorium i powtarzalności testów.

- dodano deterministyczny GitHub Actions workflow dla `compileall`, `pytest` i offline fixture;
- CI uruchamia się dla pushy do `main`, pull requestów oraz tagów `v*`;
- dodano cache zależności developerskich przez `requirements-dev.txt`;
- dodano szablony zgłoszeń: bug, regression i feature request;
- README zawiera status CI, instrukcję testów i procedurę zgłaszania regresji;
- dodano raport audytu release `v0.1.1`;
- włączono ochronę gałęzi `main` z wymaganym PR i statusem CI;
- potwierdzono test offline: `18 passed`, fixture PASS, przypadki negatywne `10/10`;
- nie dodano wag Bielika, blobów Ollama, audio ani kodu Audioticonu.

## [v0.1.0] — 2026-11-06

Pierwsze publiczne wydanie wrappera Bielika dla Writing Agent i Audiobook Director.

- kontrakty JSON i validator;
- tryb annotation-only dla propozycji reżyserii audiobooka;
- ochrona tekstu źródłowego po stronie adaptera;
- offline fixture z 10 testami negatywnymi;
- dokumentacja architektury, bezpieczeństwa i ograniczeń.

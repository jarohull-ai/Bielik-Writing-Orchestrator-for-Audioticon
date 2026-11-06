# Changelog

## Unreleased

- dodano eksperymentalny profil `granite4:3b` dla Audiobook Director w trybie annotation-only;
- dodano porównawczy runner holdoutu 120 scen, retry/fallback i raport Granite’a;
- nie zmieniono wag, wspólnego validatora ani kodu Audioticonu.

## [v0.2.0] — 2026-11-06

Audiobook Director v0.2 — rozszerzona walidacja annotation-only.

- dodano holdout 120 polskich scen w 12 kategoriach;
- dodano automatyczny runner, wyniki JSON i raport diagnostyczny;
- poprawiono deterministyczne dzielenie scen wielomówcowych;
- dodano segment-scoped pytania autora dla \`unknown\`;
- potwierdzono \`120/120\` poprawnego JSON i przejść validatora;
- potwierdzono zachowanie tekstu \`120/120\`, narrator \`60/60\` i unknown \`10/10\`;
- wszystkie wyniki pozostają \`proposed\`, bez auto-accept i renderowania;
- nie dodano wag Bielika, TTS, DSP ani kodu Audioticonu.

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

# Release v0.3.1 — audyt

## Zakres

Audyt obejmuje PR #6 i wspólny interfejs profili `bielik` oraz `granite4-3b`.
Bazą jest release `v0.3.0`, commit `56ddee5f07285eda8a30b7bbe25484ea208090ef`.

## Wyniki lokalne

- `compileall`: PASS;
- `pytest`: 30 passed;
- fixture v1: PASS;
- przypadki negatywne: 10/10;
- Bielik holdout: 120/120 JSON, 120/120 validator, 120/120 tekst;
- Granite holdout: 119/120 JSON, 119/120 validator, 120/120 tekst;
- akceptacja poprawnej propozycji: PASS;
- blokada zmienionego tekstu/hash’a: PASS;
- blokada niedozwolonych przejść: PASS;
- historia decyzji: PASS.

## Bezpieczeństwo

Każda propozycja rozpoczyna jako `proposed`. `approved` może powstać wyłącznie
po ręcznym wywołaniu akceptacji, notatce recenzenta i ponownej walidacji. Nie ma
automatycznego renderowania ani auto-accept.

Nie zmieniono wag, validatora ani kodu Audioticonu. TTS, DSP i Audioticon nie
były uruchamiane w testach. Nie wykonano renderu przed publikacją release’u.

## CI i publikacja

- PR #6: CI PASS;
- merge: oczekuje na wymagane review GitHub;
- tag `v0.3.1`: nieutworzony przed scaleniem;
- GitHub Release: nieutworzony przed scaleniem.

Po scaleniu należy ponownie sprawdzić `main`, utworzyć tag, poczekać na CI taga,
a następnie utworzyć release. Dopiero później można przejść do jednej ręcznie
zatwierdzonej sceny i pojedynczego renderu.

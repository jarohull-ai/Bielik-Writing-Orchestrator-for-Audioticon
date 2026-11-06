# Audiobook Director v0.3.1 — wspólny interfejs profili

## Zakres

Wersja v0.3.1 bazuje na zamrożonym release `v0.3.0` (`56ddee5`) i dodaje
model-agnostyczną kopertę propozycji oraz ręczny workflow review dla profili:

- `bielik` — profil rekomendowany;
- `granite4-3b` — profil bezpieczny, eksperymentalny, słabszy w dialogach i pauzach.

Nie zmieniono wag, validatora, tekstu źródłowego ani kodu Audioticonu. Nie
uruchamiano TTS, DSP, Audioticonu ani renderowania.

## Wspólny kontrakt

Każda propozycja ma `proposal_id`, `profile`, `status`, `source_text_hash`,
`segments`, `validation`, `created_at`, `reviewed_at`, `reviewer_note`, historię
decyzji oraz `accepted_for_render=false`.

Dozwolone są wyłącznie przejścia wykonane ręcznie przez użytkownika:

```text
proposed → approved
proposed → rejected
```

Akceptacja wykonuje ponowną walidację hasha, pokrycia, mówców, enumów i pytań
autora. Zmieniony tekst, nieaktualny hash lub błąd validatora blokują akceptację.
Status `approved` nie uruchamia renderowania.

## Wyniki pełnego holdoutu v0.2

Wspólny holdout obejmuje 120 scen. Poniższe dane pochodzą z pełnych artefaktów
profili z baseline’u v0.3.0 i zostały sprawdzone po dodaniu interfejsu.

| Metryka | Bielik | Granite 4 3B |
|---|---:|---:|
| JSON | 120/120 | 119/120 |
| Validator | 120/120 | 119/120 |
| Tekst źródłowy | 120/120 | 120/120 |
| Narrator | 60/60 | 60/60 |
| Znani mówcy | 89/89 | 87/89 |
| Unknown | 10/10 | 10/10 |
| Pytania autora | 10/10 | 10/10 |
| Pauzy | 138/159 | 74/157 |
| Retry | 0 | 2 |
| FAIL | 0 | 1 |
| Automatyczny render | 0 | 0 |
| Auto-accept | 0 | 0 |

## Testy v0.3.1

- `compileall`: PASS;
- `pytest`: 30 passed;
- fixture v1: PASS;
- przypadki negatywne: 10/10;
- akceptacja poprawnej propozycji: PASS;
- odrzucenie błędnej propozycji: PASS;
- blokada zmienionego tekstu i hasha: PASS;
- blokada niedozwolonych przejść: PASS;
- TTS/DSP/Audioticon: 0 uruchomień.

## Rekomendacja

Bielik pozostaje profilem rekomendowanym. Granite może służyć jako alternatywny
profil dla ostrożnych propozycji narracyjnych, ale nie ma przewagi w dialogach
ani pauzach. Żaden profil nie powinien zatwierdzać propozycji ani uruchamiać
renderowania bez ręcznej decyzji użytkownika.

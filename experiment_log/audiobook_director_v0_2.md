# Audiobook Director v0.2 — rozszerzona walidacja Bielika

Przypadki: **120**
PASS: **60**, WARN: **60**, FAIL: **0**

## Metryki

| Metryka | Wynik |
|---|---:|
| valid_json | 120/120 |
| validator_pass | 120/120 |
| text_preservation | 120/120 |
| narrator_assignment | 60/60 |
| known_speaker_assignment | 89/89 |
| unknown_speaker_usage | 10/10 |
| author_question_completeness | 10/10 |
| emotion_accuracy | 109/159 |
| pace_accuracy | 109/159 |
| pause_accuracy | 138/159 |
| metakomentarze | 0 |
| odrzucone propozycje | 0 |
| automatyczne rendery | 0 |

## Wyniki kategorii

| Kategoria | N | PASS | WARN | FAIL | Validator | Tekst |
|---|---:|---:|---:|---:|---:|---:|
| Narracja | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Spokojna narracja | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Szept i intymny ton | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Pauzy krótkie i długie | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Emocje i tempo | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Jednoznaczny dialog | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Narracja do dialogu | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Dialog do narracji | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Wielu mówców | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Nieznany mówca | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Ton Styl Uwagi jako treść | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Polskie znaki i interpunkcja | 10 | 10 | 0 | 0 | 10/10 | 10/10 |

## Najczęstsze błędy


## Najlepsze przykłady

- `v02_dialogue_to_narration_01` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_02` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_03` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_04` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_05` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_06` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_07` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_08` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_09` — PASS, score `1.0`, Dialog do narracji
- `v02_dialogue_to_narration_10` — PASS, score `1.0`, Dialog do narracji

## Najsłabsze przykłady


## Analiza pierwotnych FAIL-i

Przed poprawką v0.2: 10 FAIL, 110/120 przejść validatora, 9/10 kompletnych pytań autora.

- v02_polish_punctuation_02, v02_polish_punctuation_03, v02_polish_punctuation_04, v02_polish_punctuation_05, v02_polish_punctuation_06, v02_polish_punctuation_07, v02_polish_punctuation_08, v02_polish_punctuation_09, v02_polish_punctuation_10 — przyczyna: brak podziału przy zmianie mówcy; jeden segment zawierał kwestie Anny i Marka, a Bielik zwracał duplikat segment_001 albo drugiego mówcę w tym samym segmencie; poprawka: deterministyczny segmenter rozpoznaje atrybucję Anna/Marek po granicy zdania; tekst pozostaje źródłem adaptera; wynik: naprawione; 9/9 przechodzi validator.
- v02_unknown_speaker_09 — przyczyna: speaker=unknown bez pytania zawierającego identyfikator segmentu; poprawka: adapter dopisuje wyłącznie segment-scoped question; nie zgaduje mówcy i zapisuje ostrzeżenie adaptera; wynik: naprawione; pytanie autora 10/10.

Żaden przypadek nie został przepuszczony przez rozluźnienie validatora ani zgadywanie mówcy.

- `v02_pauses_10` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_09` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_08` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_07` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_06` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_05` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_04` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_03` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_02` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej
- `v02_pauses_01` — WARN, score `0.75`, rozbieżność artystyczna do oceny ręcznej

## Porównanie z v1

v1: **11/11** poprawnego JSON, **7/11** przejść validatora; v0.2: **120/120** poprawnego JSON, **120/120** przejść validatora. Zakresy są różne: v1 obejmuje fixture + 10 przypadków, v0.2 obejmuje 120 scen w 12 rodzinach, więc wyników nie należy traktować jako równoważnego benchmarku.

## Rekomendacja

Bielik nadaje się do konserwatywnych propozycji metadanych dla narracji spokojnej, intymnej i szeptanej oraz do ostrożnego przypisywania narracji do `narrator`. Nadal nie powinien samodzielnie zatwierdzać mówców, zmieniać tekstu, uruchamiać renderowania, prowadzić pełnej reżyserii dialogów ani zastępować ręcznej decyzji autora.

Audioticon, TTS i DSP nie były uruchamiane. Wszystkie wyniki pozostają `proposed`; `accepted_for_render=false`. Wagi Bielika nie były modyfikowane.

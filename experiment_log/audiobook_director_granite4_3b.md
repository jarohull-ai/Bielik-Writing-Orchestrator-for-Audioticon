# Granite 4 3B — Audiobook Director v0.2

Profil działa wyłącznie w trybie `annotation-only` / `proposal_only`. Tekst źródłowy pozostaje własnością adaptera.

Model: `granite4:3b`  
Przypadki: **120**  
PASS: **39**, WARN: **80**, FAIL: **1**

## Metryki

| Metryka | Granite 4 3B | Bielik v0.2 |
|---|---:|---:|
| Poprawny JSON | 119/120 | 120/120 |
| Validator | 119/120 | 120/120 |
| Zachowanie tekstu | 120/120 | 120/120 |
| Narrator | 60/60 | 60/60 |
| Znani mówcy | 87/89 | 89/89 |
| Unknown | 10/10 | 10/10 |
| Pytania autora | 10/10 | 10/10 |
| Emocje | 100/157 | 109/159 |
| Tempo | 108/157 | 109/159 |
| Pauzy | 74/157 | 138/159 |

## Operacyjnie

- Łączna liczba retry: **2**.
- Średni czas odpowiedzi Ollamy: **2520624158 ns** według metadanych modelu.
- Automatyczne rendery: **0**; auto-accept: **0**.
- TTS, DSP i Audioticon: **nieuruchamiane**.
- Wagi Granite’a i Bielika: **niemodyfikowane**.

## Wyniki według kategorii

| Kategoria | N | PASS | WARN | FAIL | Validator | Narrator |
|---|---:|---:|---:|---:|---:|---:|
| Narracja | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Spokojna narracja | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Szept i intymny ton | 10 | 0 | 10 | 0 | 10/10 | 0/0 |
| Pauzy krótkie i długie | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Emocje i tempo | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Jednoznaczny dialog | 10 | 0 | 10 | 0 | 10/10 | 0/0 |
| Narracja do dialogu | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Dialog do narracji | 10 | 10 | 0 | 0 | 10/10 | 0/0 |
| Wielu mówców | 10 | 0 | 10 | 0 | 10/10 | 0/0 |
| Nieznany mówca | 10 | 0 | 10 | 0 | 10/10 | 0/0 |
| Ton Styl Uwagi jako treść | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Polskie znaki i interpunkcja | 10 | 9 | 0 | 1 | 9/10 | 0/0 |

## Najczęstsze błędy

- `dialog przypisany niewłaściwemu mówcy`: **1**

## Przypadki wymagające uwagi

- `v02_polish_punctuation_05` — FAIL; retry: 2; błędy: speaker_mismatch:segment_001:expected_Anna

## Rekomendacja

Na tym holdoucie Granite nie przewyższa Bielika: ma jeden FAIL, 87/89 znanych mówców zamiast 89/89 oraz słabsze pauzy (74/157 vs 138/159). Pozostaje profilem eksperymentalnym dla narracji; nie zastępuje Bielika w dialogach.

Granite 4 3B oceniono na identycznym holdoucie i przez ten sam validator. Ten raport mierzy kontrakt i zgodność adnotacji, nie jakość artystyczną.

Wszystkie propozycje pozostają `proposed` i wymagają ręcznej akceptacji.

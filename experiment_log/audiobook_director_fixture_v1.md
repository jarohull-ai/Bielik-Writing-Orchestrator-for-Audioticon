# Audiobook Director — ręcznie zatwierdzony fixture v1

Pozytywny fixture: **PASS**
Przypadki negatywne: **10/10**

Audioticon, TTS, DSP i Bielik nie były uruchamiane. Repozytorium Audioticonu nie było modyfikowane. Wagi Bielika nie były używane ani zmieniane.

## Źródłowy tekst

```text
Na końcu korytarza paliła się latarnia. Ton głosu narratora był spokojny, a słowo Styl pojawiło się w notatce; Uwagi należały do autora.

— Słyszysz to? — zapytała Anna.

Zza drzwi dobiegł metaliczny trzask.

— Biegnij! — krzyknął Marek.

— Nie otwierajcie... — powiedział nieznajomy.
```

## Ręcznie zatwierdzony JSON

```json
{
  "project_id": "audioticon-test",
  "scene_id": "corridor-lantern-01",
  "source_text_hash": "10e3f95c3776b0916e95d7db43d3c52b694cb442c42f53349cf97df8dd8ee9bd",
  "status": "approved_fixture",
  "segments": [
    {
      "index": 0,
      "speaker": "narrator",
      "text": "Na końcu korytarza paliła się latarnia. Ton głosu narratora był spokojny, a słowo Styl pojawiło się w notatce; Uwagi należały do autora.",
      "voice": "pl_PL-darkman-medium",
      "emotion": "calm",
      "pace": "normal",
      "pitch": "normal",
      "pause_before_ms": 0,
      "pause_after_ms": 400,
      "sound_cues": []
    },
    {
      "index": 1,
      "speaker": "Anna",
      "text": "— Słyszysz to? — zapytała Anna.",
      "voice": "pl-PL-ZofiaNeural",
      "emotion": "fear",
      "pace": "normal",
      "pitch": "high",
      "pause_before_ms": 400,
      "pause_after_ms": 400,
      "sound_cues": []
    },
    {
      "index": 2,
      "speaker": "narrator",
      "text": "Zza drzwi dobiegł metaliczny trzask.",
      "voice": "pl_PL-darkman-medium",
      "emotion": "tension",
      "pace": "slow",
      "pitch": "low",
      "pause_before_ms": 400,
      "pause_after_ms": 900,
      "sound_cues": [
        {
          "type": "dsp_preset",
          "name": "cathedral:kaplica"
        }
      ]
    },
    {
      "index": 3,
      "speaker": "Marek",
      "text": "— Biegnij! — krzyknął Marek.",
      "voice": "pl-PL-MarekNeural",
      "emotion": "anger",
      "pace": "fast",
      "pitch": "high",
      "pause_before_ms": 0,
      "pause_after_ms": 900,
      "sound_cues": [
        {
          "type": "dsp_preset",
          "name": "radio:wojskowe"
        }
      ]
    },
    {
      "index": 4,
      "speaker": "unknown",
      "text": "— Nie otwierajcie... — powiedział nieznajomy.",
      "voice": "pl_PL-darkman-medium",
      "emotion": "whisper",
      "pace": "slow",
      "pitch": "low",
      "pause_before_ms": 900,
      "pause_after_ms": 900,
      "sound_cues": [
        {
          "type": "dsp_preset",
          "name": "whisper:intymny"
        }
      ]
    }
  ],
  "open_questions": [
    "segment_4: wskaż postać mówiącą tę kwestię"
  ],
  "warnings": [
    "Fixture zatwierdzony ręcznie wyłącznie jako dane testowe; nie jest zgodą na renderowanie."
  ]
}
```

## Decyzje negatywne

- `missing_segment`: PASS — odrzucono; `segment_text_does_not_cover_source, segment_2:invalid_index, segment_3:invalid_index`
- `changed_word`: PASS — odrzucono; `segment_text_does_not_cover_source`
- `changed_punctuation`: PASS — odrzucono; `segment_text_does_not_cover_source`
- `reordered_segments`: PASS — odrzucono; `segment_text_does_not_cover_source, segment_0:invalid_index, segment_1:invalid_index`
- `bad_hash`: PASS — odrzucono; `source_hash_mismatch`
- `unknown_speaker`: PASS — odrzucono; `segment_4:unknown_speaker_id`
- `unknown_preset`: PASS — odrzucono; `segment_2:invalid_dsp_preset`
- `approved_model_status`: PASS — odrzucono; `unapproved_status`
- `extra_text`: PASS — odrzucono; `segment_text_does_not_cover_source`
- `missing_author_question`: PASS — odrzucono; `segment_4:missing_author_question`

## Eksport adaptera

```text
[narrator] Na końcu korytarza paliła się latarnia. Ton głosu narratora był spokojny, a słowo Styl pojawiło się w notatce; Uwagi należały do autora. ⏸️
📉 ⏸️ [Anna] — Słyszysz to? — zapytała Anna. ⏸️
🐢 📈 ⏸️ [narrator] Zza drzwi dobiegł metaliczny trzask. 🛑
🐇 [Marek] — Biegnij! — krzyknął Marek. 🛑
🐢 🤫 🛑 [unknown] — Nie otwierajcie... — powiedział nieznajomy. 🛑
```

Fixture ma status `approved_fixture`, który oznacza zatwierdzenie danych testowych przez człowieka. Status `approved` pozostaje zabroniony dla wyniku modelu.

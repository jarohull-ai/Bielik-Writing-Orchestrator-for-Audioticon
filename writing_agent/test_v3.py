import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import writing_agent.ollama_agent as agent
from writing_agent.contract import classify_request
from writing_agent.project_store import commit_change

def fake_data(text):
    return ({"message":{"content":text},"eval_duration":1,"eval_count":1}, text)

def test_retry_sequence():
    for _ in range(10):
        calls=[]
        def fake(*args, **kwargs):
            calls.append(1)
            return fake_data("" if len(calls) < 3 else "Gotowy tekst.")
        with patch.object(agent, "_call", side_effect=fake):
            result=agent.generate("Napisz scenę", seed=7)
        assert result["answer"] == "Gotowy tekst." and len(result["attempts"]) == 3 and not result["fallback"]

def test_empty_fallback():
    for _ in range(10):
        with patch.object(agent, "_call", return_value=fake_data("")):
            result=agent.generate("Napisz scenę", seed=7)
        assert result["fallback"] and result["answer"].startswith("Błąd techniczny") and len(result["attempts"]) == 3

def test_bible_requires_author_and_source():
    for i in range(10):
        with tempfile.TemporaryDirectory() as tmp:
            with open(Path(tmp)/"characters.json","w") as f: json.dump({"version":1},f)
            try:
                commit_change(tmp,"characters.json",{"characters":[]},"test")
                raise AssertionError("commit without approval should fail")
            except PermissionError: pass
            try:
                commit_change(tmp,"characters.json",{"characters":[]},"test",True)
                raise AssertionError("commit without source should fail")
            except ValueError: pass
            commit_change(tmp,"characters.json",{"characters":[]},"test",True,"author")

def test_analysis_contracts():
    prompts=["Zinterpretuj metaforę", "Wyjaśnij podtekst", "Sprawdź ciągłość wieku", "Oceń symbol", "Podaj interpretację sceny", "Zinterpretuj ciszę", "Wyjaśnij znaczenie obrazu", "Omów podtekst dialogu", "Zinterpretuj relację", "Wyjaśnij metaforę"]
    assert all(classify_request(p).output_mode == "ANALYSIS_ONLY" for p in prompts)

if __name__ == "__main__":
    test_retry_sequence(); test_empty_fallback(); test_bible_requires_author_and_source(); test_analysis_contracts()
    print("writing_agent v3: retry 10/10, fallback 10/10, bible 10/10, analysis 10/10")

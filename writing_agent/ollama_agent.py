import json
import re
from urllib.request import Request, urlopen

from .router import route_request
from .tools import load_bible
from .post_renderer import render

CREATIVE_SYSTEM = (
    "Jesteś polskim agentem pisarskim. Odpowiadaj konkretnie i zwięźle. "
    "W trybie kreatywnym możesz wymyślać elementy fikcji, ale nie zmieniaj po cichu ustaleń biblii projektu. "
    "Oddziel tekst od krótkich uwag redakcyjnych. Zachowaj głos autora."
)
WRITING_SYSTEM = (
    "Dla dialogu nadaj postaciom różne głosy, pokazuj reakcje i podtekst, ogranicz ekspozycję. "
    "Dla scen używaj kilku konkretnych szczegółów zmysłowych, działania, miejsca i punktu widzenia; "
    "nie dodawaj przypadkowych postaci, faktów świata ani ozdobników bez funkcji. "
    "Nowe elementy fikcji traktuj jako propozycje, nie jako zatwierdzone fakty biblii."
)
FACTUAL_SYSTEM = (
    "Jesteś polskim agentem pisarskim w trybie faktograficznym. "
    "Nie przedstawiaj hipotez jako faktów. Bez evidence zaznacz brak potwierdzenia. "
    "Konflikt źródeł zgłoś zamiast wybierać arbitralnie. Odpowiadaj zwięźle."
)
ANALYSIS_SYSTEM = (
    "Jesteś polskim analitykiem tekstu. Analizuj znaczenie, metafory, podtekst i spójność. "
    "Nie dopisuj scen, postaci ani wydarzeń. Wyraźnie oddziel interpretację od faktu i zaznacz niepewność. "
    "Zwróć JSON: observation, interpretation, confidence (high|medium|low), inference (true|false). Odpowiadaj konkretnie."
)

def _analysis_contract(answer: str) -> str:
    text = answer.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict) and {"observation", "interpretation", "confidence", "inference"} <= set(value):
            return json.dumps(value, ensure_ascii=False)
    except json.JSONDecodeError:
        pass
    return json.dumps({"observation": text, "interpretation": text, "confidence": "low", "inference": True}, ensure_ascii=False)

def _call(model, system, user, seed, temperature, num_predict):
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "stream": False,
               "options": {"temperature": temperature, "seed": seed, "num_predict": num_predict, "stop": ["<|im_start|>", "<|im_end|>"]}}
    req = Request("http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=180) as response:
        data = json.loads(response.read())
    return data, data.get("message", {}).get("content", "").strip()

def generate(prompt: str, model: str = "bielik-4.5b-v3:q5", mode: str | None = None,
             seed: int = 42, num_predict: int = 256, bible_root=None) -> dict:
    routed = route_request(prompt, mode)
    if routed["tool"] != "model_generation":
        result = routed.get("result", {})
        answer = result.get("text") if isinstance(result, dict) else str(result)
        if not answer:
            answer = json.dumps(result, ensure_ascii=False)
        if routed["output_mode"] == "ANALYSIS_ONLY":
            answer = _analysis_contract(answer)
        return {**routed, "answer": answer, "attempts": [], "fallback": False}
    if routed["output_mode"] == "ANALYSIS_ONLY":
        system = ANALYSIS_SYSTEM
    else:
        system = FACTUAL_SYSTEM if routed["mode"] == "factual" else CREATIVE_SYSTEM
    if routed["output_mode"] == "TEXT_ONLY":
        system += " Zwróć wyłącznie gotowy tekst dla autora. Nie dodawaj nagłówków, metakomentarzy, analizy, opisu stylu ani uwag. Nie opisuj, co zrobiłeś. Zacznij od właściwej treści."
        if routed["intent"] in {"create", "expand", "rewrite", "shorten", "edit"}:
            system += " " + WRITING_SYSTEM
    if routed.get("result", {}).get("requested_tool") == "character_designer":
        system += " Zwróć wyłącznie poprawny JSON z polami: name, goal, fear, motivation, relationships, arc, voice, status=proposed. Nie traktuj całej prośby jako imienia."
    context = json.dumps(load_bible(bible_root), ensure_ascii=False)
    user = (f"Intencja: {routed['intent']}\nTryb: {routed['mode']}\n"
            f"Biblia projektu (ustalenia są nadrzędne): {context}\n\nProśba autora:\n{prompt}")
    attempts=[]; answer=""; data={}
    text_limit = max(num_predict, 512)
    prompts=[(user,0.1,text_limit,"initial"),(user,0.1,min(text_limit*2,1024),"retry_same_prompt"),
             (f"Odpowiedz krótko i bez wstępu.\n{prompt}",0.0,max(96,num_predict//2),"retry_short_prompt")]
    for attempt,(attempt_user,temp,limit,reason) in enumerate(prompts):
        try:
            data, answer = _call(model, system, attempt_user, seed, temp, limit)
        except Exception as exc:
            attempts.append({"attempt":attempt,"temperature":temp,"reason":reason,"error":f"{type(exc).__name__}: {exc}"})
            continue
        truncated = data.get("done_reason") == "length"
        attempts.append({"attempt":attempt,"temperature":temp,"num_predict":limit,"reason":reason,"empty":not bool(answer),"truncated":truncated})
        if answer and not truncated: break
    fallback = not bool(answer)
    if fallback:
        answer = "Błąd techniczny: model nie zwrócił odpowiedzi po dwóch ponowieniach."
    rendered = render(answer, routed["output_mode"])
    if routed["output_mode"] == "TEXT_ONLY" and not rendered.text:
        fallback = True
        rendered = render("Błąd techniczny: odpowiedź zawierała wyłącznie metakomentarz.", "TEXT_ONLY")
    final_text = _analysis_contract(rendered.text) if routed["output_mode"] == "ANALYSIS_ONLY" and not fallback else rendered.text
    return {"intent": routed["intent"], "mode": routed["mode"], "output_mode": routed["output_mode"], "tool": "model_generation",
            "answer": final_text, "render": rendered.__dict__, "attempts": attempts, "fallback": fallback,
            "eval_duration_ns": data.get("eval_duration", 0), "eval_count": data.get("eval_count", 0)}

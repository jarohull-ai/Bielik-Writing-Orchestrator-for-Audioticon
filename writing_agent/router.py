from .contract import RequestContract, classify_request
from .tools import character_designer, continuity_checker, style_editor, load_bible
from .input_validator import validate_input

def route_request(text: str, mode: str | None = None) -> dict:
    contract: RequestContract = classify_request(text, mode)  # type: ignore[arg-type]
    input_check = validate_input(contract.intent, text)
    if not input_check.valid:
        return {"intent": contract.intent, "mode": contract.mode, "output_mode": "TEXT_ONLY",
                "tool": "input_validator", "confidence": 1.0, "result": {"text": input_check.clarification},
                "input_valid": False}
    if contract.intent in {"shorten", "rewrite", "edit"}:
        tool = "model_generation"
        result = {"requested_tool": "style_editor", "operation": contract.intent}
    elif contract.intent == "check_continuity":
        tool = "continuity_checker"
        result = continuity_checker(text, load_bible())
    elif "postać" in text.lower() or "bohater" in text.lower() or "antagonist" in text.lower():
        low = text.lower()
        operation = "character_expand" if any(k in low for k in ("istniejącą postać", "z biblii", "rozwiń tę postać")) else "character_new"
        if ":" in text and text.split(":", 1)[1].strip():
            tool = "character_designer"
            result = character_designer(text.split(":", 1)[1].strip(), operation=operation)
            result["operation"] = operation
        else:
            tool = "model_generation"
            result = {"requested_tool": "character_designer", "operation": operation}
    else:
        tool = "model_generation"
        result = {"prompt": text, "bible": load_bible(), "mode": contract.mode}
    output_mode = "STRUCTURED_JSON" if tool == "character_designer" or result.get("requested_tool") == "character_designer" else contract.output_mode
    if contract.intent == "check_continuity" and tool != "model_generation":
        output_mode = "STRUCTURED_JSON"
    return {"intent": contract.intent, "mode": contract.mode, "output_mode": output_mode,
            "tool": tool, "confidence": contract.confidence, "result": result}

import argparse, json
from .ollama_agent import generate

def main():
    ap = argparse.ArgumentParser(description="Lokalny polski Writing Agent")
    ap.add_argument("prompt")
    ap.add_argument("--mode", choices=["creative", "factual", "mixed"])
    ap.add_argument("--model", default="bielik-4.5b-v3:q5")
    args = ap.parse_args()
    print(json.dumps(generate(args.prompt, model=args.model, mode=args.mode), ensure_ascii=False, indent=2))

if __name__ == "__main__": main()

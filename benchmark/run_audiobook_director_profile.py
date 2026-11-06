#!/usr/bin/env python3
"""Common profile entry point for one annotation-only proposal."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from writing_agent.audiobook_proposals import available_profiles, propose_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=available_profiles(), required=True)
    parser.add_argument("source_text")
    parser.add_argument("--scene-id", default="scene-001")
    parser.add_argument("--project-id", default="local-project")
    args = parser.parse_args()
    proposal = propose_profile(args.profile, args.source_text, scene_id=args.scene_id, project_id=args.project_id)
    print(json.dumps(proposal, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

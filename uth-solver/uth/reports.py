from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .rules import UTHRules


def metadata(sample_count: int, seed: int, rules: UTHRules = UTHRules()) -> dict[str, object]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        commit = "unknown"
    return {"created_at": datetime.now(timezone.utc).isoformat(), "rules_version": rules.rules_version,
            "paytable": rules.blind_paytable, "sample_count": sample_count, "seed": seed,
            "solver_version": "0.1.0", "git_commit": commit}


def write_json(path: str | Path, result: dict[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

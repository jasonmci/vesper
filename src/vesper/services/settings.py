from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SETTINGS_DIR = Path.home() / ".vesper"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def load_settings() -> Dict[str, Any]:
    try:
        text = SETTINGS_FILE.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception:
        return {}


def save_settings(data: Dict[str, Any]) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

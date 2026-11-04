"""Carrega settings.yaml + .env em um único objeto."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
OUTPUT_DIR = ROOT / "output"
DATA_DIR = ROOT / "data"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    load_dotenv(ROOT / ".env")
    with open(path or CONFIG_DIR / "settings.yaml", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    settings["env"] = {k: v for k, v in os.environ.items() if k.isupper()}
    return settings


def load_yaml(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)

"""Несекретные настройки приложения (секреты живут в keyring, см. secrets.py)."""

import json
import os
from typing import Any

from platformdirs import user_config_path
from pydantic import BaseModel, Field, ValidationError

CONFIG_DIR = user_config_path("demon-cry-tui")
CONFIG_PATH = CONFIG_DIR / "config.json"


class Config(BaseModel):
    """Прочие настройки, которые не являются секретами."""

    request_timeout: float = Field(default=30.0, gt=0)


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        return Config()

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return Config.model_validate(data)
    except json.JSONDecodeError, OSError, ValidationError, TypeError:
        return Config()


def save_config(cfg: Config) -> None:
    _write_json(cfg.model_dump(mode="json"))


def _write_json(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = CONFIG_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(temp_path, CONFIG_PATH)

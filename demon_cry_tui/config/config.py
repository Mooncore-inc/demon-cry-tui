import json
import os

from platformdirs import user_config_path
from pydantic import BaseModel, Field, ValidationError

CONFIG_DIR = user_config_path("demon-cry-tui")
CONFIG_PATH = CONFIG_DIR / "config.json"


class Config(BaseModel):
    api_url: str = Field(default="http://localhost:8000")
    token: str = Field(default="")  # TODO: migrate to keyring


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        return Config()

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return Config(**data)
    except json.JSONDecodeError, ValidationError:
        return Config()


def save_config(cfg: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = CONFIG_PATH.with_suffix(".tmp")
    temp_path.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
    os.replace(temp_path, CONFIG_PATH)

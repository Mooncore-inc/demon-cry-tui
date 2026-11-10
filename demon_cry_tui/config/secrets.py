"""Именованное хранилище секретов поверх системного keyring."""

from typing import Final

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

SERVICE_NAME: Final = "demon-cry-tui"


class SecretStoreError(RuntimeError):
    """Keyring недоступен или вернул ошибку бэкенда."""


class SecretStore:
    """Секреты по строковому ключу (имя ключа = username в keyring)."""

    def __init__(self, service: str = SERVICE_NAME) -> None:
        self.service = service

    @property
    def backend(self) -> str:
        return type(keyring.get_keyring()).__name__

    def get(self, name: str) -> str | None:
        try:
            return keyring.get_password(self.service, name)
        except KeyringError as exc:
            raise SecretStoreError(self._error_text(exc)) from exc

    def set(self, name: str, value: str) -> None:
        try:
            keyring.set_password(self.service, name, value)
        except KeyringError as exc:
            raise SecretStoreError(self._error_text(exc)) from exc

    def delete(self, name: str) -> None:
        try:
            keyring.delete_password(self.service, name)
        except PasswordDeleteError:
            return
        except KeyringError as exc:
            raise SecretStoreError(self._error_text(exc)) from exc

    def _error_text(self, exc: KeyringError) -> str:
        return f"keyring ({self.backend}): {exc}"

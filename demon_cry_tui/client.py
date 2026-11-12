"""Фасад над DemonCryAPI: активный клиент из keyring и один вход для вызовов."""

from typing import Any

from demon_cry_tui.api import DemonCryAPI
from demon_cry_tui.config import ActiveClient, ConnectionStore


class ClientError(RuntimeError):
    """Нет активного клиента или у него нет токена."""


class DemonCryClient:
    def __init__(self, connections: ConnectionStore, timeout: float) -> None:
        self._connections = connections
        self._timeout = timeout

    @property
    def backend(self) -> str:
        return self._connections.backend

    def active(self) -> ActiveClient | None:
        return self._connections.active()

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        active = self.active()
        if active is None:
            raise ClientError("no active client")
        if not active.token:
            raise ClientError("client has no token")

        async with DemonCryAPI(
            active.client.api_url,
            active.token,
            self._timeout,
        ) as api:
            return await getattr(api, method)(*args, **kwargs)

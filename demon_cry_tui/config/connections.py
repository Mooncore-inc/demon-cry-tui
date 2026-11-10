"""Клиенты DemonCry: название, сервер и токен."""

from typing import NamedTuple
from uuid import uuid4

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from demon_cry_tui.config.secrets import SecretStore

CATALOG_KEY = "catalog"
URL_ERROR = "Invalid API URL, expected http(s)://host"


class CatalogError(RuntimeError):
    """Некорректный каталог или неверные данные клиента."""


class Client(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str
    name: str
    api_url: str

    @field_validator("api_url")
    @classmethod
    def _normalize_url(cls, value: str) -> str:
        try:
            url = AnyHttpUrl(value.strip())
        except ValidationError as exc:
            raise ValueError(URL_ERROR) from exc
        return str(url).rstrip("/")


class Catalog(BaseModel):
    version: int = 1
    clients: list[Client] = Field(default_factory=list)
    active_id: str | None = None

    def client(self, client_id: str) -> Client | None:
        return next((item for item in self.clients if item.id == client_id), None)


class ActiveClient(NamedTuple):
    client: Client
    token: str


class ConnectionStore:
    """Клиенты и активный выбор в keyring."""

    def __init__(self, secrets: SecretStore | None = None) -> None:
        self._secrets = secrets if secrets is not None else SecretStore()

    @property
    def backend(self) -> str:
        return self._secrets.backend

    def load(self) -> Catalog:
        raw = self._secrets.get(CATALOG_KEY)
        if not raw:
            return Catalog()
        try:
            return Catalog.model_validate_json(raw)
        except ValidationError as exc:
            reason = exc.errors()[0]["msg"] if exc.errors() else "invalid JSON"
            raise CatalogError(f"connection catalog is corrupted: {reason}") from exc

    def add_client(self, name: str, api_url: str, token: str = "") -> Client:
        catalog = self.load()
        try:
            client = Client(
                id=_new_id(),
                name=_clean_name(catalog, name),
                api_url=api_url,
            )
        except ValidationError as exc:
            raise CatalogError(URL_ERROR) from exc
        catalog.clients.append(client)
        if catalog.active_id is None:
            catalog.active_id = client.id
        self._save(catalog)
        self._write_token(client.id, token)
        return client

    def update_client(
        self, client_id: str, name: str, api_url: str, token: str
    ) -> None:
        catalog = self.load()
        client = _require_client(catalog, client_id)
        client.name = _clean_name(catalog, name, skip_id=client_id)
        try:
            client.api_url = api_url
        except (ValidationError, ValueError) as exc:
            raise CatalogError(URL_ERROR) from exc
        self._save(catalog)
        self._write_token(client_id, token)

    def delete_client(self, client_id: str) -> None:
        catalog = self.load()
        _require_client(catalog, client_id)
        catalog.clients = [item for item in catalog.clients if item.id != client_id]
        if catalog.active_id == client_id:
            catalog.active_id = None
        self._secrets.delete(_token_key(client_id))
        self._save(catalog)

    def set_active(self, client_id: str) -> None:
        catalog = self.load()
        _require_client(catalog, client_id)
        catalog.active_id = client_id
        self._save(catalog)

    def token(self, client_id: str) -> str:
        return self._secrets.get(_token_key(client_id)) or ""

    def active(self) -> ActiveClient | None:
        catalog = self.load()
        if catalog.active_id is None:
            return None
        client = catalog.client(catalog.active_id)
        if client is None:
            return None
        return ActiveClient(client=client, token=self.token(client.id))

    def _save(self, catalog: Catalog) -> None:
        self._secrets.set(CATALOG_KEY, catalog.model_dump_json())

    def _write_token(self, client_id: str, token: str) -> None:
        name = _token_key(client_id)
        if cleaned := token.strip():
            self._secrets.set(name, cleaned)
        else:
            self._secrets.delete(name)


def _token_key(client_id: str) -> str:
    return f"token:{client_id}"


def _new_id() -> str:
    return uuid4().hex[:8]


def _clean_name(catalog: Catalog, name: str, *, skip_id: str | None = None) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise CatalogError("Client name must not be empty")
    folded = cleaned.casefold()
    if any(
        item.name.casefold() == folded and item.id != skip_id
        for item in catalog.clients
    ):
        raise CatalogError(f"Client '{cleaned}' already exists")
    return cleaned


def _require_client(catalog: Catalog, client_id: str) -> Client:
    client = catalog.client(client_id)
    if client is None:
        raise CatalogError(f"Unknown client: {client_id}")
    return client

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict


class Investigate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class DemonCryAPIError(Exception):
    """Исключение для ошибок API DemonCry."""

    def __init__(self, status_code: int, message: str, url: str) -> None:
        super().__init__(f"{status_code} {url}: {message}")
        self.status_code = status_code


class DemonCryAPI:
    """Thin async wrapper around the DemonCry REST API."""

    def __init__(self, base_url: str, token: str, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=timeout,
        )

    async def __aenter__(self) -> DemonCryAPI:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def _req(self, method: str, path: str, **kwargs: Any) -> Any:
        r = await self._client.request(method, path, **kwargs)

        if r.status_code >= 400:
            raise DemonCryAPIError(r.status_code, r.text, str(r.url))

        if not r.content:
            return None

        try:
            return r.json()
        except ValueError:
            return r.text

    async def list_investigates(self) -> list[Investigate]:
        data = await self._req("GET", "/api/v1/investigates/")
        return [Investigate.model_validate(item) for item in data]

    async def create_investigate(self, name: str) -> Investigate:
        data = await self._req("POST", "/api/v1/investigates/", json={"name": name})
        return Investigate.model_validate(data)

    async def delete_investigate(self, inv_id: int) -> None:
        await self._req("DELETE", f"/api/v1/investigates/{inv_id}")

    async def list_entities(self, inv_id: int) -> list[dict[str, Any]]:
        return await self._req("GET", f"/api/v1/investigates/{inv_id}/entities")

    async def create_entity(
        self, inv_id: int, value: str, type_: str | None = None
    ) -> dict[str, Any]:
        body = {"value": value}
        if type_:
            body["type"] = type_
        return await self._req(
            "POST", f"/api/v1/investigates/{inv_id}/entities", json=body
        )

    async def get_entity(self, inv_id: int, entity_id: int) -> dict[str, Any]:
        return await self._req(
            "GET", f"/api/v1/investigates/{inv_id}/entities/{entity_id}"
        )

    async def list_links(self, inv_id: int) -> list[dict[str, Any]]:
        return await self._req("GET", f"/api/v1/investigates/{inv_id}/links")

    async def get_graph(self, inv_id: int) -> dict[str, Any]:
        return await self._req("GET", f"/api/v1/investigates/{inv_id}/graph")

    async def list_tools(self) -> list[dict[str, Any]]:
        return await self._req("GET", "/api/v1/investigate/tools")

    async def execute_tool(
        self,
        inv_id: int,
        tool_name: str,
        params: dict[str, Any],
        context_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        body = {
            "params": params,
            "context_entity_ids": context_ids or [],
        }
        return await self._req(
            "POST", f"/api/v1/investigates/{inv_id}/{tool_name}/execute", json=body
        )

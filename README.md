# demon-cry-tui

terminal UI for demon cry core

## Клиенты

Один клиент = название + адрес сервера + токен. Список плоский, поэтому можно
держать и свой self-hosted, и командный сервер, и несколько аккаунтов на одном.

- `ctrl+s` — список клиентов; `a` добавить, `e` изменить, `d` удалить,
  `Enter` — сделать клиента активным.
- После выбора клиента в левом сайдбаре показываются все расследования
  (`GET /api/v1/investigates/`), `ctrl+r` — перезагрузить, `Enter` на
  расследовании — загрузить его граф (`/graph`) справа: сущности как узлы
  дерева, под ними связи с дочерними сущностями (`relation → value`),
  повторные/циклические узлы помечаются `(seen)`.
- `ctrl+n` или последний пункт списка `+ add investigation` — создать
  расследование (`POST /api/v1/investigates/`), после создания список
  перезагружается.
- `ctrl+e` — создать сущность в открытом расследовании
  (`POST /api/v1/investigates/{id}/entities`): спрашивает value (обязательно),
  type и label; после создания граф перезагружается.
- `e` — редактировать: в графе — label/data выделенной сущности
  (`PATCH .../entities/{id}`, value и type неизменяемы), в списке — имя
  расследования (`PATCH /investigates/{id}`).
- `ctrl+t` — инструменты: список из `GET /api/v1/investigate/tools`, форма
  параметров строится из JSON Schema инструмента (`domain`, `record_type` и
  т.п.), запуск — `POST /api/v1/investigates/{id}/{tool}/execute`; выделенная
  в графе сущность уходит в `context_entity_ids`, после запуска граф
  перезагружается.
- Каталог клиентов хранится в системном keyring записью `catalog`, токены —
  отдельными записями `token:<client>`. В `config.json` (каталог
  `platformdirs`) лежат только несекретные настройки.

```bash
make setup          # зависимости + pre-commit
make format         # ruff format
make lint-ruff
make secrets-reset  # удалить все секреты приложения из keyring
uv run demon-cry-tui
```

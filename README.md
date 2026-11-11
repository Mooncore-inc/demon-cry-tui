# demon-cry-tui

terminal UI for demon cry core

## Клиенты

Один клиент = название + адрес сервера + токен. Список плоский, поэтому можно
держать и свой self-hosted, и командный сервер, и несколько аккаунтов на одном.

- `ctrl+s` — список клиентов; `a` добавить, `e` изменить, `d` удалить,
  `Enter` — сделать клиента активным.
- После выбора клиента в левом сайдбаре показываются все расследования
  (`GET /api/v1/investigates/`), `ctrl+r` — перезагрузить, `Enter` на
  расследовании — открыть его в основной области.
- `ctrl+n` или последний пункт списка `+ add investigation` — создать
  расследование (`POST /api/v1/investigates/`), после создания список
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

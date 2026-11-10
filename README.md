# demon-cry-tui

terminal UI for demon cry core

## Клиенты

Один клиент = название + адрес сервера + токен. Список плоский, поэтому можно
держать и свой self-hosted, и командный сервер, и несколько аккаунтов на одном.

- `ctrl+s` — список клиентов; `a` добавить, `e` изменить, `d` удалить,
  `Enter` — сделать клиента активным.
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

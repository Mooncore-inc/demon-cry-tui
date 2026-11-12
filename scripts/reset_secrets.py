"""Удаление всех секретов демона из системного keyring."""

import argparse
import sys

import secretstorage
from secretstorage.exceptions import SecretStorageException

from demon_cry_tui.config import SERVICE_NAME


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", default=SERVICE_NAME)
    parser.add_argument("-y", "--yes", action="store_true", help="skip confirmation")
    args = parser.parse_args()

    try:
        collection = secretstorage.get_default_collection(secretstorage.dbus_init())
    except SecretStorageException as exc:
        print(f"keyring unavailable: {exc}", file=sys.stderr)
        return 1

    items = list(collection.search_items({"service": args.service}))
    if not items:
        print(f"no secrets for {args.service}")
        return 0

    print(f"wallet {collection.get_label()!r}: {len(items)} secret(s)")
    for item in items:
        print(f"  {item.get_label()}")

    if not args.yes:
        answer = input(f"delete all secrets for {args.service}? [y/N] ").strip().lower()
        if answer not in {"y", "yes", "д", "да"}:
            print("aborted")
            return 1

    for item in items:
        item.delete()
    print(f"deleted: {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

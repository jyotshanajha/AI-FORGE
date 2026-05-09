import json
from pathlib import Path
from threading import RLock
from typing import Any


_STORE_PATH = Path(__file__).resolve().parents[2] / ".dev_fallback_store.json"
_LOCK = RLock()


def _default_store() -> dict[str, Any]:
    return {
        "users": {},
        "threads_by_user_email": {},
        "messages_by_thread_id": {},
    }


def _read_store_unlocked() -> dict[str, Any]:
    if not _STORE_PATH.exists():
        return _default_store()

    try:
        data = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return _default_store()

    if not isinstance(data, dict):
        return _default_store()

    merged = _default_store()
    merged.update(data)
    return merged


def _write_store_unlocked(store: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, ensure_ascii=True, indent=2), encoding="utf-8")


def get_store() -> dict[str, Any]:
    with _LOCK:
        return _read_store_unlocked()


def update_store(mutator: Any) -> dict[str, Any]:
    with _LOCK:
        store = _read_store_unlocked()
        mutator(store)
        _write_store_unlocked(store)
        return store

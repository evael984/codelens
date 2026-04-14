"""User cache (after)."""

import time

_CACHE: dict[str, dict] = {}
_CACHE_TS: dict[str, float] = {}
_TTL_SECONDS = 60


def get_user_by_email(email: str) -> dict | None:
    ts = _CACHE_TS.get(email, 0)
    if time.time() - ts > _TTL_SECONDS:
        _CACHE.pop(email, None)
        _CACHE_TS.pop(email, None)
        return None
    return _CACHE.get(email)


def put_user(user: dict) -> None:
    _CACHE[user["email"]] = user
    _CACHE_TS[user["email"]] = time.time()


def update_user(user_id: str, new_email: str, store) -> dict:
    user = store.load(user_id)
    old_email = user["email"]
    user["email"] = new_email
    store.save(user)
    _CACHE.pop(old_email, None)
    _CACHE_TS.pop(old_email, None)
    put_user(user)
    return user


def delete_user(user_id: str, store) -> None:
    store.delete(user_id)

"""User cache (before)."""

_CACHE: dict[str, dict] = {}


def get_user_by_email(email: str) -> dict | None:
    return _CACHE.get(email)


def put_user(user: dict) -> None:
    _CACHE[user["email"]] = user


def update_user(user_id: str, new_email: str, store) -> dict:
    user = store.load(user_id)
    user["email"] = new_email
    store.save(user)
    put_user(user)
    return user


def delete_user(user_id: str, store) -> None:
    user = store.load(user_id)
    store.delete(user_id)
    _CACHE.pop(user["email"], None)

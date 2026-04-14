# Add input validation to login()

This PR adds null/empty validation to the `login()` function so we surface a
clear error instead of silently returning `True` for empty users.

## Changes

- `auth.py`: raise `ValueError` when user is missing
- Added unit test for the new error path

## Out of scope

- Password validation (separate ticket: AUTH-204)

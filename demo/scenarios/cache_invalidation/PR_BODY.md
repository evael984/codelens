# Fix cache invalidation bug on user update

When a user updates their email, the old email was still being returned from
`get_user_by_email()` for up to 5 minutes (cache TTL). This PR invalidates the
cache entry for the *old* email immediately on update.

## Changes

- `cache.py`: invalidate old key on update
- Added regression test for the email-change scenario

## Out of scope

- Cache invalidation on delete (covered by ticket CACHE-88)

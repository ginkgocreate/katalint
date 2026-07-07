---
type: task
---

# Add password reset flow

Implement a password reset flow for the authentication module. The work is
scoped to the login and validation helpers plus their tests, and should not
touch anything else.

## Files in scope

- `src/auth/login.py`
- `src/auth/validators.py`
- `tests/auth/test_login.py`

## Acceptance Criteria

- A user can request a reset token from the login helper.
- The validation helper rejects expired tokens.
- Unit tests cover the happy path and the expired-token case.

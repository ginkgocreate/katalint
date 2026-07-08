---
type: task
---

# Add rate limiting to the login endpoint

Introduce a per-IP rate limit on the `/login` endpoint so repeated failed
attempts are throttled and abuse is reduced.

## Acceptance Criteria

- The `/login` endpoint rejects more than 5 failed attempts per IP within 60 seconds with HTTP 429.
- Successful logins reset the failure counter for that IP.
- A unit test covers both the throttled and reset behaviors.

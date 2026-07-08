---
type: task
---

# Refactor the notification service

Clean up the notification service so that email and SMS delivery share a
common queueing path and error-handling logic.

## Context

The current implementation duplicates retry logic across two modules, which
makes it hard to change delivery behavior consistently.

## Notes

Coordinate with the platform team before changing the queue configuration.

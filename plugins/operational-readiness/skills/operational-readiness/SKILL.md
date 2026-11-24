---
name: operational-readiness
description: The user's operational standards for services - metrics for new or changed behavior, structured logging, retries, timeouts and fallbacks on every external call, and distributed tracing. Use before writing or changing service code that handles requests, calls external systems or emits telemetry, and when reviewing operational readiness.
---

# Operational Readiness

The rules are in the `standards/` directory next to this file:

- `standards/general.md`: principles and rule IDs (OM metrics, OL logging,
  OR resilience, OT tracing).

Each project names its own tools in `.claude/operational.md` at the
repository root: metrics library and naming scheme, logging library and
required fields, resilience library and default policies, tracing library and
attribute conventions. Read it before
writing code. If it is missing, follow the conventions already in the
codebase and tell the user the file would make reviews more precise.

The ones most often missed:

1. **OM:** new behavior gets metrics; changed or removed behavior updates
   or removes its metrics.
2. **OL:** log with structured fields, never by concatenating or
   interpolating values into the message.
3. **OR:** every external call has a timeout, a retry policy where retrying
   is safe, and a defined fallback or failure path.
4. **OT:** important operations are spans, trace context crosses every
   process boundary, and errors are recorded on the span.

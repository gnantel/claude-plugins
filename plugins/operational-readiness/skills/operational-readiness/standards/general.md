# Operational Standards

Applies to services and other long-running code. Each project's
`.claude/operational.md` names the concrete tools and conventions (metrics
library and naming, logging library and required fields, resilience library
and default policies). Where it is silent, follow the codebase's existing
patterns. Each rule has an ID so reviews can cite it.

> Draft: seeded from the first checks listed (metrics, logging, retries and
> fallbacks). Extend and sharpen as review experience accumulates.

---

## Metrics (OM)

### OM1. New behavior is measured

A new endpoint, job, consumer, external integration or significant code path
emits metrics: at least a count of outcomes (success/failure, labelled by
outcome) and a latency measurement where duration matters.

### OM2. Changed and removed behavior keeps metrics in sync

- When behavior changes, its metrics still describe it: names, labels and
  units remain accurate.
- When code is removed, its metrics are removed too. No orphaned metrics.
- A renamed or removed metric is called out in the PR description, because
  dashboards and alerts may depend on it.

### OM3. Labels have bounded cardinality

Labels take values from a small, known set (outcome, method, status class).
Never user IDs, request IDs, raw URLs, emails or free text.

### OM4. Follow the project's naming scheme

Names, units and suffixes follow `.claude/operational.md` (for example
Prometheus conventions: `snake_case`, base units, `_total` for counters,
`_seconds` for durations).

## Logging (OL)

### OL1. Structured logging only

Values go in structured fields, not into the message string. The message is
a constant describing the event.

Bad:
```
log.info("Charged customer " + customerId + " amount " + amount)
log.info(f"Charged customer {customer_id} amount {amount}")
```

Good:
```
log.info("customer charged", customer_id=customer_id, amount=amount)
```

### OL2. Significant events are logged

Log at boundaries and decisions that matter when diagnosing a problem:
requests that fail, external call failures and retries exhausted, fallbacks
taken, state transitions, and jobs starting and finishing. Do not log every
line of normal flow.

### OL3. Levels mean something

- `error`: needs attention; someone should look.
- `warn`: unexpected but handled (fallback taken, retry succeeded late).
- `info`: significant normal events.
- `debug`: detail for diagnosing, off in production by default.

An exception that is handled and recovered from is not an `error`.

### OL4. Errors carry context and cause

An error log includes the exception/cause and the identifiers needed to
find the affected entity (as structured fields), and is logged once, where it
is handled, not at every layer it passes through.

### OL5. No secrets or personal data

Never log credentials, tokens, full payment details or personal data beyond
what `.claude/operational.md` allows.

## Resilience (OR)

An *external call* is any call that leaves the process: HTTP/gRPC services,
databases, caches, queues, file or object storage, and third-party SDKs.

### OR1. Every external call has a timeout

No call may wait forever. Timeouts are explicit, either at the call site or
in a client configured once and reused.

### OR2. Retries where safe, with backoff

- Retry transient failures (timeouts, connection errors, 5xx, throttling)
  with exponential backoff and jitter, and a bounded attempt count.
- Only retry operations that are idempotent, or made idempotent (for
  example with an idempotency key).
- Never retry non-transient failures (4xx validation, auth errors).
- Do not stack retries in several layers for the same call.

### OR3. Every external call has a defined failure path

When retries are exhausted, the code does something deliberate: a fallback
value or cached result, degraded behavior, queuing for later, or a clear
error to the caller. An exception bubbling up unhandled because nobody
thought about it is a violation.

### OR4. Protect against a failing dependency

High-volume calls to a dependency that can fail or slow down use a circuit
breaker or bulkhead (as the project's resilience library provides), so one
failing dependency cannot exhaust threads, connections or the caller.

### OR5. Resilience is observable

Retries, fallbacks and open circuits emit metrics (OM) and logs (OL2), so
degraded behavior is visible rather than silent.

## Tracing (OT)

Follow the project's tracing library and conventions (OpenTelemetry where
used). A *process boundary* is any point where work leaves or enters the
process: HTTP/gRPC calls, database and cache calls, queue publishes and
consumes, and thread or task hand-offs.

### OT1. Important operations are spans

Inbound requests, outbound calls (HTTP, RPC, database, queue), message
handling and significant internal steps run inside a span with a clear,
low-cardinality operation name (for example `GET /orders/{id}`, not
`GET /orders/8431`). Many tracing libraries instrument common clients and
frameworks automatically; check that before adding spans by hand.

### OT2. Trace context propagates

- Outbound requests and published messages inject the trace context into
  headers or message metadata; inbound requests and consumed messages
  extract it.
- Async work, thread pools and background tasks started from a span keep the
  parent context, so the work stays in the same trace.

### OT3. Spans carry useful, safe attributes

Attributes identify what the operation acted on and follow the project's
semantic conventions (OpenTelemetry semantic conventions where used).

- Attribute keys are a small, fixed set, never built from data.
- Values may be high-cardinality (order, model or request IDs, request
  lengths): that is what makes a trace searchable. Keep them small: no
  payloads or whole bodies.
- No secrets or personal data (as OL5).
- An attribute that is also used as a metric label is bounded there (OM3).

### OT4. Errors are recorded on the span

A failed operation records the exception on its span and sets the span
status to error, so a failed trace can be found without the logs. Handled
and recovered failures do not set error status (as OL3).

### OT5. Logs link to traces

Where the project's logging supports it, log records carry the current trace
and span IDs, so a log line leads to its trace and back.

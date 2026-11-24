# Operational Standards

Applies to services and other long-running code. Each project's
`.claude/operational.md` names the concrete tools and conventions (metrics
library and naming, logging library and required fields, resilience library
and default policies, feature-flag setup). Where it is silent, follow the codebase's existing
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

## Feature gating (OF)

A *flag* is a switch that turns new behavior on for some requests and off
for others, and is meant to be removed once the behavior is the default.
Follow the project's flag setup (its OpenFeature wrapper, provider and
naming scheme); do not invent one.

### OF1. Risky behavior is gated

Gate new user-visible behavior, changed behavior on a hot or risky path
(payments, auth, data writes, high-volume requests) and migrations. Pure
refactors, internal tooling and code not yet reachable need no gate.

### OF2. A flag is temporary; a setting is configuration

- Use a **flag** for a rollout (per request or by percentage) of a change
  that will become the default and lose its gate: a new pricing algorithm,
  a rewritten checkout, a switch to a new storage backend.
- Use **configuration** for a permanent, per-environment setting that
  operators keep: limits, endpoints, timeouts, modes, an integration that
  is on in some environments and never in others.

A permanent setting built as a flag will never be removed; a temporary
rollout built as configuration has no per-request control and no removal
trail.

### OF3. Evaluate through OpenFeature

Code evaluates flags through the [OpenFeature](https://openfeature.dev)
API, or the project's own wrapper around it, never through a vendor SDK
directly. The provider behind it is a project choice. Prefer free or
self-hostable providers (flagd, Unleash or Flagsmith open source) or the
cloud's own service (Azure App Configuration, AWS AppConfig) over an extra
paid service.

### OF4. Evaluation is resilient

Flag evaluation never blocks or fails a request. When the flag service is
down or slow it returns the last-known values, or the code's defaults when
there are none yet. Values refresh in the background. A stale or failing
refresh is observable (as OR5) but silent to callers: the caller does not
catch flag errors.

### OF5. Flags are read once per request

Read the flags at the start of a request (or message) into a snapshot, and
pass it down or hold it in request scope. Every check in that request sees
the same values, even if a flag changes mid-request. Building the snapshot
may evaluate each flag once. Calling the flag client again after that, in
the same request or from a loop, is a violation.

### OF6. How to gate

- The default is off: the old behavior.
- The flag is checked at one clear decision point, not scattered through
  the code.
- Both paths are tested.
- The flag's name follows the project's naming scheme.
- The chosen path is observable: a metric label (bounded, OM3) or a span
  attribute (OT3) shows which path ran.

### OF7. Removable by design

Shape the gated code so removing the flag later is a small, mechanical
change: the new path and the old path are separate functions or classes
chosen at the decision point, not interleaved conditionals, and the flag is
not passed through unrelated layers.

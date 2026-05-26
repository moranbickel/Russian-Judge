# Worked Example: R1 → R2

A complete end-to-end Russian Judge cycle on a small, realistic code change. Synthetic — chosen to illustrate the protocol's mechanics rather than represent a real production review.

The work product is a Python rate-limiter middleware function. The change adds per-IP rate limiting to an existing API. We dispatch Code RJ, see what R1 catches, address findings, and re-dispatch.

---

## The work product

A diff submitted for review. Author has self-tested locally and believes it's ship-ready.

```python
# rate_limiter.py — new
from collections import defaultdict
from time import time

REQUESTS = defaultdict(list)
WINDOW = 60     # seconds
LIMIT = 100     # requests per window

def is_rate_limited(client_ip):
    now = time()
    REQUESTS[client_ip] = [t for t in REQUESTS[client_ip] if now - t < WINDOW]
    if len(REQUESTS[client_ip]) >= LIMIT:
        return True
    REQUESTS[client_ip].append(now)
    return False
```

```python
# api.py — modified
from rate_limiter import is_rate_limited

def handle_request(request):
    if is_rate_limited(request.client_ip):
        return Response(status=429, body="Rate limit exceeded")
    # ... existing handler logic
```

---

## R1 dispatch

System message: Code RJ priming from [`templates/reviewer-prompt.md`](../templates/reviewer-prompt.md).

User message:

> **Change scope:** Add per-IP rate limiting (100 req/min) to the API.
>
> **Modality:** Code
>
> **Round:** R1
>
> [diff above pasted]

---

## R1 verdict

```
ROUND: R1
MODALITY: code

SCORE: 7.6/10

CRITICAL (C):
  - C-1: REQUESTS dict grows unbounded across distinct client IPs and is
         never garbage-collected. Long-running processes will consume
         memory proportional to total unique IPs seen, not to active
         IPs in the current window.

IMPORTANT (I):
  - I-1: REQUESTS is module-level mutable state with no locking. Under a
         multi-threaded WSGI server, concurrent requests from the same IP
         will race on list reads/writes; the rate counter can both
         under-count (allowing too many requests) and corrupt list state.
  - I-2: No tests for the rate-limiter logic in this change. The window-
         expiry, the limit threshold, and the multi-IP isolation are all
         untested behaviors.

MINOR (M):
  - M-1: WINDOW and LIMIT as bare module constants make per-route or
         per-tenant tuning impossible without a refactor.
  - M-2: `is_rate_limited` returns True/False but has the side effect of
         appending to REQUESTS. The name implies a query, the behavior
         is a command. Suggest splitting into `check_rate_limit` (mutates)
         and a clearer name, or accepting the command-query mix
         explicitly.

VERDICT: REVISE
```

---

## What happened in the gap between rounds

The author addressed C-1, I-1, I-2. Skipped M-1 (out-of-scope refactor); accepted M-2 (renamed to `check_and_record`).

```python
# rate_limiter.py — revised
from collections import defaultdict
from threading import Lock
from time import time

WINDOW = 60
LIMIT = 100

_REQUESTS = defaultdict(list)
_LOCK = Lock()
_LAST_GC = 0
_GC_INTERVAL = 600   # seconds

def _maybe_gc(now):
    """Drop entries for IPs whose newest request is older than the window."""
    global _LAST_GC
    if now - _LAST_GC < _GC_INTERVAL:
        return
    _LAST_GC = now
    cutoff = now - WINDOW
    stale = [ip for ip, ts in _REQUESTS.items() if not ts or ts[-1] < cutoff]
    for ip in stale:
        del _REQUESTS[ip]

def check_and_record(client_ip):
    now = time()
    with _LOCK:
        _maybe_gc(now)
        _REQUESTS[client_ip] = [t for t in _REQUESTS[client_ip] if now - t < WINDOW]
        if len(_REQUESTS[client_ip]) >= LIMIT:
            return True
        _REQUESTS[client_ip].append(now)
        return False
```

```python
# tests/test_rate_limiter.py — new
def test_below_limit_allows_request():
    # ...
def test_at_limit_blocks_next_request():
    # ...
def test_window_expiry_releases_quota():
    # ...
def test_distinct_ips_have_independent_quotas():
    # ...
def test_concurrent_requests_same_ip_respect_limit():
    # ... (uses ThreadPoolExecutor; verifies count under contention)
def test_gc_drops_stale_ips_after_interval():
    # ...
```

---

## R2 dispatch

Same Code RJ priming. User message includes the R2 addendum from [`templates/reviewer-prompt.md`](../templates/reviewer-prompt.md):

> This is round 2.
>
> The R1 verdict was: [pasted]
>
> I have addressed:
> - C-1: Added periodic GC of stale IPs (every 600s, drops IPs whose newest entry is older than the window).
> - I-1: Added `_LOCK` and put the read-modify-write under it. Tests include a concurrent-access case.
> - I-2: Added six tests covering the limit threshold, window expiry, multi-IP isolation, concurrency, and the GC.
> - M-2: Renamed `is_rate_limited` → `check_and_record`. Accepting the command-query mix explicitly; the name now reflects it.
>
> Not addressed:
> - M-1: Out-of-scope refactor for this change. Backlogged separately.
>
> Please verify and return a fresh verdict.
>
> [revised diff + new tests]

---

## R2 verdict

```
ROUND: R2
MODALITY: code

SCORE: 9.3/10

CRITICAL (C):
  None

IMPORTANT (I):
  None

MINOR (M):
  - M-1: (Carried from R1; author elected to defer. Acceptable.)
  - M-3: The GC is opportunistic — it only fires when a request arrives
         after _GC_INTERVAL elapsed. On a service that idles for hours
         then resumes, memory accumulates until traffic returns. Not
         blocking, but worth noting in the docstring.

VERDICT: PASS
```

Author ships. Optionally addresses M-3 in a follow-up — non-blocking.

---

## What to notice

- **The score moved 1.7 points.** That's not the meaningful number. The meaningful number is the C count going to zero and the I count going to zero. Score is the reviewer's vibe; the floor is the contract.
- **R1 had a Critical finding (C-1) the author hadn't seen.** The author had self-tested locally with one IP and one process — couldn't have surfaced the unbounded-growth or the concurrency issue from local testing alone. This is the kind of defect adversarial review is shaped for.
- **R2 surfaced one new finding (M-3).** This is normal. Fixes can introduce new edges. The verdict format requires the reviewer to flag them; the floor decides whether they block.
- **The author deferred M-1 explicitly with rationale.** The protocol allows this for non-blocking findings. The R2 verdict acknowledges the deferral and counts it correctly.
- **No round 3.** Pass floor met. Halt. Per [PROTOCOL.md §10.3](../PROTOCOL.md), running R3 to chase a higher score is an anti-pattern.

---

## What this example does NOT show

- Domain RJ on prose or specs (the same shape applies; the priming differs).
- Dual RJ on a change that touches both code and domain content (run two independent sessions).
- Cross-model dispatch (running R2 on a different model from R1 — sometimes catches what R1 missed).
- The pre-check gate decision (this change clearly invokes RJ — touches a contract, introduces a new failure mode).
- A disputed finding — where the author believes the reviewer is wrong. That's the protocol's hardest judgment call; it has its own walkthrough: [`disputed-finding-walkthrough.md`](./disputed-finding-walkthrough.md).

For those, see [PROTOCOL.md](../PROTOCOL.md) §9 (Modalities) and [`templates/pre-check-gate.md`](../templates/pre-check-gate.md).

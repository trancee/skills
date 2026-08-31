# Retry policy

Retry decision table:

| Class | Default |
|---|---|
| permission denied/revoked, adapter off/unsupported, user cancel | wait for explicit state/user action |
| invalid address/identity/settings/API usage | fail; fix code/configuration |
| authentication/encryption/authorization/pairing rejected | surface security/user action; no blind retry |
| peer explicitly rejects/max connections | peer/product policy; delayed retry only when meaningful |
| documented timeout/congestion/opaque transient with fresh observation | eligible within budget after cleanup |
| service/schema/operation protocol failure | fix stage/protocol; do not reconnect-loop |
| unknown persistent/system-wide | stop budget; gather controls/HCI/bugreport |

One scheduler owns:
- attempt counter and elapsed retry budget
- capped exponential delay (`min(cap, base * 2^n)`) with bounded random jitter
- device/session generation and fresh-observation requirement
- pending timer cancellation handle
- terminal reason

Before executing a retry: confirm owner active, same user intent/device identity, permission granted, adapter on, background policy valid, no live GATT, peer observation policy satisfied. Create a fresh GATT. Cancel the timer on any state change that invalidates intent.

Reset backoff only after a product-defined stable `Ready` duration. Connected-then-immediate-failure must not reset. Limit aggregate retries across rapid foreground/background or configuration recreation.

Test with virtual time: simultaneous callback/timeout, two failure callbacks, user cancel during delay, device switch, permission revoke, process owner close, scheduler recreation, and success followed by unstable disconnect.

# Android GATT queue change: [scope]

## Ownership
- Android/coroutines versions and device matrix:
- connection owner/epoch/callback executor:
- request channel capacity/backpressure:
- notification stream capacity/overflow:

## Operation matrix
| operation | immutable request data | submission result | expected callback/target | timeout/reset | caller result |
|---|---|---|---|---|---|
| | | | | | |

## Race semantics
- in-flight identity/matcher:
- queued/in-flight cancellation:
- timeout/disconnect/service-change reset:
- duplicate/stale/mismatched callback handling:
- subscription/reliable-write composites:

## Verification
- fake transport order/race/virtual-time tests:
- API 33/37 compilation:
- real-device/OEM scenarios:
- invariant evidence (max in-flight):
- limitations/unverified callback behavior:

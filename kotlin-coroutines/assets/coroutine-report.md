# Coroutine change: [scope]

## Ownership tree
- lifecycle owner/scope:
- parent Job:
- children/builders/results:
- completion/cancellation trigger:

## Execution and failure
- dispatchers/blocking boundaries:
- success result consumer:
- failure propagation/handler:
- cleanup/resource ownership:

## Stream/state protocol
- Flow/Channel/state primitive:
- cold/hot, buffer/replay/overflow:
- producer/collector/close ownership:
- shared-state synchronization:

## Dependencies
- Kotlin/coroutines core+modules/platform:

## Proof
| scenario | expected | observed |
|---|---|---|
| success/completion | | |
| parent/child cancellation | | |
| sibling failure/supervision | | |
| timeout/cleanup | | |
| stream backpressure/error/close | | |
| virtual-time determinism | | |
| runtime lifecycle termination | | |

## Debug evidence and limitations
- coroutine dump/log/probe:
- unverified platform/race/behavior:

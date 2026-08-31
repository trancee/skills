# Android Bluetooth socket change: [scope]

## Contract
- min/compile/target SDK:
- Android/device/OEM/peer matrix:
- RFCOMM or LE CoC, client/server:
- secure/insecure and application authentication:
- service UUID/name or PSM disclosure/lifetime:
- owner, connection deadline, background mechanism:

## Stream protocol
- frame header/encoding/integrity/max size:
- read owner/buffer/copy/EOF policy:
- write serialization/queue/backpressure:
- reconnect/resume semantics:

## Lifecycle
- permissions/features/adapter states:
- listener and connected-socket close ownership:
- coroutine/thread cancellation:
- FGS/companion/process-death behavior:

## Verification
| SDK/device/peer | scenario | expected | observed evidence | result/limitation |
|---|---|---|---|---|
| | | | | |

- unit/fake-stream tests:
- compile/lint/manifest results:
- instrumentation/real-device results:
- logcat/HCI artifacts:
- unverified hardware/OEM/background conditions:

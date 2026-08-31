# BLE inspector verification

JVM tests:
- UUID normalization/registry ambiguity and duplicate instances
- immutable scan/tree/value snapshots and stable keys
- hex/ASCII formatting for empty, nonprintable, Unicode-like, and large bounded input
- every decoder flag combination, exact/truncated/trailing lengths, endian boundaries, RFU/prohibited/sentinel/SFLOAT special values
- state reducers for permission, scan, connect, discovery, read, subscribe, write confirmation, timeout/reset, disconnect
- legacy/extended advertisement encoded-size budget calculator
- redaction/export policy

Compose tests:
- permission rationale/denial/retry and Bluetooth-off surfaces
- Start/Stop scan and lifecycle exit
- large lazy device/tree lists with stable semantics
- queued/in-flight elapsed state and per-row conflicts
- raw plus decoded output, malformed/special labels
- write confirmation content and cancellation
- subscription Starting/Active/Stopping
- accessibility labels and non-color status

Physical matrix:
- representative Android 12–17/OEM devices
- at least two known peripherals, one slow/error-injecting controllable peer when possible
- scan filters/duplicates/rotating address/missing name/failure/timeout
- connect/discover/cache/service change, API 33 values, MTU, rapid actions, timeout/disconnect
- notify/indicate start/stream/stop and reads while subscribed
- local server/legacy or extended advertising, oversized data, two centrals
- adapter toggle, permission revoke, screen rotation/background/process kill

Capture a bounded callback timeline and HCI snoop when app callbacks cannot prove packet behavior. An emulator/mocked GATT proves only deterministic UI/parser/owner logic.

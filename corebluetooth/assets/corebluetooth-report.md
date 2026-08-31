# Core Bluetooth change: [scope]

## Contract
- Apple platforms/deployment versions:
- central/peripheral and GATT client/server roles:
- peer/device/OS/firmware matrix:
- manager owner, delegate queue, connection generation:
- privacy/authorization/background modes:

## Central flow
- scan filters/identity/stop condition:
- connect timeout/cancel/reconnect:
- service/characteristic discovery and invalidation:
- read/write/subscribe callback correlation:

## Local peripheral flow
- service/characteristic properties and permissions:
- publication/advertising:
- ATT read offsets/write-batch atomicity/responses:
- subscribers/update flow control:

## Lifecycle
- foreground/background behavior:
- restoration identifiers/reconciliation:
- teardown/stale callback policy:

## Verification
- deterministic tests:
- compiled platform/deployment targets:
- real-device scenarios:
- trace evidence:
- limitations/unverified behavior:

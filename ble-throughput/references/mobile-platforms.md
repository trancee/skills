# iOS and Android throughput paths

## iOS/CoreBluetooth

Query `maximumWriteValueLength(for:)` separately for `.withoutResponse` and `.withResponse`; do not hard-code ATT MTU or historical 185-byte examples.

For central write commands:
1. while `canSendWriteWithoutResponse` is true, submit bounded queued chunks no larger than the queried maximum
2. stop as soon as it becomes false
3. resume only from `peripheralIsReady(toSendWriteWithoutResponse:)`

For peripheral notifications, stop when `CBPeripheralManager.updateValue` returns false and resume from `peripheralManagerIsReady(toUpdateSubscribers:)`. Copy/retain data according to API ownership. Connection/PHY/DLE scheduling remains OS-controlled; verify on air.

## Android/BluetoothGatt

Android 14+ requests ATT MTU 517 when the first GATT client calls `requestMtu` and ignores later MTU requests. Use `onMtuChanged` and actual peer/write behavior; request order among clients matters.

Use API 33+ `writeCharacteristic(characteristic, value, writeType)` and value-taking descriptor writes; older mutable-characteristic APIs are deprecated and race-prone. Serialize GATT operations with one queue/callback state machine. For write commands, use stack return/status/congestion callbacks and a bounded window—vendor behavior varies.

Request `CONNECTION_PRIORITY_HIGH` only for an active bulk transfer and restore balanced policy afterward. Request/read preferred PHY and record applied TX/RX values. Permissions and background limits vary by target SDK/OS.

## Matrix

Test representative phone models/chipsets and OS releases with foreground/background, screen locked, Wi-Fi traffic, Bluetooth audio, multiple connections, scanning, weak RSSI, and long transfers. Report per-cell results; phone brand averages conceal controller/scheduler bounds.

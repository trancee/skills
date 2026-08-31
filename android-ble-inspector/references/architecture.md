# Inspector architecture

Modules:
- `ScannerOwner`: permission/adapter-bound `callbackFlow` session, transient observations
- `ConnectionOwner`: selected device, connection generation, discovery, teardown
- `GattOperationOwner`: strict client queue from `android-ble-gatt-queue`
- `LocalServerOwner`: optional `android-ble-gatt-server` database plus advertiser session
- `DecoderRegistry`: pure, versioned `(service UUID, characteristic UUID) -> decoder`
- `EvidenceRecorder`: bounded redacted timeline/export
- ViewModels: immutable screen states and user intents
- composables: render state; never retain platform objects

Prefer small interfaces at these seams for fake-driven reducers/parsers, but keep Android contracts visible in implementations and state. Avoid a universal BLE repository that erases callback type, submission result, connection generation, property, permission, CCCD, or role.

Core identifiers:
- observation ID: scan-session ID + current `BluetoothDevice`/advertisement event
- connection ID: monotonic generation
- attribute ID: generation + service instance + characteristic/descriptor instance
- operation ID: monotonic request ID
- event ID: operation/subscription source + sequence

Bound all collections: scan observations, GATT tree snapshots, raw history per attribute, outbound writes, notifications, logs. State replacement must release old Android object references after disconnect/service change.

UI state flows one way: intent -> owner -> callback/result -> reducer -> immutable state -> composable. Callback timestamps/status/raw bytes enter before decoding so failures remain inspectable.

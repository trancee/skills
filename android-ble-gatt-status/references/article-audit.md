# Supplied article audit

Source: [DEV status-133 article](https://dev.to/ble_advertiser/demystifying-android-ble-gatt-status-133-common-causes-and-robust-solutions-for-connection-32la), published 2026-04-04. Treat as secondary guidance.

Keep:
- status 133 is generic/insufficient by itself
- explicit connection state ownership, cleanup, callback brevity, bounded retry/backoff, and real-device comparison matter
- direct versus automatic connection intent must be deliberate

Correct before reuse:
- Current Android API 37/37.1 public `BluetoothGatt` exposes no `GATT_ERROR`/133 constant. It exposes `GATT_FAILURE=257`, `GATT_CONNECTION_CONGESTED=143`, and `GATT_CONNECTION_TIMEOUT=147`; retain raw 133 as opaque legacy evidence.
- Inspect `status` before `newState`; a connected state with non-success status is not success.
- `autoConnect=true` is not the same as API 37 opportunistic mode; settings expose them separately.
- Fixed 500 ms service-discovery delay is cargo-cult timing unless a bounded device experiment proves it.
- “Never close before STATE_DISCONNECTED” can leak indefinitely when callback never arrives. Retire the epoch, attempt bounded graceful disconnect when relevant, then close by deadline.
- Retry must close the callback’s exact GATT before creating a fresh attempt. A shared field can already reference another attempt.
- The sample retry executor is declared once, shut down, and then scheduled again; it cannot be reused and can reject retries.
- The sample can schedule retry before closing the failing GATT and can schedule duplicate retry paths.
- Retrying every non-success status hides permission, adapter, security, user-cancel, and permanent configuration failures.
- Raw address lookup/logging assumes durable identity and leaks an identifier; use scan/association/product identity and redact logs.
- Legacy permission declarations need max-SDK branches and operation-specific runtime requests.
- Programmatic Bluetooth disable/enable is deprecated and unavailable to ordinary target-33+ apps; user toggling is diagnostic only.
- “stack corruption” is not established by status 133; require cross-client and lower-layer evidence.

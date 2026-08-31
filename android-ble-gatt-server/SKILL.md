---
name: android-ble-gatt-server
description: "Implements, reviews, tests, and troubleshoots Android BluetoothGattServer applications. Use when publishing local services, characteristics, and descriptors; handling characteristic or descriptor reads and writes, prepared-write transactions, CCCD subscriptions, per-central MTU and state, notification or indication flow control, service-add sequencing, and GATT server shutdown. Don't use for remote GATT client operation queues, scanning or advertising lifecycle, RFCOMM or LE CoC sockets, platform-independent schema design, throughput tuning, pairing cryptography, or non-Android stacks."
compatibility: "Targets Android BluetoothGattServer from API 18 through API 37.2 documentation. Prefer API 33+ value-taking notifyCharacteristicChanged; mutable attribute value APIs are deprecated. API 37.2 adds connection-update callback symbols absent from public API 37.0/37.1 SDK stubs, so branch by the actual compile SDK. Inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://developer.android.com/reference/android/bluetooth/BluetoothGattServer"
  sourceVersion: "Android API 37.2 documentation 2026-08-31; API 37.0/37.1 public SDK stubs verified 2026-08-31"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T09:30:06+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T09:30:06+02:00"
---

# Android BLE GATT Server

## Step 1: Define the local GATT server contract

1. DEFINE local service database | characteristic/descriptor read | immediate write | prepared/execute write | CCCD subscription | notification/indication | multiple centrals | connection/MTU | service update | shutdown.
2. IDENTIFY min/compile/target SDK, device/OEM/client matrix, peripheral and GATT-server roles, logical schema/version, UUID/instance identity, properties/permissions/security, per-central state, value encoding/limits, response status mapping, prepared-write budget, CCCD policy, notification queue, callback confinement, advertising owner, server lifetime, and process-death recovery.
3. READ current [`BluetoothManager`](https://developer.android.com/reference/android/bluetooth/BluetoothManager), [`BluetoothGattServer`](https://developer.android.com/reference/android/bluetooth/BluetoothGattServer), and [`BluetoothGattServerCallback`](https://developer.android.com/reference/android/bluetooth/BluetoothGattServerCallback) symbol pages for every used API.
4. READ `references/api-contracts.md` for server/client boundaries, unsupported profile queries, API 33 value methods, and API 37.2 availability.
5. ROUTE scanning/advertising/background/permission lifecycle to `android-ble`, remote `BluetoothGatt` client operations to `android-ble-gatt-queue`, logical schema/profile design to `ble-protocol-stack`, and sockets to `android-bluetooth-sockets`.

Completion: database, every ATT callback/response, per-central state, transaction/notification ordering, lifecycle owner, and SDK/device matrix are explicit.

## Step 2: Inspect the Android project

RUN from the Android project root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM manifest/SDK, `openGattServer`, retained/closed server ownership, service-add callback sequencing, characteristic/descriptor properties and permissions, request offset/length/status/response handling, prepared-write staging/execute, per-device CCCD state, API 33 notifications, `onNotificationSent` serialization, unsupported server profile calls, callback confinement, and teardown.

Completion: every warning is fixed or retained with a source-backed rationale and a real-client test.

## Step 3: Build the local attribute database

READ `references/database.md`.

1. COPY the logical service/characteristic/descriptor schema from `ble-protocol-stack`; preserve stable logical IDs separately from Android object identity.
2. CREATE `BluetoothGattService` with explicit primary/secondary type, `BluetoothGattCharacteristic` with properties and permissions, and only required `BluetoothGattDescriptor` objects.
3. ADD CCCD (`0x2902`) to each notify/indicate characteristic that supports client configuration; keep its effective value per central outside the shared descriptor object.
4. MATCH requests by the current server generation plus service/characteristic/descriptor instance. UUID-only lookup returns the first duplicate and is insufficient when repeated UUIDs are legal.
5. KEEP authoritative dynamic values in application state; treat Android attribute objects as database declarations/bindings rather than per-central mutable storage.
6. BOUND every attribute value to the schema and GATT’s 512-byte maximum before allocation/mutation.

Completion: schema validator passes; property/permission/security/value rules and duplicate-instance identity are covered by tests.

## Step 4: Open and publish the server sequentially

1. OBTAIN `BluetoothManager` from application context and open one `BluetoothGattServer` after `BLUETOOTH_CONNECT`, adapter, and lifecycle checks. Handle a failed/null open.
2. RETAIN the server for the complete peripheral session; confine callback-to-state mutation through one serial executor/handler/actor because `openGattServer` has no callback-executor parameter.
3. ADD included/secondary service dependencies before their parent where required by the schema.
4. CALL `addService` once; if submission returns `false`, fail that publication immediately. Wait for matching `onServiceAdded` and require `GATT_SUCCESS` before adding the next service.
5. START advertising through the `android-ble` owner only after every required service is published; stop/reconcile advertising when database readiness changes.
6. IF updating an exposed database, version the schema, expect Service Changed behavior, and test client cache invalidation before claiming compatibility.

Completion: open failure, add rejection, callback failure, ordered dependencies, duplicate UUIDs, database update, and advertising readiness have deterministic transitions.

## Step 5: Own connections and per-central state

1. TRACK each `BluetoothDevice` in server-owned state keyed by current server generation/device identity: connection, negotiated MTU, authorization, CCCD values, pending prepared writes, notification queue, and in-flight notification.
2. ON `onConnectionStateChange`, evaluate `status` before `newState`; initialize state only for successful connected transitions and clear all per-device state on failure/disconnect.
3. USE `BluetoothManager.getConnectedDevices(BluetoothProfile.GATT_SERVER)` only as a system/profile snapshot. Never call `BluetoothGattServer.getConnectedDevices`, `getConnectionState`, or `getDevicesMatchingConnectionStates`; those throw `UnsupportedOperationException`.
4. TREAT MAC/name/bond as transport hints, not application identity. Bind application authorization to an authenticated protocol/session where sensitive operations require it.
5. UPDATE per-device MTU from `onMtuChanged`; retain payload limits per central rather than one global MTU.
6. USE server-initiated `connect(device, autoConnect)` only for a documented product flow; correlate completion by device/generation and cancel with `cancelConnection` on teardown.

Completion: simultaneous centrals, status failure, disconnect/reconnect, identity rotation, MTU differences, and stale callbacks cannot share or retain state.

## Step 6: Complete characteristic and descriptor reads

READ `references/request-response.md`.

1. ON each read callback, validate generation/device, attribute instance, readable permission/application authorization, and `0 <= offset <= value.size`.
2. IF invalid, call `sendResponse` once with the precise GATT status, request ID, request offset, and no value.
3. IF valid, snapshot the authoritative value, slice from the requested offset within schema/transport limits, and call `sendResponse` once with `GATT_SUCCESS`.
4. FOR CCCD reads, return that central’s stored two-byte configuration rather than shared descriptor value state.
5. CHECK the Boolean returned by `sendResponse`; a failed submission is a connection/session failure signal, not permission to send a duplicate response.
6. KEEP callbacks nonblocking; snapshot/validate/respond on the confined owner and hand expensive application work elsewhere before a product deadline is exceeded.

Completion: zero/end/out-of-range offsets, dynamic value races, authorization failures, duplicate UUID instances, response rejection, and disconnect races each produce at most one response.

## Step 7: Handle immediate and prepared writes transactionally

READ `references/prepared-writes.md`.

1. VALIDATE every write’s generation/device, attribute instance, property/permission/security, offset, chunk/value size, schema encoding, and application authorization before mutation.
2. FOR an immediate write (`preparedWrite == false`), apply atomically only after validation; call `sendResponse` exactly once when `responseNeeded == true`, and send no response for a write command.
3. FOR a prepared write, stage a copied fragment by server generation, device, attribute instance, offset, and request ID. Reject overlap/gap/policy violations and enforce per-device transaction bytes/fragments/deadline.
4. ECHO the accepted prepare fragment/offset in its response when a response is required; never mutate the authoritative value yet.
5. ON `onExecuteWrite`, if `execute == false`, discard all staged fragments and respond success. If true, validate complete assembled values and cross-attribute invariants, commit all atomically, then respond once.
6. ON execute validation failure, commit nothing, discard the transaction, and return the precise error. Clear staging on disconnect, timeout, server close, or generation change.

Completion: immediate commands/requests, fragmented/out-of-order/overlap/oversize prepared writes, cancel, atomic multi-attribute execute, duplicate execute, and disconnect are deterministic.

## Step 8: Implement CCCD subscriptions per central

1. ACCEPT CCCD values only for disable, notification, or indication and only when the parent characteristic exposes the matching property.
2. APPLY CCCD writes to per-device subscription state after offset/length/security validation; do not store one shared descriptor value across centrals.
3. HANDLE prepared CCCD writes through the same transaction engine; activate/deactivate only at execute commit.
4. RETURN per-device CCCD state on descriptor reads and clear it on disconnect/server generation reset.
5. REQUIRE application authorization separately when subscribing exposes sensitive data; link-layer CCCD success alone is not product authorization.
6. NOTIFY only devices whose current CCCD state enables the selected notification/indication mode.

Completion: two centrals can select different modes; malformed/unsupported/security-failed/prepared writes and reconnect never leak subscription state.

## Step 9: Serialize notifications and indications

READ `references/subscriptions-notifications.md`.

1. COPY immutable payload bytes and reject values over 512 bytes or the target central’s effective ATT payload policy.
2. USE API 33+ `notifyCharacteristicChanged(device, characteristic, confirm, value)` and require synchronous `BluetoothStatusCodes.SUCCESS` before marking in flight.
3. KEEP one unambiguous in-flight send (server-wide by default); `onNotificationSent` identifies only device/status, so wait for it before sending additional notifications as Android requires.
4. ON callback success/failure, clear the exact in-flight item and advance/fail according to bounded per-device queue policy. Reject stale/duplicate/wrong-device callbacks.
5. SET `confirm = true` for indications and `false` for notifications only when CCCD/properties/product reliability contract agree.
6. DEFINE application acknowledgements/replay above GATT when delivery to the peer application matters; successful notification callback is not business-level processing proof.

Completion: submission rejection, callback failure, queue overflow, multi-central ordering, unsubscribe/disconnect, stale callback, notification, and indication paths preserve one-in-flight ordering.

## Step 10: Close, test, and report

READ `references/lifecycle-testing.md`.

1. STOP advertising, retire the server generation, reject new requests, cancel connections where appropriate, fail queues/transactions, clear services/state, and call `close()` exactly once.
2. IGNORE late callbacks from retired generations; do not reuse services/attributes/per-device state after reopening.
3. COMPILE against every supported SDK, including explicit API 33 and API 37.2 branches, and run deterministic callback-state tests.
4. RUN real-device tests with Android and non-Android GATT clients across permission, bond/security, MTU, cache, prepared-write, subscription, notification, process-death, and OEM conditions.
5. COPY `assets/gatt-server-report.md`; record schema, request/response matrix, transactions, per-central state, notification flow, lifecycle, evidence, and limitations.

Completion: static audit, deterministic tests, compilation, and real-client traces prove every database/request/notification/teardown invariant.

## Error Handling

- `openGattServer` fails/null -> verify adapter/support/permission/process state; do not construct a half-ready database owner.
- Second `addService` fails/races -> submit only after matching `onServiceAdded(GATT_SUCCESS)` for the first.
- Read hangs on client -> send exactly one response with matching device/request ID/offset and inspect its Boolean result.
- Write command gets an extra response -> honor `responseNeeded`; only write requests receive `sendResponse`.
- Prepared write mutates early -> stage copied fragments and commit only from successful execute.
- CCCD state leaks between clients -> key subscription state by device/generation; descriptor objects are shared declarations.
- Notifications return errors or reorder -> use API 33 submission status, one in-flight send, and `onNotificationSent` before advancing.
- Client sees stale services -> version database, wait for publication callbacks, send/test Service Changed behavior, and rediscover.
- Connected-device query throws -> call `BluetoothManager` with `GATT_SERVER`, not unsupported `BluetoothGattServer` query methods.
- API 37.2 symbol fails compilation -> guard against the actual compile SDK; 37.0/37.1 stubs lack the new connection-update callback/threshold APIs.

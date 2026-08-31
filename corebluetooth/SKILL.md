---
name: corebluetooth
description: "Implements, reviews, tests, and troubleshoots Apple Core Bluetooth central and peripheral apps. Use when scanning, connecting, discovering services, reading, writing, subscribing, advertising, publishing local GATT services, restoring state, handling background execution, opening L2CAP channels, or diagnosing CBError, CBATTError, write backpressure, stale peripherals, and delegate races. Don't use for Android BluetoothGatt, platform-independent BLE schema design, throughput or PHY tuning, pairing cryptography, Nearby Interaction, MultipeerConnectivity, External Accessory, unsupported arbitrary Bluetooth Classic profiles, or UI unrelated to Bluetooth."
compatibility: "Uses Apple Core Bluetooth documentation available 2026-08-31. Verify API/platform availability at the deployment target: CBPeripheralManager advertising is unavailable on watchOS, tvOS, and visionOS; Core Bluetooth background modes are unavailable to iPad apps running on macOS. iOS 26 adds documented Live Activity background privileges. Inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://developer.apple.com/documentation/corebluetooth"
  sourceVersion: "Apple Core Bluetooth documentation 2026-08-31; archived background guide 2013-09-18"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T08:33:01+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T08:33:01+02:00"
---

# Core Bluetooth

## Step 1: Define the Apple Bluetooth contract

1. DEFINE central/client | local peripheral/server | both roles | scanning | connection | discovery | read/write/subscribe | advertising | ATT request | L2CAP | background | restoration | Classic sample.
2. IDENTIFY Apple platforms and deployment versions, foreground/background lifecycle, peer/controller matrix, GAP and GATT roles, service/characteristic UUIDs, value schemas, security, manager owner, delegate queue/isolation, operation correlation, flow control, reconnect/restoration policy, and observable failures.
3. READ the current [Core Bluetooth overview](https://developer.apple.com/documentation/corebluetooth) and exact symbol pages for every changed API.
4. READ `references/platform-contracts.md` for privacy, availability, supported advertising, iOS 26 background behavior, and Classic limits.
5. ROUTE logical GAP/GATT/ATT/L2CAP schema design to `ble-protocol-stack`, throughput/PHY/packet tuning to `ble-throughput`, and Android APIs to `android-ble`.

Completion: roles, platforms, privacy/background requirements, state owner, callback/result boundaries, and device acceptance matrix are explicit.

## Step 2: Inspect the Apple project

RUN from the project root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM manager/delegate ownership, `poweredOn` gating, privacy keys, background modes, scan filters/stopping, retained peripherals, connection cancellation, discovery callbacks, write/notification flow control, local service publication, ATT responses/offsets, restoration identifiers, and unsupported subclassing.

Completion: every reported warning is fixed or recorded with source-backed rationale.

## Step 3: Establish manager ownership and platform configuration

1. OWN each `CBCentralManager`/`CBPeripheralManager` for the required lifetime; keep Core Bluetooth state on its serial delegate queue or an explicit isolation bridge.
2. SET a non-`nil` delegate and deliberate dispatch queue. A `nil` queue dispatches delegate events on the main queue.
3. WAIT for `centralManagerDidUpdateState`/`peripheralManagerDidUpdateState`; call role APIs only in `.poweredOn` and model `.unknown`, `.resetting`, `.unsupported`, `.unauthorized`, and `.poweredOff` separately.
4. ADD `NSBluetoothAlwaysUsageDescription`; when deploying before iOS 13, also add `NSBluetoothPeripheralUsageDescription`. Verify current platform entitlement/sandbox requirements.
5. CHECK `CBManager.authorization` where authorization state affects UI or recovery. Let system authorization flow result from legitimate API use; provide settings/recovery behavior for denied/restricted states.
6. KEEP manager owners outside ephemeral SwiftUI view values and cancel role activity during deliberate teardown.

Completion: manager lifetime, queue/isolation, state transitions, privacy strings, authorization recovery, and teardown are exercised.

## Step 4: Implement the central role

READ `references/central-role.md`.

1. SCAN only after `.poweredOn`; prefer explicit service UUIDs, parse advertisement data defensively, deduplicate by peripheral identifier/product identity, and stop when the scan objective is met.
2. RETAIN the selected `CBPeripheral`; a deallocated peripheral implicitly cancels its pending connection.
3. CONNECT with explicit product timeout because Core Bluetooth connection attempts do not time out; cancel with `cancelPeripheralConnection` on timeout or user cancellation.
4. ON connect, set `peripheral.delegate`, then discover only required services, characteristics, and descriptors in callback order.
5. HANDLE connect failure, disconnect, reconnecting disconnect callbacks, manager reset/power loss, and restored peripherals through one connection state machine.
6. ON `didModifyServices`, discard every invalidated `CBService`/characteristic reference and rediscover before use.

Completion: scan, retain, connect, cancel, discover, disconnect, service invalidation, and reconnect transitions terminate without stale objects or duplicate owners.

## Step 5: Implement central GATT operations and subscriptions

READ `references/data-flow.md`.

1. VALIDATE characteristic properties before read/write/subscribe and map each call to its exact `CBPeripheralDelegate` result.
2. CORRELATE callback-completing work by peripheral, attribute instance, operation kind, and connection generation. Serialize when overlapping operations share a callback route or correlation is otherwise ambiguous.
3. TREAT `didUpdateValueFor` as both read completion and notification delivery; keep subscription events separate from one-shot caller completion.
4. FOR `.withResponse`, complete on `didWriteValueFor`; for `.withoutResponse`, expect no per-write callback and gate chunks with `canSendWriteWithoutResponse` plus `peripheralIsReady(toSendWriteWithoutResponse:)`.
5. QUERY `maximumWriteValueLength(for:)` for the selected write type; implement application framing, ordering, integrity, and retry semantics above Core Bluetooth.
6. CONSIDER subscription ready only after `didUpdateNotificationStateFor` succeeds; continue handling updates until disable/disconnect.
7. RESET pending work on disconnect, manager reset, service invalidation, or timeout; ignore callbacks belonging to retired generations.

Completion: reads, writes, subscriptions, errors, cancellation, backpressure, and stale callbacks produce exactly one product-level outcome.

## Step 6: Implement the local peripheral role

READ `references/peripheral-role.md`.

1. BUILD `CBMutableService`/`CBMutableCharacteristic` values from the logical schema only after `.poweredOn`; publish included services before their parent.
2. WAIT for `didAdd` before considering a service published; remove/rebuild services after manager reset as required by the state model.
3. START advertising only on supported platforms and handle `peripheralManagerDidStartAdvertising`; use only local-name and service-UUID keys supported by Core Bluetooth.
4. VALIDATE every `CBATTRequest` characteristic, permissions, offset, length, value, and application authorization. Respond exactly once to each read callback.
5. TREAT a write-request array atomically: validate all, apply all only on success, then respond once using the first request; reject the whole batch if one request fails.
6. TRACK subscribe/unsubscribe callbacks and send updates only to intended subscribers.

Completion: service publication, advertising, read/write responses, batch atomicity, offsets, subscriptions, and teardown pass central-to-peripheral device tests.

## Step 7: Enforce peripheral notification flow control

1. SIZE each update against every target `CBCentral.maximumUpdateValueLength`; choose a chunk size safe for the selected recipients.
2. CALL `updateValue`; when it returns `false`, retain the unsent chunk and stop submitting.
3. RESUME only from `peripheralManagerIsReady(toUpdateSubscribers:)`; retry the same unsent chunk before advancing.
4. DEFINE framing and per-central progress when subscriber limits differ. Treat successful enqueue as transport acceptance, not application acknowledgement.
5. BOUND application queues and define overflow/disconnect policy; never spin or sleep-poll the Core Bluetooth transmit queue.

Completion: queue-full, resume, multi-central chunking, unsubscribe, disconnect, and application backpressure preserve order without loss or unbounded memory.

## Step 8: Add background execution and restoration only when required

READ `references/background-restoration.md`.

1. ADD `bluetooth-central` and/or `bluetooth-peripheral` background modes only for a user-visible session requiring that role.
2. USE explicit service UUIDs for background scans. Account for coalesced discoveries, slower scans, ignored scan options, hidden local name, and overflow-only service UUID advertising.
3. PROCESS Bluetooth wake events quickly and return control; background modes do not grant indefinite execution.
4. FOR long-lived pending connections/scans/advertising, assign a stable distinct restoration identifier, persist it, and pass it on every manager initialization.
5. IMPLEMENT `willRestoreState`; reattach delegates, retain restored peripherals/services, reconcile actual restored state idempotently, and resume only missing work.
6. IN scene-based apps, persist manager UIDs because launch options are unavailable for identifier delivery.
7. USE iOS 26 Live Activity background privileges only when the product legitimately owns a Live Activity; verify current ActivityKit/Core Bluetooth rules rather than using it as a generic keepalive.

Completion: foreground-only, suspended, Bluetooth wake, system termination/restoration, scene launch, force quit, and unsupported-platform behavior match documented guarantees.

## Step 9: Handle errors and teardown

1. MAP `CBError`, `CBATTError`, manager states, callback `Error`, product timeout, cancellation, and protocol errors into typed outcomes without discarding code/domain/context.
2. CANCEL scans/connections/subscriptions/advertising and fail pending operations exactly once when ownership ends.
3. CLEAR invalid peripheral/service/characteristic references on disconnect, service modification, or manager reset; reconnect through a fresh generation.
4. KEEP delegate callbacks nonblocking; copy required data/state on the delegate queue, then hand bounded work to application processing.
5. LOG manager/peripheral generation, operation, UUID role, callback, elapsed time, and error code without device identifiers or characteristic payloads unless explicitly safe.

Completion: every callback, timeout, cancellation, reset, and teardown path has one owner and one terminal result.

## Step 10: Verify and report

READ `references/testing.md`.

1. RUN deterministic state-machine/flow-control tests, compile against every supported platform/deployment target, and exercise two real Bluetooth devices.
2. VERIFY privacy crash prevention, authorization states, powered-off/resetting, scan/connect/discovery failures, write modes, notification backpressure, ATT offsets/batches, background transitions, and restoration.
3. CAPTURE over-air evidence when advertisement bytes, ATT procedures, errors, or peer behavior cannot be proven from app callbacks.
4. COPY `assets/corebluetooth-report.md`; record platform matrix, ownership, role flows, flow control, background/restoration, verification, and limitations.

Completion: simulator/unit evidence covers app logic; real-device and trace evidence covers radio, peer, background, and restoration behavior.

## Error Handling

- Manager remains `.unknown`/`.resetting` -> wait for state callback; never infer availability from construction.
- App crashes on Bluetooth access -> add the deployment-appropriate usage-description keys to the built target’s effective `Info.plist`.
- Scan finds nothing in background -> provide service UUID filters and test overflow/coalescing/slower scan behavior on devices.
- Connection hangs -> retain the peripheral, run a product timeout, and call `cancelPeripheralConnection`; Core Bluetooth has no implicit connect timeout.
- Discovery callback succeeds but attributes are missing -> validate exact UUIDs and rediscover only from current-generation services.
- Read continuation consumes notification -> separate subscription stream from one-shot reads or serialize the ambiguous characteristic route.
- `.withoutResponse` floods/stalls -> obey `canSendWriteWithoutResponse` and resume callback; no write-result callback exists.
- Peripheral update returns `false` -> retain/retry the same chunk after readiness callback.
- ATT request hangs -> validate offset/value and call `respond(to:withResult:)` exactly once; write batches respond with their first request.
- Restoration duplicates work -> reconcile restored objects and current properties before scanning, reconnecting, republishing, or resubscribing.
- App subclasses a `CB*` framework class -> replace inheritance with composition; Core Bluetooth class subclassing is unsupported.

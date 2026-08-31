---
name: android-ble-inspector
description: "Builds, reviews, tests, and troubleshoots Android BLE inspector and diagnostic-tool apps with Jetpack Compose. Use when creating scanner device lists, GATT trees, read or write controls, subscription progress, raw and decoded value views, local advertiser/server demos, standard health decoders, or real-device investigation workflows. Don't use for headless production BLE libraries, standalone GATT queue or server implementations, platform-independent schema design, Bluetooth Classic or socket transports, RF or throughput optimization, general Compose UI, or medical diagnosis and interpretation."
compatibility: "Targets Android-only Jetpack Compose diagnostic apps and composes Android BLE platform skills through API 37. Source project uses min SDK 26, target SDK 36, Kotlin 2.2.10, and AGP 9.2.1; verify current project versions rather than copying them. Physical devices are required for BLE behavior. Analyzer requires Python 3.11+."
metadata:
  category: "development"
  source: "https://gist.githubusercontent.com/roywatson/7ce389862e245a622dba2e34e28331e6/raw/506e408d1fa9f7616c4b4c00d7efb43ddd414cd8/android_ble_tools.md"
  sourceVersion: "gist revision 506e408d1fa9f7616c4b4c00d7efb43ddd414cd8; repository inspected 2026-08-31"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T09:38:56+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T09:38:56+02:00"
---

# Android BLE Inspector

## Step 1: Define the diagnostic contract

1. DEFINE scanner | advertisement viewer | GATT tree | characteristic read | controlled write | notify/indicate observation | standard decoder | local greeting peripheral | timing/race investigation | hardware interoperability.
2. IDENTIFY Android/device/OEM and peer matrix, supported roles, intended users, foreground-only lifecycle, permission profiles, scan power/time/filter policy, device identity/display policy, connection/GATT owners, safe operation set, write confirmation, raw-data sensitivity/retention, decoder source/version, and evidence to capture.
3. DEFAULT to read-only inspection. Enable writes, subscriptions, adapter mutation, or local peripheral behavior only through explicit visible user actions and capability checks.
4. READ `references/article-audit.md` before copying the supplied sample’s operation mutex, address deduplication, health parsers, advertisement sizing, name resolution, or adapter-name behavior.
5. ROUTE platform lifecycle to `android-ble`, remote GATT serialization to `android-ble-gatt-queue`, local GATT server behavior to `android-ble-gatt-server`, logical schemas to `ble-protocol-stack`, and general Compose architecture to `compose-multiplatform`.

Completion: diagnostic questions, allowed radio mutations, ownership, data sensitivity, decoder authority, device matrix, and proof outputs are explicit.

## Step 2: Inspect the project

RUN from the Android project root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM Compose/ViewModel/lifecycle collection, permission profiles, scan callback cleanup/timeout/failure, filter/power policy, device identity, connection/GATT queue, explicit operation UI states, CCCD subscription, raw-byte rendering, decoder bounds/special values, advertiser failure/size handling, adapter-name mutation, test coverage, and device-data logging.

Completion: every warning is fixed or tied to a documented diagnostic requirement and device test.

## Step 3: Compose thin diagnostic modules

READ `references/architecture.md`.

1. KEEP Android platform behavior visible behind small role interfaces: scanner, central connector, connected peripheral, local peripheral server, decoder registry, and evidence recorder.
2. KEEP each platform owner concrete and lifecycle-bound; interfaces clarify screens/tests but never pretend BLE callback, permission, queue, and background behavior is platform-neutral.
3. HOIST immutable screen state into ViewModels; keep sockets/GATT/scanner/advertiser/server objects outside composables and cancel them from owner teardown.
4. EXPOSE operation IDs, queued/in-flight state, timestamps, callback status, and raw bytes so the inspector explains delay instead of hiding it.
5. COLLECT `StateFlow` with `collectAsStateWithLifecycle` on Android and model one-shot UI events separately from durable BLE state.

Completion: each radio/GATT object has one non-composable owner; screens render state and send intents only.

## Step 4: Implement action-scoped permission UX

1. MAP scan, connect/read/subscribe, advertise/server, and combined demo actions to the exact runtime permissions and legacy branches defined by `android-ble`.
2. REQUEST only the profile required by the user’s current action; explain why before the system prompt and preserve a denied/permanently-denied recovery state.
3. APPLY `neverForLocation` only when the inspector never derives physical location; record its filtering implications and avoid simultaneous location claims.
4. CHECK BLE hardware, adapter support/state, scanner/advertiser availability, and permission immediately before the action because settings may change while the UI remains open.
5. SHOW disabled controls with actionable reasons instead of throwing `SecurityException` or silently doing nothing.

Completion: every tab/action has granted, denied, permanently denied, unsupported, Bluetooth-off, and revoked-during-operation behavior.

## Step 5: Build the scanner and device-selection surface

1. WRAP `startScan` in `callbackFlow`; install the exact callback before start and call `stopScan(callback)` from `awaitClose` plus explicit stop/timeout paths.
2. HANDLE `onScanFailed`, permission revoke, adapter-off, owner cancellation, and repeated Start/Stop idempotently.
3. USE service/manufacturer/service-data filters when answering a targeted question. Use low-latency scanning only during a visible bounded interactive session.
4. MODEL observations separately from product identity: preserve current `BluetoothDevice`, address type/ephemeral identifier, latest advertisement bytes, RSSI, timestamp, and deduplication evidence.
5. NEVER key durable identity solely by address/name/RSSI. Redact addresses by default and avoid connecting to every unnamed device merely to resolve a display name.
6. RENDER a stable-key lazy list with age/RSSI, connectability, advertised UUIDs/data summaries, raw advertising bytes, and clear scan status/error/stop controls.

Completion: timeout, cancellation, screen exit, scan failure, duplicate/rotating-address observations, large result sets, and missing names stop cleanly and remain diagnosable.

## Step 6: Build connection and GATT-tree inspection

1. CONNECT only the user-selected observation through the `android-ble` epoch state machine; stop or deliberately continue scanning according to the test contract.
2. SHOW `Connecting -> Discovering -> Ready` with elapsed time and callback/status failures. Never show connected/ready before matching callbacks settle.
3. AFTER discovery, snapshot services, characteristics, descriptors, UUIDs, instance IDs, properties, permissions, and current generation into immutable UI models.
4. KEY tree rows by connection generation plus service/characteristic/descriptor instance, not UUID alone; duplicate UUID instances are valid.
5. RENDER the tree lazily and disclose details on demand. Always expose full UUID and properties; map names only from a versioned registry and label unknowns honestly.
6. INVALIDATE the complete tree on service change, disconnect, permission loss, GATT close, or new connection generation.

Completion: slow discovery, duplicate UUIDs, service change, disconnect/reconnect, rotation, and large trees cannot display or operate on stale Android objects.

## Step 7: Model reads, writes, and observations explicitly

READ `references/ui-state.md`.

1. ROUTE every GATT operation through `android-ble-gatt-queue`; a mutex is valid only when held through callback completion and reset-on-timeout semantics.
2. ENABLE controls only when the matching characteristic property and current state allow the operation.
3. ASSIGN each user intent an operation ID and display queued/in-flight/success/error/timeout/cancelled state plus elapsed time. Disable only conflicting actions, not unrelated inspection.
4. FOR subscriptions, show `Subscribing` until local routing and CCCD write callback succeed; show `Unsubscribing` until CCCD disable settles.
5. KEEP notification values as a bounded event/history stream independent from one-shot read completion.
6. REQUIRE a confirmation surface for writes showing target UUID/instance, write type, encoded bytes/length, expected side effect, and lack of rollback. Default unknown characteristics to no-write.
7. ON timeout, close/reset the GATT generation and mark queued operations invalid; never retry into an uncertain connection.

Completion: rapid multi-row taps, slow callbacks, rejection, timeout, cancellation, notifications during reads, and reconnect preserve exact operation/UI correlation.

## Step 8: Render raw bytes and verified decoders

READ `references/decoding.md`.

1. COPY callback bytes and retain a bounded in-memory sample history with monotonic time and source operation/event ID.
2. SHOW byte count, hex, printable ASCII with escaped/nonprintable markers, and optional structured decode side by side. Raw bytes remain available when decoding fails.
3. SELECT decoders by service + characteristic + schema/profile version, not characteristic UUID alone when context can disambiguate.
4. VALIDATE every flags byte, required/optional field length, byte order, reserved bits/values, units, range, and trailing-byte policy before emitting a typed result.
5. REPRESENT IEEE-11073 SFLOAT special values (`NaN`, `NRes`, positive/negative infinity, reserved) explicitly rather than converting them into ordinary floats.
6. LABEL health values as protocol decoding, not diagnosis; use current adopted Bluetooth SIG service/characteristic specifications and mandatory errata.
7. UNIT-TEST valid boundaries, every optional-field combination, truncation, unknown flags, reserved values, and raw formatting deterministically.

Completion: malformed/truncated/unknown/profile-version bytes never crash, overread, or masquerade as a valid measurement.

## Step 9: Add an optional local peripheral demo safely

1. ROUTE GATT database/read/write/CCCD/notification mechanics to `android-ble-gatt-server` and advertising ownership to `android-ble`.
2. PUBLISH the GATT database fully before advertising the service; show server/advertiser start, connection, request, subscription, and failure state separately.
3. CALCULATE legacy advertising and scan-response payload budgets including AD structure overhead; handle `ADVERTISE_FAILED_DATA_TOO_LARGE` and extended-advertising capability explicitly.
4. USE the adapter’s existing name only when requested. Do not change the global Bluetooth adapter name for a transient inspector label; a crash can strand device-wide state.
5. STOP advertising, close GATT server, restore only state the app truly owns, and clear connected-central state on tab exit/owner teardown.

Completion: unsupported advertising, oversized payload, partial server publication, two centrals, adapter-off, permission revoke, exit, and process death leave no global mutation or leaked server.

## Step 10: Verify on deterministic logic and physical hardware

READ `references/testing.md`.

1. RUN JVM tests for UUID/name mapping, immutable models, raw formatting, every decoder branch, operation/UI reducers, and advertisement-size calculations.
2. RUN Compose semantics tests for permission states, scan controls, stable device/tree rows, progress/error/confirmation, raw/decoded output, and accessibility.
3. RUN the actual app on representative physical Android devices and peripherals; exercise scanner, client, subscription, local server/advertiser, timing, failure, and lifecycle paths.
4. CAPTURE callback timeline, operation IDs, status, queue depth, raw bytes, and optional HCI trace with explicit redaction/export controls.
5. COPY `assets/ble-inspector-report.md`; record diagnostic scope, safety policy, screens/states, platform modules, decoder sources/tests, hardware matrix, findings, and limitations.

Completion: deterministic tests prove parsers/state; Compose tests prove controls; physical traces prove BLE/OEM/peer behavior. Emulator-only evidence is insufficient.

## Error Handling

- Scan continues after screen exit -> use one `callbackFlow` owner and stop the identical callback from `awaitClose`/timeout/Stop.
- Rows merge different peripherals -> separate observation identity from product identity; never persist address-only deduplication as truth.
- Inspector connects to every unnamed device -> stop probing; show unknown names or require user-selected targeted resolution.
- Read button appears frozen -> render queued/in-flight elapsed state and await the matching callback; do not use a shorter retry loop.
- Subscription shows active without values -> wait for CCCD callback and expose local-routing versus remote-configuration failures.
- Notification completes a read -> separate observation events from operation completion through the GATT queue.
- Decoder crashes or shows impossible health value -> validate flags/length/reserved SFLOAT values against the adopted SIG specification and keep raw bytes visible.
- Advertisement fails as too large -> calculate the exact selected advertising mode/packet budget and trim/move fields; 31 bytes is a legacy-advertising constraint, not a universal limit.
- Device name remains changed after crash -> remove adapter-name mutation; the Bluetooth adapter name is global device state.
- Hardware behavior differs from JVM tests -> trust the physical callback/HCI timeline; mocks prove only deterministic app logic.

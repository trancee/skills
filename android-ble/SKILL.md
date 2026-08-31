---
name: android-ble
description: "Implements, migrates, tests, and troubleshoots Android Bluetooth Low Energy discovery, advertising, GATT client, and platform lifecycle. Use when building scan, advertise, GATT connection, or subscription flows; handling Nearby Devices permissions; maintaining background connections with CompanionDeviceService or connectedDevice foreground services; adopting Android 17 BluetoothGattConnectionSettings and autonomous re-pairing; or diagnosing scan, bond, MTU, process-death, and OEM failures. Don't use for local GATT server request/response internals, coroutine GATT operation-queue internals, BluetoothSocket RFCOMM or LE L2CAP CoC transports, Bluetooth Classic profiles, generic GAP/GATT schema design, PHY and throughput tuning, iOS CoreBluetooth, pairing cryptography, or UI unrelated to BLE."
compatibility: "Targets Android 17/API 37 while preserving explicit branches for Android 12/API 31 Nearby Devices permissions, Android 13/API 33 memory-safe GATT APIs, and Android 14/API 34 foreground-service types/MTU behavior. Android 17 affects all apps and target-37 apps differently; verify live behavior pages and SDK stubs. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://developer.android.com/develop/connectivity/bluetooth/ble/ble-overview"
  sourceVersion: "Android BLE overview 2026-02-26; Android 17 API 37/37.1 documentation 2026-08-28; supplied articles reviewed 2026-08-30"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T23:09:17+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T09:30:06+02:00"
---

# Android BLE

## Step 1: Define the Android BLE contract

1. DEFINE scan/discovery | advertise/peripheral | direct/automatic GATT connection | service discovery/cache | read/write/subscribe | background presence/connection | bond/re-pairing | Android 17 migration | OEM failure.
2. IDENTIFY min/compile/target SDK, device/Android/OEM matrix, BLE central/peripheral and GATT client/server roles, identity/filter, foreground/background/process-death behavior, permissions, association/bond model, connection owner, callback executor, operation queue, timeout/retry policy, and user-visible behavior.
3. READ `references/ble-overview.md` and the current [Android BLE overview](https://developer.android.com/develop/connectivity/bluetooth/ble/ble-overview) before choosing the platform flow, role names, or security boundary.
4. SEPARATE central/peripheral link roles from GATT client/server procedure roles. Name both axes in state, logs, and tests.
5. TREAT pairing/link protection as shared device transport security, not app isolation. For sensitive data, define application-layer confidentiality, authentication, and key ownership.
6. READ the official [Android BLE background guide](https://developer.android.com/develop/connectivity/bluetooth/ble/background), [Bluetooth permissions](https://developer.android.com/develop/connectivity/bluetooth/bt-permissions), and relevant API-level branch before editing.
7. READ `references/source-audit.md` before applying Android 17 claims from secondary sources. Separate all-app changes, target-37 changes, older enforced requirements, empirical OEM behavior, and Bluetooth Classic-only changes.
8. ROUTE local `BluetoothGattServer` database/request/notification internals to `android-ble-gatt-server`, remote client operation serialization/races to `android-ble-gatt-queue`, RFCOMM and LE L2CAP CoC socket transports to `android-bluetooth-sockets`, logical GAP/GATT/ATT/L2CAP design to `ble-protocol-stack`, PHY/MTU throughput tuning to `ble-throughput`, application security protocols to `noise-protocol`, and generic Kotlin/coroutine/build mechanics to their dedicated skills.

Completion: SDK/device matrix, both role axes, permission/background model, transport/application security boundary, connection/operation owner, and observable success/failure states are explicit.

## Step 2: Inspect the app

RUN from the Android project root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM SDK levels, BLE features/permissions, `neverForLocation`, foreground service types/permissions, scan API/filter/failure handling, advertisement callbacks, legacy/new `connectGatt`, connection settings/executor, GATT operation serialization, API 33 value-taking methods/callbacks, CCCD writes, MTU handling, Companion Device APIs, bond/pairing-context handling, background activity/audio/loopback paths, device-address identity, and cleanup.

Completion: every reported candidate is inspected in its lifecycle owner and mapped to an API-level branch.

## Step 3: Configure features and permissions

READ `references/permissions-manifest.md`.

1. DECLARE `android.hardware.bluetooth_le` required only when the app cannot function without BLE; check adapter/scanner/advertiser capability at runtime.
2. FOR target 31+, request `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT`, and/or `BLUETOOTH_ADVERTISE` only for used operations; retain legacy permissions/location with correct `maxSdkVersion` for older OS branches.
3. SET `neverForLocation` only when the product can truthfully guarantee scan results never derive location; otherwise request the applicable location permissions.
4. CHECK permission and adapter state at each externally triggered operation, including after revocation/process restoration; degrade to a user-actionable state instead of catching `SecurityException` broadly.
5. DECLARE foreground-service permissions/types and notification permission/channel for the exact background use case.

Completion: install/runtime permission paths pass for denied, granted, revoked, old-SDK, no-adapter, and disabled-adapter states.

## Step 4: Build scanning and advertising as owned sessions

READ `references/scanning-advertising.md`.

1. CREATE one idempotent scan/advertise session owner with explicit start/active/stop/failure states and the exact callback or `PendingIntent` identity needed to stop it.
2. USE validated `ScanFilter` service/manufacturer/service-data criteria. Unfiltered callback scans stop on screen-off; address/name/RSSI alone is not durable device identity.
3. USE callback scanning while the process is intentionally alive; use filtered `PendingIntent` scanning to wake a dead process, or Companion Device Manager for association/presence use cases.
4. HANDLE `onScanFailed`/PendingIntent error extras and advertiser callback status. Debounce Bluetooth/power/lifecycle transitions instead of start/stop retry loops.
5. PARSE advertising bytes defensively and version application identifiers; deduplicate by product identity plus observation epoch, not a permanently assumed random address.

Completion: start/stop/failure/permission/Bluetooth-toggle/process-death paths produce one session without silent restart storms.

## Step 5: Connect with an epoch-based GATT state machine

READ `references/gatt-lifecycle.md`.

1. ON API 37+, construct `BluetoothGattConnectionSettings` and call `connectGatt(settings, executor, callback)`; set transport, direct/auto-connect, automatic MTU, opportunistic mode, and supported thresholds deliberately.
2. ON older APIs, use the least-ambiguous `connectGatt` overload and explicit LE transport where required; isolate the compatibility branch.
3. ASSIGN a monotonically increasing connection epoch. Ignore callbacks from stale `BluetoothGatt` instances/epochs after cancel, disconnect, close, permission loss, or reconnect.
4. TRANSITION connect -> discover -> configure MTU/subscriptions -> ready. Evaluate both callback `status` and state; connection state alone is insufficient.
5. OWN `disconnect()` then `close()` exactly once and cancel queued/in-flight operations/timeouts on terminal state.

Completion: direct/auto connection, timeout, remote/local disconnect, status failure, reconnect, and stale callback tests pass without leaked GATT instances.

## Step 6: Integrate the dedicated GATT operation queue

1. READ and apply `android-ble-gatt-queue` for coroutine serialization, callback matching, cancellation, timeout/reset, and composite operation ownership.
2. USE API 33+ value-taking `writeCharacteristic`/`writeDescriptor` and value-bearing read/notification callbacks; copy byte arrays and avoid mutable characteristic/descriptor value fields.
3. KEEP subscription semantics explicit: local `setCharacteristicNotification` followed by queued CCCD write; ready only after descriptor success.
4. ON `onServiceChanged`, reset the queue epoch, invalidate cached objects/queued handles, and rediscover before further access.
5. ON Android 14+, account for first-client ATT MTU 517 request behavior; use automatic MTU settings/callback effective value rather than repeated requests.

Completion: the dedicated queue owns every callback-completing request while this connection lifecycle owns readiness, discovery, service changes, and MTU policy.

## Step 7: Choose background execution from the use case

READ `references/background-companion.md`.

1. IF the process only needs wake-on-match, use filtered `PendingIntent` scanning and short Worker/job work.
2. IF the app owns an associated companion and needs presence/long-lived connection, prefer Companion Device Manager/`CompanionDeviceService` with the exact association permissions.
3. IF a user-visible long transfer/connection needs process priority, start a `connectedDevice` foreground service while foreground or under a documented exemption; satisfy type-specific permission prerequisites before creation.
4. EXPECT process death to close GATT. Persist logical device/transfer state, never platform GATT objects, and rebuild discovery/subscription on restart.
5. STOP scans/connections/services when work ends; foreground service is not permission to maintain needless radio work.

Completion: foreground, background, screen-off, process-kill, reboot, permission-revoke, and user-stop behavior matches one documented mechanism.

## Step 8: Apply Android 17 changes precisely

READ `references/android17.md`.

1. TEST autonomous re-pairing on all apps running Android 17. Read `EXTRA_PAIRING_CONTEXT`; recognize `PAIRING_CONTEXT_REPAIRING`, preserve system UI/key replacement, and handle `ACTION_KEY_MISSING` only after failed repair.
2. MIGRATE target-37 GATT connections to `BluetoothGattConnectionSettings` plus explicit callback `Executor`.
3. ROUTE target-37 RFCOMM EOF migration and all `BluetoothSocket` behavior to `android-bluetooth-sockets`; never apply socket EOF behavior to GATT callbacks.
4. REPLACE background activity auto-launch with a user-visible notification/action unless a documented BAL exception applies.
5. FOR BLE-triggered audio, meet Android 17 visibility/foreground-service/WIU rules. A background-started `connectedDevice` service alone does not grant target-37 audio capability.
6. IF the BLE gateway uses loopback across Android profiles, redesign for Android 17's cross-profile block; same-profile loopback is unaffected. Do not add an undocumented permission as a guess.

Completion: each Android 17 item is classified as all-app, target-37, socket-only, cross-profile-only, or unrelated and has an exercised branch.

## Step 9: Handle pairing and identity

1. LET system pairing UI own ordinary user pairing. General apps do not silently set PINs/confirm pairing; API 37 deprecates `setPin(byte[])` and autonomous repair must not be intercepted.
2. TRACK bond transitions, pairing context, key-missing reason, transport, and connection epoch; wait for the required bond/security state before retrying protected GATT operations.
3. USE Companion Device association, bonded identity, or authenticated application identifier according to product threat model. Raw MAC/name/manufacturer data alone is not authenticated identity.
4. ROUTE LE L2CAP CoC PSM, security, stream framing, EOF, buffer, and close ownership to `android-bluetooth-sockets`.
5. ROUTE application-layer authentication/encryption protocol design to its protocol skill.

Completion: bond loss/repair/rejection, address rotation, and protected GATT access are deterministic.

## Step 10: Verify and report

READ `references/testing.md`.

1. COMPILE with API 37/37.1 SDK and run lint for target 37 plus supported older branches.
2. RUN instrumentation on Android 17 and representative Android 12–16/OEM devices for permissions, scan/advertise, direct/auto connection, service cache, operations, subscriptions, background/process death, bond repair, and user stop.
3. USE Android 17 compatibility toggles/ADB commands for audio behaviors where documented; capture logcat, bugreport/dumpsys, HCI snoop, callbacks, epochs, and statuses.
4. TEST platform API availability branches without reflection/string constant fallbacks and verify release manifest merging.
5. COPY `assets/android-ble-report.md`; fill SDK/device matrix, manifest/permissions, session states, GATT queue, background mechanism, Android 17 classification, evidence, and OEM limitations.

Completion: release build and real-device matrix prove every changed Android branch; unavailable hardware/OS behavior remains explicitly unverified.

## Error Handling

- Scan returns nothing -> check permission/location assertion, adapter/scanner, filter bytes, screen/background/process state, scan failure callback, restart frequency, and OEM policy before changing UUIDs.
- `SCAN_FAILED_APPLICATION_REGISTRATION_FAILED` -> stop duplicate scan owners, reuse stable callbacks, debounce restart transitions, and back off; the commonly reported 5-in-30-second threshold is empirical, not an Android 17 API contract.
- `SecurityException` starting foreground service -> verify manifest type/permission, runtime Nearby permission, foreground/exemption state, and type prerequisite before retry.
- Connect callback races after cancellation -> reject stale GATT/epoch, close once, and keep old callbacks from advancing the new state machine.
- GATT status failure/timeout -> terminate the matching operation/epoch, record status and device state, then apply bounded state-machine retry rather than a generic delay loop.
- Notifications enabled locally but absent -> write/confirm CCCD, preserve connection process, handle security/service change, and inspect characteristic properties.
- Android 17 repair prompt misclassified -> use `PAIRING_CONTEXT_REPAIRING`; `PAIRING_CONTEXT_AUTONOMOUS` from secondary examples is not the API 37 constant.
- Android 17 audio silently fails -> inspect `AudioHardening` logs and visibility/FGS/WIU; use user-visible notification if unsolicited background playback is not allowed.
- Bluetooth socket transport issue -> switch to `android-bluetooth-sockets`; keep GATT callback and socket stream lifecycle separate.

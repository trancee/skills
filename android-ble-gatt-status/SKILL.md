---
name: android-ble-gatt-status
description: "Diagnoses, mitigates, and tests Android BluetoothGatt connection and status failures, including legacy status 133. Use when onConnectionStateChange reports non-success, connections fail intermittently, callbacks arrive for stale attempts, reconnect loops leak GATT objects, service discovery fails after connect, behavior differs by OEM or device, or HCI and logcat evidence is needed to separate app, stack, controller, RF, security, and peripheral causes. Don't use for ordinary BLE feature implementation, local GATT server requests, operation-queue design without connection failures, BluetoothSocket errors, generic retry libraries, or non-Android BLE stacks."
compatibility: "Targets Android BluetoothGatt through API 37.2 documentation. Current public API 37/37.1 exposes GATT_FAILURE=257, GATT_CONNECTION_CONGESTED=143, and GATT_CONNECTION_TIMEOUT=147; it does not expose a GATT_ERROR/status-133 constant. Treat raw 133/0x85 as opaque evidence, not a diagnosis. Analyzer requires Python 3.11+."
metadata:
  category: "development"
  source: "https://dev.to/ble_advertiser/demystifying-android-ble-gatt-status-133-common-causes-and-robust-solutions-for-connection-32la"
  sourceVersion: "supplied article 2026-04-04; Android API 37.2 docs and API 37.1 public SDK stubs verified 2026-08-31"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T09:54:21+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T09:54:21+02:00"
---

# Android BLE GATT Status Diagnosis

## Step 1: Frame the failure without naming a cause

1. DEFINE initial direct-connect failure | auto-connect stall | disconnect after connection | service-discovery failure | operation status failure | timeout | stale callback | retry storm | OEM-only issue | persistent system-wide failure.
2. CAPTURE exact callback/API stage, decimal/hex status, `newState`, submission result, attempt ID, connection epoch, elapsed time, Android/API/OEM/device/peripheral firmware matrix, app/process state, adapter/permission/bond state, scan observation freshness/connectability/RSSI, and reproduction rate.
3. TREAT `status == 133` (`0x85`) as a legacy raw/opaque status. Current public API 37/37.1 has no `GATT_ERROR` or 133 constant; do not infer RF, cache, resource leak, or stack corruption from that number alone.
4. EVALUATE callback `status` before accepting `newState`. Only `GATT_SUCCESS` plus `STATE_CONNECTED` establishes a usable connection.
5. READ `references/status-semantics.md` and exact current `BluetoothGatt`/`BluetoothGattCallback` symbols before classifying a status.
6. READ `references/article-audit.md` before copying the supplied retry, close, delay, address, auto-connect, or adapter-reset examples.
7. ROUTE ordinary lifecycle changes to `android-ble`, client operation serialization to `android-ble-gatt-queue`, local server failures to `android-ble-gatt-server`, and inspector UI to `android-ble-inspector`.

Completion: the failure is an observed stage/status/state/timeline/matrix, not “status 133 means X.”

## Step 2: Inspect connection and retry code

RUN from the Android project root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM status-first callback handling, attempt/epoch/GATT matching, API 37 settings/executor, one connection owner, timeout/cleanup, fresh GATT per retry, retry classification/budget/backoff/jitter, service-discovery sequencing, fixed delays, raw-address identity/logging, hidden refresh, adapter toggling, permission branches, and diagnostic evidence.

Completion: every analyzer warning is fixed or retained with a source-backed/device-evidenced reason.

## Step 3: Build a minimal reproduction matrix

1. REPRODUCE the exact product path without changing retry, delay, or cache behavior mid-run; record successes/failures over enough cold/warm attempts to estimate frequency.
2. CROSS-CHECK same Android device/app with a known-good peripheral, same peripheral with another Android device/client, and—when safe—a reputable generic BLE client on the failing phone.
3. VARY one dimension at a time: foreground/background, bonded/unbonded, fresh/recent scan, direct/auto, near/far/RF contention, first/reconnect, Bluetooth toggle/reboot, app reinstall/data clear, and peer reset/firmware.
4. USE a controllable peripheral to inject non-connectable advertising, max connections, delayed responses, disconnect reasons, malformed services, security rejection, and power cycles.
5. SEPARATE connection callback failure from post-connect service discovery/MTU/CCCD/operation failure; the latter cannot be diagnosed as connect status 133.

Completion: the matrix identifies the narrowest failing boundary and at least one control path, or records that failure remains system/peripheral-wide.

## Step 4: Capture evidence across layers

READ `references/evidence.md`.

1. LOG a monotonic event timeline: scan observation, connect submission, callback GATT identity/epoch/status/newState, cleanup, scheduled/cancelled retry, discovery submission/callback, and process/lifecycle transitions.
2. REDACT addresses/names/payloads; use a session-local device pseudonym and object/attempt IDs.
3. CAPTURE logcat Bluetooth tags, `dumpsys bluetooth_manager`, permission/AppOps/bond state, bugreport, app exit reason, and Bluetooth HCI snoop/peer trace when available.
4. CORRELATE HCI connection-complete/disconnection/security/controller reason with the app callback by monotonic time. Distinguish absent controller attempt from rejected/timeout/disconnected links.
5. RECORD missing evidence explicitly. App status alone cannot prove stack, controller, RF, or peripheral cause.

Completion: each causal claim cites app, system, controller/air, or peer evidence and states gaps.

## Step 5: Validate the connection owner and API branch

READ `references/connection-lifecycle.md`.

1. REQUIRE current permission, adapter-on, supported feature, intended `BluetoothDevice`, recent/connectable observation where applicable, and one idle connection owner before `connectGatt`.
2. FOR API 37+, construct `BluetoothGattConnectionSettings`; distinguish direct/auto-connect from `opportunistic` mode, choose LE transport, automatic MTU, thresholds, and explicit serial callback executor deliberately.
3. FOR older APIs, isolate the least-ambiguous overload with explicit LE transport where supported. Never reflection-call private connect/refresh methods.
4. CREATE exactly one fresh `BluetoothGatt` attempt and install attempt/epoch state before callbacks can arrive. Handle null/throw/submission failure without retrying an unowned object.
5. MATCH every callback by the callback’s `gatt` object plus attempt ID/epoch. Never let a field holding a newer GATT cause cleanup/state changes for an older callback.
6. START service discovery only after `GATT_SUCCESS + STATE_CONNECTED`; check `discoverServices()` submission. Use no fixed “stabilization” delay unless a bounded device-specific experiment proves and documents it.

Completion: duplicate taps, fast callbacks, stale callbacks, permission/radio change, and direct/auto branches cannot create two live owners or advance the wrong attempt.

## Step 6: Retire and close failed attempts deterministically

1. ON any terminal non-success, atomically retire the exact attempt/epoch before scheduling work; fail its GATT operation queue and reject further callbacks.
2. CALL `disconnect()` when a connected attempt needs graceful teardown, then wait only for a bounded disconnected callback. CALL `close()` at callback or deadline and clear the field only if it still references that same GATT.
3. FOR failed/connecting/cancelled attempts, close the retired GATT without waiting indefinitely for a callback that may never arrive. The supplied article’s “never close before disconnected” rule is too absolute.
4. MAKE cleanup idempotent across callback, timeout, user cancel, permission revoke, Bluetooth off, lifecycle shutdown, and retry cancellation.
5. CREATE a new GATT for retry. Never call `connect()` on a failed/stale instance or reuse its discovered services/characteristics.

Completion: each attempt closes exactly once; late callbacks are ignored/closed and cannot affect a replacement attempt.

## Step 7: Classify the failure before retry

1. CLASSIFY local precondition: unsupported/off/resetting adapter, permission/AppOps, process/background restriction, stale/rotating address, non-connectable observation, duplicate owner, or invalid API configuration.
2. CLASSIFY security: bond/key missing, insufficient authentication/encryption/authorization, pairing UI/rejection, or application-authentication failure.
3. CLASSIFY peer/RF/controller: peer absent/not connectable/max connections/rebooting, range/interference, controller timeout/reject/disconnect reason, or phone controller failure.
4. CLASSIFY GATT stage: connection, service discovery/cache/service-changed, MTU/configuration, or queued operation. Preserve public statuses such as timeout/congested/security/failure instead of collapsing all to 133.
5. CLASSIFY platform/OEM only after same app/peripheral succeeds on controls and lower-layer evidence or reproducible device/OS specificity supports it.
6. MARK unknown when evidence cannot distinguish causes; unknown is a valid result and may be transient, but it does not justify destructive recovery.

Completion: each failure maps to transient, permanent/user-action, code/configuration, peer, platform, or unknown with evidence.

## Step 8: Retry only eligible failures

READ `references/retry-policy.md`.

1. RETRY only product-eligible transient failures after complete prior-attempt cleanup. Do not retry permission denial, Bluetooth off/unsupported, user cancel, invalid address/configuration, permanent security/pairing rejection, or schema/protocol defects.
2. OWN one retry scheduler in the connection state machine. Cancel its timer on success, user disconnect, owner shutdown, device switch, permission revoke, or adapter off.
3. USE capped exponential backoff with jitter, attempt/time budget, fresh scan/identity policy, and a final observable failure. Persist no live GATT objects across process death.
4. CREATE a fresh GATT at retry execution time and revalidate every precondition. Prevent duplicate callback/timeout paths from scheduling multiple retries.
5. RESET backoff only after a defined stable-ready interval, not merely a connected callback.
6. TEST virtual-time sequences for callback/timeout races, close failure, stale retry, scheduler shutdown, and permanent-status suppression.

Completion: retries cannot overlap, reuse stale state, loop forever, or hide a permanent/user-action failure.

## Step 9: Apply system/OEM interventions only as diagnostics

1. ASK the user to toggle Bluetooth or reboot only after app cleanup and cross-client controls suggest system-wide failure; label this a diagnostic/recovery action, not code mitigation.
2. NEVER call deprecated `BluetoothAdapter.disable()`/`enable()` from ordinary production code. Target-33+ ordinary apps cannot programmatically toggle Bluetooth.
3. NEVER call hidden `BluetoothGatt.refresh()` through reflection as a generic 133 fix. Use documented Service Changed/cache behavior and only device-specific supported recovery.
4. CAPTURE before/after evidence for Bluetooth toggle, reboot, peer reset, or app reinstall so success does not become unsupported causal folklore.
5. ESCALATE reproducible OEM/OS defects with minimal app, bugreport, HCI snoop, timestamps, device/build/firmware, and control results.

Completion: every invasive intervention is user-controlled, diagnostic, evidenced, and absent from automatic retry paths.

## Step 10: Verify and report

READ `references/testing.md`.

1. RUN deterministic connection-owner/retry tests, compile every SDK branch, and execute the reproduction matrix on real devices.
2. ASSERT one live attempt, status-first transitions, callback GATT/epoch matching, bounded cleanup, fresh retry objects, one scheduler, and no post-cancel retry.
3. VERIFY failures across permission, adapter, peer absent, non-connectable, max connections, security, controller timeout, service discovery, operation timeout, process death, and OEM controls.
4. COPY `assets/gatt-status-report.md`; record failure signature, matrix, timeline, status classification, cleanup/retry behavior, lower-layer evidence, conclusion, confidence, and unknowns.

Completion: the claimed cause/mitigation follows from reproduced controls and layer evidence; otherwise report the status as unresolved/opaque.

## Error Handling

- Code checks only `status == 133` -> handle every non-success status, preserve the raw value, and route by stage/evidence.
- `STATE_CONNECTED` with non-success status advances -> evaluate status first and retire the attempt.
- Retry starts before old GATT closes -> serialize cleanup, then construct a fresh attempt.
- Callback closes the field’s GATT -> close the callback argument/attempt object and compare-and-clear the field by identity.
- Retry scheduler was shut down then reused -> replace it with one lifecycle-owned cancellable scheduler; test cancellation/recreation.
- Discovery starts after `postDelayed(500)` -> submit from verified connected transition and measure; isolate any proven device workaround.
- `autoConnect` called opportunistic -> separate `setAutoConnectEnabled` from `setOpportunisticEnabled`; they are different API 37 settings.
- Persistent 133 triggers app-controlled Bluetooth reset -> remove programmatic toggle; gather cross-client/HCI evidence and require user action.
- Logs contain MAC addresses -> replace with per-session pseudonyms before exporting diagnostics.

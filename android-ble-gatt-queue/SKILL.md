---
name: android-ble-gatt-queue
description: "Implements, reviews, tests, and debugs coroutine-based serialization for Android BluetoothGatt client operations. Use when reads, writes, descriptors, MTU, discovery, or subscriptions overlap; callbacks complete the wrong request; operations hang or time out; caller cancellation races callbacks; reconnects deliver stale events; or a bounded Channel, actor, or CompletableDeferred adapter is needed. Don't use for local BluetoothGattServer request/response callbacks, scanning, advertising, background permissions, generic GATT schema design, BLE throughput tuning, non-Android stacks, ordinary coroutine pipelines, or concurrent EATT bearer scheduling."
compatibility: "Targets Android BluetoothGatt through API 37 and kotlinx.coroutines 1.11.0. Prefer API 33+ value-taking writes and value-bearing read/notification callbacks; onCharacteristicWrite/onDescriptorWrite callbacks do not contain written value. API 37 supports Executor-based GATT callbacks. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://dev.to/ble_advertiser/solving-the-android-ble-gatt-race-condition-reliable-sequential-operations-with-kotlin-coroutines-k04"
  sourceVersion: "Android API 37 documentation (2026-08-28); supplied article reviewed 2026-08-31; kotlinx.coroutines 1.11.0"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T08:23:27+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T09:54:21+02:00"
---

# Android BLE GATT Queue

## Step 1: Define the serialization contract

1. DEFINE overlapping operations | wrong callback | timeout/hang | caller cancellation | disconnect/reconnect | subscription race | queue backpressure | migration.
2. IDENTIFY connection owner/epoch, callback executor/thread, supported GATT operations, submission return contract, expected callback type/target/result, per-operation timeout, caller cancellation semantics, queue capacity, reconnect policy, and unsolicited event consumers.
3. READ the official [`BluetoothGatt`](https://developer.android.com/reference/android/bluetooth/BluetoothGatt) and [`BluetoothGattCallback`](https://developer.android.com/reference/android/bluetooth/BluetoothGattCallback) methods for every queued operation/API branch.
4. READ `references/article-audit.md` before reusing the supplied article's sample; its loop does not wait for callbacks and several callback/signature/value assumptions are incorrect.
5. ROUTE connection/status failures to `android-ble-gatt-status`, local `BluetoothGattServer` callbacks to `android-ble-gatt-server`, connection/scan/background/permission ownership to `android-ble`, logical GATT procedure/schema to `ble-protocol-stack`, throughput to `ble-throughput`, and generic structured-concurrency choices to `kotlin-coroutines`.

Completion: each operation has one submission, one matching completion callback, one timeout/reset policy, and one caller result type.

## Step 2: Inspect queue candidates

RUN from the Android project root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM GATT calls/callbacks, queue/actor/channel capacity, in-flight slot/operation IDs, callback matching, epoch checks, API 33 value APIs, timeout/reset, cancellation, notification stream, CCCD composite operations, disconnect draining, `GlobalScope`, delay polling, value-keyed completion maps, and nonexistent callback overloads.

Completion: every GATT initiation site is inside the single owner or intentionally outside with a documented synchronous-only contract.

## Step 3: Choose the single-owner architecture

READ `references/operation-model.md`.

1. CREATE one lifecycle-owned scope and one bounded request `Channel`/actor per `BluetoothGatt` connection epoch.
2. PROCESS one in-flight callback-completing operation at a time. The worker must await its internal callback completion before receiving/submitting the next request.
3. KEEP a single in-flight record instead of a map keyed by operation equality. Assign a monotonic operation ID and expected callback discriminator.
4. CONSTRAIN state mutation to one serial executor/dispatcher or protect the in-flight record atomically; API 37 should pass an explicit serial `Executor` to `connectGatt`.
5. SEPARATE requested operations from unsolicited notifications, connection changes, service changes, PHY changes, and other events.

Completion: no path can submit a second callback-completing GATT request while the first in-flight record remains active.

## Step 4: Define operations and immutable request data

1. MODEL operation variants for discover services, characteristic/descriptor read/write, MTU, RSSI, subscription, and reliable write only when supported.
2. COPY mutable `ByteArray` input at enqueue time; store logical UUID/discovered object identity, write type, expected callback, timeout, epoch, and reply handle.
3. USE API 33+ `writeCharacteristic(characteristic, value, writeType)` and `writeDescriptor(descriptor, value)`. Interpret `BluetoothStatusCodes.SUCCESS` as synchronous acceptance.
4. USE value-bearing API 33 read/notification callbacks. `onCharacteristicWrite` and `onDescriptorWrite` still provide status but no value; retain the in-flight request bytes if diagnostics need them.
5. MATCH duplicate UUID instances by the discovered service/characteristic/descriptor object or stable instance context, not UUID alone.

Completion: two identical writes remain distinct requests and request bytes cannot change after enqueue.

## Step 5: Submit and await the Android operation

READ `references/callback-matrix.md`.

1. RECEIVE the next non-cancelled request only when ready and no in-flight operation exists.
2. INSTALL the in-flight record before invoking Android so a synchronous/fast callback cannot outrun registration.
3. CALL the exact Android method once on the owner context; translate Boolean/`BluetoothStatusCodes` synchronous rejection into a typed submission failure.
4. IF accepted, await a separate internal completion with timeout. Do not merely continue the `for (operation in channel)` loop after initiation.
5. CLEAR the in-flight record by ID/epoch only after matched callback or connection reset, then complete the caller reply and advance.

Completion: submission rejection, callback success/status failure, and timeout each terminate exactly one request and preserve queue order.

## Step 6: Route callbacks without races

1. VERIFY callback `BluetoothGatt` instance and connection epoch before any state change.
2. COMPARE callback kind and target against the single in-flight expected callback. Reject/log stale, duplicate, mismatched, and unsolicited callbacks without completing another request.
3. COPY value parameters immediately; never read mutable `characteristic.value`/`descriptor.value` for API 33+ results.
4. COMPLETE the internal deferred exactly once using nonblocking callback work; move parsing/storage/UI work to downstream consumers.
5. EMIT `onCharacteristicChanged` through a separately bounded notification stream; dropped/overflow behavior must be explicit and cannot unblock the operation worker.
6. ON `onServiceChanged` or terminal connection callback, invalidate discovery objects and reset/fail the queue.

Completion: every callback either matches the current operation, enters a named unsolicited stream, or is rejected as stale/mismatched.

## Step 7: Implement cancellation and timeout semantics

READ `references/cancellation-timeouts.md`.

1. LINK queued caller replies to caller cancellation so a request cancelled before submission is skipped/failed without touching Android.
2. IF the caller cancels after submission, cancel only its outward result; keep the internal in-flight wait until callback or reset because Android GATT requests are not individually cancellable.
3. ON timeout, treat GATT synchronization as unknown: fail the request, close/reset the connection epoch, and fail/drain queued requests. Never launch the next operation on the same uncertain `BluetoothGatt`.
4. PROPAGATE owner-scope cancellation through channel close, in-flight reset, queued reply failure, `disconnect`/`close`, and notification-stream closure.
5. IGNORE late callbacks from the retired GATT/epoch.

Completion: cancellation at queued/in-flight/callback boundaries cannot overlap operations, leak continuations, or resume a completed caller.

## Step 8: Implement subscriptions and reliable writes as composites

READ `references/composite-operations.md`.

1. FOR subscription, perform synchronous local `setCharacteristicNotification`; then enqueue/write the CCCD as the callback-completing step and report ready only after `onDescriptorWrite` success.
2. ROLLBACK local notification routing if CCCD submission/callback fails or the operation is cancelled before submission.
3. KEEP notifications unsolicited and independent after subscription readiness.
4. FOR reliable write, own begin -> each write/callback/value verification -> execute/abort -> `onReliableWriteCompleted` as one exclusive composite transaction.
5. TREAT service discovery/configuration sequences as explicit composites or sequential public suspend calls—never fixed delays such as “wait 500 ms.”

Completion: composite operations expose one result while preserving each Android callback boundary and rollback path.

## Step 9: Reset on disconnect, permission loss, or service change

1. INCREMENT/retire the connection epoch before closing so late callbacks fail matching.
2. FAIL internal in-flight and queued caller replies with a typed terminal cause; clear request-owned byte buffers/references.
3. CALL `disconnect()` when appropriate and `close()` exactly once; cancel timeouts/worker and close notification stream.
4. RECONNECT with a fresh GATT, callback executor, discovered object graph, actor, and epoch. Never reuse old characteristic/descriptor instances.
5. REDISCOVER and re-establish CCCDs before accepting ordinary operations after process death/service change.

Completion: old callbacks/resources cannot mutate the new queue and reconnect begins from a clean state.

## Step 10: Test and report

READ `references/testing.md`.

1. RUN deterministic fake-transport tests for strict order, fast callbacks, synchronous rejection, mismatch/duplicate/stale callback, queued/in-flight cancellation, timeout reset, disconnect drain, notification overflow, and composites.
2. COMPILE the Android adapter against API 33 and API 37 signatures; verify min-SDK compatibility branches.
3. RUN real-device operations with repeated identical writes and forced peripheral disconnect/stall/service-change on representative Android/OEM stacks.
4. ASSERT never more than one callback-completing operation is submitted per epoch, and no post-timeout operation uses the same GATT.
5. COPY `assets/gatt-queue-report.md`; fill operation/callback matrix, owner/capacity, matching, cancellation/timeout/reset, composite behavior, tests, and limitations.

Completion: model tests, Android compilation, and device trace prove strict serialization and cleanup across every terminal boundary.

## Error Handling

- Queue loop submits all operations immediately -> move callback await inside the worker iteration; channel receive alone does not serialize asynchronous completion.
- `Channel.UNLIMITED` used -> select a bounded capacity/backpressure policy; unlimited is not unbuffered and can exhaust memory/stale the workload.
- Completion map keyed by operation/data class -> replace with one in-flight record and monotonic ID; identical operations must not collide.
- Read returns `characteristic.value` -> complete with the callback `value` parameter on API 33+.
- API 33 `onCharacteristicWrite(..., value, status)` override -> remove it; that callback overload does not exist.
- Subscription completes after `setCharacteristicNotification` -> wait for the queued CCCD descriptor-write callback.
- Timeout removes map entry then advances -> reset/close the GATT epoch first; the timed-out Android operation may still complete later.
- Caller cancellation frees in-flight slot -> retain internal transport wait/reset while suppressing outward completion.
- Callback launches arbitrary coroutines -> copy/route through bounded owned streams; callback ordering must remain explicit.
- `delay()` waits for connection/discovery -> await the actual state/callback deferred with timeout.

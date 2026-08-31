---
name: android-bluetooth-sockets
description: "Implements, reviews, tests, and troubleshoots Android BluetoothSocket and BluetoothServerSocket transports. Use when building RFCOMM or SPP clients and servers, Bluetooth LE L2CAP CoC channels, blocking connect, accept, read, and write loops, Kotlin coroutine adapters, stream framing, cancellation by close, API 36 BluetoothSocketSettings migration, or diagnosing EOF, timeout, pairing, permission, SDP UUID, PSM, and socket exception failures. Don't use for GATT operations, BLE advertising or scanning alone, audio profiles or SCO, raw Link Layer work, non-Android sockets, generic TCP, or protocol cryptography."
compatibility: "Covers Android BluetoothSocket APIs through API 37.1: RFCOMM since API 5, public LE L2CAP CoC since API 29, BluetoothSocketException since API 34, and BluetoothSocketSettings/TYPE_LE since API 36. Target-37 RFCOMM streams return -1 at EOF. The API 36 settings docs contain stale data-path links absent from API 37.0/37.1 public SDK stubs; verify future SDKs before adopting them. Inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://developer.android.com/reference/android/bluetooth/BluetoothSocket"
  sourceVersion: "Android API 37/37.1 documentation and public SDK stubs; pages updated 2026-08-03 through 2026-08-14"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T08:45:01+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T08:45:01+02:00"
---

# Android Bluetooth Sockets

## Step 1: Define the socket contract

1. DEFINE RFCOMM/SPP client | RFCOMM server | LE L2CAP CoC client | LE CoC server | blocking-call hang | stream corruption | API 36 settings migration | target-37 EOF | background connection.
2. IDENTIFY min/compile/target SDK, Android/device/OEM and peer matrix, transport, client/server roles, RFCOMM service UUID/name or LE PSM-disclosure mechanism, authentication/encryption requirements, adapter/permission state, connection deadline, message framing, payload bounds, one read owner, one write serializer, lifecycle/process owner, background mechanism, and retry semantics.
3. READ the exact current [`BluetoothSocket`](https://developer.android.com/reference/android/bluetooth/BluetoothSocket), [`BluetoothServerSocket`](https://developer.android.com/reference/android/bluetooth/BluetoothServerSocket), and [`BluetoothSocketSettings`](https://developer.android.com/reference/android/bluetooth/BluetoothSocketSettings) pages for the selected SDK branch.
4. READ `references/api-matrix.md`; inspect the compile SDK stubs before using settings symbols not listed there.
5. ROUTE GATT to `android-ble`/`android-ble-gatt-queue`, logical LE CoC protocol design to `ble-protocol-stack`, throughput tuning to `ble-throughput`, and application cryptographic handshakes to `noise-protocol`.

Completion: transport, API branch, peer rendezvous, security, blocking-call owner, framing, cancellation, background, and observable failure states are explicit.

## Step 2: Inspect the Android project

RUN from the Android project root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM SDK/permissions/features, socket API pairing, settings fields, secure/insecure choice, discovery cancellation, blocking-call execution, accept/connect cancellation by close, stream EOF/partial reads, framing, serialized writes, bounded buffers, exceptions, server/connected socket cleanup, and process-lifetime mechanism.

Completion: every warning is fixed or recorded with source-backed rationale and a device test.

## Step 3: Configure adapter, permissions, and ownership

READ `references/permissions-background.md`.

1. OBTAIN `BluetoothAdapter` through `BluetoothManager`; branch unsupported, off, turning, permission-denied, and ready states.
2. FOR target API 31+, declare/request `BLUETOOTH_CONNECT` before listen/connect/stream ownership. Declare/request `BLUETOOTH_SCAN` when discovering devices or calling `cancelDiscovery`; add `BLUETOOTH_ADVERTISE` only for discoverability.
3. KEEP legacy `BLUETOOTH`/`BLUETOOTH_ADMIN` declarations capped at API 30 and apply location requirements only to actual legacy discovery behavior.
4. REQUEST adapter enablement through the system UI; ordinary target-33+ apps must not call deprecated programmatic `enable()`/`disable()`.
5. OWN each listening socket and connected socket in a lifecycle service/repository, not an Activity/ViewModel task that can disappear while blocking I/O remains.
6. MODEL process death as connection loss; persist protocol progress/peer identity, never socket/stream objects.

Completion: manifest merge, runtime permission branches, adapter transitions, owner teardown, and process restart are exercised on every supported SDK branch.

## Step 4: Select matching server/client APIs

1. FOR RFCOMM before API 36, pair `listenUsingRfcommWithServiceRecord(name, uuid)` with `createRfcommSocketToServiceRecord(uuid)`; use the same stable service UUID on both peers.
2. FOR LE CoC before API 36, pair `listenUsingL2capChannel()` with `createL2capChannel(psm)`; disclose the server’s dynamic `getPsm()` through an authenticated product channel.
3. USE insecure variants only when the threat model accepts unauthenticated links and the application protocol authenticates the peer where required.
4. FOR API 36+, use `BluetoothSocketSettings` only when one settings-based branch improves the product. Pair `listenUsingSocketSettings(settings)` with `createUsingSocketSettings(settings)` and configure RFCOMM UUID or client LE PSM explicitly.
5. SET authentication and encryption explicitly in settings; both default to `false`. Restrict settings sockets to documented `TYPE_RFCOMM` or `TYPE_LE`.
6. BRANCH settings code with `SDK_INT >= 36`; keep the legacy creation path for lower devices without reflection/string fallbacks.

Completion: server/client transport, RFCOMM UUID or LE PSM, and authentication/encryption match exactly across peers and SDK branches.

## Step 5: Implement the listening server

READ `references/client-server.md`.

1. CREATE one `BluetoothServerSocket` off the main thread after permission/adapter checks.
2. CALL blocking `accept()` or `accept(timeout)` on a dedicated I/O worker. Treat timeout, deliberate close, adapter-off, permission loss, and transport failure as distinct terminal causes.
3. ON success, transfer the already-connected `BluetoothSocket` to a connection owner; never call `connect()` on an accepted socket.
4. CLOSE the listening socket when no more clients are wanted. Its closure aborts `accept()` but does not close accepted connected sockets.
5. IF accepting repeatedly, enforce the transport’s channel/client limits, bound concurrent connection owners, and reject/close excess sockets deterministically.
6. FOR LE CoC, expose the dynamic PSM only while the server socket owns it; republish after close, adapter off, or process restart.

Completion: accept success/timeout/cancel/retry, listener close, accepted socket independence, capacity, and PSM invalidation pass device tests.

## Step 6: Implement the outgoing client

1. CREATE a fresh socket for each attempt; never reuse a socket after failed/cancelled `connect()`.
2. CALL `cancelDiscovery()` before `connect()` after obtaining `BLUETOOTH_SCAN`; device discovery is system-wide/heavyweight and slows connection establishment.
3. RUN blocking `connect()` on a dedicated I/O worker. On product timeout/cancellation, close that socket from another thread/context to abort the call.
4. TREAT a normal return as connected; inspect API 34+ `BluetoothSocketException.errorCode` before the broader `IOException` branch.
5. VERIFY `connectionType`, peer, and negotiated transport assumptions after connect where relevant. Treat `isConnected` as a snapshot, not proof of peer application liveness.
6. HAND the connected socket to exactly one connection owner; close it on every failed handoff.

Completion: discovery-active, success, timeout, cancellation, permission revoke, adapter off, security failure, and retry each close exactly one attempt socket.

## Step 7: Implement a framed byte-stream protocol

READ `references/stream-framing.md`.

1. GET input/output streams only from the connected socket and run blocking I/O outside the main thread.
2. KEEP one read loop. For every nonempty buffer read, handle `-1` as EOF, accept partial reads, and copy only `0..<count` before asynchronous handoff.
3. FEED bytes into a bounded incremental decoder; never equate one `read()` with one message or one Bluetooth packet.
4. DEFINE a length/delimiter/fixed-size framing contract with maximum frame size, version/type, integrity/authentication as required, and malformed/truncated-frame behavior.
5. SERIALIZE all writes through one writer/queue because message bytes from concurrent writers must not interleave. Bound queue depth/bytes and propagate backpressure.
6. HANDLE partial application progress and blocking `write`; close on terminal I/O failure. Use max transmit/receive packet sizes only as buffer/throughput hints, not message boundaries.

Completion: fragmented/coalesced frames, EOF, malformed length, oversized input, slow peer, concurrent writers, queue overflow, and mid-frame disconnect are deterministic.

## Step 8: Bridge blocking sockets to coroutines safely

READ `references/coroutines-lifecycle.md`.

1. RUN `accept`, `connect`, `read`, and potentially blocking `write` on `Dispatchers.IO` or dedicated bounded executors.
2. REGISTER cancellation cleanup before/with the blocking call so coroutine cancellation closes the exact server/connected socket; cancellation alone does not interrupt Java blocking I/O.
3. MAKE closure idempotent and owner-scoped. Closing a socket from another thread immediately aborts ongoing operations with `IOException`/EOF.
4. COPY read bytes before `send`/emit/callback; never expose a shared reusable read buffer.
5. USE bounded channels for decoded frames and outbound writes. Cancel child reader/writer/parser jobs together on first terminal socket failure.
6. PRESERVE the original terminal cause while suppressing expected close-induced I/O errors during deliberate cancellation.

Completion: cancellation during accept/connect/read/write, simultaneous peer close, double close, and parent-scope failure terminate every child without leaked blockers or buffers.

## Step 9: Preserve process priority only for required sessions

1. FOR a user-visible long-running connection, use a `connectedDevice` foreground service started under current background-start rules; on API 34+, declare its type and `FOREGROUND_SERVICE_CONNECTED_DEVICE` permission and meet a runtime prerequisite.
2. FOR associated companion workflows, evaluate Companion Device Manager/presence APIs before a permanent foreground service.
3. STOP service and close sockets as soon as the session ends. A foreground service raises process importance; it does not make a socket survive process death or radio loss.
4. RECONNECT from persisted protocol state after process restart through a fresh listener/client socket and fresh streams.
5. KEEP UI launch/user notifications compliant with background activity restrictions; never auto-open an Activity from a socket event without a documented exception.

Completion: foreground/background, screen-off, user stop, task removal, process kill, reboot, adapter toggle, and permission revoke match the chosen lifecycle mechanism.

## Step 10: Verify and report

READ `references/testing.md`.

1. RUN deterministic framing/ownership/cancellation tests with byte-stream fakes, compile every API branch, then run server/client instrumentation on real devices.
2. TEST matched/mismatched RFCOMM UUIDs, secure/insecure pairing, LE PSM publication/invalidation, settings validation, discovery contention, timeouts, partial reads, target-37 EOF, slow/full writers, and process/background boundaries.
3. CAPTURE `BluetoothSocketException.errorCode`, `IOException`, adapter/bond state, HCI snoop/logcat, and protocol frame counters without MAC addresses or payload secrets.
4. COPY `assets/android-bluetooth-sockets-report.md`; record API/device matrix, transport/security, ownership, framing, lifecycle, failures, evidence, and limitations.

Completion: unit tests prove stream/owner invariants; real-device evidence proves Android/OEM/peer transport behavior and cleanup.

## Error Handling

- `accept()`/`connect()` freezes UI -> move the blocking call to owned I/O execution; close its socket to cancel.
- Connect is slow/fails during discovery -> request `BLUETOOTH_SCAN`, call `cancelDiscovery()`, then connect with a fresh socket.
- Accepted socket fails after `connect()` -> remove the call; `accept()` returns an already-connected socket.
- RFCOMM peers never meet -> verify identical service UUIDs, server SDP lifetime, discoverability/pairing, security variant, and permissions.
- LE CoC fails -> verify API 29/36 branch, secure/insecure parity, live dynamic PSM disclosure, PSM range, peer transport support, and exception code.
- API 36 settings throw `IllegalArgumentException` -> provide RFCOMM UUID or valid client LE PSM, supported socket type, and explicit security fields.
- Settings code references `getDataPath`/`DATA_PATH_NO_OFFLOAD` -> remove it for current public API 37/37.1; those stale reference links are absent from public SDK stubs.
- Read loop spins/crashes at disconnect -> break on `read() == -1`, catch `IOException`, and never pass a negative count downstream.
- Messages corrupt/merge -> add incremental framing and one serialized writer; packet/read boundaries are not messages.
- Coroutine timeout returns but thread remains blocked -> close the exact socket/server socket in cancellation cleanup.
- Connection dies in background -> use a justified connected-device lifecycle mechanism and persist protocol progress; sockets do not survive process death.

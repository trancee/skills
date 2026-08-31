---
name: ble-protocol-stack
description: "Designs, implements, validates, and troubleshoots Bluetooth Low Energy GAP, GATT, ATT, and L2CAP interactions. Use when defining advertising, scanning, and connection roles; modeling GATT services, characteristics, descriptors, properties, permissions, and values; implementing ATT reads, writes, subscriptions, notifications, indications, long values, and caching; configuring L2CAP fixed, credit-based, or enhanced ATT bearers; or diagnosing discovery, UUID, MTU, CCCD, and cross-platform interoperability failures. Don't use for Bluetooth Classic, LE Audio or ISO streams, RF and PHY tuning, throughput optimization, pairing cryptography, platform UI, or generic network protocols."
compatibility: "Uses Bluetooth Core Specification 6.2 terminology and requirements. Platform/controller APIs expose subsets and may synthesize GATT declarations/descriptors. Verify mandatory specification updates, assigned numbers, profile specifications, and platform behavior for the product's claimed Core/profile versions. Schema validator requires Python 3.11+."
metadata:
  category: "development"
  source: "https://argenox.com/blog/understanding-ble-gap-gatt-and-l2cap"
  sourceVersion: "Bluetooth Core Specification 6.2; Argenox article 2026-04-08"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T22:55:25+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T22:55:25+02:00"
---

# BLE Protocol Stack

## Step 1: Define the protocol contract

1. DEFINE advertising/discovery | connection lifecycle | GATT database | client procedure | notification/indication | caching/versioning | ATT bearer/EATT | L2CAP CoC | interoperability defect.
2. IDENTIFY GAP roles, Link Layer central/peripheral, GATT client/server per procedure, service owner, peer/platform/controller/stack/Core/profile versions, UUID namespace, value schemas, permissions/security levels, cache policy, ATT bearers, L2CAP channels, failure/reconnect behavior, and compatibility matrix.
3. READ `references/layers-roles.md`, then the current Core 6.2 GAP/GATT/ATT/L2CAP sections it identifies for the change.
4. SEPARATE roles: central/peripheral controls link establishment; client/server controls each GATT procedure. Either connected peer can be client, server, or both.
5. ROUTE Apple platform mechanics to `corebluetooth`, Android GATT client/platform mechanics to `android-ble`, Android local GATT server mechanics to `android-ble-gatt-server`, Android RFCOMM/LE CoC socket mechanics to `android-bluetooth-sockets`, PHY/DLE/interval/throughput tuning to `ble-throughput`, and application cryptographic handshakes to `noise-protocol`.

Completion: roles, discovery/connection flow, logical schema, wire procedures, security/cache/channel ownership, and target matrix are explicit.

## Step 2: Model and validate the logical schema

1. COPY `assets/gatt-schema.json`; replace examples with the product's GAP advertisement, GATT database, and optional LE credit-based channels.
2. ASSIGN stable logical IDs distinct from runtime attribute handles; handles are server-instance bindings discovered by clients.
3. USE 16-bit UUIDs only for Bluetooth SIG-assigned definitions and 128-bit UUIDs for vendor definitions. Verify every SIG UUID/profile against [Assigned Numbers](https://www.bluetooth.com/specifications/assigned-numbers) and its profile specification.
4. DEFINE each value's byte length, encoding, byte order, units/scaling/range/sentinel/version, properties, permissions, subscription security, and error behavior.
5. RUN:
```bash
python3 scripts/validate-schema.py path/to/gatt-schema.json --json
```

READ `references/gatt-schema.md`.

Completion: schema validation passes and every logical field maps to an explicit GAP/GATT/L2CAP contract.

## Step 3: Design GAP advertising, scanning, and connection flow

READ `references/gap-advertising.md`.

1. SELECT broadcaster/observer/peripheral/central capabilities independently; support concurrent roles only when controller/host combinations allow them.
2. PLACE only discovery/routing data in advertising. Keep secrets, mutable bulk state, and authorization decisions out.
3. FIT encoded AD structures—including length/type overhead—within the selected legacy/extended/scan-response limits; preserve a legacy discovery path when required by peers.
4. SCAN by stable service/manufacturer identifiers and validate payload format/version; device name/address/RSSI alone is not identity.
5. DEFINE connect/cancel/timeout/reconnect/backoff and link-state ownership. Begin GATT work only after connection and required security state.

Completion: advertisements encode deterministically, target scanners discover them, and connection transitions cannot race or leak stale peers.

## Step 4: Design services, characteristics, and descriptors

1. GROUP one coherent capability per service; reuse adopted SIG services exactly or allocate vendor 128-bit UUIDs.
2. DEFINE characteristic properties as permitted GATT procedures and permissions as server enforcement. A property bit does not grant security/access.
3. USE read for current snapshots, write/write-command for client changes, notification for unconfirmed updates, and indication for confirmed sparse events.
4. ADD one CCCD (`0x2902`) for every notify/indicate characteristic, whether explicitly or stack-generated; store configuration per client and persist for bonded clients as required.
5. ADD Extended Properties (`0x2900`) only with its property bit; add presentation/user descriptors only when semantics require them.
6. KEEP values at most 512 octets and specify application segmentation for larger objects.

Completion: every characteristic procedure, permission, descriptor, value format, and client-specific state is internally consistent.

## Step 5: Implement ATT procedures and serialization

READ `references/att-procedures.md`.

1. DISCOVER services, characteristics, descriptors, and handles before access unless a valid cache is proven current.
2. SERIALIZE request/response procedures per unenhanced ATT bearer; correlate callbacks to one operation owner and reject stale/disconnected completions.
3. IMPLEMENT read/read-blob and write/prepare/execute offset/length/atomicity precisely; validate entire queued write before commit or cancel it.
4. ENABLE notifications/indications by writing the peer's CCCD, not by toggling only local callbacks. Confirm indication lifecycle and allow no conflicting outstanding transaction.
5. RETURN exact ATT errors for invalid handle, permission, authentication, authorization, encryption key size, offset, length, unsupported request, resources, or database state.
6. COPY callback data before lifetime expires and keep callbacks nonblocking.

Completion: positive and negative procedures produce the expected ATT opcode/error and state transition on each bearer.

## Step 6: Handle MTU, long values, and application framing

1. TREAT ATT MTU as a per-bearer maximum PDU size; on the fixed bearer, use the minimum exchanged receive MTUs after the one exchange.
2. SIZE each procedure from its own opcode/handle/offset overhead; do not equate MTU with characteristic-value bytes.
3. USE read blob for long reads and prepare/execute for reliable long writes when the peer/profile supports them.
4. KEEP the 512-octet maximum attribute value; split larger application objects with explicit transfer ID, total length, offsets/sequences, integrity, cancellation, and resume behavior.
5. DISTINGUISH ATT/L2CAP SDU segmentation from lower-layer fragmentation. Diagnose at the layer that owns the boundary.

Completion: every boundary value (empty, exact MTU, MTU+1, max attribute, multi-segment object) is handled without truncation or partial commit.

## Step 7: Preserve discovery cache correctness

READ `references/caching-eatt.md`.

1. KEEP handles stable when the database does not change; clients never treat hard-coded handles as schema identity.
2. WHEN services/characteristics/descriptor bindings can change, expose and drive Service Changed; retain pending changed ranges for bonded disconnected clients.
3. SUPPORT Database Hash/Robust Caching together when claiming robust caching and follow change-aware/change-unaware transitions.
4. INVALIDATE affected cached handle ranges before new requests; rediscover or obtain authenticated out-of-band definitions before reuse.
5. VERSION vendor value payloads independently from handles so additive schema evolution remains decodable.

Completion: firmware/database changes force correct cache invalidation across bonded, unbonded, connected, and reconnecting clients.

## Step 8: Choose ATT bearers or L2CAP channels

READ `references/l2cap-eatt.md`.

1. USE the fixed ATT bearer (LE CID `0x0004`) for baseline GATT interoperability.
2. USE EATT only when both peers/security/platform support it; schedule independent transactions across bearers without assuming cross-bearer ordering.
3. USE LE/Enhanced Credit Based L2CAP CoC for application SDUs only when both peers expose the SPSM/channel APIs and GATT is the agreed discovery mechanism where required.
4. NEGOTIATE directional MTU/MPS/initial credits; decrement one credit per K-frame, replenish from bounded receive capacity, and stop at zero.
5. PRESERVE SDU boundaries, validate SDU length/segment totals, reject oversize MTU/MPS, and close channels on protocol violations.

Completion: bearer/channel mode, CID/SPSM, MTU/MPS/credits, security, framing, ordering, and close behavior are explicit and interoperable.

## Step 9: Test and troubleshoot the full lifecycle

READ `references/platform-testing.md`.

1. RUN advertise -> scan -> connect -> secure -> discover/cache -> subscribe -> transfer -> unsubscribe -> disconnect -> reconnect.
2. TEST both role combinations actually supported, multiple clients/bearers, cancellation/races, background/permission changes, service/database updates, and resource exhaustion.
3. CAPTURE host logs and over-the-air/HCI traces; map each API callback to GAP procedure, ATT opcode/error, L2CAP CID/credit, and connection epoch.
4. CROSS-TEST representative iOS/Android/embedded stacks and a generic GATT client, using logical IDs/UUIDs rather than platform object identity.
5. COPY `assets/ble-stack-report.md`; fill roles, advertising, database/value schema, procedures/errors, cache behavior, bearers/channels, traces, and platform gaps.

Completion: every contract path passes on the declared matrix or is tied to one evidenced platform/controller limitation.

## Error Handling

- Central assumed to be GATT client -> remap GAP and GATT roles per procedure; preserve connection role separately.
- Device discovered inconsistently -> inspect encoded AD structures, scan mode/filter/duplicate policy, legacy versus extended support, permissions, and background limits.
- Characteristic visible but access fails -> compare property, value-attribute permission, current link security, handle, length/offset, and server error.
- Notifications never arrive -> verify characteristic property, CCCD discovery/write/security/per-client value, local subscription registration, and server update path.
- Indication stalls -> wait for/trace confirmation and enforce one indication transaction per bearer instead of retrying blindly.
- Works once then fails after firmware update -> invalidate handles through Service Changed/Database Hash and rediscover; never pin runtime handles.
- Long write partially applies -> stage prepare writes by client/bearer, validate offsets/length/security, and commit only on execute.
- EATT reorders operations -> define application ordering and transaction ownership across independent bearers.
- CoC stalls -> inspect peer credits, receive-buffer release, MTU/MPS/SDU segmentation, CID/SPSM, and security; never transmit K-frames at zero credits.
- Throughput-only issue -> switch to `ble-throughput` after confirming the GAP/GATT/L2CAP contract is correct.

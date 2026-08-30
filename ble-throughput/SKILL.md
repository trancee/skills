---
name: ble-throughput
description: "Measures, models, diagnoses, and optimizes Bluetooth Low Energy data throughput. Use when sizing ATT or GATT payloads, enabling DLE or 2M/Coded PHY, choosing connection intervals and packets per event, selecting notifications, write commands, or L2CAP CoC, implementing queue backpressure, segmentation, or reliability, comparing iOS, Android, and embedded behavior, analyzing sniffer traces, or balancing throughput, latency, power, range, and coexistence. Don't use for Bluetooth Classic, LE Audio or ISO stream design, pairing and security architecture, RF certification, generic app networking, or unsupported headline-speed guarantees."
compatibility: "Uses Bluetooth Core 6.2 terminology while preserving the legacy 7.5 ms/1.25 ms connection-interval baseline. Shorter Connection Intervals down to 375 us require Core 6.2 SCI support on both peers/hosts/controllers. Mobile behavior is device/OS dependent. Calculator models one-direction ATT traffic on uncoded 1M/2M PHY only and requires Python 3.11+."
metadata:
  category: "development"
  source: "https://interrupt.memfault.com/blog/ble-throughput-primer"
  sourceVersion: "Bluetooth Core 6.2; supplied sources reviewed 2026-08-30"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T18:55:31+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T18:55:31+02:00"
---

# BLE Throughput

## Step 1: Define the transfer contract

1. DEFINE slow-transfer diagnosis | target throughput | firmware update | sensor stream | latency/power tradeoff | iOS/Android interoperability | embedded-to-embedded | GATT versus L2CAP CoC.
2. IDENTIFY direction, useful bytes, transfer size/duration, latency/deadline, loss/retry semantics, central/peripheral and client/server roles, foreground/background state, peer/controller/stack/OS versions, supported Core features, RF range/environment, power budget, and concurrent radios/connections.
3. SELECT the metric before tuning: useful application bytes accepted by the receiver per elapsed steady-state second. Record latency, energy, failures, retries, and memory separately.
4. TREAT PHY headline rates and article/device examples as context, never guarantees. Historical iOS/Android packet-count/MTU limits are not current platform constants.
5. READ `references/source-notes.md` to distinguish current specification/platform facts from empirical guidance.

Completion: workload, direction, useful-byte boundary, device matrix, tradeoffs, and acceptance thresholds are explicit.

## Step 2: Capture an evidence-rich baseline

1. BUILD a release-like sender/receiver with sequence numbers, useful-byte counters, monotonic timestamps, queue depth/high-water marks, and explicit completion/checksum.
2. WARM the connection through service discovery, security, MTU, data-length, PHY, and connection-parameter procedures before the measurement window.
3. RECORD requested and effective PHY per direction, ATT MTU, LL max TX/RX octets/time, connection interval/rate, peripheral latency/subrate, event duration, data packets per event, operation type, payload size, encryption, RSSI, retries, and app callbacks/backpressure.
4. CAPTURE an over-the-air trace when effective parameters, retransmissions, More Data behavior, or event closure is uncertain. Host logs alone cannot prove on-air scheduling.
5. RUN repeated long-enough trials across device/OS/RF/background/Wi-Fi/concurrency conditions; report distribution and failures, not the best run.

READ `references/measurement.md` for instrumentation and trace interpretation.

Completion: application counters and trace/stack evidence identify the first unsaturated layer.

## Step 3: Model bounds without claiming prediction

RUN the one-direction uncoded ATT model:
```bash
python3 scripts/calculate.py \
  --phy 2m \
  --att-mtu 247 \
  --ll-payload-octets 251 \
  --connection-interval-ms 15 \
  --event-duration-ms 7.5 \
  --packets-per-event 6 \
  --operation notification \
  --json
```

READ `references/throughput-model.md`.

1. ENTER observed effective values, not requested settings.
2. COMPARE radio-continuous, event-airtime, packet-cap, and request/confirmation-limited bounds with measured useful throughput.
3. USE aligned ATT value sizes derived from actual MTU/LL payload; 244 and 495 bytes are examples for 251-octet LL payloads, not universal constants.
4. ACCOUNT separately for application headers, security framing, ACK windows, flash/storage, parsing, and retransmissions.
5. MODEL Coded PHY, EATT, L2CAP CoC, bidirectional traffic, Core 6 frame-space updates, and 6.2 SCI only from negotiated trace/controller specifics; the bundled uncoded ATT model intentionally excludes them.

Completion: each bound states assumptions, and the measured gap points to a layer instead of a headline PHY rate.

## Step 4: Tune the radio and Link Layer one variable at a time

READ `references/link-layer.md`.

1. REQUEST 2M PHY only when both peers support it and RF margin is adequate; confirm effective TX/RX PHY after the update.
2. ENABLE DLE and adequate controller/host ACL buffers; confirm negotiated max octets/time and full LL payloads on air.
3. REQUEST connection parameters appropriate to workload, then record what the central actually applies. Optimize event utilization before blindly minimizing interval.
4. SET peripheral latency/subrate for the measured direction/latency contract; zero can help central-to-peripheral saturation but costs power.
5. PRELOAD enough packets to keep events open without unbounded queues. Sequence PHY, DLE, parameter, and security procedures because controllers may serialize them.
6. RE-TEST 1M versus 2M under weak/noisy RF; faster PHY can lose to retransmissions, while Coded PHY prioritizes range/reliability over throughput.

Completion: trace shows intended negotiated features, filled events, bounded queues, and measured RF/power tradeoffs.

## Step 5: Align ATT MTU, LL payload, and value size

1. NEGOTIATE/observe ATT MTU; effective fixed-bearer MTU is the minimum accepted peer value and is per ATT bearer.
2. DISTINGUISH ATT MTU from DLE. Large ATT PDUs fragment across LL packets; DLE alone does not enlarge an ATT value.
3. SIZE notification/write-command values to efficiently fill LL fragments after 4-byte L2CAP and operation-specific ATT overhead.
4. TEST at least the aligned size, one byte above it, maximum allowed value, and application-header-adjusted size. Choose measured useful throughput, not largest MTU.
5. SEGMENT values larger than the chosen application chunk with sequence/length/checksum/resume semantics where end-to-end integrity requires them.

Completion: the chosen chunk has measured efficiency and correct reassembly at loss/duplicate/disconnect boundaries.

## Step 6: Select the transfer method and implement backpressure

READ `references/application-pipeline.md`.

1. USE notifications for server/peripheral-to-client/central streaming and write commands (write without response) for the reverse high-throughput path when their weaker application acknowledgment semantics are acceptable.
2. USE indications/write requests for control points or sparse operations needing protocol-level confirmation; do not serialize the bulk stream behind one round trip.
3. KEEP a bounded transmit window fed until platform backpressure closes it; resume only from the documented ready/completion callback.
4. PROCESS receive data off the Bluetooth callback quickly into a bounded queue; avoid blocking, flash writes, parsing, UI work, or response generation on the callback path.
5. EVALUATE LE L2CAP CoC/EATT only when both platform versions and peers support the required bearer/credit model; benchmark end to end.

Completion: neither sender starvation nor receiver work closes events/drops buffers, and queue memory stays bounded.

## Step 7: Apply current mobile platform behavior

READ `references/mobile-platforms.md`.

1. ON iOS, query `maximumWriteValueLength(for:)`; gate write commands on `canSendWriteWithoutResponse` and resume from `peripheralIsReady(toSendWriteWithoutResponse:)`. For peripheral notifications, stop when `updateValue` returns false and resume from its ready callback.
2. ON Android 14+, expect the first GATT-client MTU request to request 517 and later requests to be ignored; trust `onMtuChanged`, peer limits, and actual write result. Use API 33+ value-taking write methods.
3. REQUEST high connection priority/2M PHY only for the transfer window and restore balanced policy afterward where the API supports it.
4. SERIALIZE Android GATT operations/callback ownership; treat congestion/status/disconnect as state transitions, not retry loops.
5. TEST foreground/background, screen state, Wi-Fi/audio coexistence, thermal/battery policy, and representative vendors/OS versions.

Completion: platform flow-control APIs drive the queue and the device matrix records effective—not assumed—parameters.

## Step 8: Verify tradeoffs and report

1. RE-RUN the baseline matrix after each single-variable change; retain raw counters/traces/configuration.
2. VERIFY exact useful-byte integrity, no silent drops, bounded memory, reconnect/resume, cancellation, timeout, and receiver-overrun behavior.
3. MEASURE throughput distribution, transfer latency, energy/radio-on time, range/RSSI/retransmissions, coexistence, and fairness across connections/directions.
4. REMOVE benchmark-only logging/test hooks from production hot paths while retaining low-cost operational counters needed to diagnose regressions.
5. COPY `assets/throughput-report.md`; fill workload, negotiated parameters, model assumptions, measured results, bottleneck evidence, changes, tradeoffs, and device matrix.

Completion: the target is met across the declared matrix or the first immutable controller/OS/RF bound is demonstrated.

## Error Handling

- Requested 2M/DLE/MTU/interval differs from effective -> use callback/HCI/sniffer evidence and optimize the negotiated value; never report the request as applied.
- Calculator rejects interval below 7.5 ms -> add `--shorter-connection-intervals` only when both peers/controllers/hosts negotiate Core 6.2 SCI; otherwise use baseline intervals.
- MTU increases but throughput does not -> inspect DLE, LL fragmentation, aligned payload size, packets/event, queue starvation, and operation type.
- One-byte size increase causes regression -> it crossed an LL-fragment boundary; select the previous aligned size after application overhead.
- Write without response fails/stalls -> stop enqueueing at platform backpressure and resume only from the ready callback; never busy-loop.
- Notifications disappear under load -> inspect receiver callback latency, host/controller buffers, sequence gaps, and bounded application recovery.
- 2M performs worse -> compare RSSI/CRC retries/event termination against 1M in the same RF condition.
- Mobile results vary -> stratify by device, OS, foreground/background, radio coexistence, and effective parameters; do not average incompatible runs.
- Reliability layer halves throughput -> replace per-chunk stop-and-wait with a bounded window/selective recovery consistent with memory and loss requirements.
- Sniffer and app counters disagree -> reconcile retransmissions, duplicated/dropped host packets, measurement boundaries, and useful versus protocol bytes.

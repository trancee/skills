# Measurement and trace plan

Measure receiver-accepted useful bytes over a monotonic steady-state window. Exclude headers, retransmissions, setup, discovery, negotiation, and checksum bytes unless the product metric includes them. Report setup latency separately.

Per trial record:
- hardware/controller/firmware/stack/OS/app versions and roles
- direction, operation/bearer, characteristic/PSM, security state
- requested/effective PHY TX/RX, LL max octets/time, ATT MTU
- connection interval/rate, event duration, peripheral latency/subrate
- observed data packets/event, empty responses, retransmissions/CRC failures
- application chunk/header, queue capacity/high-water, ready/completion callbacks
- RSSI/location/channel/interference, Wi-Fi/audio/scanning/other connections
- useful bytes, elapsed time, checksum/gaps/duplicates/retries, disconnects
- current/energy/radio-on measurement where power matters

Use a transfer large enough to amortize startup and repeat after warm-up. Preserve raw per-run results; summarize median and tail/low percentile plus failure rate. Do not choose the fastest run.

On-air trace diagnoses:
- LL_LENGTH_REQ/RSP and actual payload sizes -> DLE/effective lengths
- PHY update and packet symbols -> actual PHY per direction
- connection anchors -> interval/event duration/packets per event
- MD bit/empty packets -> sender starvation or peer/event closure
- repeated SN/NESN/CRC behavior -> link retransmissions
- ATT opcodes -> command/request/notification/indication and confirmations
- L2CAP fragmentation -> ATT value to LL packet mapping

Synchronize app counters with GPIO/log markers where possible. If encrypted captures cannot decode ATT, LL timing/length/retry evidence still identifies radio/controller limits.

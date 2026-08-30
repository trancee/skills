# ATT operations, queues, and reliability

High-throughput GATT directions:
- client/central -> server/peripheral: ATT Write Command / write without response
- server/peripheral -> client/central: Handle Value Notification

Write Requests and Indications add ATT response/confirmation serialization. Reserve them for sparse control/commit operations or explicit protocol semantics rather than every bulk chunk.

“No response” does not mean “infinite enqueue.” Maintain a bounded window tied to stack acceptance/readiness callbacks. Stop immediately on congestion/full; retain buffer ownership until the API permits reuse; resume from one owner. Busy loops, fixed delays, and unbounded queues hide loss and increase latency/memory.

The receive callback copies/enqueues only what must outlive the callback, then returns. Parse, checksum, decompress, persist, render, and send application acknowledgments outside the Bluetooth callback. Bound the receiver queue and define overrun/disconnect behavior.

BLE LL retransmits corrupted radio packets, but host/controller/application buffers and disconnects can still lose chunks. For end-to-end transfer integrity use:
- transfer/session ID and total length
- monotonically increasing chunk offset/sequence
- final digest/commit
- bounded cumulative/selective acknowledgment window when recovery is needed
- duplicate/idempotent handling and resume checkpoint

Avoid stop-and-wait per chunk: each application round trip can cost connection events. Tune window from receiver memory and loss, and send acknowledgments sparsely/cumulatively.

ATT values max at 512 bytes and larger objects need application segmentation. L2CAP CoC can reduce GATT overhead and uses credit flow control, but platform/API/peer support, security, framing, credits, and recovery still need measurement.

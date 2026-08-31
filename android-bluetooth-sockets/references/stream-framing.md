# Byte-stream framing and buffers

BluetoothSocket streams are byte streams, not message queues. A single write may arrive across reads; multiple writes may coalesce. `getMaxReceivePacketSize`/`getMaxTransmitPacketSize` are optimization hints, never application frame boundaries.

Choose one framing contract:
- fixed header: magic/version/type/unsigned payload length/message ID, then payload and optional authentication tag/checksum
- delimiter: only for bounded escaped/text protocols with explicit maximum line length
- fixed size: only when every message has exactly the negotiated size

Decoder state: `Header -> Payload -> Integrity -> Emit`. Reject unsupported version/type, length above the negotiated maximum, integer overflow, invalid integrity, and EOF mid-frame. Bound buffered bytes before allocation; never allocate directly from an untrusted length.

Read loop with nonempty buffer:
1. call blocking `read`
2. on `-1`, terminate as orderly EOF (target-37 RFCOMM explicitly follows this; older/OEM paths may throw instead)
3. on positive count, copy exactly that range before dispatch because the buffer is reused
4. feed decoder repeatedly until it needs more bytes
5. on `IOException`, terminate and close once

Serialize writes as complete encoded frames through one bounded writer actor/mutex. Report queue-full according to product policy. `write` may block under flow control; an enqueue is not a peer acknowledgement. Preserve application sequence/ack/resume state when loss matters.

Never send the whole reusable read buffer to a handler/channel. Never use `available()` as a complete-message predicate. Never busy-loop on zero/empty work.

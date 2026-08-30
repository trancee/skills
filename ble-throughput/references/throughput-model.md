# Uncoded one-direction ATT model

The calculator models one ATT value sent through L2CAP over uncoded LE 1M/2M, with an empty reverse LL packet after each data LL packet.

For notification/write command:
- ATT overhead = 3 bytes (opcode + handle)
- L2CAP basic header = 4 bytes
- maximum attribute value = 512 bytes
- fragments per value = `ceil((value + 7) / max_ll_payload_octets)`

For each LL fragment, uncoded airtime includes preamble (1 byte at 1M, 2 at 2M), access address 4, LL header 2, data fragment, optional encryption MIC 4, and CRC 3. Reverse empty packet and two inter-frame spaces are included. Controller/event scheduling overhead is an explicit input.

The model reports:
- aligned value sizes `k * LL_payload - 7` under MTU/value limits
- fragment count and per-value exchange airtime
- continuous-radio bound
- event-airtime operation count
- packet-cap operation count
- modeled useful throughput from the tighter event/packet bound

Indications/write requests are conservatively capped to one value per event because confirmation/response serialization dominates and varies by stack. Measure callback cadence for the real bound.

Assumptions deliberately excluded: Coded PHY coding/header timing, configurable Core 6 frame spacing negotiation, Core 6.2 SCI scheduling, EATT, L2CAP CoC/credits, bidirectional useful data, retransmissions, host latency, buffer drops, application headers/security/reliability, and power/coexistence.

With LL payload 251, value 244 fills one LL packet (`244+3+4=251`); value 495 fills two (`495+3+4=502`). At ATT MTU 517, the 512-byte attribute maximum needs three LL packets, so the largest value is not automatically the most efficient.

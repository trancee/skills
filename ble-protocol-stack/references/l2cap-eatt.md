# L2CAP channels, SDUs, MPS, and credits

Source: [Bluetooth Core 6.2 L2CAP](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/logical-link-control-and-adaptation-protocol-specification.html).

L2CAP multiplexes upper protocols by CID and carries upper-layer SDUs. Distinguish:
- SDU segmentation/reassembly: L2CAP credit/retransmission modes split an upper SDU into K/I frames using MPS
- PDU fragmentation/recombination: HCI/controller/lower layer splits an L2CAP PDU for transport

LE fixed CIDs include ATT `0x0004`, signaling `0x0005`, and Security Manager `0x0006`. Dynamic LE CIDs are local endpoints in `0x0040..0x007F`; local and remote CID values differ.

LE Credit Based Flow Control uses one channel per request and supports minimum MTU/MPS 23. Enhanced Credit Based supports grouped channels and minimum MTU/MPS 64. MPS may be up to 65,533; actual platforms impose lower limits.

SPSM `0x0001..0x007F` is SIG-assigned; `0x0080..0x00FF` is dynamic and may be discovered via GATT each reconnection. Do not persist a dynamic SPSM as universal identity.

Initial/current credits count K-frames, not bytes or SDUs. Send only with credit >0, decrement per K-frame, grant credits only after bounded receive capacity is available, and prevent 16-bit overflow. Zero credits means wait, not disconnect/busy-loop.

Reject/close on SDU length > MTU, K-frame payload > MPS, segment total > declared SDU, invalid CID/SPSM, insufficient security, credit overflow, malformed sequence, or resource exhaustion. Preserve SDU boundaries to the application and define close/cancel semantics.

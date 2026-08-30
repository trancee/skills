# Layers and roles

Sources: Bluetooth Core 6.2 [GAP](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/generic-access-profile.html), [GATT](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/generic-attribute-profile--gatt-.html), [ATT](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/attribute-protocol--att-.html), and [L2CAP](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/logical-link-control-and-adaptation-protocol-specification.html).

Layer ownership:
- GAP: discoverability, advertising/scanning, connection modes/procedures, generic security modes and identity/privacy behavior
- GATT: service/characteristic hierarchy and client/server procedures
- ATT: attribute request/command/response/notification/indication/confirmation wire PDUs and errors
- L2CAP: protocol/channel multiplexing, ATT bearer channels, SDU/PDU segmentation/reassembly, lower-layer fragmentation, credit flow control
- Link Layer/PHY: connection scheduling, retransmissions, data length, channels/radio

LE GAP roles: Broadcaster, Observer, Peripheral, Central. GATT roles are Client and Server and are procedure-scoped; a device can act as both concurrently. Central is not synonymous with GATT client, and Peripheral is not synonymous with server.

GATT server attributes contain handle, UUID/type, value, and permissions. Handles are ordered server-instance locators and can change when database bindings change. UUID plus higher-layer context identifies semantics; logical product IDs/versioning identify application contracts.

ATT fixed bearer runs on LE L2CAP CID `0x0004`; LE signaling uses `0x0005`, Security Manager `0x0006`. Dynamic LE CIDs `0x0040..0x007F` serve credit-based channels.

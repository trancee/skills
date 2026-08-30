# GAP advertising, scanning, and connection

Source: [Bluetooth Core 6.2 GAP](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/generic-access-profile.html) and [Argenox layer guide](https://argenox.com/blog/understanding-ble-gap-gatt-and-l2cap).

Legacy advertising/scan-response data each allow 31 encoded octets. Each AD structure consumes one length octet, one AD type octet, and its data. Extended/periodic advertising has different controller/platform limits, fragmentation, PHY, and compatibility; query capabilities and preserve legacy advertising when target scanners require it.

Choose connectable/scannable/directed/undirected/legacy/extended modes from discovery/privacy/latency/power needs. Do not advertise a service UUID that the connected database cannot expose for that product state unless the application contract defines deferred availability.

Advertising identifiers are discovery hints, not authenticated identity. Names may truncate/change; random/private addresses rotate; RSSI varies. Filter by validated service/manufacturer/service-data format and authenticate/authorize after connection.

Version custom manufacturer/service data. Define byte order, length, flags, reserved fields, and backward-compatible parsing. Keep secrets and sensitive mutable state out; advertising is observable and replayable.

Scanning owns interval/window, active/passive mode, duplicate policy, timeout/cancellation, permission/background state, and result expiry. Connection owns one epoch/token so late scan/connect/discovery callbacks cannot mutate a newer session.

GAP continues beyond connection through connection/security/privacy/lifecycle procedures; it does not simply hand off permanently to GATT.

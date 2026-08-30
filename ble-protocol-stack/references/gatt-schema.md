# GATT schema design

Source: [Bluetooth Core 6.2 GATT Sections 2–3](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/generic-attribute-profile--gatt-.html).

A profile contains services; a service contains included services and characteristics; a characteristic has declaration, value, and optional descriptors. Each is represented by attributes.

Use SIG-adopted services/characteristics/descriptors exactly as their profile defines. Vendor functionality uses 128-bit UUIDs. Multiple service/characteristic instances may share a UUID; assign stable logical instance IDs and discover handles rather than assuming uniqueness/order.

Characteristic properties declare permitted procedures: broadcast, read, write without response, write, notify, indicate, authenticated signed writes, extended properties. Value/descriptor permissions independently enforce open/encrypted/authenticated/authorized access. Never infer permissions from properties.

Notify/indicate requires one CCCD (`0x2902`) per characteristic between client/server, irrespective of ATT bearer count. Configuration is per client, defaults zero for non-bonded connections, and persists across connections for bonded clients. Extended Properties requires descriptor `0x2900`.

Value contract must define min/max bytes (maximum attribute value 512), encoding, byte order (characteristic value follows its defining profile/application), units/scaling/range/sentinel, semantic version, atomicity, update cadence, and malformed-value ATT error.

Compatibility: existing standardized service behavior cannot be redefined. Add optional characteristics/includes where allowed; version vendor payloads. Database binding changes require caching machinery.

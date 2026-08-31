# CCCD and outbound updates

CCCD UUID: `00002902-0000-1000-8000-00805f9b34fb`.

Accepted little-endian values:
- disable: `00 00`
- notifications: `01 00`, only with `PROPERTY_NOTIFY`
- indications: `02 00`, only with `PROPERTY_INDICATE`

Track selected mode by server generation + device + characteristic instance. Do not store it in the shared descriptor. Validate offset, exact two-byte length, link security, and application authorization. Read callbacks return the requesting device’s mode.

Outbound queue item: monotonic ID, generation, device, characteristic instance, confirm flag, copied bytes, enqueue time, and caller result. Enforce value <= 512 and product/effective-MTU payload policy.

Default to one server-wide in-flight `notifyCharacteristicChanged` operation because `onNotificationSent` lacks characteristic/value/request ID and Android requires waiting before additional notifications. Deepen to per-device concurrency only with deterministic correlation and device/OEM evidence.

API 33+ submission returns `BluetoothStatusCodes.SUCCESS` or an immediate failure. Install in-flight identity before calling. After acceptance, advance only from matching device/generation `onNotificationSent`; evaluate GATT status. On timeout, disconnect/reset the uncertain device/server flow before reusing an ambiguous callback slot.

Notification (`confirm=false`) and indication (`confirm=true`) transport semantics do not prove that the peer application parsed/persisted the value. Add application sequence/ack/replay when delivery matters.

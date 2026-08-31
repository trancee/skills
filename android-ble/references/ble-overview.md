# Android BLE foundations

Primary source: [Bluetooth Low Energy overview](https://developer.android.com/develop/connectivity/bluetooth/ble/ble-overview), last updated 2026-02-26.

Android’s ordinary BLE application flow is:
1. declare/request the permissions required by the selected operation and target SDK
2. obtain `BluetoothAdapter` and verify hardware/radio availability
3. scan for the intended peripheral with product-specific filters
4. connect to the peer’s GATT server
5. discover required services and characteristics
6. transfer small attribute values through explicit read/write/subscription procedures

Keep the two role axes separate:
- central/peripheral describes link discovery and establishment: the central scans and initiates; the peripheral advertises and accepts
- GATT client/server describes attribute procedures after connection: the client requests; the server fulfills

These axes are independent. An Android app can act as a central and GATT client in the common phone-to-sensor flow, or expose a `BluetoothGattServer` and act as a GATT server. Name both roles in designs, states, logs, and tests; route local server request/response mechanics to `android-ble-gatt-server`.

Use GATT terminology precisely: a service groups characteristics; a characteristic has one value and zero or more descriptors; ATT transports the attributes identified by UUIDs; a Bluetooth SIG profile defines interoperable behavior beyond UUID presence. A discovered UUID alone does not prove profile conformance, value encoding, authorization, or peer identity.

Treat BLE pairing/link protection as shared device transport security, not application isolation. Android’s overview cautions that BLE data exchanged with a paired device is accessible to all apps on the user’s device. Sensitive application data therefore needs an application-layer confidentiality/authentication design and product-specific key ownership; route that protocol to `noise-protocol` or the applicable security skill.

BLE is optimized for small, low-power transfers. Route sustained-rate, PHY, connection-interval, data-length, ATT MTU, and queue tuning to `ble-throughput`; route logical GATT schema/profile work to `ble-protocol-stack`.

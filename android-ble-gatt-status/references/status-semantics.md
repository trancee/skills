# Status semantics

`BluetoothGattCallback.onConnectionStateChange(gatt, status, newState)` reports an operation status plus resulting connection state. A usable connection requires `status == BluetoothGatt.GATT_SUCCESS` and `newState == STATE_CONNECTED`. Evaluate status first, then state.

Current public API 37/37.1 constants include:
- `GATT_SUCCESS = 0`
- `GATT_READ_NOT_PERMITTED = 2`
- `GATT_WRITE_NOT_PERMITTED = 3`
- `GATT_INSUFFICIENT_AUTHENTICATION = 5`
- `GATT_REQUEST_NOT_SUPPORTED = 6`
- `GATT_INVALID_OFFSET = 7`
- `GATT_INSUFFICIENT_AUTHORIZATION = 8`
- `GATT_INVALID_ATTRIBUTE_LENGTH = 13`
- `GATT_INSUFFICIENT_ENCRYPTION = 15`
- `GATT_CONNECTION_CONGESTED = 143`
- `GATT_CONNECTION_TIMEOUT = 147` (API 35+)
- `GATT_FAILURE = 257`

Raw decimal 133 (`0x85`) is widely seen from underlying Android/OEM stacks but has no public `BluetoothGatt.GATT_ERROR` constant in API 37/37.1. Record it as `rawStatus=133`, callback stage, Android build, and lower-layer evidence. Never alias it to `GATT_FAILURE` because 257 is the public constant.

A callback status is not necessarily an HCI reason or ATT error. Map only when HCI/peer trace demonstrates the corresponding controller/air event. Preserve unknown values numerically.

Connection failures, service-discovery failures, and characteristic/descriptor operation failures share the status type but have different stages and remediation. Always attach the originating callback/API stage.

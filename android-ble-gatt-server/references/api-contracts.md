# Android GATT server API contracts

Sources: `BluetoothManager`, `BluetoothGatt`, `BluetoothGattConnectionSettings`, `BluetoothGattService`, `BluetoothGattCharacteristic`, `BluetoothGattDescriptor`, `BluetoothGattServer`, `BluetoothGattServerCallback`, and `BluetoothDevice` documentation read 2026-08-31.

- `BluetoothManager.openGattServer(applicationContext, callback)` creates the local-server proxy and requires `BLUETOOTH_CONNECT` for target API 31+. It has no public executor parameter; explicitly confine callback-owned state.
- `BluetoothGattServer` is the local GATT server. `BluetoothGatt` is a remote GATT client and belongs to `android-ble`/`android-ble-gatt-queue`.
- `BluetoothGattConnectionSettings` is API 37 client connection configuration. It is not used to open a local server. API 37.2 adds RSSI/pathloss thresholds and `BluetoothGattServerCallback.onConnectionUpdated`; public Android 37.0/37.1 stubs lack them.
- `addService` is asynchronous. Do not submit another service until `onServiceAdded`; submission `true` means initiated, not published.
- `BluetoothGattServer.getConnectedDevices`, `getConnectionState`, and `getDevicesMatchingConnectionStates` are unsupported and throw every call. Query `BluetoothManager` with `BluetoothProfile.GATT_SERVER`, but retain app-owned callback state because manager results are system/profile snapshots.
- API 33+ `notifyCharacteristicChanged(device, characteristic, confirm, value)` copies explicit bytes, returns `BluetoothStatusCodes`, and rejects values over the 512-byte GATT attribute maximum. The mutable-value overload is deprecated.
- `sendResponse` returns Boolean. Read/write callbacks carry request ID and offset; writes also carry `preparedWrite` and `responseNeeded`; execute carries its own request ID and commit/cancel flag.
- Android requires waiting for `onNotificationSent` before sending additional notifications. That callback carries only device and status, not characteristic/value/request ID.
- Attribute UUID convenience lookups return the first duplicate. Preserve current object/instance identity when a schema permits repeated UUIDs.

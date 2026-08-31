# GATT connection and operation lifecycle

Sources: [BluetoothDevice](https://developer.android.com/reference/android/bluetooth/BluetoothDevice), [BluetoothGattConnectionSettings](https://developer.android.com/reference/android/bluetooth/BluetoothGattConnectionSettings), [BluetoothGatt](https://developer.android.com/reference/android/bluetooth/BluetoothGatt), and [BluetoothGattCallback](https://developer.android.com/reference/android/bluetooth/BluetoothGattCallback).

API 37 connection:
```kotlin
val settings = BluetoothGattConnectionSettings.Builder()
    .setTransport(BluetoothDevice.TRANSPORT_LE)
    .setAutoConnectEnabled(autoConnect)
    .setAutomaticMtuEnabled(true)
    .build()
val gatt = device.connectGatt(settings, executor, callback)
```

Optional opportunistic/RSSI/pathloss thresholds have specific semantics/version availability and controller discretion. Branch by SDK without reflection.

Model one owner:
`Idle -> Scanning/Connecting -> Connected -> Discovering -> Configuring -> Ready -> Disconnecting -> Closed/RetryWait`.
Every attempt gets an epoch and GATT instance. A callback advances state only when both match. Evaluate status before newState. On terminal failure cancel timeout/current/queued operations, disconnect when meaningful, close exactly once, then route cause/evidence/retry diagnosis to `android-ble-gatt-status`.

Delegate asynchronous request serialization, callback matching, cancellation, timeout reset, and subscription composites to `android-ble-gatt-queue`. This lifecycle owns GATT instance/epoch/readiness and must reset that queue before retiring the epoch.

API 33+ methods accept immutable value bytes and read/notification callbacks provide value bytes. Prefer them over mutable `.value` state. `onServiceChanged` invalidates discovered objects and resets queued operations.

Android 14+ first client MTU request behavior and API 37 automatic MTU require one MTU owner. Use `onMtuChanged`; payload size is effective MTU minus procedure overhead and peer limits.

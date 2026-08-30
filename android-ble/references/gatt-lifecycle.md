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
Every attempt gets an epoch and GATT instance. A callback advances state only when both match. Evaluate status before newState. On terminal failure cancel timeout/current/queued operations, disconnect when meaningful, close exactly once, then schedule policy retry.

Serialize asynchronous GATT requests. Submission success means accepted, not completed. Correlate completion type + characteristic/descriptor UUID/instance + epoch + status. Only then dequeue next. Timeouts terminate the operation/connection rather than issuing overlapping requests.

API 33+ methods accept immutable value bytes and read/notification callbacks provide value bytes. Prefer them over mutable `.value` state. Subscription requires local notification registration and successful CCCD descriptor write. `onServiceChanged` invalidates discovered objects/queued operations.

Android 14+ first client MTU request behavior and API 37 automatic MTU require one MTU owner. Use `onMtuChanged`; payload size is effective MTU minus procedure overhead and peer limits.

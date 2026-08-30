# Scanning, advertising, and identity

Sources: [BluetoothLeScanner](https://developer.android.com/reference/android/bluetooth/le/BluetoothLeScanner) and [background BLE](https://developer.android.com/develop/connectivity/bluetooth/ble/background).

Use `ScanCallback` while process lifetime is owned. Use filtered `startScan(filters, settings, PendingIntent)` when the process may be absent and should be started by a match. PendingIntent delivery includes result list/callback type or error code; validate extras and use the same PendingIntent identity to stop.

Unfiltered callback scanning stops when the screen turns off and resumes on screen-on. Use real `ScanFilter` criteria, but treat filtering as power/delivery selection—not authentication. Avoid rapid stop/start; keep one session token, debounce adapter/lifecycle changes, and handle every `onScanFailed` code.

Companion Device Manager performs user-mediated association without location permission and can support presence callbacks/long-lived companion behavior. Association is not the same as bond or active GATT connection.

Advertising owns advertiser support, settings/data/scan response size, one callback identity, start success/failure, timeout, and stop. Verify encoded service/manufacturer/service data against the product schema and platform length/capability limits.

Identity hierarchy: system companion association/bonded identity or authenticated application ID > validated service/manufacturer payload > transient address/name/RSSI. Resolvable/private addresses and platform privacy can change; never use an unauthenticated address as account/security identity.

# Supplied article audit

Source: [DEV article](https://dev.to/ble_advertiser/solving-the-android-ble-gatt-race-condition-reliable-sequential-operations-with-kotlin-coroutines-k04). API oracle: Android [`BluetoothGatt`](https://developer.android.com/reference/android/bluetooth/BluetoothGatt) and [`BluetoothGattCallback`](https://developer.android.com/reference/android/bluetooth/BluetoothGattCallback).

Keep the article's core diagnosis: Android GATT calls are asynchronous and callback-completing operations require application serialization/timeouts.

Do not copy its sample architecture:
- the channel consumer submits an operation then immediately receives the next; it never awaits callback completion inside the loop, so it does not serialize
- `Channel.UNLIMITED` is unbounded, not “unbuffered”
- a `ConcurrentHashMap<GattOperation, Deferred>` keyed by value equality collides for identical requests and is unnecessary with one in-flight operation
- the sample constructs dummy write operations for callback lookup
- API 33 has value-taking write methods and value-bearing read/notification callbacks, but no `onCharacteristicWrite(gatt, characteristic, value, status)` overload and no status-bearing notification overload
- read completion uses mutable `characteristic.value` instead of callback bytes
- `setCharacteristicNotification` is synchronous local routing; remote subscription completes on separate CCCD descriptor write callback, which the sample does not queue
- timeout removes bookkeeping and allows the next request while the Android operation may still be active
- caller cancellation is not wired to launched/deferred work
- polling connection state with `delay(1000)` and waiting `delay(500)` after discovery are races
- mutable pre-API-33 `.value` APIs, device-address logging, exposed/private methods, and collector initialization contain additional defects

Use one bounded queue, one worker awaiting one internal completion, one in-flight ID/epoch, exact callback matrix, and reset-on-timeout.

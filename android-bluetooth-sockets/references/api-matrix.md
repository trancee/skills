# Android Bluetooth socket API matrix

Primary sources: [`BluetoothSocket`](https://developer.android.com/reference/android/bluetooth/BluetoothSocket), [`BluetoothServerSocket`](https://developer.android.com/reference/android/bluetooth/BluetoothServerSocket), [`BluetoothSocketSettings`](https://developer.android.com/reference/android/bluetooth/BluetoothSocketSettings), `BluetoothAdapter`, and `BluetoothDevice`, read 2026-08-31.

| Transport/API | Server | Client | Rendezvous | Added |
|---|---|---|---|---|
| secure RFCOMM | `listenUsingRfcommWithServiceRecord(name,uuid)` | `createRfcommSocketToServiceRecord(uuid)` | matching SDP service UUID | 5 |
| insecure RFCOMM | `listenUsingInsecureRfcommWithServiceRecord(name,uuid)` | `createInsecureRfcommSocketToServiceRecord(uuid)` | matching SDP service UUID | 10 |
| secure LE CoC | `listenUsingL2capChannel()` | `createL2capChannel(psm)` | server dynamic `getPsm()` disclosed by app | 29 |
| insecure LE CoC | `listenUsingInsecureL2capChannel()` | `createInsecureL2capChannel(psm)` | server dynamic `getPsm()` disclosed by app | 29 |
| settings RFCOMM | `listenUsingSocketSettings(settings)` | `createUsingSocketSettings(settings)` | `TYPE_RFCOMM`, UUID; optional service name | 36 |
| settings LE CoC | same | same | server dynamic PSM; client `TYPE_LE` + PSM 128–255 | 36 |

`BluetoothSocketSettings` authentication/encryption default to `false`; set both deliberately. Current listen documentation says settings APIs support only `TYPE_RFCOMM` and `TYPE_LE`, regardless of broader constants shown elsewhere. `TYPE_SCO` is not an ordinary app socket design path.

`BluetoothSocketSettings` documentation currently contains broken references to `getDataPath`, `setDataPath`, and `DATA_PATH_NO_OFFLOAD`. Neither Android 37.0 nor 37.1 public `android.jar` exposes those settings members. Do not guess/reflection-call them; recheck a future compile SDK.

The server’s LE PSM is released on listening-socket close, Bluetooth off, or unexpected app exit. The application owns authenticated disclosure and refresh.

`BluetoothSocketException` is an `IOException` subtype added in API 34. Catch it first when its error code changes recovery; otherwise retain the `IOException` cause. Socket/server close aborts blocking calls immediately. Server close never closes sockets already returned by `accept`.

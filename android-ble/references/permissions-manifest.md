# Permissions, features, and foreground services

Sources: [Bluetooth permissions](https://developer.android.com/develop/connectivity/bluetooth/bt-permissions) and [foreground service types](https://developer.android.com/develop/background-work/services/fgs/service-types#connected-device).

For target API 31+:
- scan/discover: `BLUETOOTH_SCAN` runtime permission
- advertise: `BLUETOOTH_ADVERTISE` runtime permission
- connect/bond/GATT: `BLUETOOTH_CONNECT` runtime permission
- legacy `BLUETOOTH`/`BLUETOOTH_ADMIN`: cap with `maxSdkVersion=30`
- location: request when scan results derive physical location; `neverForLocation` is a binding product assertion and may filter some devices

Declare `android.hardware.bluetooth_le` with `required=true` only if mandatory. Always check adapter/scanner/advertiser/multiple-advertisement capability and enabled state.

For target API 34+, a BLE foreground service commonly needs:
- `FOREGROUND_SERVICE`
- `FOREGROUND_SERVICE_CONNECTED_DEVICE`
- service `android:foregroundServiceType="connectedDevice"`
- at least one connected-device runtime/manifest prerequisite, normally granted `BLUETOOTH_CONNECT`, `BLUETOOTH_SCAN`, or `BLUETOOTH_ADVERTISE`

Declare `POST_NOTIFICATIONS`/notification channel behavior according to target and user-visible service UX. FGS launch restrictions still apply; a valid type does not authorize a background start.

If BLE event handling starts audio, `mediaPlayback` and Android 17 audio/WIU rules are separate from `connectedDevice`. Start user-intended audio lifecycle while visible or through a documented user/system trigger.

Permission state is mutable. Check at session start and external callbacks; on revocation stop scan/advertise/GATT/service, close owned resources, and expose a recoverable UI state.

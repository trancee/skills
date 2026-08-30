# Android 17 source audit

Primary sources override the supplied articles:
- [Android 17 summary](https://developer.android.com/about/versions/17/summary)
- [all-app changes](https://developer.android.com/about/versions/17/behavior-changes-all)
- [target-37 changes](https://developer.android.com/about/versions/17/behavior-changes-17)
- [BluetoothDevice API 37](https://developer.android.com/reference/android/bluetooth/BluetoothDevice)
- [background audio hardening](https://developer.android.com/about/versions/17/changes/bg-audio)

Verified Android 17 Bluetooth changes:
- all apps: autonomous bond repair; pairing/bond intents expose `EXTRA_PAIRING_CONTEXT`; autonomous system repair constant is `PAIRING_CONTEXT_REPAIRING`; keys replace only after successful repair at equal/stronger security; failed repair yields `ACTION_KEY_MISSING`
- target 37: RFCOMM `BluetoothSocket` InputStream returns `-1` on close/drop, matching standard streams and existing LE CoC behavior
- API 37: legacy `connectGatt(Context, autoConnect, callback, ...)` overloads deprecated; use `BluetoothGattConnectionSettings`, `Executor`, callback

Corrections/qualification for the supplied Medium articles:
- `PAIRING_CONTEXT_AUTONOMOUS` is not the documented constant; use `PAIRING_CONTEXT_REPAIRING`.
- RFCOMM EOF is Bluetooth Classic socket behavior, not a GATT/BLE callback change.
- scan restart throttling predates Android 17 and the often-repeated “5 starts in 30 seconds” is undocumented implementation behavior; design one stable session and handle `onScanFailed`, never encode that number as API contract.
- `connectedDevice` foreground-service type/permission enforcement began with Android 14, not Android 17.
- unfiltered callback scans stopping on screen-off is documented; broad OEM claims about all filtered scans need device evidence.
- random/private Bluetooth addresses are not a new Android 17 change; avoid address-only product identity generally.
- Android 17 blocks cross-profile loopback; same-profile loopback is unaffected. Official behavior guidance does not justify adding `USE_LOOPBACK_INTERFACE` to an ordinary app.
- background audio hardening is real, but target-37 background audio requires an FGS with WIU capability (or documented alarm exception); merely adding `connectedDevice|mediaPlayback` does not make a background-started service WIU-capable.

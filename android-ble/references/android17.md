# Android 17 migration matrix

Sources: [Android 17 summary](https://developer.android.com/about/versions/17/summary), [all-app changes](https://developer.android.com/about/versions/17/behavior-changes-all), [target-37 changes](https://developer.android.com/about/versions/17/behavior-changes-17), and [background audio](https://developer.android.com/about/versions/17/changes/bg-audio).

| Change | Applies | BLE relevance | Required action |
|---|---|---|---|
| autonomous Bluetooth re-pairing | all apps on Android 17 | bond loss for LE or Classic | read `EXTRA_PAIRING_CONTEXT`; leave `PAIRING_CONTEXT_REPAIRING` to system flow; keys replace only on successful equal/stronger repair; handle failed `ACTION_KEY_MISSING` |
| new GATT connection settings | API 37 surface | BLE GATT client | migrate deprecated Context/autoConnect overloads to settings + Executor + callback; branch older SDK |
| RFCOMM InputStream EOF | target API 37 | Classic RFCOMM only; aligns with LE CoC | break on `read() == -1`; still catch I/O failure; never pass negative length |
| BAL hardening | target API 37 | dashboard auto-launch from BLE callback | use user-tapped notification or documented exception; migrate legacy BAL mode |
| background audio hardening | all Android 17, stricter target 37 | BLE-triggered beep/alert | visible activity or valid FGS; target 37 background FGS needs WIU unless alarm exception; inspect `AudioHardening` logs |
| cross-profile loopback block | all apps on Android 17 | only BLE gateways bridging profiles via localhost | same-profile unaffected; redesign/document cross-profile transport; no guessed permission |

Autonomous pairing context API uses `PAIRING_CONTEXT_REPAIRING`, `PAIRING_CONTEXT_USER_APPROVAL_REQUESTED`, and `PAIRING_CONTEXT_USER_PARTICIPATION_REQUESTED`. General apps should not auto-confirm/set PIN; API 37 deprecates `setPin(byte[])` and documents privileged ownership.

Official audio test command:
```bash
adb shell cmd audio set-enable-hardening enable
adb shell cmd audio set-enable-hardening throw
adb dumpsys audio
```

The commonly cited scan-rate threshold and OEM screen-off behavior are not Android 17 normative changes. Test/observe them, but design idempotent scanning without hard-coded undocumented quotas.

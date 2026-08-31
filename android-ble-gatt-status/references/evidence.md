# Evidence ladder

## App timeline

Record monotonic nanoseconds/milliseconds, attempt ID, connection epoch, callback GATT identity hash, redacted device pseudonym, event, decimal/hex status, state, submission result, elapsed time, retry decision, permission/adapter/bond/process state, scan age/RSSI/connectable flag, and queue depth. Do not log MAC/name/payload secrets.

## Android system

Capture targeted logcat Bluetooth/GATT/controller tags, `adb shell dumpsys bluetooth_manager`, AppOps/permission state, bugreport, and `ApplicationExitInfo` for process death. Record exact Android build fingerprint/device/OEM and app target/compile version.

## Controller/air

Enable Bluetooth HCI snoop through supported developer settings/test setup. Correlate LE Create Connection/extended command, command status, connection complete/enhanced connection complete, authentication/encryption, disconnect complete, and reason codes by time. Use an over-air sniffer when controller logs cannot prove advertisements/interference/peer response.

## Peer

Capture peripheral advertising/connectability, connection limit, firmware logs, reset reason, security/bond database, and disconnect behavior. A known-good peer/app control narrows but does not by itself prove root cause.

## Causal bar

- app cause: deterministic app-state violation precedes failure and fixing it removes failure across controlled repeats
- peer/RF/controller cause: lower-layer/peer evidence identifies rejection/timeout/disconnect and controls agree
- platform/OEM cause: minimal app reproduces specifically on device/build with controls and bugreport/HCI evidence
- unknown: only opaque app status or inconsistent controls exist

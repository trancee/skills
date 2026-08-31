# Android BLE verification matrix

Build/static:
- compile/target 37 with API 37/37.1 SDK, min-SDK branches, manifest merge, lint, release shrinker
- API 31 Nearby permissions and `neverForLocation` truth
- API 33 immutable value methods/callbacks
- API 34 FGS type/permission/start prerequisites
- API 37 connection settings/executor and pairing-context constants

State tests with fake adapter/clock/executor:
- one scan/advertise/GATT owner and monotonically increasing epoch
- permission denied/revoked, Bluetooth unavailable/off/on, submit false/status error/timeout
- stale/duplicate/out-of-order callbacks cannot advance state
- queue starts one operation; disconnect clears it; CCCD ready after descriptor success
- process restoration recreates discovery/subscriptions from logical state

Real-device tests:
- Android 17 plus representative 12–16 and OEMs
- callback and PendingIntent filtered scans, screen-off/background/process kill
- direct/auto GATT, API 37 automatic MTU, bond loss/autonomous repair/failure
- service-changed cache invalidation, API 33 value snapshots, characteristic/descriptor failures
- companion presence and connectedDevice FGS start/user stop/revocation
- advertise success/failure where supported
- background audio hardening/BAL/cross-profile gateway only if product uses them

Evidence: timestamped state/epoch/status logs without payload secrets, `adb dumpsys bluetooth_manager`, bugreport, Bluetooth HCI snoop, notification/FGS state, permission/AppOps, process-death trigger, and peripheral trace.

No emulator-only pass proves radio/OEM/background/bond behavior. Keep metrics low-cardinality and never log device addresses, pairing keys, health payloads, or full advertisement contents by default.

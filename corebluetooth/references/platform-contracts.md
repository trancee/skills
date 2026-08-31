# Platform, privacy, and API contracts

Primary source: [Core Bluetooth](https://developer.apple.com/documentation/corebluetooth), read 2026-08-31.

- Core Bluetooth manager/peer/attribute classes are framework-owned. Use composition; Apple states that subclassing any Core Bluetooth class is unsupported and undefined.
- `NSBluetoothAlwaysUsageDescription` is required for Bluetooth access in apps linked on or after iOS 13. Add `NSBluetoothPeripheralUsageDescription` too when deployment supports iOS 12 or earlier. Verify the effective built target, not merely a source plist.
- A manager may act only after its state becomes `.poweredOn`. Treat authorization independently through `CBManager.authorization` where available.
- `CBCentralManager` is available across current Apple platforms, with per-symbol version differences. Check exact symbol availability at the deployment target.
- `CBPeripheralManager` advertising is unavailable on watchOS, tvOS, and visionOS even though some peripheral-manager symbols appear in shared headers/documentation.
- Core Bluetooth background execution modes are unsupported for iPad apps running on macOS.
- `startAdvertising` accepts only `CBAdvertisementDataLocalNameKey` and `CBAdvertisementDataServiceUUIDsKey`; Core Bluetooth sends them best-effort within platform limits.
- iOS 26 documents foreground-equivalent Core Bluetooth privileges while an app with an instantiated `CBManager` runs a legitimate Live Activity. This supplements rather than erases lifecycle, product eligibility, battery, and platform constraints.
- Apple provides a Core Bluetooth Classic sample, but Core Bluetooth is not a general arbitrary BR/EDR profile API. Verify the device/profile/MFi/entitlement/platform contract before choosing it; otherwise use the documented framework such as External Accessory.
- Core Bluetooth exposes L2CAP channels, but logical PSM/framing/security/backpressure design belongs in `ble-protocol-stack`.

Use current symbol pages as the availability oracle. Treat the archived programming guide as background semantics/context where current pages do not replace it, not as an API-signature oracle.

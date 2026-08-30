# Source currency and authority

Current normative baseline: [Bluetooth Core Specification 6.2 feature overview](https://www.bluetooth.com/bluetooth-core-6-2-feature-overview/) plus the linked Core 6.2 specification. Core 6.2 adds Shorter Connection Intervals (SCI): 375 us minimum/125 us resolution only when peer controller and host feature support is negotiated; legacy Baseline Connection Interval Values remain 7.5 ms+ in 1.25 ms units.

Current platform APIs:
- [Android `BluetoothGatt.requestMtu`](https://developer.android.com/reference/android/bluetooth/BluetoothGatt#requestMtu(int)): Android 14+ requests ATT MTU 517 for the first GATT client request and ignores later requests; callback/effective peer value still governs.
- [Apple `maximumWriteValueLength(for:)`](https://developer.apple.com/documentation/corebluetooth/cbperipheral/maximumwritevaluelength(for:)): query per write type.
- [Apple write-command backpressure](https://developer.apple.com/documentation/corebluetooth/cbperipheral/cansendwritewithoutresponse): stop/resume through readiness state/callback.

Supplied engineering sources:
- [Memfault practical guide](https://interrupt.memfault.com/blog/ble-throughput-primer) (2019): useful layer/trace diagnosis; phone MTU/packet examples are historical.
- [Novel Bits throughput guide](https://novelbits.io/bluetooth-5-speed-maximum-throughput/) (updated 2026): packet airtime and PHY/DLE/MTU explanation.
- [Punch Through mobile article](https://punchthrough.com/maximizing-ble-throughput-on-ios-and-android/) (2016; page explicitly warns parts are outdated): use concepts, not device constants.
- [Punch Through FAQ](https://punchthrough.com/ble-throughput-optimization-faq/) (2026): current empirical payload/phone guidance; measurements remain device-specific.
- [Argenox Bluetooth 6 guide](https://argenox.com/blog/bluetooth-le-throughput-max-performance) (2026): stack/buffer/Core 6 considerations; validate claims against effective trace/spec.

Resolve disagreements in this order: current adopted Core + mandatory errata, current OS API docs, controller/stack docs, on-air trace, repeatable measurements, then article heuristics. Never transplant a historical phone's packets/event, interval, or MTU into a compatibility claim.

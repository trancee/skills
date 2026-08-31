# Supplied article audit

Source: [Android BLE Tools article](https://gist.githubusercontent.com/roywatson/7ce389862e245a622dba2e34e28331e6/raw/506e408d1fa9f7616c4b4c00d7efb43ddd414cd8/android_ble_tools.md) and [repository](https://github.com/roywatson/android_ble_tools), inspected 2026-08-31.

Keep:
- Android-specific BLE behavior remains visible instead of hidden by a false platform-neutral abstraction
- callbackFlow + `awaitClose` fits bounded interactive scanning
- GATT UI exposes human-scale progress and callback completion
- subscription setup distinguishes local routing from CCCD completion
- timeout retires/closes uncertain GATT rather than retrying into it
- raw bytes remain visible beside decoded values
- parser/formatting logic receives JVM tests while radio behavior requires physical devices

Qualify or replace:
- A `Mutex` serializes GATT only if held through the exact callback completion; delegate full semantics to `android-ble-gatt-queue`.
- An eight-second Polar read is one empirical observation, not a universal timeout. Measure by operation/device and reset on timeout.
- Address deduplication is a transient observation heuristic, not durable identity; random/private addresses rotate and addresses are sensitive.
- Connecting to unnamed scan results to read Generic Access Device Name is intrusive, slow, and can disturb devices. Require selection/target filters.
- The 31-byte failure applies to legacy `startAdvertising`; extended advertising has different capability/budgets. Calculate the chosen mode.
- `setIncludeDeviceName(true)` uses adapter state. Temporarily changing `BluetoothAdapter.name` mutates global device state and can remain changed after crash; an inspector should not do this.
- The shown SFLOAT arithmetic omits special encodings (`NaN`, `NRes`, infinities, reserved). Use typed special results and official SIG specifications.
- Heart Rate/Blood Pressure flags, optional fields, RFU bits, units, and errata must come from current adopted specifications, not UUID folklore.
- A BLE diagnostic tool must default read-only and require explicit confirmation for writes or global/radio mutation.

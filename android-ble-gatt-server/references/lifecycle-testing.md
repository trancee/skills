# Lifecycle and verification

Deterministic callback-state tests:
- open failure/null, add-service rejection/callback failure/strict order
- duplicate UUID instance routing and database generation retirement
- connection status before state, simultaneous devices, disconnect cleanup
- characteristic/descriptor read: zero/end/invalid offsets, authorization, send-response false, one response
- immediate write request versus command, invalid length/value, no mutation on failure
- prepared fragments: order/gap/overlap/retransmit/bounds/timeout; execute/cancel/duplicate/disconnect; atomic multi-attribute commit
- per-device CCCD read/write/mode/property/security, prepared CCCD, disconnect clearing
- notification: API 33 submission failure, callback success/failure/mismatch/duplicate/stale, bounded queue, indication mode, timeout reset
- close during request/transaction/notification and late callbacks

Compile matrix:
- min SDK/API 18 compatibility
- API 33 explicit value notification branch
- API 37.0/37.1 without `onConnectionUpdated`/threshold APIs
- API 37.2 symbols only when the compile SDK actually supplies them
- target API 31+ `BLUETOOTH_CONNECT` and API 34+ connected-device lifecycle declarations where used

Real clients: Android `BluetoothGatt`, iOS Core Bluetooth, embedded stack, generic GATT explorer. Test discovery/cache/Service Changed, read/write offsets, prepared/execute, two centrals with independent CCCDs/MTUs, rapid notifications, bond/security changes, radio toggle, permission revoke, background/process death, and representative OEMs.

Capture server generation, device-scoped pseudonym, request ID/type/attribute logical ID/offset/length/status, transaction/queue depth, MTU, callback elapsed time, and HCI/ATT trace. Exclude MAC addresses and payload secrets.

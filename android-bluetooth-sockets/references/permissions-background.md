# Permissions, adapter, and process lifetime

Target API 31+:
- `BLUETOOTH_CONNECT` runtime permission: communicate with paired devices, listen, connect, inspect peer state
- `BLUETOOTH_SCAN` runtime permission: discover and call `BluetoothAdapter.cancelDiscovery`
- `BLUETOOTH_ADVERTISE` runtime permission: make the local device discoverable

Cap legacy `BLUETOOTH` and `BLUETOOTH_ADMIN` declarations at API 30. Apply location permissions/`neverForLocation` only from actual discovery/location use; route discovery design to the broader Android Bluetooth skill.

Check hardware feature (`android.hardware.bluetooth` for RFCOMM, `android.hardware.bluetooth_le` for LE CoC), nullable adapter, adapter state, and permission before creating sockets. Request enablement with `ACTION_REQUEST_ENABLE`; ordinary target-33+ apps cannot programmatically enable/disable Bluetooth.

Official socket guidance says always call `cancelDiscovery` before connect because discovery is adapter-wide and degrades connection speed/traffic. On API 31+, this requires `BLUETOOTH_SCAN`; make that permission a deliberate prerequisite or record the degraded/unsupported branch rather than swallowing `SecurityException`.

A connected socket survives only while the app process and radio/link survive. For a user-visible long transfer/connection, use a `connectedDevice` foreground service under current start restrictions. On API 34+, declare `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_CONNECTED_DEVICE`, service type `connectedDevice`, and satisfy a listed runtime prerequisite such as granted `BLUETOOTH_CONNECT`. Companion Device Manager/presence may better fit associated devices.

Persist only peer/product identity, transfer checkpoint, frame sequence, and reconnect policy. On restart, reacquire adapter/permissions/device and create fresh sockets. Never serialize descriptors, sockets, streams, PSM validity, or thread/coroutine state.

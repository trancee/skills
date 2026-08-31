# Central role lifecycle

State model:
`unavailable -> idle -> scanning/retrieving -> connecting -> discovering -> ready -> disconnecting -> idle`, with a monotonically increasing manager/connection generation.

Create one long-lived `CBCentralManager` owner. The initializer’s queue controls central delegate callbacks; `nil` means main queue. Retain discovered/selected `CBPeripheral` instances strongly and assign each peripheral delegate after connection or restoration.

Scan with required service UUIDs whenever possible. A new `scanForPeripherals` call replaces previous scan parameters. Treat advertisement dictionaries, names, manufacturer data, and RSSI as snapshots/hints; identify the selected peer with the product’s authenticated identity rather than display name alone. Allow duplicate discoveries only for a measured need and stop scanning promptly.

`retrievePeripherals(withIdentifiers:)` returns known objects, not proof that they are nearby or connected. `retrieveConnectedPeripherals(withServices:)` returns system-connected peripherals matching services, not ownership by this app. Validate state and connect deliberately.

`connect` completes via `didConnect` or `didFailToConnect`; attempts do not time out. Implement an app deadline that calls `cancelPeripheralConnection`. On disconnect, retire the connection generation, fail pending work, clear discovered attribute instances, and apply bounded reconnect policy.

Discover required services first; from `didDiscoverServices`, locate exact current instances and discover required characteristics; discover descriptors only when the application needs them. Inspect every callback error before properties. `didModifyServices` makes listed services unusable: discard their descendants and rediscover.

Restored peripherals may already be connecting/connected and partially discovered. Reattach delegates, inspect current state/services/subscriptions, and resume from the first missing transition instead of restarting blindly.

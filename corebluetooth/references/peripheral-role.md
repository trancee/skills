# Local peripheral role

Build the local GATT database from `CBMutableService`, `CBMutableCharacteristic`, and optional descriptors. Define characteristic properties separately from `CBAttributePermissions`; require encryption/authentication only according to the product security contract. Use `nil` characteristic value for dynamic values handled through ATT request callbacks.

Publish included services first, then parents. `add` completes at `peripheralManager(_:didAdd:error:)`; keep a publication state per service. Start advertising after required services publish and handle the advertising callback. Core Bluetooth advertising accepts only local name and service UUID keys and sends them best-effort.

Read request:
1. verify manager generation, characteristic identity, permission/application authorization, and `offset <= value.count`
2. set `request.value` to the suffix beginning at the requested offset (within product/central limits)
3. call `respond(to:withResult:)` exactly once with success or a precise `CBATTError.Code`

Write batch:
1. require a nonempty request array
2. validate every characteristic, offset, value, permission, length, and transaction-level invariant without mutation
3. reject the entire batch immediately if any request is invalid
4. apply all values atomically in application state
5. respond exactly once using the first request

Track `didSubscribeTo`/`didUnsubscribeFrom`. Maintain per-central transfer state when chunk size/progress differs. `CBCentral` identity is process/framework state, not a durable authenticated product identity.

On power/reset/teardown, stop advertising, remove services where appropriate, retire pending requests/updates, and rebuild only after `.poweredOn`. Never subclass Core Bluetooth classes.

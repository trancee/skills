# Local service database

Build from a validated logical schema:
- service: UUID, primary/secondary type, included-service dependencies
- characteristic: UUID, properties, permissions, value schema, maximum length, security/application authorization
- descriptor: UUID, permissions, value schema; add CCCD only for notify/indicate configuration

Properties describe supported GATT procedures; permissions describe link-security access. Product authorization and application-layer confidentiality remain separate.

Publish dependency order explicitly. A service is usable only after `addService == true` and matching `onServiceAdded(status == GATT_SUCCESS)`. Add one at a time. Treat publication failure as a database readiness failure; do not advertise readiness for a partial required schema.

Do not keep per-central dynamic values inside shared `BluetoothGattCharacteristic`/`BluetoothGattDescriptor` objects. Store authoritative values and CCCDs in server state, snapshot for callbacks, and use API 33+ explicit notification values.

Keys must distinguish server generation, service instance, characteristic instance, descriptor instance, and device where state is per-central. UUID-only lookup is ambiguous when repeated services/characteristics exist.

Database updates can trigger Service Changed to clients. Version value encodings/schema, retire removed object references, republish in order, and test Android/iOS/embedded cache invalidation and rediscovery.

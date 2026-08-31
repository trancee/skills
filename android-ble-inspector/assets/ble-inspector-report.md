# Android BLE inspector change: [scope]

## Diagnostic contract
- questions/use cases and intended users:
- allowed reads/writes/radio/global mutations:
- Android/device/OEM/peripheral matrix:
- permissions, scan power/timeout/filter policy:
- raw data sensitivity, redaction, retention/export:

## Architecture and state
- scanner/connection/GATT queue/server owners:
- screen/session/per-attribute state model:
- observation/product/connection/attribute/operation IDs:
- collection bounds and lifecycle teardown:

## Surfaces
- scanner/device identity:
- GATT tree/stable rows:
- read/write/subscription controls and progress:
- raw hex/ASCII and decoder registry:
- local server/advertiser demo:

## Decoders
| service/characteristic | adopted spec/errata | flags/optional fields | special values | tests |
|---|---|---|---|---|
| | | | | |

## Verification
- JVM parser/reducer/size tests:
- Compose semantics/accessibility tests:
- physical device/peripheral scenarios:
- callback/HCI evidence:
- findings and limitations:

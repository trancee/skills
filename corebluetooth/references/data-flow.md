# Central operations and flow control

| Call | Completion/readiness |
|---|---|
| `discoverServices` | `didDiscoverServices` |
| `discoverCharacteristics` | `didDiscoverCharacteristicsFor` |
| `discoverDescriptors` | `didDiscoverDescriptorsFor` |
| `readValue(for: CBCharacteristic)` | `didUpdateValueFor characteristic` |
| `readValue(for: CBDescriptor)` | `didUpdateValueFor descriptor` |
| `writeValue(..., type: .withResponse)` | `didWriteValueFor characteristic` |
| `writeValue(..., type: .withoutResponse)` | no per-write callback; gate on `canSendWriteWithoutResponse`, resume at `peripheralIsReady(toSendWriteWithoutResponse:)` |
| descriptor write | `didWriteValueFor descriptor` |
| `setNotifyValue` | `didUpdateNotificationStateFor`; later values use `didUpdateValueFor characteristic` |
| `readRSSI` | `didReadRSSI` |
| `openL2CAPChannel` | `didOpen` |

Check characteristic properties before selecting `.withResponse`, `.withoutResponse`, notify, or indicate behavior. Core Bluetooth copies data passed to characteristic writes.

`didUpdateValueFor characteristic` multiplexes one-shot reads and unsolicited notification/indication updates. A continuation map keyed only by characteristic can consume the wrong event. Keep a per-connection-generation operation record and a separate subscription stream; serialize reads on an actively notifying characteristic unless the application can correlate its protocol values unambiguously.

For `.withResponse`, preserve request identity until callback error/success. For `.withoutResponse`, chunk to `maximumWriteValueLength(for: .withoutResponse)`, submit while `canSendWriteWithoutResponse` remains true, then stop and resume from the readiness delegate. Core Bluetooth provides no delivery error for individual command writes; add sequence/ack/retry at the application protocol when delivery matters.

For local-peripheral notifications, chunk for the smallest target `CBCentral.maximumUpdateValueLength`. `updateValue == false` means Core Bluetooth’s transmit queue is full; retain and retry the same chunk only after `peripheralManagerIsReady(toUpdateSubscribers:)`. A `true` result is accepted for transmission, not peer application acknowledgement.

Bound queues and copy `Data` crossing isolation. Timeout/cancellation of a callback API does not erase a later delegate event: retire generation/operation identity before advancing so late callbacks cannot complete new work.

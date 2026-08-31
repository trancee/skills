# Android GATT submission/callback matrix

Verify exact current docs for the compile SDK.

| Operation | Submission result | Matching callback/result |
|---|---|---|
| `discoverServices()` | Boolean accepted | `onServicesDiscovered(gatt,status)` |
| `readCharacteristic(c)` | Boolean accepted | API 33+ `onCharacteristicRead(gatt,c,value,status)` |
| `writeCharacteristic(c,value,type)` | `BluetoothStatusCodes` submission status | `onCharacteristicWrite(gatt,c,status)`; no callback value |
| `readDescriptor(d)` | Boolean accepted | API 33+ `onDescriptorRead(gatt,d,status,value)` |
| `writeDescriptor(d,value)` | `BluetoothStatusCodes` submission status | `onDescriptorWrite(gatt,d,status)`; no callback value |
| `requestMtu(n)` | Boolean accepted | `onMtuChanged(gatt,mtu,status)` |
| `readRemoteRssi()` | Boolean accepted | `onReadRemoteRssi(gatt,rssi,status)` |
| reliable write execute | Boolean accepted | `onReliableWriteCompleted(gatt,status)` after per-write callbacks |
| `setCharacteristicNotification(c,on)` | Boolean immediate local result | no completion callback; pair with CCCD descriptor write |

`setPreferredPhy` has `onPhyUpdate` but is connection configuration and may be owned outside the ordinary request queue. Notifications arrive via API 33+ `onCharacteristicChanged(gatt,c,value)` and are unsolicited; they never complete a read/write request. `onServiceChanged` and connection-state callbacks are terminal/invalidation events.

Match: GATT instance + epoch + callback kind + discovered object/instance. Check submission acceptance separately from callback GATT status. Copy callback values immediately. API 33 memory-safe callbacks avoid mutable characteristic/descriptor value races.

Write-without-response still uses the documented write callback path, but device/stack behavior and throughput policy require real-device verification. Do not invent completion from a delay.

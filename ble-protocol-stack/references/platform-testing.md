# Platform integration and testing

Platform APIs rename/synthesize parts of the model. Map every call/callback to GAP role/procedure, GATT client/server action, ATT PDU/error, and L2CAP channel. Do not infer wire behavior from API success alone.

Test schema:
- UUID byte/canonical forms and duplicate logical instances
- property/permission/security matrix for every characteristic/descriptor
- empty/min/max/too-long/malformed values and offsets
- read/read-blob, write command/request, prepare/execute commit/cancel
- CCCD notify/indicate enable/disable, bonded persistence, multiple clients
- Service Changed/Database Hash/cache invalidation across firmware versions
- disconnect/reconnect/cancel and stale callback epochs
- multiple ATT bearers/EATT ordering and database-out-of-sync
- CoC SPSM/CID/MTU/MPS/credit exhaustion/replenishment/malformed SDU

Cross-test iOS CoreBluetooth, Android BluetoothGatt, embedded stack, and a generic inspector/sniffer. Android/iOS may cache services aggressively, limit exposed bearers/channels, synthesize CCCDs, and serialize operations differently; record OS/device/stack versions.

Capture over-air or HCI evidence for advertising bytes, discovery handle ranges, ATT opcodes/errors, CCCD writes, MTU exchange, Service Changed/Database Hash, EATT bearer setup, L2CAP signaling/CIDs/credits, and disconnect reason.

Fuzz/decode custom advertising/value/application frames with strict lengths before field access. Security tests verify attribute/channel permission behavior across unencrypted, encrypted, authenticated, bonded, unauthorized, and key-size states. Pairing algorithm design remains outside this skill.

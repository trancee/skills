# ATT procedures and errors

Source: [Bluetooth Core 6.2 ATT](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/attribute-protocol--att-.html) and [GATT procedure mapping](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/generic-attribute-profile--gatt-.html).

PDU classes:
- command: no ATT response (Write Command)
- request/response: one transaction on an unenhanced bearer
- notification: server update without ATT acknowledgment
- indication/confirmation: confirmed server update

Use procedure-specific payload limits; common Write Command/Request and single Notification/Indication values are `ATT_MTU - 3`. Attribute values cap at 512. Signed write, multiple notification, offsets, prepare writes, and other opcodes have different overhead.

Long reads repeat Read Blob with increasing offsets until completion/error. Long/reliable writes stage Prepare Write fragments and atomically commit/cancel with Execute Write. Key staging by client, bearer/transaction, handle, and offset; validate overlap/gaps/total/security before mutation.

CCCD write enables server delivery for that client. Local callback registration alone is insufficient. Notifications can be lost above LL/application buffers; indications serialize on confirmation and are not bulk-stream primitives.

Server validates handle, PDU length, offset, property/procedure support, read/write permission, authentication, authorization, encryption/key size, prepared-write resources, and database awareness. Return the most precise ATT error without leaking protected data.

On disconnect cancel pending requests, staged writes, indications, and callbacks from that connection epoch. Copy callback buffers before platform-owned lifetime ends.

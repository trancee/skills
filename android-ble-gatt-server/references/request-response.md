# Read and immediate-write responses

Read callback algorithm:
1. reject stale generation/disconnected device/unknown current attribute
2. verify property, Android permission declaration, link security, and application authorization
3. snapshot authoritative bytes
4. require `0 <= offset <= value.size`; otherwise `GATT_INVALID_OFFSET`
5. choose the response suffix/chunk within schema and connection policy
6. call `sendResponse(device, requestId, status, offset, value)` once
7. if submission returns false, terminate/degrade the device session; never resend the same ATT response blindly

Use precise status: success, read/write not permitted, insufficient authentication/encryption/authorization, invalid offset/attribute length, request not supported, or failure.

Immediate write algorithm:
1. copy callback bytes
2. validate current attribute, write property, permissions/security/authorization, offset, length, encoding/range, and product state without mutation
3. apply atomically only after all validation succeeds
4. if `responseNeeded`, call `sendResponse` once with result; otherwise send none because a write command has no ATT response

Descriptor callbacks follow identical bounds/security rules. CCCD values are exactly two bytes and effective per device. Read CCCD from per-device subscription state.

Keep callbacks fast. If product validation requires slow work, define a bounded deadline and ownership; remote ATT requests cannot wait indefinitely while arbitrary asynchronous work runs.

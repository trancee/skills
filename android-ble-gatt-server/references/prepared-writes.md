# Prepared and execute writes

A prepared write is a transaction proposal, not immediate mutation. Maintain one bounded transaction per server generation/device with fragments keyed by attribute instance and offset.

For every `preparedWrite == true` callback:
1. copy bytes immediately
2. validate device/generation/attribute/security/authorization and offset/length
3. reject overlapping fragments unless the product explicitly supports identical retransmission
4. enforce transaction limits: total bytes, fragment count, attributes, and deadline
5. stage without changing authoritative state
6. if `responseNeeded`, echo the accepted offset/value with success; otherwise follow the callback contract without inventing a response

On `onExecuteWrite(device, requestId, execute)`:
- false: discard all staged fragments and respond success
- true: require a valid active transaction, assemble each value with explicit gap policy, validate final encodings/lengths and cross-attribute invariants, then commit all values atomically and respond success
- any failure: commit none, discard staging, and respond once with the precise status

Clear transactions on execute, disconnect, timeout, permission loss, server close, or generation retirement. Duplicate/late execute requests cannot recommit.

Include CCCD fragments in the same engine; subscription state changes only at execute commit. Keep request IDs for diagnostics/response matching but use device/attribute/offset for fragment ownership because prepare requests have distinct IDs.

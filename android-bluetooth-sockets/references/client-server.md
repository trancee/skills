# Client and server ownership

Model explicit owners:
`Idle -> Listening/Connecting -> Connected -> Closing -> Closed`, with a monotonically increasing attempt/session ID. Only the current owner may publish success, retry, or close.

Server:
1. create one listening socket from a matched transport/security configuration
2. for LE CoC, capture and publish the dynamic PSM while that listener remains alive
3. block in `accept` off-main; `accept(timeout)` reports timeout as `IOException`
4. transfer each returned already-connected socket to a connection owner
5. close rejected/unowned sockets immediately
6. close listener to abort acceptance; close every accepted socket separately

RFCOMM supports one connected client per channel at a time. If the product requires multiple peers, define separate listening/channel ownership and test device limits instead of assuming TCP server semantics.

Client:
1. obtain the intended `BluetoothDevice` from a user-approved discovery/association/bonded identity
2. cancel adapter discovery after `BLUETOOTH_SCAN` is granted
3. create a fresh matched socket
4. block in `connect` off-main
5. on timeout/cancellation, close from another context and await worker termination
6. on success, transfer exactly once; on failure, close and recreate for retry

Connection attempts may have platform timeouts, but the API does not promise a stable duration. Use a product deadline. `isConnected` is a momentary transport state; the next read/write is authoritative for liveness.

Secure RFCOMM/LE CoC requests authenticated/encrypted links. Insecure variants can expose traffic or peer identity to active attackers; pair them with an application authentication protocol when the product requires peer authenticity.

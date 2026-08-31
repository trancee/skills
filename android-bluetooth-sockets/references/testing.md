# Verification matrix

Deterministic fake-stream/owner tests:
- fragmented header/payload, coalesced frames, exact buffer boundary, EOF before/within/after frame
- invalid length/version/type/integrity, allocation cap, decoder reset
- concurrent writers preserve whole-frame order; bounded queue rejects/blocks by policy
- slow/blocking writer, reader failure, writer failure, simultaneous close, idempotent close
- cancellation/timeout during accept/connect/read/write closes exact socket and joins worker
- stale attempt/session cannot publish success or close replacement session
- expected close-induced `IOException` preserves primary terminal cause

Compile branches:
- legacy RFCOMM at min SDK
- API 29 secure/insecure LE CoC
- API 34 `BluetoothSocketException.errorCode`
- API 36 settings RFCOMM/TYPE_LE and lower-SDK guard
- API 37 target EOF behavior
- merged permissions/features/foreground-service declarations

Real-device matrix:
- Android/OEM versions, Classic-only/dual/LE peers, server/client direction
- matched/mismatched UUID, SDP lifetime, discoverability, bond/pairing reject
- LE PSM publication, close/off/process-death invalidation, secure/insecure failures
- adapter discovery contention, radio toggle, permission revoke, range loss
- partial/high-volume/slow-consumer transfer, frame corruption, reconnect/resume
- background/screen-off/foreground-service/user-stop/process-kill/reboot

Capture `BluetoothSocketException.errorCode`, `IOException` cause, socket type/max packet hints, session/frame counters, bond/adapter/permission state, logcat, and HCI snoop where needed. Redact MAC addresses, names, UUIDs when sensitive, and payloads/secrets.

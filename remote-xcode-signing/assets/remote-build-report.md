# Remote Xcode signing record

## Contract
- Remote alias/account (redacted if shared):
- Repository revision and remote path:
- macOS/Xcode/SDK/DEVELOPER_DIR:
- Project/workspace, shared scheme, configuration, destination:
- Distribution method; manual/automatic policy:
- Team and app/extension bundle IDs:
- Authorized keychain/trust/provisioning/MCP mutations:

## Signing evidence
- Identity certificate fingerprint/type/validity/issuer:
- Matching private key present; no private bytes recorded:
- Intermediate location and trust policy:
- Keychain ownership/lock timeout/narrow access:
- Same-SSH-session signing probe command/result:
- Per-target settings inspector findings/resolutions:
- Profiles: signer, App ID, entitlements, expiry, distribution/device match:

## Build artifacts
- Archive command/exit/path:
- Export command/exit/ExportOptions method:
- IPA/checksum:
- Raw logs/result bundle:
- Exported and embedded signature verification:
- Profile/entitlement/identity checks:
- Device installation evidence (or unverified):

## MCP
- Exact server/version/backend:
- Remote stdio command and client schema (no secrets):
- GUI-session or headless-preview prerequisites:
- Permissions/project scope explicitly approved:
- Initialize/tools-list and actual build result:
- Signing/profile setup remains independent:
- Telemetry/macro-validation policy:

## Cleanup and limits
- Search list/default state restored:
- Only job-owned keychain/profiles/secrets removed:
- Cleanup failure or stale-job recovery ownership:
- Unavailable host/signing/device evidence:
- Remaining findings and excluded publishing/upload:

---
name: remote-xcode-signing
description: "Builds, archives, exports, and diagnoses signed iOS apps on remote Macs over SSH. Use when configuring Xcode CI keychains, certificate trust and private-key access, provisioning profiles, xcodebuild signing, or SSH-connected Xcode MCP servers. Don't use for notarizing macOS apps, App Store uploads, Linux cross-compilation with xtool, unrelated SSH administration, or bypassing macOS security approvals."
compatibility: "Build/sign execution requires a remote macOS account, full compatible Xcode, authorized signing assets, and SSH access. Apple MCP: traditional open-Xcode bridge or version-specific Xcode 27 headless preview. MobileBuildMCP 2.7.1 is separate. Settings inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://developer.apple.com/documentation/technotes/tn3161-inside-code-signing-certificates"
  sourceVersion: "Apple signing threads 690923/253761477; Xcode external-agent docs and Xcode 27 headless preview; MobileBuildMCP 2.7.1@d13ff0c707b0681769cf31da0eb42c4f94ceafff; inspected 2026-10-07"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-07T12:13:08+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-07T12:13:08+02:00"
---

# Remote Xcode signing

## 1. Contract and transport

1. RECORD remote SSH alias/account, repository revision/path, full Xcode path/version, project or workspace, shared scheme, configuration, app/extensions, Team ID, bundle IDs, distribution method, and manual/automatic signing policy.
2. USE the same non-root account for keychain provisioning, SSH build, and any Xcode/MCP session. Use trusted SSH host keys and noninteractive authentication; no agent forwarding or host-key-check bypass by default.
3. SELECT direct `xcodebuild` for reproducible archive/export. MCP is optional agent orchestration, not a signing prerequisite or credential manager.
4. READ `references/source-evidence.md` when reconciling the supplied guides, trust errors, or claims about headless MCP.
5. REQUIRE explicit authorization before importing private keys, changing certificate trust/search lists, enabling MCP permissions, registering devices, or contacting Apple's provisioning service. Keep publishing/upload outside this workflow.

Gate: one authorized host/account, build tuple, signing/distribution contract, and mutation scope.

## 2. Preflight in the actual SSH session

READ `references/archive-export.md`. Pin `DEVELOPER_DIR` per process instead of changing a shared Mac's global Xcode selection.

1. CHECK `id -un`, `sw_vers`, `xcodebuild -version`, SDKs, installed `xcodebuild -help`, and first-launch/license completion. Initial Xcode installation/license acceptance is an administrator prerequisite, not a silent build-step repair.
2. DISCOVER schemes and effective target settings; capture `xcodebuild -showBuildSettings -json` using the intended project/workspace, scheme, configuration, and device destination.
3. Resolve this package's `scripts/` locally; inspect the captured JSON:
   ```bash
   python3 scripts/inspect-signing-settings.py remote-settings.json --json
   ```
4. REVIEW per-target device platform, team, bundle ID, signing enabled/style, and manual profile selection. Inspector findings are configuration evidence, not certificate trust/private-key-use proof.

Gate: selected Xcode and scheme resolve; effective device signing settings match every app/extension.

## 3. Establish usable signing assets

READ `references/keychains-trust.md` before keychain/profile changes.

1. PREFER a dedicated CI user plus a job-owned file-based keychain containing only the intended signing identity. A `.cer` without its matching private key cannot sign; provision an authorized `.p12` or existing usable identity.
2. SEPARATE three failures: certificate chain/trust, locked keychain, private-key ACL/partition access. Unlocking alone cannot repair all three.
3. VERIFY the leaf's issuer, validity, EKU, and matching Apple intermediate. Preserve System Default trust. The supplied threads' WWDR G3 System-keychain workaround is historical evidence, not permission to install arbitrary roots or always-trust everything.
4. CONFIGURE narrow `/usr/bin/codesign` access and the documented `apple:` partition on the job key; no `security import -A`, blanket login/System-key ACL changes, or permanently unlocked login keychain.
5. PRESERVE/restore the user's exact keychain search list; serialize builds sharing that account. Stage profiles per target; never apply one profile globally to app and extensions.
6. RUN `security find-identity -v -p codesigning` and a real disposable Mach-O signing probe in the same SSH context. A visible identity is insufficient until private-key signing succeeds without a dialog.

Gate: correct identity/chain and profiles; noninteractive key use succeeds in SSH; state-restoration ownership explicit.

## 4. Archive, export, and verify

READ `references/archive-export.md`; manual export -> COPY `assets/ExportOptions.plist` and replace team/profile mappings from effective targets plus the installed help.

1. ARCHIVE for `generic/platform=iOS` with unique DerivedData, archive, result bundle, and log paths. Retain per-target signing settings; no `CODE_SIGNING_ALLOWED=NO` as a signing-error workaround.
2. AUTOMATIC provisioning only when authorized: supply `-allowProvisioningUpdates` and a configured account or permitted App Store Connect authentication key. A `.p8` authenticates portal operations; it is not the app's code-signing private key.
3. EXPORT the archive separately with `-exportArchive`, `-archivePath`, `-exportPath`, and `-exportOptionsPlist`. Select local export, not upload.
4. PRESERVE exit status across log capture; require the expected archive and IPA rather than trusting a formatter's success text.
5. VERIFY the exported app's signature, identity/team, every embedded executable bundle, embedded profile/entitlements, and expected distribution method. Device installability additionally requires the appropriate device/profile policy and an actual device test.
6. COPY only intended artifacts/logs back over SSH; exclude keychains, `.p12`/`.p8`, secret files, and private search-list snapshots.

Gate: archive/export succeed; exported signatures and provisioning match the contract; installation claims have device evidence.

## 5. Add MCP only when it earns its access

READ `references/mcp-over-ssh.md` before choosing/configuring any server.

1. DISTINGUISH Apple `xcrun mcpbridge`, Apple's Xcode 27 early headless service, MobileBuildMCP (formerly XcodeBuildMCP), and separately named third-party servers.
2. LAUNCH stdio servers on the Mac through `ssh -T`; no PTY or stdout banners. Configure remote absolute executable paths, working directory, and environment; local client env is not automatically transmitted by SSH.
3. APPLE traditional bridge -> approved Intelligence setting plus open Xcode/project in the intended user session. Xcode 27 headless preview -> check installed help/status and narrowly authorized permissions; never enable all-agent access as an implicit workaround.
4. MOBILEBUILDMCP -> pin release, opt out of telemetry if required, advertise only needed workflows, and keep signing assets configured independently.
5. VERIFY MCP initialize/tools-list, select the intended project/scheme, then exercise one allowed build. Archive/export/signing capabilities must be present in that exact server's tools; otherwise use the direct CLI workflow, not an invented MCP operation.

Gate: authenticated SSH stdio works; server capabilities/permissions explicit; signing proof still comes from the Mac's actual build/keychain.

## 6. Restore and report

1. RESTORE search-list/default state changed by this job; remove only job-owned profiles/keychain/secrets after dependent processes finish. Do not delete pre-existing identities/profiles.
2. COPY `assets/remote-build-report.md`; fill source revision, host/toolchain, settings, signing probe, archive/export, signature/profile verification, MCP branch, cleanup, and limits without credential values.
3. NO accessible Mac, signing assets, or device -> finish configuration/source checks and identify exactly which execution evidence remains unavailable. Linux checks cannot establish macOS signing success.

## Error Handling

- Chain warning / `CSSMERR_TP_NOT_TRUSTED` -> issuer/intermediate availability and System Default trust in SSH; partition ACL changes do not repair a missing chain.
- `errSecInternalComponent` -> inspect preceding diagnostics; distinguish chain, unlock, and private-key permission failures before changing state.
- `User interaction is not allowed` / `-25308` -> unlocked intended keychain plus narrow key-use permissions; no GUI prompt can be assumed in headless SSH.
- No valid identity -> matching private key, certificate validity/EKU/chain, search list, account, and installed Apple intermediates.
- Profile mismatch -> per-target team/bundle ID/certificate/entitlements/expiry/device/distribution; not one global profile override.
- MCP works but signing fails -> repair keychain/provisioning in the same remote account; MCP is not a trust bypass.
- MCP reports no Xcode/project -> choose traditional GUI-session prerequisites or verified headless preview; do not edit private permission JSON to force access.
- MCP stdio parse failure -> remove PTY/startup stdout noise; keep diagnostics on stderr; test host authentication separately.

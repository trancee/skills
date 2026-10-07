# Source evidence and limits

Inspected 2026-10-07. Live remote macOS signing was not performed; no target Mac/account/signing assets were supplied.

## Supplied pages

1. [My Remote Mac Xcode builds](https://docs.myremotemac.com/ci-cd/xcode-builds/): terminal archive command and dedicated-keychain import/partition commands. Its `security list-keychains -d user -s build.keychain` replaces the user list; this skill preserves/restores existing entries instead. Its Xcode 16.0 install example is not a current universal version recommendation. It omits unlock/lifetime/cleanup/profile checks needed for a full unattended job.
2. [Apple Developer thread 690923](https://developer.apple.com/forums/thread/690923): author reports SSH-only chain warning plus `errSecInternalComponent`; GUI succeeds. September 2021 accepted workaround imports WWDR G3 **public intermediate** into System rather than only the custom keychain. No established universal root cause; choose intermediate from the actual leaf issuer.
3. [Apple Support thread 253761477](https://discussions.apple.com/thread/253761477): SSH `CSSMERR_TP_NOT_TRUSTED`; partition-list change did not solve chain trust. March 2022 follow-up says the preceding thread's solution worked. Its SSL/CT verification experiment is not the correct code-signing policy test.

Static fetches initially returned Apple security-verification/navigation pages. Ordinary browser rendering made both supplied threads readable; no security challenge was clicked/solved, permission granted, login performed, or account content published. Main post/answers were read; forum workarounds are historical reports, not normative APIs.

## First-party signing authority

- [TN3161 certificates](https://developer.apple.com/documentation/technotes/tn3161-inside-code-signing-certificates): identity = leaf certificate + matching private key; chain/expiry/EKU matter; certificate fingerprint disambiguates identity. Cloud-managed private keys are not directly exportable assets.
- [TN3125 provisioning](https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles): profile authorizes signer, App ID, devices/distribution, time, entitlements; each app/extension is a separate executable bundle. Profile plist decoding is a debugging technique, not a stable production schema.
- [Apple PKI](https://www.apple.com/certificateauthority/): source of Apple intermediates. Preserve System Default trust rather than applying arbitrary Always Trust overrides.
- Installed `man security`, `man codesign`, and `xcodebuild -help` win over secondary [security](https://keith.github.io/xcode-man-pages/security.1.html) / [xcodebuild](https://keith.github.io/xcode-man-pages/xcodebuild.1.html) mirrors. Security manual describes the `apple:` partition requirement for codesign and separate code-signing verification policies.

## Additional Gemini/Grok advice

Treat model-generated recipes as suggestions, not sources or authorization. Checked citations: [Jenkins/SSH question](https://stackoverflow.com/questions/26475404/xcode-codesign-error-from-jenkins-ssh-user-interaction-is-not-allowed), [Julio Merino's 2020 report](https://jmmv.dev/2020/05/codesign-and-ssh.html), plus installed security/Xcode help.

- Correct branch: unlock the actual keychain and authorize the signing private key; bounded job-keychain timeout; pre-stage identity/profiles; explicit device archive then export.
- `set-keychain-settings` changes keychain settings persistently, not only the SSH session. The keychain password may differ from the current OS login password.
- Partition changes affect matching **keys**, not public certificates. The security manual requires `apple:` for codesign; it does not establish `codesign:` as universally required. `-D` matches key description, not necessarily identity common name.
- Do not strip search-list quotes and let the shell split/glob paths. Preserve exact arguments, original default/search-list state, and cleanup failure evidence. Unique keychains do not isolate per-user search-list mutations.
- The 2014 answer's LaunchDaemon/Aqua restriction concerns GUI/simulator work in historical Xcode; it does not prove current CLI archive/signing over SSH is impossible.
- Julio Merino reports importing a **private identity** into System after login-keychain attempts failed on macOS 10.15.5, and questions whether that is the right approach. This differs from the Apple thread's **public intermediate** workaround; neither establishes universal sshd access to System keys.
- A visible identity/simulator build does not prove private-key use/device provisioning. Global app-profile overrides break extension mappings; `.p8` portal authentication is distinct from `.p12` signing identity.
- Hardened runtime (`codesign -o runtime`), Developer ID notarization, and stapling are macOS distribution workflows, not the iOS archive/export recipe.

Use the dedicated CI workflow instead of broad login/System-keychain ACL changes, disabled timeouts, embedded passwords, or a blanket diagnosis for `errSecInternalComponent`.


## MCP authority and version boundary

- [Apple external-agent guide](https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode): approved Intelligence toggle, `xcrun mcpbridge`, open project in Xcode. This is the traditional GUI-session path.
- [Xcode 27 notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes), 181836944: early-preview MCP service without open workspace; enable/status commands; optional unsafe broad permission mode; configuration/relaunch/reboot limitations. It does **not** warrant assuming all installations are unattended-ready.
- [MobileBuildMCP npm metadata](https://registry.npmjs.org/mobilebuildmcp/2.7.1): published version 2.7.1, gitHead `d13ff0c707b0681769cf31da0eb42c4f94ceafff`; [GitHub release](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.7.1) agrees. Old XcodeBuildMCP links redirect; current executable/package/config/env naming is MobileBuildMCP.
- [MobileBuildMCP device-signing docs](https://github.com/getsentry/xcodebuildmcp.com/blob/main/app/docs/_content/device-signing.mdx): build/install/launch after signing setup; no automatic signing setup or profile creation/management. Optional IDE proxy does not remove Apple authorization/session requirements.
- [r-huijts/xcode-mcp-server](https://github.com/r-huijts/xcode-mcp-server): another separately implemented server advertising build/archive/export operations. No equivalence with Apple's bridge or claim that it manages private keys/profiles.

## Decision

Use direct SSH `xcodebuild archive` + `-exportArchive` with a usable dedicated CI identity/profile setup. Diagnose trust-chain discovery separately from unlock/ACL failures. Add SSH-transported MCP for agent workflow benefits; choose Apple headless preview only after version/permission/transport verification. MCP does not solve signing authorization.

Unverified here: actual Mac/Xcode selection, System intermediate import, private-key ACL/partition changes, archive/export, Apple headless-service startup/permission behavior, remote stdio handshake, and device install. The bundled inspector can prove only properties of captured build-settings JSON.

## Exercised portable evidence

- Real `mobilebuildmcp@2.7.1 --help` ran with telemetry disabled; confirms current executable/server mode, not Mac backend availability.
- Real 2.7.1 stdio process in a temporary Linux workspace negotiated MCP `2025-06-18`; `initialize` and `tools/list` succeeded. Enabled `project-discovery,device,utilities` advertised 20 tools, including `list_schemes`, `show_build_settings`, `build_device`, and `build_run_device`. No dedicated archive/export-named tool appeared in that selected surface; other workflows were not exhaustively probed.
- No build/device/signing tool was invoked. This is local protocol evidence, **not** remote SSH, macOS keychain, or signed-IPA evidence.
- Inspector smoke: separate app/extension manual profiles accepted; simulator/other-platform, disabled signing, unresolved team/profile/identity, duplicate bundle IDs, mismatched team, missing selected target, malformed/duplicate/oversize JSON rejected. Arbitrary credential setting omitted from output; JSON deterministic.
- Seven shell examples passed Bash syntax checks; both SSH MCP JSON examples parsed and use `ssh -T` with host-key verification. Export plist parses as manual **local export** with separate bundle mappings. None of these checks establishes macOS execution or authorizes state changes.

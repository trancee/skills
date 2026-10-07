# Remote archive/export

## Remote context

Use a reviewed SSH alias whose host key is already verified. Keep source/build/keychain operations under one non-root CI account. SSH encryption does not fix private-key authorization or certificate trust.

```bash
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes build-mac \
  'id -un; sw_vers; /usr/bin/xcode-select -p; /usr/bin/xcodebuild -version'
```

For every following command on the Mac, set the selected full Xcode path:

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcodebuild -version
xcodebuild -showsdks
xcodebuild -help
```

Do not run `sudo xcodebuild archive`; root has a different home/keychain/profile context. Administrator first-launch/license setup is separate and must be authorized. Pin compatible macOS/Xcode/SDK/deployment floors from [Xcode support](https://developer.apple.com/support/xcode/). Xcode 27 notes require macOS 26.6+; that is not the same as MobileBuildMCP's lower macOS floor.

## Discover, do not guess

Choose **one** `-workspace` or `-project`. Scheme must be shared/available to the build account:

```bash
xcodebuild -list -json -workspace MyApp.xcworkspace
xcodebuild -showBuildSettings -json -workspace MyApp.xcworkspace \
  -scheme MyApp -configuration Release -destination 'generic/platform=iOS' \
  > remote-settings.json
```

Copy that JSON to the client and run this package's inspector. Keep build settings private: they can include arbitrary user-defined values. Inspector output uses an allowlist and omits arbitrary settings/credential values.

## Manual signing

Pre-stage a matching Apple Development or Distribution identity and the profile for every app/extension target. Configure profiles at their owning target/project/xcconfig. A global `PROVISIONING_PROFILE_SPECIFIER` often assigns the app's profile to extensions incorrectly.

Install profiles in the location recognized by the **selected** Xcode. Current installations may use `~/Library/Developer/Xcode/UserData/Provisioning Profiles`; [Apple's account-help instructions](https://developer.apple.com/help/account/provisioning-profiles/edit-download-or-delete-profiles) also name `~/Library/MobileDevice/Provisioning Profiles`. Verify actual discovery instead of inferring a universal folder from Xcode's major version. Do not blindly copy/overwrite both locations; retain each job-owned file's identity and restore/delete only those files.

Check certificate membership, team/App ID prefix versus bundle ID, expiry, entitlements, distribution method, and device UDIDs where required. App Store distribution profiles do not authorize arbitrary local device installation. Decode profiles with `security cms -D -i PROFILE` only for diagnostics; their plist format is not a stable product API ([TN3125](https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles)).

Archive within the prepared keychain job:

```bash
: "${OUT:?absolute unique artifact directory outside the private keychain temp directory}"
: "${WORKSPACE:?workspace path on the Mac}"
: "${SCHEME:?discovered shared scheme}"
xcodebuild -workspace "$WORKSPACE" -scheme "$SCHEME" \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$OUT/DerivedData" \
  -archivePath "$OUT/MyApp.xcarchive" \
  -resultBundlePath "$OUT/archive.xcresult" \
  archive
```

Unique result-bundle paths must not already exist. Keep per-target signing controls; explicit identity overrides must agree with every signed target. If needed, an approved `OTHER_CODE_SIGN_FLAGS` keychain selection can narrow identity lookup; preserve existing flags and test nested-target behavior rather than globally replacing them.

## Automatic provisioning

Use only when Apple portal mutations/network access are authorized. `-allowProvisioningUpdates` may create/update profiles, app IDs, certificates, or download missing profiles depending on signing style. Optional `-allowProvisioningDeviceRegistration` is another explicit account mutation, not a default.

Authentication choices:

- Authorized account configured in Xcode for that remote user; resolve any interactive account/2FA state beforehand.
- Permitted App Store Connect API key: `-authenticationKeyPath PATH.p8 -authenticationKeyID ID -authenticationKeyIssuerID ISSUER`, with `-allowProvisioningUpdates`, when supported by installed help and account roles.

A `.p8` authenticates Apple Developer service operations; it is not the certificate/private-key identity that signs the binary. Do not assume account/key permissions or cloud signing are available. Keep the `.p8` local to the protected job; never transfer its bytes through MCP arguments or logs.

## Export separately

Inspect `xcodebuild -help` for that release's export options/method names. On current Xcode, iOS examples include `app-store-connect`, `release-testing`, `debugging`, and `enterprise`; older `app-store`/`ad-hoc`/`development` aliases are not a reason to guess a current method.

For manual export, copy `assets/ExportOptions.plist`; fill `teamID`, approved method, and all app/extension bundle-to-profile mappings. The template uses `destination=export`, not upload:

```bash
xcodebuild -exportArchive -archivePath "$OUT/MyApp.xcarchive" \
  -exportPath "$OUT/export" -exportOptionsPlist "$EXPORT_OPTIONS"
```

Signing can occur again during export: keep identities/profiles/keychain accessible until export finishes. A successful device build is not an archive, and an archive is not an exported IPA. Do not assume an MCP `build` tool also performs export.

## Evidence and artifact retrieval

- Preserve the raw `xcodebuild` exit code. If piping to a formatter/`tee`, set supported `pipefail` or capture statuses explicitly; a formatter's exit 0 is not build success.
- Record source revision, Xcode/SDK, scheme/configuration/destination, target signing settings, archive/IPA paths, checksums, logs, and result bundles.
- Extract the exported IPA into a disposable directory; `codesign --verify --deep --strict --verbose=2 Payload/MyApp.app` is a verification operation, not permission to deep re-sign.
- Inspect `codesign --display --verbose=4 --entitlements :- APP` and each embedded executable's profile/identity. Compare against requested team/bundle/entitlements/distribution; simulator ad-hoc signatures do not prove physical-device signing.
- Fetch only intended `.ipa`, `.xcarchive`, `.xcresult`, and sanitized logs with SSH/SFTP/SCP. Do not copy private keychains, `.p12`, `.p8`, or secret snapshots. Publishing/TestFlight upload requires a separate request.

Sources: installed `man xcodebuild`/`xcodebuild -help`; [rendered manual](https://keith.github.io/xcode-man-pages/xcodebuild.1.html); [My Remote Mac build guide](https://docs.myremotemac.com/ci-cd/xcode-builds/); [TN3161](https://developer.apple.com/documentation/technotes/tn3161-inside-code-signing-certificates).

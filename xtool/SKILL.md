---
name: xtool
description: "Installs, configures, uses, and troubleshoots xtool for SwiftPM-driven iOS development. Use when setting up xtool on Linux, WSL, or macOS; installing a Darwin Swift SDK; authenticating with Apple; creating, building, signing, or deploying an iOS app; or diagnosing device failures. Don't use for Xcode-only projects, Android development, or unrelated Swift tooling."
metadata:
  source: "https://xtool.sh/"
  category: "development"
  createdAt: "2026-08-28T19:26:56+02:00"
  updatedAt: "2026-08-30T11:05:26+02:00"
---

# xtool iOS development

## Procedures

**Step 1: Refresh requirements and bound the task**

1. Read the current [xtool overview](https://xtool.sh/documentation/xtool/) and the installation guide for the host before running installation commands.
2. Identify the host as Linux, Windows through WSL, or macOS; identify the architecture, desired operation, physical-device availability, Apple account mode, and existing Swift/Xcode state.
3. Record the installed or intended xtool, Swift, and Xcode point releases. Treat broad requirements such as “Xcode 26” as a range that still requires point-release compatibility evidence.
4. Inspect current command flags with `xtool --help` and `xtool help <subcommand>` rather than guessing from this skill.

**Step 2: Load the host branch**

1. For Linux or WSL, read `references/linux-wsl.md` and follow its Swift, `usbmuxd`, USBIPD, Xcode archive, and AppImage requirements.
2. For macOS, read `references/macos.md` and follow its Xcode SDK, Swift, Homebrew/application, and authentication requirements.
3. Reject native Windows execution; configure WSL and USB passthrough instead.
4. Prefer an official Swift.org/Swiftly toolchain on Linux. Prove Apple cross-target compatibility with an iOS build rather than accepting a matching version string alone.

**Step 3: Run a non-secret preflight**

1. Run the bundled environment checker with the Swift version required by the current host guide:

   ```bash
   python3 scripts/check-environment.py --min-swift 6.3
   ```

2. Add `--xcode-xip path/to/Xcode.xip` on Linux/WSL when the archive is available.
3. Add `--require-device-tools` when physical-device deployment is in scope.
4. Resolve missing executables, unsupported hosts, and version failures before running interactive setup.
5. Treat a Linux Swift executable under `/usr` as a warning that requires an official-toolchain check and a later `xtool dev build` proof.

**Step 4: Install xtool**

1. Install the current AppImage on Linux/WSL or the current Homebrew/application release on macOS according to the loaded host reference.
2. Place the CLI on `PATH` and preserve executable permissions.
3. Run `xtool --version` and `xtool --help`; require the expected CLI overview before continuing.
4. If upgrading, retain the previous binary until the new binary and existing project build successfully.

**Step 5: Authenticate and install the SDK**

1. Run `xtool setup` interactively.
2. Require the account holder to enter API keys, Apple ID passwords, and 2FA codes directly into xtool's prompt. Keep secrets out of chat, command arguments, logs, and shell history.
3. Select API Key only with paid Apple Developer Program membership; select Password only when use of Apple's private APIs is acceptable.
4. On Linux/WSL, provide the compatible `Xcode.xip` path and allow xtool to build/install the Darwin Swift SDK.
5. Verify setup without printing account details:

   ```bash
   python3 scripts/check-environment.py \
     --min-swift 6.3 \
     --require-auth \
     --require-sdk
   ```

6. Require `xtool auth status` to report logged-in state, `xtool sdk status` to report an installed SDK, and `swift sdk list` to contain `darwin`.

**Step 6: Prove compiler and SDK compatibility**

1. Generate a disposable project with `xtool new <Name>` or use the target project when creating it is part of the request.
2. Read `references/project-config.md` before editing generated files or `xtool.yml`.
3. Run `xtool dev build` from the package directory.
4. Require a linked `.app` artifact. Do not treat `swift sdk list` or SDK installation alone as proof that Swift and the Xcode SDK are compatible.
5. If the build fails in SDK modules, compare the exact xtool, official Swift, and Xcode point-release combination with current documentation, releases, and issues before modifying the generated SDK manually.

**Step 7: Configure and develop the application**

1. Preserve the generated `Package.swift`, `xtool.yml`, and `.sourcekit-lsp/config.json` roles described in `references/project-config.md`.
2. Give the app a unique bundle identifier and select the intended SwiftPM product.
3. Add resources through SwiftPM by default; use `xtool.yml` root resources only when bundle-root placement is required.
4. Configure plist overrides, icons, entitlements, and extensions with fields supported by the current xtool documentation.
5. Configure the editor's Swift/SourceKit-LSP integration. Use the WSL remote on Windows.
6. Re-run `xtool dev build` after configuration changes before involving signing or a device.

**Step 8: Deploy to a physical device**

1. Connect and unlock the iOS device over USB.
2. On WSL, bind and attach the device with USBIPD. On Linux, require `usbmuxd`; use `ideviceinfo` when available to confirm visibility.
3. Run `xtool dev` from the project directory.
4. Accept the iOS Trust prompt and enter the device passcode on first pairing. Rerun `xtool dev` if pairing interrupted the first attempt.
5. Enable Developer Mode when iOS requests it.
6. If iOS reports an untrusted developer, trust the developer identity under **Settings > General > VPN & Device Management**.
7. Require the app to install and launch. Without a physical device, report only the verified build and mark signing/install/launch unexercised.

**Step 9: Diagnose from the failed boundary**

1. If the CLI is missing, inspect `PATH`, installation location, and AppImage executable permissions.
2. If authentication fails, inspect `xtool help auth` and repair authentication without repeating SDK extraction.
3. If the SDK is absent, inspect `xtool help sdk`, the Xcode archive path, disk space, and exact version pairing.
4. If SDK installation fails on framework links, versioned SDK aliases, `SwiftShims`, `Darwin`, or module maps, replace an unsupported Xcode point release with a verified pairing; avoid maintaining a hand-patched partial SDK.
5. If the device is absent, separate USB transport, pairing, Developer Mode, signing, installation, and launch into distinct checks.
6. If project configuration fails, compare `Package.swift`, `xtool.yml`, plist/entitlements, resources, and product names with `references/project-config.md` and current xtool help.

**Step 10: Report completion**

1. Copy `assets/setup-report.md` when documenting setup or troubleshooting.
2. Record host, architecture, executable paths, versions, Xcode/SDK source, authentication state with account details redacted, SDK state, build artifact, and device result.
3. Distinguish installation, authentication, SDK registration, app build, signing, installation, and launch; report only boundaries actually exercised.
4. Remove disposable projects and nonessential extracted SDK/debug artifacts after the verified build.

## Error Handling

- If current documentation and remembered versions disagree, follow current documentation, then require an actual `xtool dev build` before declaring compatibility.
- If Apple credentials are required, pause at the interactive prompt and let the account holder enter them privately.
- If `scripts/check-environment.py` reports a missing tool, install or select the host-specific prerequisite before retrying setup.
- If the checker warns that Swift resolves under `/usr`, install/select the official Swift.org toolchain and rebuild before diagnosing application code.
- If Xcode extraction succeeds but finalization or compilation fails, change to an explicitly verified Xcode point release rather than suppressing the error.
- If no physical device is available, finish and report the `.app` build proof; mark deployment as not exercised.
- If device trust or Developer Mode requires human action, provide the exact device setting and resume `xtool dev` after completion.

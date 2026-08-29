---
name: xtool-ios-development
description: "Installs, configures, troubleshoots, and uses xtool for SwiftPM-driven iOS development on Linux, WSL, or macOS. Use when setting up xtool, building or deploying an iOS app with SwiftPM, managing the Darwin SDK, or diagnosing device setup. Don't use for Xcode project development without xtool, Android development, or unrelated Swift tooling."
metadata:
  source: "https://xtool.sh/documentation/xtool/"
  createdAt: "2026-08-28T19:26:56+02:00"
  updatedAt: "2026-08-29T17:06:38+02:00"
---

# xtool iOS development

Use this procedure to install xtool, perform its one-time Apple/SDK setup, and build or deploy SwiftPM iOS applications.

## 1. Refresh and pair requirements

Read the official host guide before running installation commands because Swift, Xcode, and xtool compatibility changes:

- Linux/WSL: https://xtool.sh/documentation/xtool/installation-linux
- macOS: https://xtool.sh/documentation/xtool/installation-macos
- First app: https://xtool.sh/tutorials/xtool/first-app

Use the currently documented Swift release and an Xcode release that xtool has verified. Treat “Xcode 26” as a major-version range, not permission to choose the newest point release: newer Xcode point releases can change SDK aliases, framework layouts, compiler interfaces, or module maps before xtool supports them. If current docs do not name a point release, check xtool releases/issues for successful reports and prefer the newest explicitly verified pairing.

## 2. Choose the host branch

### Linux or Windows through WSL

1. On Windows, install WSL and USBIPD, then attach the iOS USB device to WSL. xtool runs inside WSL, not in native Windows.
2. Install Swift using the official Swift.org mechanism, preferably Swiftly, rather than a distribution package. A distro build can report the right version while omitting Apple cross-compilation targets. Confirm the active executable and version:

   ```bash
   which swift
   swift --version
   ```

   With Swiftly, `which swift` should resolve under `~/.local/share/swiftly/bin`. Confirm the toolchain contains Apple target modules before SDK work:

   ```bash
   find "${SWIFTLY_TOOLCHAINS_DIR:-$HOME/.local/share/swiftly/toolchains}" \
     -path '*/usr/lib/swift/embedded/Swift.swiftmodule/arm64-apple-ios.swiftmodule' \
     -print -quit
   ```

3. Confirm `usbmuxd` is available:

   ```bash
   usbmuxd --help
   ```

   Install it from the distribution package manager when absent. Debian/Ubuntu use:

   ```bash
   sudo apt-get install usbmuxd
   ```

4. Download the compatible Xcode release from Apple Developer Downloads. Preserve the path to `Xcode.xip`; xtool uses it to construct the Darwin Swift SDK.
5. Download the latest AppImage for the machine architecture, install it as `xtool` on `PATH`, and verify it:

   ```bash
   curl -fL \
     "https://github.com/xtool-org/xtool/releases/latest/download/xtool-$(uname -m).AppImage" \
     -o xtool
   chmod +x xtool
   mkdir -p ~/.local/bin
   mv xtool ~/.local/bin/
   xtool --help
   ```

   Use `/usr/local/bin` instead when a system-wide installation is required.

### macOS

1. Install Xcode, launch it once, and complete its installation prompts.
2. Confirm the iOS SDK and Swift toolchain:

   ```bash
   xcrun -sdk iphoneos -show-sdk-path
   swift --version
   ```

3. Prefer Homebrew for installation:

   ```bash
   brew install xtool-org/tap/xtool
   xtool --help
   ```

   Without Homebrew, download `xtool.app` from the latest GitHub release, move it to `/Applications`, launch it, and run the script it presents to put `xtool` on `PATH`.

Installation is complete only when `xtool --help` prints the CLI overview.

## 3. Run one-time setup

Run setup interactively:

```bash
xtool setup
```

Let the user enter credentials directly into xtool's prompt. Keep API keys, passwords, and 2FA codes out of chat, command arguments, logs, and shell history.

Choose the login mode deliberately:

- **API Key** requires paid Apple Developer Program membership.
- **Password** works with any Apple ID but uses Apple's private APIs.

On Linux/WSL, provide the path to the downloaded `Xcode.xip` when prompted. xtool extracts it and installs the Darwin Swift SDK. Verify all three boundaries:

```bash
xtool auth status
xtool sdk status
swift sdk list
```

Authentication must say logged in, xtool must report an installed path, and Swift must list `darwin` before attempting an iOS build.

Use `xtool auth` to manage Apple Developer Services authentication and `xtool sdk` to manage the Darwin SDK after initial setup. Inspect current flags before acting:

```bash
xtool help auth
xtool help sdk
```

## 4. Create and run an app

Generate a project and enter it:

```bash
xtool new Hello
cd Hello
```

Inspect the generated files before editing:

- `Package.swift` defines the SwiftPM products and targets.
- `xtool.yml` defines app-bundle metadata; at minimum it contains `version: 1` and a unique `bundleID`.
- `.sourcekit-lsp/config.json` configures SourceKit-LSP for the Darwin SDK.
- `Sources/Hello/` contains the application source.

Prove SDK/compiler compatibility before connecting a device:

```bash
xtool dev build
```

A successful check links the app and writes `xtool/<Name>.app`. `swift sdk list` alone is not sufficient proof; malformed or incompatible SDK bundles can still register successfully.

Build, sign, install, and run the device deployment flow:

```bash
xtool dev
```

The first build may be slow while SwiftPM builds and globally caches iOS SDK modules. Connect the iOS device over USB. On first pairing, accept **Trust** on the device and enter its passcode; rerun `xtool dev` if pairing caused the first invocation to fail. Enable iOS Developer Mode when requested. If iOS reports an untrusted developer, open **Settings > General > VPN & Device Management > [Apple ID] > Trust**.

Configure the editor's Swift extension/SourceKit-LSP support. For VS Code on Windows, open the project through the WSL remote. After source changes, rerun `xtool dev` to rebuild and reinstall.

Completion means the generated app launches on the physical iOS device. Without a device, report the successful `.app` build separately and state that signing/install/launch remain unexercised.

## 5. Use the CLI by intent

Start with `xtool --help` and `xtool help <subcommand>`; do not guess flags.

- `xtool setup`: initial configuration.
- `xtool auth`: authentication management.
- `xtool sdk`: Darwin Swift SDK management.
- `xtool new`: generate an xtool SwiftPM project.
- `xtool dev build`: compile and bundle without requiring a connected device.
- `xtool dev`: build, sign, install, and support the development loop.
- `xtool ds`: interact with Apple Developer Services.
- `xtool devices`: list connected devices.
- `xtool install`: install an IPA on a device.
- `xtool uninstall`: remove an installed app.
- `xtool launch`: launch an installed app.

## 6. Configure the app bundle

Use `xtool.yml` as the app-bundling source of truth. A minimal file is:

```yaml
version: 1
bundleID: com.example.Hello
```

Available common controls:

```yaml
version: 1
bundleID: com.example.Hello
product: Hello
infoPath: Info.plist
iconPath: Resources/AppIcon.png
entitlementsPath: App.entitlements
resources:
  - Resources/GoogleServices-Info.plist
```

- `infoPath` points to a partial `Info.plist`; xtool merges its keys into the generated plist.
- Prefer SwiftPM target resources for ordinary package resources. Access those with `Bundle.module`.
- Use top-level `resources` only for files that must sit at the root of the `.app` bundle.
- `iconPath` names the app icon image.
- `entitlementsPath` names the entitlements plist.
- `product` disambiguates the SwiftPM product used for the app.

For an app extension, add a separate SwiftPM library product and target, then declare it under `extensions`:

```yaml
version: 1
bundleID: com.example.Hello
product: Hello
extensions:
  - product: HelloWidget
    infoPath: HelloWidget-Info.plist
```

The extension plist must identify its extension point. xtool's current documentation states that ExtensionKit-based extensions are not yet supported; verify that limitation against the current extension guide before planning one.

## 7. Diagnose setup failures

Work from the failed boundary:

1. `xtool` not found: confirm its installed location is on `PATH` and the AppImage is executable.
2. `xtool sdk install` fails while creating testing-framework symlinks or cannot find versioned SDKs: the selected Xcode point release is newer than the installed xtool understands. Install an explicitly verified Xcode point release; do not hand-maintain a partially generated SDK.
3. `xtool dev build` reports `no such module 'SwiftShims'`, unsupported compiler, or missing Apple target support: ensure the active `swift` is the official Swift.org/Swiftly toolchain, not a distro package with the same version string. Reinstall the Darwin SDK after changing toolchains.
4. `swift sdk list` contains `darwin` but compilation reports missing `Darwin`, `_DarwinFoundation*`, or split module-map errors: the Xcode SDK layout is incompatible with this xtool version. Replace it with a verified Xcode point release.
5. Build cannot find iOS modules on Linux/WSL: confirm `swift sdk list` contains `darwin`, `xtool sdk status` reports an installation, and the project retained `.sourcekit-lsp/config.json`.
6. Device missing on Linux: confirm USB visibility, `usbmuxd --help`, and, when available, `ideviceinfo`.
7. Device missing in WSL: re-check USBIPD binding and attachment to the active WSL distribution.
8. Pairing failure: accept the device Trust prompt, unlock the device, then rerun `xtool dev`.
9. Installation or launch blocked by iOS: enable Developer Mode and trust the developer identity in device settings.
10. Authentication or SDK state suspect: inspect `xtool help auth` or `xtool help sdk`, then use those management commands rather than repeating the entire installation.

## Official references

- Overview: https://xtool.sh/documentation/xtool/
- Linux/WSL installation: https://xtool.sh/documentation/xtool/installation-linux
- macOS installation: https://xtool.sh/documentation/xtool/installation-macos
- First app tutorial: https://xtool.sh/tutorials/xtool/first-app
- App bundle controls: https://xtool.sh/documentation/xtool/control
- App extensions: https://xtool.sh/documentation/xtool/appex
- Repository and CLI overview: https://github.com/xtool-org/xtool

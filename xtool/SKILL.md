---
name: xtool
description: "Installs/configures/builds/deploys/debugs xtool SwiftPM iOS apps on Linux, WSL, macOS. Use for Darwin SDK, Apple auth, device pairing, Developer Mode, signing/install/launch. Don't use for Xcode-only, Android, or unrelated Swift."
metadata:
  category: "development"
  source: "https://xtool.sh/"
  sourceVersion: "xtool 1.17.0 (9e8bfd432c99c7ef9ade6c4b6723f1321ed0e7ed)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-28T19:26:56+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:48:01+02:00"
---

# xtool

## 1. Scope+branch

1. READ current [overview](https://xtool.sh/documentation/xtool/) + host install guide.
2. RECORD host/arch/goal/device/account mode/current Swift-Xcode-xtool exact versions; inspect `xtool --help` + `xtool help SUBCOMMAND`.
3. Linux|WSL -> READ `references/linux-wsl.md`. macOS -> READ `references/macos.md`. Native Windows => WSL+USB passthrough.
4. Linux: prefer official Swift.org/Swiftly; matching version string insufficient.

## 2. Preflight

```bash
python3 scripts/check-environment.py --min-swift CURRENT_REQUIRED
```

Add as needed: `--xcode-xip PATH`; `--require-device-tools`.
Resolve missing executable/host/version first. Linux Swift under `/usr` => warning; later `xtool dev build` required.

## 3. Install+setup

1. Install current AppImage (Linux/WSL) or Homebrew/app (macOS); CLI on `PATH`; executable bit preserved.
2. Upgrade: retain prior binary until new binary builds existing project.
3. VERIFY `xtool --version` + `xtool --help`.
4. RUN interactive `xtool setup`.
5. Human enters API key/password/2FA only in xtool prompt; never chat/argv/log/history.
6. API Key requires paid program; Password uses private APIs and any Apple ID.
7. Linux/WSL: supply compatible `Xcode.xip`; generate/install Darwin SDK.
8. VERIFY:
   ```bash
   python3 scripts/check-environment.py --min-swift CURRENT_REQUIRED --require-auth --require-sdk
   ```
   Require `xtool auth status` logged in; `xtool sdk status` installed; `swift sdk list` contains `darwin`.

## 4. Build proof

1. `xtool new NAME` disposable OR target project.
2. READ `references/project-config.md` before generated-file/`xtool.yml` edits.
3. RUN `xtool dev build` in package.
4. PASS only linked `.app`; SDK listing/install alone insufficient.
5. SDK-module failure => compare exact xtool+official Swift+Xcode point release with docs/releases/issues; never patch partial SDK first.

## 5. Configure

- preserve roles: `Package.swift`, `xtool.yml`, `.sourcekit-lsp/config.json`
- unique bundle ID; intended SwiftPM product
- ordinary resources via SwiftPM/`Bundle.module`; root `xtool.yml.resources` only bundle-root files
- only current documented plist/icon/entitlement/extension fields
- editor Swift/SourceKit-LSP; Windows uses WSL remote
- config change -> `xtool dev build` before signing/device

## 6. Device

1. Connect+unlock USB device.
2. WSL: USBIPD bind+attach. Linux: `usbmuxd`; `ideviceinfo` if available.
3. RUN `xtool dev`.
4. First pair: accept Trust+passcode; rerun after pairing interruption.
5. Enable Developer Mode if requested.
6. Untrusted developer => **Settings > General > VPN & Device Management** -> trust identity.
7. PASS only install+launch. No device => build proof only; signing/install/launch unverified.

## 7. Diagnose+report

- missing CLI -> `PATH`, location, AppImage mode
- auth -> `xtool help auth`; repair without SDK re-extract
- SDK -> `xtool help sdk`, XIP, disk, exact pairing
- framework links/SDK aliases/`SwiftShims`/`Darwin`/module map -> supported Xcode point release, not hand patch
- device -> isolate USB transport, pairing, Developer Mode, signing, install, launch
- config -> compare product/plist/entitlement/resource names with reference+help
- OUT: copy `assets/setup-report.md`; record host/arch/paths/versions, redacted auth state, SDK, artifact, device boundaries; remove disposable artifacts

## Fail

- docs != memory => docs + actual build proof
- credential needed => pause for private human input
- official Swift absent/`/usr` warning => select official toolchain; rebuild
- no device => report `.app` only
- trust/Developer Mode => exact human setting; resume `xtool dev`

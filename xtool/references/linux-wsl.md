# xtool Linux/WSL

REFRESH [host guide](https://xtool.sh/documentation/xtool/installation-linux).

## Prereqs

Current guide: official Swift 6.4 from [Swift.org](https://swift.org/install/linux)/Swiftly; distro builds may omit Apple cross-target modules.
```bash
which swift
swift --version
usbmuxd --help
```
Debian/Ubuntu: `sudo apt-get install usbmuxd`.
Windows: WSL+USBIPD; bind+attach device to active distro; xtool runs inside WSL.
Current guide requires Apple `Xcode 27.xip`; preserve the exact point release/path. Historical xtool 1.17.0 proof: Swiftly 6.3.2 + Xcode 26.4.1 passed, Xcode 26.6 failed SDK finalization/module maps. That evidence does not validate xtool 1.21.0; rerun a linked-app build with the current tuple.

## AppImage

```bash
curl -fL "https://github.com/xtool-org/xtool/releases/latest/download/xtool-$(uname -m).AppImage" -o xtool
chmod +x xtool
mkdir -p ~/.local/bin
mv xtool ~/.local/bin/
xtool --help
```
System-wide `/usr/local/bin` only if intended.

## Setup

```bash
xtool setup
```
Credentials only terminal prompt. API Key=paid program; Password=any Apple ID+private APIs. Supply compatible XIP.
```bash
xtool auth status
xtool sdk status
swift sdk list
```
Require auth, installed SDK path, `darwin`; then disposable `xtool dev build` proof.

1.21.0 obtains clang resources from the Swift toolchain, prunes Xcode during XIP installation, and dynamically links the AppImage executable. [Release notes](https://github.com/xtool-org/xtool/releases/tag/1.21.0): diagnose toolchain/library/resource paths before altering extracted SDK files.

## Device

USB connect+unlock; `ideviceinfo` if available; accept Trust+passcode; pairing interruption => rerun `xtool dev`.

# xtool Linux/WSL

REFRESH [host guide](https://xtool.sh/documentation/xtool/installation-linux).

## Prereqs

Official [Swift.org](https://swift.org/install/linux)/Swiftly required version preferred; distro build may omit Apple cross-target modules.
```bash
which swift
swift --version
usbmuxd --help
```
Debian/Ubuntu: `sudo apt-get install usbmuxd`.
Windows: WSL+USBIPD; bind+attach device to active distro; xtool runs inside WSL.
Download required Apple `Xcode.xip`; major version insufficient.
Observed xtool 1.17.0 pairing: Swiftly Swift 6.3.2 + Xcode 26.4.1 PASS; Xcode 26.6 SDK finalization/module maps FAIL. Recheck releases/issues.

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

## Device

USB connect+unlock; `ideviceinfo` if available; accept Trust+passcode; pairing interruption => rerun `xtool dev`.

# xtool setup on Linux and WSL

Read this reference only for Linux or Windows through WSL. Refresh the [official Linux/WSL installation guide](https://xtool.sh/documentation/xtool/installation-linux) before applying version requirements.

## Prerequisites

Install the Swift version currently required by xtool from [Swift.org](https://swift.org/install/linux), preferably through Swiftly. Confirm the active executable and version:

```bash
which swift
swift --version
```

A distribution package can report the expected version while omitting Apple cross-compilation targets. Prefer the official Swift.org toolchain and prove compatibility with `xtool dev build`; version output alone is insufficient.

Install `usbmuxd` through the distribution package manager and verify it:

```bash
usbmuxd --help
```

On Debian/Ubuntu:

```bash
sudo apt-get install usbmuxd
```

On Windows, install WSL and USBIPD, bind the iOS USB device, and attach it to the active WSL distribution. Run xtool inside WSL.

Download the Xcode release required by the current xtool guide from Apple Developer Downloads. Preserve the path to `Xcode.xip`. A major-version statement such as “Xcode 26” does not guarantee every point release works with a particular xtool release.

For xtool 1.17.0, this repository's verified pairing was official Swiftly Swift 6.3.2 with Xcode 26.4.1. Xcode 26.6 failed SDK finalization and module-map discovery. Treat this as version-specific evidence, not a permanent recommendation; re-check current releases and issues.

## Install the AppImage

Install the current AppImage for the host architecture:

```bash
curl -fL \
  "https://github.com/xtool-org/xtool/releases/latest/download/xtool-$(uname -m).AppImage" \
  -o xtool
chmod +x xtool
mkdir -p ~/.local/bin
mv xtool ~/.local/bin/
xtool --help
```

Use `/usr/local/bin` for a system-wide installation only when appropriate.

## Authenticate and install the Darwin SDK

Run interactive setup:

```bash
xtool setup
```

Enter credentials only in xtool's terminal prompt. Keep API keys, Apple ID passwords, and 2FA codes out of chat, command arguments, logs, and shell history.

Select the login mode deliberately:

- API Key requires paid Apple Developer Program membership.
- Password works with any Apple ID but uses Apple's private APIs.

Provide the compatible `Xcode.xip` path when prompted. Verify all boundaries:

```bash
xtool auth status
xtool sdk status
swift sdk list
```

Require logged-in authentication, an installed xtool SDK path, and `darwin` in Swift's SDK list. Then prove the compiler/SDK pair by generating a disposable project and running `xtool dev build`.

## Device access

Connect and unlock the iOS device over USB. Use `ideviceinfo` when installed to verify Linux visibility. Accept the iOS Trust prompt on first pairing. If pairing interrupts the first deployment, rerun `xtool dev` after trust is established.

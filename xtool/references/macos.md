# xtool setup on macOS

Read this reference only for macOS. Refresh the [official macOS installation guide](https://xtool.sh/documentation/xtool/installation-macos) before applying toolchain requirements.

## Prerequisites

Install Xcode, launch it once, and complete all installation prompts. Verify the iOS SDK and Swift toolchain:

```bash
xcrun -sdk iphoneos -show-sdk-path
swift --version
```

xtool does not use the Xcode build system, but it requires Xcode's iOS SDK and toolchain on macOS.

## Install xtool

Prefer Homebrew:

```bash
brew install xtool-org/tap/xtool
xtool --help
```

Without Homebrew, download `xtool.app` from the latest official GitHub release, move it to `/Applications`, launch it, and run the script presented by the app to add the CLI to `PATH`. Require `xtool --help` to print the CLI overview.

## Authenticate

Run:

```bash
xtool setup
```

Enter credentials only in xtool's terminal prompt. Keep API keys, passwords, and 2FA codes out of chat, arguments, logs, and shell history.

Select API Key for a paid Apple Developer Program account or Password for an Apple ID when the private-API tradeoff is acceptable. Verify:

```bash
xtool auth status
```

Generate a disposable project and run `xtool dev build` before relying on device deployment.

# xtool macOS

REFRESH [host guide](https://xtool.sh/documentation/xtool/installation-macos).

1. Install+launch Xcode; complete prompts.
2. VERIFY:
   ```bash
   xcrun -sdk iphoneos -show-sdk-path
   swift --version
   ```
3. Install:
   ```bash
   brew install xtool-org/tap/xtool
   xtool --help
   ```
   No Homebrew: latest `xtool.app` -> `/Applications` -> launch -> run provided PATH script -> `xtool --help`.
4. Auth:
   ```bash
   xtool setup
   xtool auth status
   ```
   Credentials only xtool prompt. API Key=paid program; Password=Apple ID+private APIs.
5. Disposable project -> `xtool dev build` before device deployment.

xtool bypasses Xcode build system but requires Xcode iOS SDK+toolchain.

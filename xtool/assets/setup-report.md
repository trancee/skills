# xtool setup report

## Host

- **Operating system:** [Linux | WSL | macOS]
- **Architecture:** [architecture]
- **xtool:** [path and version]
- **Swift:** [path and version]
- **Xcode/SDK source:** [Xcode version or Xcode.xip filename]

## Setup state

| Boundary | Command | Result |
| --- | --- | --- |
| xtool CLI | `xtool --help` | [pass/fail] |
| Apple authentication | `xtool auth status` | [pass/fail; redact account details] |
| Darwin SDK | `xtool sdk status` | [pass/fail] |
| Swift SDK registration | `swift sdk list` | [pass/fail] |
| Linux device transport | `usbmuxd --help` | [pass/fail/not applicable] |
| macOS iOS SDK | `xcrun -sdk iphoneos -show-sdk-path` | [pass/fail/not applicable] |

## Build proof

- **Project:** [path or disposable project name]
- **Command:** `xtool dev build`
- **Artifact:** [path to .app/.ipa]
- **Result:** [exact observed result]

## Device proof

- **Device connected:** [yes/no]
- **Pairing/trust:** [verified/not exercised]
- **Developer Mode:** [enabled/not exercised]
- **Command:** `xtool dev`
- **Install/launch result:** [exact observed result or not exercised]

## Limitations

- [Unverified boundary, missing device, unsupported Xcode point release, or other limitation]

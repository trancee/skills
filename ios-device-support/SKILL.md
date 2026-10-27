---
name: ios-device-support
description: "Finds and evaluates iOS DeviceSupport files for connected iPhones and Xcode. Use when Xcode cannot prepare an older iPhone for development, reports missing DeveloperDiskImage or device support, or requires exact iOS version/build lookup across filsv/iOSDeviceSupport and iGhibli/iOS-DeviceSupport. Distinguishes missing legacy images, dropped Xcode device support, and iOS 17+ personalized images. Don't use for simulator runtimes, provisioning/signing repairs, firmware restores, or guaranteed support for an OS dropped by Xcode."
compatibility: "Lookup: Python 3.9+, HTTPS to public GitHub APIs; optional libimobiledevice idevice_id/ideviceinfo and usbmuxd for an already paired USB device. Xcode repair/verification requires macOS and the physical device. Legacy image/signature lookup is for iOS below 17; modern personalized images and Xcode support-range limits require a separate compatibility decision."
metadata:
  category: "build-delivery"
  source: "https://github.com/filsv/iOSDeviceSupport"
  sourceVersion: "filsv/iOSDeviceSupport@bae78cebf7d2453b77825d464ef2a015164aafd5; iGhibli/iOS-DeviceSupport@3dd2d899550ddc253db40e6eabe145600d4bd773; Apple Xcode system requirements and libimobiledevice CLI inspected 2026-10-27"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-27T21:07:39+00:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-27T21:17:04+00:00"
---

# Find the right iPhone DeviceSupport candidate

Resolve bundled files from this skill root. Use [filsv/iOSDeviceSupport](https://github.com/filsv/iOSDeviceSupport) and [iGhibli/iOS-DeviceSupport](https://github.com/iGhibli/iOS-DeviceSupport) as third-party legacy-image inventories, not authorities guaranteeing Xcode compatibility.

## Step 1: Identify the device and the actual failure

1. Record the connected device's exact **ProductVersion and BuildVersion**, selected Xcode version/build and developer directory, macOS version, and first relevant prepare/install/debug error. A model name or iOS major alone cannot select a support image.
2. Read `references/compatibility-installation.md` before proposing a repair. Compare Apple's **Device Support** range for that Xcode, not its SDK, deployment target or simulator range. If the device OS was genuinely dropped, prefer a supported older Xcode plus compatible macOS/host; copying a DDI cannot restore a removed protocol stack or official support.
3. Distinguish trust/pairing/locked-device or USB failure from a missing legacy image, modern image personalization, or signing/build error. Follow normal user-reviewed trust/Developer Mode setup; do not bypass approval or modify global Xcode settings.
4. Identify the selected installation with the session's `DEVELOPER_DIR` or `xcode-select -p`; verify `xcodebuild -version` under that selection. Never assume `/Applications/Xcode.app` when beta/older Xcodes coexist. Do not query or modify the wrong Mac in remote workflows.

Gate: exact device OS/build and actual Xcode support-range/failure classification are known. Any missing Mac/device evidence remains explicit.

## Step 2: Look up the actual inventory

1. Read `references/selection-and-verification.md` for connected-device discovery, saved plist/manual identity, matching precedence, multiple sources and payload checks.
2. From this skill root, query one already paired USB device:
   ```bash
   python3 scripts/find-support.py
   ```
   Several devices -> select the intended `--udid` explicitly. The helper uses libimobiledevice's no-auto-pairing query and will not select an arbitrary phone. If the local host cannot access the device, collect a private plist on the host that can and pass `--device-plist path/to/device.plist`; explicit `--ios-version` plus `--build-version` also works.
3. For iOS **17+**, follow the `modern-personalized-route` result and supported Xcode/CoreDevice preparation. These two repositories are not a source of modern personalized DDI support. Do not fabricate a `17.0.zip`, rename a 16.x image, or apply the historical private DVT defaults workaround as a general fix.
4. For older iOS, require complete inventories of both repositories, immutable resolved commits, existing paths and ranked candidates. An exact build-labelled file outranks an unlabelled exact-version file. An Xcode build embedded in `FromXcode...` is not an iOS BuildVersion.
5. Keep equal-ranked candidates visible across sources. Generic versions have unverified build compatibility; annotated sources, patch fallbacks and prerelease-looking generic matches require review. Exit 3 means no automatic selection, not success. Never substitute arbitrary nearest versions or treat renaming as compatibility proof.

Gate: candidate identity and real pinned URLs are established, or a specific modern/review/no-match route is reported without an invented file.

## Step 3: Verify source and package before changing Xcode

1. Prefer the corresponding image from an authorized compatible Apple Xcode distribution when available. For third-party candidates, review the pinned source/provenance and download only the intended file(s) to owned staging; do not execute either repository's bulk installer or pipe a remote script into a shell.
2. Compare reported sizes and Git blob identities, compute local SHA-256, list archive members and safely stage only the intended regular files. Require the paired nonempty `DeveloperDiskImage.dmg` and `.dmg.signature` from the same package; inspect actual contents rather than assuming the zip label guarantees the payload's build.
3. Preserve version/build mismatches and competing source payloads in the record. A matching hash proves content identity relative to that repository, not Apple authenticity. A signature filename's presence is not signature validation.
4. Reapply the compatibility gate: missing legacy files may justify a narrowly reviewed repair; a dropped OS range requires a supported toolchain/host path or an explicitly acknowledged unsupported experiment, never a guaranteed repair claim.

Gate: staging/provenance/pair structure are checked and the exact proposed destination, permissions, backup and rollback scope are reviewed.

## Step 4: Apply only an authorized repair and verify the phone

1. Follow the compatibility reference's manual installation branch only after authorization to modify that specific Xcode installation. Preserve existing files; no bulk extraction, recursive ownership/permission changes, global Xcode selection change, or unrelated cache removal.
2. Close Xcode, add only the reviewed missing version directory under the selected developer directory's `Platforms/iPhoneOS.platform/DeviceSupport`, then reconnect/reopen and let Xcode prepare the device. Existing contents or conflicting version directories require deliberate resolution, not silent overwrite.
3. Require the intended development action to work on that physical phone: successful prepare plus the requested install/launch/debug operation. Archive inspection, device enumeration, a simulator run, or a successful build alone cannot establish device support.
4. On failure, capture the exact error and remove only this operation's owned addition or restore its reviewed backup. Reassess protocol/toolchain/trust/personalization issues rather than repeatedly renaming images.

Gate: actual device behavior is observed; otherwise label installation/debug compatibility unverified and identify the unavailable prerequisite.

## Step 5: Report the evidence and limits

Copy `assets/device-support-report.md`. Fill device version/build without private identifiers, selected Xcode/macOS, Apple support range, source revisions, ranked choice, payload checks, authorized changes, physical-device outcome and rollback. Distinguish **file found**, **package verified**, **Xcode support established**, and **device operation exercised**.

## Error Handling

- No/multiple USB devices or query failure -> check cable/unlock/usbmuxd/permissions and existing trust on the correct host; choose a UDID or saved plist. No pairing is attempted by the helper.
- Missing build/non-numeric version -> read the device's actual information; never use an Xcode build or guess a minor version.
- GitHub error/rate limit/truncated tree -> report lookup unavailable; no-match cannot be inferred from an incomplete source.
- No exact build/version -> report review/no-match, available relevant candidates and unresolved compatibility; no README fallback or renaming guarantee.
- Existing support pair but prepare still fails -> inspect the selected Xcode's support range and current device diagnostic; additional ZIP copies are not a substitute for diagnosis.
- Modern personalized image or genuinely dropped OS -> supported Xcode/CoreDevice or compatible older Xcode/macOS/host, not a legacy DDI copy.

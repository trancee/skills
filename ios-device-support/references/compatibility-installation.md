# Compatibility, installation and rollback

## Separate a missing file from a dropped device OS

Read Apple's current [SDKs and system requirements](https://developer.apple.com/xcode/system-requirements/) for the **exact selected Xcode release**. Its Device Support column means supported on-device installation/debugging, not merely a list of bundled disk images. SDKs, deployment targets, simulator runtimes and physical-device support are different constraints.

Observed examples from that table on 2026-10-27:

| Xcode | Supported macOS | Physical-device iOS range |
| --- | --- | --- |
| 15.4 | Sonoma 14.x | iOS 12 or later |
| 16.4 | Sequoia 15.3 through Tahoe 26.1.x | iOS 15 or later |
| 27.1 | Tahoe 26.6 or later | iOS 17 or later |

1. If a connected iPhone runs below the selected Xcode's support range, identify an older Apple Xcode release **and compatible macOS host** that support it. For example, an iOS 13 phone falls outside Xcode 16.4's range even if a 13.x DDI archive exists. Copying that archive does not establish restored debugger/protocol support.
2. Keep the project's build requirements separate. A project may require a compiler/SDK newer than the toolchain that can debug the old phone; a remote/alternate compatible Mac may help, but an arbitrarily mixed compiler/debugger workflow is not guaranteed. Report incompatible constraints rather than claiming the image solves them.
3. If the device is within the toolchain's range and the actual error is a missing legacy support image, proceed to a reviewed support-file repair. Prefer images supplied by an authorized compatible Apple Xcode distribution. Treat a third-party copy into an unsupported combination as an explicitly unverified experiment, not a supported fix.

## Confirm the intended Xcode and connected-device state

Use the [command-line tools selection guidance](https://developer.apple.com/documentation/xcode/configuring-command-line-tools-settings) and the existing process environment. `DEVELOPER_DIR` overrides global selection for command-line tools; it does not switch an already open GUI Xcode instance. Verify both the CLI selection and the actual app the user opens.

```bash
xcode-select -p
xcodebuild -version
xcrun --find xcodebuild
```

If selecting another installed Xcode is required, prefer a process-scoped `DEVELOPER_DIR` ending in its `Contents/Developer` directory. Do not silently run `sudo xcode-select --switch` on a shared Mac. A Command Line Tools-only selection is not a full Xcode installation and has no iPhoneOS DeviceSupport directory.

Unlock the intended USB device and follow normal Trust/pairing prompts. On iOS 16+, enable [Developer Mode](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device) when required, including its on-device restart/confirmation. These are security decisions for the user, not settings the lookup helper changes. Old device OS versions do not have the same Developer Mode UI. Inspect the selected Xcode's Devices and Simulators or current Device Hub and installed tool help; do not assume CoreDevice discovers every legacy phone.

## Repository comparison and modern-image boundary

- [filsv at bae78cebf7d2453b77825d464ef2a015164aafd5](https://github.com/filsv/iOSDeviceSupport/tree/bae78cebf7d2453b77825d464ef2a015164aafd5) has 157 tree entries including ZIPs and some unpacked image/signature pairs; the highest numeric ZIP version observed is 16.6.
- [iGhibli at 3dd2d899550ddc253db40e6eabe145600d4bd773](https://github.com/iGhibli/iOS-DeviceSupport/tree/3dd2d899550ddc253db40e6eabe145600d4bd773) has 131 tree entries; archives are under `DeviceSupport/`, with extra exact-build and Xcode-provenance labels up through 16.4.
- The [filsv installer](https://github.com/filsv/iOSDeviceSupport/blob/bae78cebf7d2453b77825d464ef2a015164aafd5/scripts/install_device_support.sh) hardcodes Xcode.app, changes ownership/permissions and maps absent 16.7/16.8/16.9 names to 16.5 before renaming. Its README's 12.2 (16E5181e) link actually points to a 12.1 file. These are reasons to inspect actual trees and payloads, not execute its installer.
- The [iGhibli deploy script](https://github.com/iGhibli/iOS-DeviceSupport/blob/3dd2d899550ddc253db40e6eabe145600d4bd773/deploy.py) extracts multiple ZIPs by default; its version option is a substring filter, not an exact iPhone-build resolver. Archive filenames are compared with installed folder names before extraction, which does not guarantee no internal-folder overlap/overwrite. Do not run it as a blanket repair.
- iOS 17+ uses a different personalized development-image flow. The [libimobiledevice image-mounter implementation](https://github.com/libimobiledevice/libimobiledevice/blob/master/tools/ideviceimagemounter.c) explicitly distinguishes modern bundles containing a DMG, BuildManifest and Firmware from the old DMG/signature pair. Let a supported Xcode/CoreDevice prepare the device; neither archive contains a modern-image fix. The historical Xcode 14 `DVTEnableCoreDevice` workaround in filsv's README is not a general repair or Developer Mode toggle.

Use the separate selection reference for exact-build/version precedence and payload checks; filenames alone do not authenticate images or prove compatibility.

## Apply a narrowly authorized legacy repair

1. Finish staging and image/signature verification first. Record the exact selected Xcode developer directory, original DeviceSupport contents and proposed version/build folder. Obtain authorization for this specific Xcode modification and any required administrator access.
2. Close the intended Xcode instance and disconnect the phone. Resolve the destination from the verified full developer directory: `Platforms/iPhoneOS.platform/DeviceSupport/`. This is not the user-level `Library/Developer/Xcode/iOS DeviceSupport` cache and not a simulator runtime directory.
3. If the same-named destination already exists, stop and compare it. Do not merge or overwrite silently. If replacement is deliberately authorized, move only that version directory to a uniquely named private backup outside the lookup directory and record its exact path before adding anything.
4. Copy only the reviewed version directory containing the paired image/signature, with readable regular files, into the intended destination. Limit privilege to this one change; no recursive chown/chmod across Xcode, installer execution, signature bypass, or unrelated cache purge. Do not relabel an image to pretend it has a different OS/build.
5. Reopen that Xcode, reconnect/unlock/trust as needed and observe preparation status. Exercise the requested real-device install/launch/debug action. Record mount/preparation errors separately from signing, deployment-target and transport errors. A successful build or an image being present cannot establish debugger compatibility.

## Roll back and report

If the change fails or must be reverted, close the same Xcode, remove **only** the version directory added by this operation and restore the exact recorded backup if one was made. Inspect the path first; do not use broad wildcards or delete shared device caches. Reopen and verify the prior state.

No Mac/Xcode or accessible physical iPhone was available during skill verification. File lookup, downloads and archive identity/structure were exercised separately; copying, mounting, rollback and real-device debugging remain unexercised. Report that boundary explicitly.
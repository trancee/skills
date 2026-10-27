# Device identity and support-file selection

Resolve `scripts/` from this skill package, not the consumer project. The helper is standard-library Python 3.9+; GitHub HTTPS access is required for inventory. Live USB queries additionally require libimobiledevice's `idevice_id`, `ideviceinfo`, and working usbmuxd/USB access. It never pairs, installs, mounts, or modifies Xcode.

## Acquire the actual iPhone version and build

1. Select the physical device by UDID locally when several are connected. Keep UDIDs, serials, device names, network addresses and full information plists out of committed/public reports.
2. Prefer the selected Xcode's Devices and Simulators information or its installed `xcrun xcdevice`/`devicectl` help for platform-native discovery. Old iOS devices may be invisible to CoreDevice; libimobiledevice can query a paired USB device without relying on the current Xcode's support range.
3. Query once, preserving **both** `ProductVersion` and `BuildVersion`. The device's build is not the selected Xcode's build. For an already paired/unlocked device, installed `ideviceinfo -s -u UDID -x` returns a plist without auto-pairing. If access fails, follow the normal user-reviewed trust/pairing flow; do not silently create pair records or grant trust.
4. Capture an XML or binary plist privately if the lookup must run elsewhere. A reduced plist containing only ProductVersion, BuildVersion and optionally ProductType is sufficient. The helper accepts it through `--device-plist`; never infer the patch version from a model name or marketing major release.

The helper's no-argument mode enumerates USB devices with `idevice_id -l` and requires exactly one. It will not pick the first phone when several are present. Network devices are not implicitly selected.

## Run the lookup

```bash
python3 scripts/find-support.py
python3 scripts/find-support.py --udid ACTUAL-LOCAL-UDID
python3 scripts/find-support.py --device-plist path/to/private-device.plist
python3 scripts/find-support.py --ios-version 10.1 --build-version 14B72
```

Both inventories are searched by default. Restrict a source explicitly with `--source filsv` or `--source ighibli`. For reproducibility:

```bash
python3 scripts/find-support.py --ios-version 10.1 --build-version 14B72 \
  --filsv-ref bae78cebf7d2453b77825d464ef2a015164aafd5 \
  --ighibli-ref 3dd2d899550ddc253db40e6eabe145600d4bd773
```

Moving refs resolve once to immutable commits before inventorying; every artifact URL contains that commit. Output includes repository, label, matching class, path, byte size and Git blob SHA-1. Generic version matches do not establish device-build compatibility. These hashes identify repository content, not Apple authenticity. A GitHub API rate/network/schema/truncation error aborts selection rather than pretending the absent source had no match. No token is required for normal public access; if rate limited, wait or use a reviewed local inventory through code/tools instead of inferring absence.

## Match policy

| Condition | Result |
| --- | --- |
| iOS 17 or newer | Exit 3, `modern-personalized-route`; no legacy archive selected or fetched |
| Exact numeric iOS version plus standalone iOS build label | Highest-ranked candidates across both sources; exit 0 |
| Exact numeric version, no build/provenance annotation, release-looking device build | Lower-ranked version candidates; build explicitly unverified; exit 0 |
| Same version but Xcode/provenance-labelled archive | Manual-review candidates, not an exact device-build match |
| Missing exact patch but same major/minor generic file | Manual-review candidate only; exit 3 if nothing stronger exists |
| Prerelease-looking build without exact build evidence | Manual review; generic release files are not automatically promoted |
| Only a different build-labelled file, unrelated minor, or missing version | No automatic substitution; exit 3 |
| Device/plist/input/network/inventory failure | Actionable stderr; exit 2, no acceptance inferred |

Trailing numeric zeros normalize (`16.0.0` and `16.0`) without treating `16.0.1` as `16.0`. Build identifiers compare exactly and case-sensitively. A lowercase terminal build suffix is treated conservatively as prerelease-looking, not a complete release-channel classifier.

A label such as `16.4(FromXcode_14.3(14E222b))` describes an Xcode source; **14E222b must not be interpreted as the iPhone's iOS build**. Equally ranked files from different repositories remain separate candidates. Prefer a matching image from an authorized compatible Apple Xcode installation when available; otherwise review source provenance and compare actual payloads. Never choose by stars, lexicographic newest, or a filename's incidental timestamp.

## Verify the actual payload before using it

1. Review the [pinned filsv tree](https://github.com/filsv/iOSDeviceSupport/tree/bae78cebf7d2453b77825d464ef2a015164aafd5) and [pinned iGhibli tree](https://github.com/iGhibli/iOS-DeviceSupport/tree/3dd2d899550ddc253db40e6eabe145600d4bd773). Their READMEs and scripts are leads, not verified compatibility databases. Follow the helper's real tree paths, especially for spaces/parentheses.
2. Download only the chosen artifact(s) to a fresh owned staging directory over verified HTTPS. Preserve exact URLs, revision, byte sizes and a locally computed SHA-256. To compare with the reported Git SHA-1, hash `b"blob " + str(size).encode() + b"\0" + content`; an ordinary file SHA-1 is not a Git blob hash.
3. List archive entries before extraction. Reject absolute/traversal paths, symlinks, duplicate member names, unexpected executables, encrypted/oversized payloads and unrelated content. Ignore AppleDouble `__MACOSX`/`._` metadata rather than mistaking it for support files. Extract only the required reviewed regular files to staging, never directly into Xcode.
4. Require a nonempty `DeveloperDiskImage.dmg` and its nonempty `DeveloperDiskImage.dmg.signature` in the same version directory. Use both from the same package; never combine an image from one candidate with a signature from another. An archive name or internal folder can differ from its payload provenance; inspect available image metadata with trusted macOS tools before a compatibility claim.
5. A readable archive, hash match and present signature file establish packaging/content identity, **not** cryptographic authenticity or actual mount/debug success. Retain the device/Xcode compatibility gate and final physical-device verification.
6. If only a workaround such as copying 16.6 for a 16.7.x phone exists, report that exact substitution and evidence gap. Renaming a folder cannot change image contents or restore a dropped Xcode protocol stack; do not present it as the proper exact support file.

Source CLI semantics: [libimobiledevice ideviceinfo](https://github.com/libimobiledevice/libimobiledevice/blob/master/tools/ideviceinfo.c) and [idevice_id](https://github.com/libimobiledevice/libimobiledevice/blob/master/tools/idevice_id.c). For iOS 17+ image format contrast, see [ideviceimagemounter](https://github.com/libimobiledevice/libimobiledevice/blob/master/tools/ideviceimagemounter.c): modern bundles include a BuildManifest and Firmware, unlike the legacy image/signature pair.

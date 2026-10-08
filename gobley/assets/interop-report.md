# Gobley interop record

## Contract
- Gradle module and Cargo package/library target:
- Rust API and Kotlin package:
- Gobley plugins/bindgen, resolved UniFFI, Rust compiler/toolchain:
- Gradle/Kotlin/atomicfu/JDK; target NDK/Xcode/linker:
- Generation mode and configuration owner:
- Cargo profiles/features; debug/release selection:

## Target evidence
| Kotlin target / Rust triple | Build host | Task / exit | Actual call, error, lifecycle | Artifact / native dependencies | Status |
| --- | --- | --- | --- | --- | --- |

## Boundary evidence
- Result and typed-error assertions:
- Object close/ownership behavior:
- Async cancellation/runtime or custom-type round trips, if applicable:
- Generator/runtime checksum alignment:

## Packaging and consumers
- Android ABIs, minified release, JNA rules, 16 KB validation:
- JVM runtime classifier/resource entries and process architecture:
- Native static library/cinterop and deployment floors:
- Separate publication consumer resolution and actual calls:

## Limits
- Unverified hosts/architectures/device or release paths:
- Compatibility warnings and excluded unsupported targets:
- Disposable build outputs removed; sensitive information excluded:

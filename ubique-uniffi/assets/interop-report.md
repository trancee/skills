# Ubique UniFFI interop record

## Version and ownership
- Plugin/runtime/generator release and immutable source revision:
- Exact UniFFI versions from each selected Cargo.lock:
- Rust/Kotlin/Gradle/JDK/AGP/NDK/Xcode tuple:
- Module/crate/namespace/Kotlin package map:
- Generation mode and package configuration owner:

## Safety and composition
- Default allocator review, including dependencies/features:
- Shared-crate version alignment across modules:
- Shared object/record identity and round-trip evidence:
- Foreign-trait defining-module boundary:
- Runtime dependency ownership and generator alignment:

## Target verification
| Kotlin target / Rust triple | Host / build mode | Command / exit | Actual calls and errors | Packaged crate and runtime libraries | Status |
| --- | --- | --- | --- | --- | --- |

## API behavior
- Typed results/errors and panic handling:
- Object close/post-close/exception paths:
- Async/callback/custom/borrowed boundaries, if applicable:
- API checksum and contract-version policy:

## Packaging and limits
- Android ABIs, host tests, R8/native release behavior:
- Native commonization and published runtime cinterop identity:
- JVM resource prefixes and release cross-toolchain evidence:
- Separate publication consumer:
- Unverified paths and unavailable prerequisites:

---
name: aws-lc
description: "Builds, integrates, ports, tests, and troubleshoots AWS-LC cryptography and TLS libraries. Use for CMake source builds, libcrypto/libssl consumers, OpenSSL compatibility and linkage, cross-compilation, AWS-LC FIPS build and service-indicator boundaries, OpenSSL 3 provider integration, and release upgrades. Don't use for AWS KMS administration, application protocol design, blanket FIPS certification claims, or unrelated cryptographic libraries."
compatibility: "Source builds need CMake, C/C++ compilers, Perl, Go, and preferably Ninja; Windows assembly needs NASM. Provider builds need OpenSSL 3.5+ development headers/libraries. Target SDKs and toolchains are required for cross-compilation."
metadata:
  category: "cryptography"
  source: "https://github.com/aws/aws-lc"
  sourceVersion: "aws/aws-lc v5.12.0 @ cd481c207e38f06aeb5766f4a1cdfce10a4c0af8; AWS cryptography overview accessed 2026-11-01"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-11-01T13:40:34+01:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-11-01T13:40:34+01:00"
---

# AWS-LC

PATHS: resolve bundled `references/` and `assets/` from the activated skill directory. Resolve source/build/install paths separately in the target project.

## 1. Select the boundary and revision

1. CLASSIFY: source build | direct C/C++ integration | OpenSSL migration/upgrade | OpenSSL 3 provider | FIPS deployment requirement | cross-compilation.
2. RECORD the exact AWS-LC tag/commit, target OS/architecture, compiler, static/shared choice, install prefix, and consuming application's dependency graph. Preserve the project's existing pin; choose a reviewed release for a new integration and update it deliberately.
3. READ the selected revision's `BUILDING.md`, `INCORPORATING.md`, public headers, and release notes. The authored baseline is [v5.12.0](https://github.com/aws/aws-lc/releases/tag/v5.12.0), not a claim about the latest release. Read [the AWS overview](https://aws.amazon.com/security/opensource/cryptography/) for portfolio context, not build flags or validation authority.
4. FIPS requirement -> READ [references/fips.md](references/fips.md) **before choosing a source revision or compiler**. Direct API compatibility, a FIPS build, service approval, and CMVP validation are separate claims.
5. Source/toolchain/cross-compilation -> READ [references/build.md](references/build.md).
6. Direct linkage or migration/upgrade -> READ [references/integration.md](references/integration.md).
7. OpenSSL 3 fetch/provider APIs -> READ [references/provider.md](references/provider.md). Keep application translation units on OpenSSL's headers; direct AWS-LC linkage is a different arrangement.

DONE: selected route, immutable revision, toolchain, artifact layout, and required runtime behavior are explicit.

## 2. Build without changing the host crypto library

1. CONFIGURE out of tree with the selected toolchain and explicit `CMAKE_BUILD_TYPE`. Use a private install prefix; preserve the system OpenSSL and its configuration.
2. KEEP Go and Perl for complete code generation/tests and FIPS builds. If the consumer cannot depend on them, use the selected revision's pre-generated files and report reduced test coverage.
3. CHOOSE ordinary static/shared versus Linux/BSD distribution-packaging mode. The latter changes library names, header paths, pkg-config names, and ELF identity; use the matching consumer recipe.
4. BUILD, INSTALL into the private prefix, and record effective CMake options. Create a fresh build directory when changing compiler, architecture, revision, linkage mode, or FIPS settings.
5. For a read-only source tree, inspect `ENABLE_SOURCE_MODIFICATION` and generated-header behavior. Prefer a disposable source copy when configuring FIPS or version-dependent headers; installed headers must match the actual build.

DONE: real libraries and the appropriate public headers exist under the selected prefix, with no overwrite of the host's crypto installation.

## 3. Integrate and preserve semantics

1. DIRECT consumer -> compile and link against **one** selected header/library set. Migrate every affected caller; rebuild dependencies that embedded public structures. Use `OPENSSL_IS_AWSLC` for compile-time identity, not compatibility version numbers.
2. PROVIDER consumer -> keep OpenSSL's `libcrypto` in the application; load the AWS-LC module backed by isolated AWS-LC shared `libcrypto`. Assert the provider serving the actual operation; optional fetch preferences can fall back.
3. CHECK ownership, return codes, supported algorithms, trust/hostname verification, TLS versions/groups/ciphers, session behavior, and security-setting no-ops against the selected headers and consuming tests. A setter returning success is not evidence that its policy is enforced.
4. For updates spanning v5.12.0, apply the HPKE ownership/ABI, AES-XTS data-unit, reparsed-X509 metadata, RSA-PSS, and cipher-selector changes in `references/integration.md` where those APIs are used.
5. PRESERVE protocol requirements. If a required feature is absent, state the exact missing capability; do not weaken certificate checks, silently change algorithms, or invent a compatibility fallback.

DONE: all consuming targets use the intended API/ABI set, and required policy has observable enforcement rather than assumed compatibility.

## 4. Prove the running consumer

1. RUN upstream tests for the changed surface. The normal `run_tests` target includes native and Go/TLS-runner tests; a filtered native binary or `run_minimal_tests` is narrower coverage. Follow the selected source's paths and flags.
2. DIRECT integration -> READ [assets/CMakeLists.txt](assets/CMakeLists.txt) and [assets/smoke.c](assets/smoke.c); copy both into a disposable probe directory. Build against the actual install prefix and run with expected FIPS mode `0` or `1`. Require the SHA-256 and AES-GCM known answers, successful authenticated decryption, and modified-tag rejection. Fixed keys/nonces belong only to this probe, not production encryption.
3. PROVIDER integration -> READ [assets/provider-smoke.c](assets/provider-smoke.c); compile only against OpenSSL and run against the module directory. Require `provider=awslc` and the SHA2-256 known answer; exercise the real required algorithm separately because this baseline provider serves SHA-2 digests only.
4. INSPECT the real executable/module's link map or loader resolution, not only build flags. Shared -> verify dependencies/rpath and actual resolved AWS-LC paths; static -> verify AWS-LC-specific symbols/runtime version. System OpenSSL may report compatibility version `1.1.1` in pkg-config, so that number is not identity proof.
5. TLS changes -> run a local handshake and data exchange with the actual consumer, plus relevant trust/hostname/algorithm failure paths. A crypto probe does not establish TLS deployment correctness.
6. FIPS -> verify runtime build identity **and successful operation approval** as described in `references/fips.md`; retain the independent certificate/security-policy match. Label unsupported environments and unexercised cross-platform paths explicitly.

DONE: the final consumer executes the requested operation using the intended implementation, passes relevant failure paths, and the evidence names the exact revision/build and coverage limits.

## Error Handling

- Missing Go/Perl or generation failure -> verify the selected revision's required versions and `GO_EXECUTABLE`/`PERL_EXECUTABLE`; inspect the first failing command. FIPS requires both tools.
- Headers found but symbols missing/wrong runtime identity -> inspect include precedence, cached CMake/pkg-config discovery, static link order, and loader paths. Reconfigure a fresh consumer build against the explicit prefix.
- Distribution build cannot find `-lcrypto` or `openssl/*.h` -> select native suffixed paths, or enable the upstream OpenSSL shim deliberately in the private prefix. Do not point the linker at the system library to make it pass.
- Provider load/fetch fails -> verify OpenSSL 3.5+ headers/runtime, shared build, module directory, required algorithm registration, and `libcrypto-awslc` loader resolution.
- Port compiles but policy fails -> inspect no-op APIs/default differences in the exact revision; reproduce with the required behavioral assertion before choosing a supported implementation.
- FIPS integrity/self-test failure -> preserve the failed artifact and build diagnostics; rebuild under the applicable policy. Integrity-bypass or break-test builds are diagnostic artifacts, not deployable compliance fixes.

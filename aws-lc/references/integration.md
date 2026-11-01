# Direct linkage, OpenSSL migration, and upgrades

Sources: [INCORPORATING.md](https://github.com/aws/aws-lc/blob/v5.12.0/INCORPORATING.md), [PORTING.md](https://github.com/aws/aws-lc/blob/v5.12.0/PORTING.md), [functionality differences](https://github.com/aws/aws-lc/blob/v5.12.0/docs/porting/functionality-differences.md), [configuration differences](https://github.com/aws/aws-lc/blob/v5.12.0/docs/porting/configuration-differences.md), and [public headers](https://github.com/aws/aws-lc/tree/v5.12.0/include/openssl). Headers at the selected pin resolve stale prose: this baseline's porting guide contains inherited BoringSSL descriptions and older ABI guidance alongside newer distribution packaging.

## 1. Establish one header/library set

1. INVENTORY direct and transitive consumers of `openssl/*.h`, libcrypto/libssl, FFI bindings, plugins, and embedded public structures. Recompile the whole affected graph; AWS-LC is not an ABI-compatible binary replacement for OpenSSL.
2. Ordinary install -> headers at `<prefix>/include/openssl`, libraries `crypto` and `ssl`. Dist package -> headers at `<prefix>/include/aws-lc/openssl`, libraries `crypto-awslc` and `ssl-awslc`. Static order is application objects, ssl, crypto, system thread dependencies.
3. Preserve the project's build convention. If it uses `find_package(OpenSSL)`, pass `OPENSSL_ROOT_DIR` with a private ordinary install or deliberate dist-package shim; inspect actual `OPENSSL_INCLUDE_DIR`, `OPENSSL_CRYPTO_LIBRARY`, and `OPENSSL_SSL_LIBRARY` after configuration. Cached discovery and pkg-config hints can select the system implementation instead.
4. For an explicit-prefix disposable proof, copy `assets/CMakeLists.txt` and `assets/smoke.c` from the skill into a probe directory, then run:

```bash
cmake -S probe -B probe-build -GNinja \
  -DAWSLC_PREFIX="$AWSLC_PREFIX" -DCMAKE_BUILD_TYPE=Release
cmake --build probe-build
./probe-build/awslc-smoke 0
```

Dist mode -> add `-DAWSLC_DIST_PKG=ON`. Shared Windows -> add `-DAWSLC_WINDOWS_SHARED=ON` and supply the matching DLL at runtime. FIPS build -> expect `1` instead of `0`. Crypto-only consumers can drop the asset's ssl discovery/link: the probe exercises libcrypto, not TLS. Use a new probe build directory when switching prefixes/linkage modes. The asset's `NO_DEFAULT_PATH` discovery and `OPENSSL_IS_AWSLC` compile gate reject accidental fallback.

## 2. pkg-config and loader boundaries

Ordinary or dist-shim interface:

```bash
export PKG_CONFIG_PATH="$AWSLC_PREFIX/lib/pkgconfig"
cc $(pkg-config --cflags libssl) app.c \
  $(pkg-config --libs --static libssl libcrypto) -o app
```

Native dist interface -> substitute `libssl-awslc` and `libcrypto-awslc`. Shared linking -> omit `--static`; configure an intentional runtime loader path. `PKG_CONFIG_PATH` adds precedence but still permits system modules; inspect the emitted include/library flags. pkg-config's reported `1.1.1` is the OpenSSL compatibility value, not the AWS-LC release identity.

- Linux shared -> inspect `readelf -d app` and loader resolution (`ldd` for trusted local binaries). Require selected-prefix crypto paths/expected SONAMEs and rpath/runpath. An rpath is not proof if a conflicting loaded library interposes symbols.
- macOS shared -> inspect `otool -L` and the actual runtime library identities.
- Static -> crypto libraries may be absent from dynamic dependencies. Use `nm`/link map for AWS-LC-specific symbols, and print `awslc_version_string()` or `OpenSSL_version(OPENSSL_VERSION)` at runtime.
- Distribution packaging supplies versioned SONAMEs/ELF symbols; it does not make AWS-LC ABI-compatible with OpenSSL or make every AWS-LC release pair safe for public structs.

## 3. Migrate behavior, not just compilation

1. Use `OPENSSL_IS_AWSLC` for implementation branches. Preserve opaque types with accessors and `*_up_ref`; respect `size_t` length/index APIs and range-check narrowing at application boundaries.
2. Check ownership in the selected headers, especially parse/reuse, set0/set1, get0/get1, and externally allocated objects. Avoid code that assumes exact OpenSSL function/reason codes; handle actual API outcomes and retain diagnostic error stacks.
3. Search consumers of cipher/group/protocol/verification/security-level setters. Require the corresponding desired behavior in tests. Baseline examples: `SSL_CTX_set_security_level` is a no-op, its getter returns zero, FFDH TLS cipher suites are absent, TLS server/DTLS renegotiation is unsupported, and TLS 1.3 post-handshake authentication is not supplied by compatibility setters.
4. System crypto policy is opt-in via `ENABLE_CRYPTO_POLICIES=ON`, best-effort, and can be overridden by application setters. It drops `@SECLEVEL=N`; missing/unsupported directives may leave built-in defaults. It is not a strict replacement for required application policy. Read exact policy parsing/defaults before claiming equivalence.
5. Prefer maintained high-level EVP/AEAD APIs where supported; check success before consuming output. Keep production AEAD nonces unique under each key, authenticate required associated data, and discard unauthenticated plaintext on failure. Preserve the protocol's required algorithms and key formats.
6. TLS consumer -> explicitly test trusted and untrusted chains, hostname match/mismatch, configured versions/groups/ciphers, application-data exchange, and required resumption/client-auth behavior. Upstream library tests do not prove application trust configuration.

## 4. v5.12.0 upgrade gate

Read [the release notes](https://github.com/aws/aws-lc/releases/tag/v5.12.0) and selected [HPKE header](https://github.com/aws/aws-lc/blob/v5.12.0/include/openssl/hpke.h).

- `EVP_HPKE_KEY` now owns heap key material; its 64-bit size shrank from 4808 bytes in v5.9.0–v5.11.0 to 72. **v5.12.0 headers against those older libraries can overwrite the smaller object.** Upgrade headers/libraries/callers together, including FFI layouts.
- Release live material with `EVP_HPKE_KEY_cleanup` before init/generate/copy into the same destination and on completion. Cleanup requires a zeroed or initialized object. Use `EVP_HPKE_KEY_copy` or `EVP_HPKE_KEY_move`; struct assignment/`memcpy` duplicates ownership and can double-free/use-after-free. Move destinations must be zeroed/initialized. `EVP_HPKE_MAX_EXPANDED_PRIVATE_KEY_LENGTH` was removed.
- AES-XTS accepts one complete data unit per operation. Repeated non-empty calls on an already-used context fail; reinitialize with a key or IV for the next unit. All-NULL reinit does not reset state.
- Reparsing an existing X509 clears `ex_data` and auxiliary metadata and invokes free callbacks; reattach application metadata if needed.
- Restricted RSA-PSS AUTO verification enforces the key's minimum salt length.
- The `SHA256` cipher-list selector matches HMAC-SHA256 suites, no longer AEAD/SHA1 suites; assert the actual negotiated/permitted list if the consumer uses it.
- X509 verification rejects a fixed blocklist of certificate SPKI digests; preserve this rejection rather than bypassing verification for a failing chain.

DONE: updated callers obey the selected ownership/API contracts, header/library identities match, and affected consumer-visible acceptance and rejection behavior is exercised.

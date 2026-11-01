# OpenSSL 3 provider integration

Sources: [provider README](https://github.com/aws/aws-lc/blob/v5.12.0/provider/README.md), [algorithm support](https://github.com/aws/aws-lc/blob/v5.12.0/provider/ALGORITHM_SUPPORT.md), and [provider CMake](https://github.com/aws/aws-lc/blob/v5.12.0/provider/CMakeLists.txt).

## 1. Choose the correct linkage arrangement

1. KEEP the application compiled/linked against real OpenSSL 3.5+ and its provider APIs. The module's frontend uses OpenSSL headers; its backend uses AWS-LC headers and links AWS-LC shared libcrypto. Those header sets cannot coexist in one translation unit.
2. CHECK exact algorithm availability before selecting this route. The v5.12.0 provider registers SHA-2 digests (224, 256, 384, 512, 512/224, 512/256), **not ciphers, signatures, KEMs, KDFs, MACs, key exchange, key management, or RNGs**. Replacing the TLS/crypto implementation wholesale requires a different integration or later proven provider coverage.
3. Pin the OpenSSL runtime and development headers consistently. `BUILD_AWSLC_PROVIDER` requires shared libraries and OpenSSL 3.5+; `OPENSSL_ROOT_DIR` here names **OpenSSL's** install prefix, not AWS-LC's.

## 2. Build/install into a private Linux prefix

```bash
cmake -S aws-lc-src -B aws-lc-provider-build -GNinja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
  -DENABLE_DIST_PKG=ON -DBUILD_AWSLC_PROVIDER=ON \
  -DOPENSSL_ROOT_DIR="$OPENSSL_PREFIX" \
  -DCMAKE_INSTALL_PREFIX="$AWSLC_PREFIX" -DCMAKE_INSTALL_LIBDIR=lib
cmake --build aws-lc-provider-build --parallel "$JOBS"
cmake --install aws-lc-provider-build
```

System OpenSSL 3.5+ development packages -> omit `OPENSSL_ROOT_DIR`. Default module install directory is `<prefix>/lib/ossl-modules`; setting `AWSLC_PROVIDER_MODULESDIR` selects another destination deliberately. Keep this private rather than modifying the host OpenSSL modules/configuration.

Upstream installed-provider guidance requires distribution mode's suffixed SONAME and symbol versioning to keep module references off OpenSSL's libcrypto. Installation is documented for Linux; other supported platforms run from the build tree (`provider/awslc.so`, or `awslc.dylib` on macOS). Verify actual platform support and loader behavior at the chosen revision.

## 3. Prove the module and serving provider

1. RUN `provider/awslc_provider_test` (public OpenSSL EVP/provider frontend) and `provider/awslc_provider_backend_test` (AWS-LC-only backend) from the build. The frontend binary exercises the arrangement used by applications; a backend-only pass is insufficient.
2. Linux -> inspect the installed module's dynamic dependencies and actual loader resolution. It must bind its cryptographic backend to `libcrypto-awslc.so.1` from the selected prefix, not OpenSSL's `libcrypto.so.3`. Set an appropriate process-local loader path if no rpath covers the install:

```bash
LD_LIBRARY_PATH="$AWSLC_PREFIX/lib" ldd "$AWSLC_PREFIX/lib/ossl-modules/awslc.so"
```

3. READ/copy `assets/provider-smoke.c` from the skill into a disposable probe directory. Compile using the application's OpenSSL headers/libcrypto, then run against the module directory. For a system OpenSSL installation:

```bash
cc provider-smoke.c -lcrypto -o provider-smoke
LD_LIBRARY_PATH="$AWSLC_PREFIX/lib" ./provider-smoke "$AWSLC_PREFIX/lib/ossl-modules"
```

For a private OpenSSL install, use its include/link/loader paths too, while preserving AWS-LC's native suffixed backend library. Require the digest vector and `provider=awslc`; the probe does not enable FIPS enforcement.

4. Query registrations through the matching OpenSSL CLI:

```bash
LD_LIBRARY_PATH="$AWSLC_PREFIX/lib" openssl list -digest-algorithms \
  -provider-path "$AWSLC_PREFIX/lib/ossl-modules" -provider awslc
```

A listed algorithm or loaded provider is weaker evidence than a successful fetch/operation with identity asserted. The application's `OpenSSL_version()` still identifies its OpenSSL library; that is expected in the provider arrangement.

## 4. Make fallback policy explicit

- `EVP_MD_fetch(ctx, "SHA2-256", "provider=awslc")` requires AWS-LC for the requested implementation.
- `?provider=awslc` is an optional preference. With the default provider loaded, unsupported fetches can fall back. Assert `OSSL_PROVIDER_get0_name(EVP_MD_get0_provider(md))` when the requirement is AWS-LC execution.
- Use a private `OSSL_LIB_CTX` or process-local `OPENSSL_CONF` for evaluation; leave global OpenSSL configuration unchanged. Load the default provider only when fallback is intended.
- FIPS requirement -> apply the policy/module-match gate in `references/fips.md`, fetch approved-only implementations with `fips=yes` as needed, and verify completed-operation approval. A preference allowing default-provider fallback cannot establish AWS-LC FIPS enforcement.

DONE: application/OpenSSL and module/AWS-LC identities are separated and proven, the real required algorithm is served by the selected provider, and fallback/approval behavior matches the request.

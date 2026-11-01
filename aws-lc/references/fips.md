# FIPS build, operation approval, and validation authority

Primary sources: [selected FIPS.md](https://github.com/aws/aws-lc/blob/v5.12.0/crypto/fipsmodule/FIPS.md), [CMake checks](https://github.com/aws/aws-lc/blob/v5.12.0/CMakeLists.txt), [crypto.h](https://github.com/aws/aws-lc/blob/v5.12.0/include/openssl/crypto.h), and [service_indicator.h](https://github.com/aws/aws-lc/blob/v5.12.0/include/openssl/service_indicator.h). Use the module's own source and security policy for a validation-dependent deployment, not a mainline example.

## 1. Match the authority before building

1. IDENTIFY whether the request means a development FIPS-enabled build, runtime approved-service enforcement, or deployment under a particular CMVP validation. Record separate evidence for each.
2. Validation-dependent -> select the exact module/version and static/dynamic form, retrieve its current [CMVP certificate](https://csrc.nist.gov/projects/cryptographic-module-validation-program/validated-modules/search) and security policy, and map requirements to source revision, operational environment, compiler/toolchain, installation, initialization, entropy, algorithms, parameters, and operating procedures.
3. Example authority only: [certificate #5314](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/5314) identifies AWS-LC 3 Cryptographic Module (static), has approved-mode and Security Policy section 11.1 conditions, and links [its policy](https://csrc.nist.gov/CSRC/media/projects/cryptographic-module-validation-program/documents/security-policies/140sp5314.pdf). This is not authority for an arbitrary v5.12.0 shared build. Select the certificate that actually matches the required module/form/environment; recheck status and caveats at use time.
4. Keep CAVP/ACVP algorithm test results, CMVP module validation, and formal-verification claims distinct. A successful mainline `-DFIPS=1` build or known-answer test does not establish any deployment's certification/compliance. Resolve unsupported deployment claims with the policy owner/compliance specialist rather than asserting a match.

DONE: the requested claim and, when needed, certificate/security-policy/source/environment correspondence are recorded. If the correspondence is missing, continue reachable development work but mark validation applicability unresolved.

## 2. Build a distinct FIPS artifact

Development example; use the source/toolchain/options mandated by the applicable policy for a validated deployment:

```bash
cmake -S aws-lc-src -B aws-lc-fips-build -GNinja \
  -DFIPS=1 -DBUILD_SHARED_LIBS=ON -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$AWSLC_FIPS_PREFIX" \
  -DCMAKE_INSTALL_LIBDIR=lib
cmake --build aws-lc-fips-build --parallel "$JOBS"
cmake --install aws-lc-fips-build
```

- Baseline FIPS configuration requires Go **and** Perl; CPU-jitter entropy opt-out is rejected.
- Static FIPS is Linux-only per baseline CMake guards. Windows FIPS requires shared Release; inspect the chosen revision's platform checks and policy for other environments. Do not infer a validated macOS path from source supporting a shared-build mechanism.
- Source-generated headers, library build mode, and runtime identity must agree. Keep separate source copies/build directories/prefixes from ordinary builds.
- Preserve the build's integrity-hash injection and self-test mechanisms. Baseline ASan/MSan paths do not perform the normal FIPS integrity arrangement; sanitizer or `BORINGSSL_FIPS_BREAK_TESTS` builds are diagnostic only. Do not disable integrity checks to deploy a failed artifact.
- Run upstream FIPS-specific tests with `run_tests` when available and the consumer operation separately. A scoped smoke does not cover every self-test, entropy path, or policy requirement.

## 3. Verify successful approved operations at runtime

1. CHECK `FIPS_mode()==1`, runtime version/module identity, and the actual linked prefix. `FIPS_version()` is a module-family identifier independent of the AWS-LC release; it is zero in non-FIPS builds. None of these alone proves certificate applicability or per-operation approval.
2. CHECK both the operation's return value and approval. AWS-LC allows approved **and non-approved** algorithms/parameter combinations; mode alone does not reject all non-approved operations.
3. READ the installed `service_indicator.h`. The counter is per-thread; sample immediately around exactly the relevant service on that same thread. Keep other cryptographic operations out of the bracket. APIs return `uint64_t`; compare values for inequality, not a monotonic `after > before`, because rollover is possible.

```c
uint64_t before = FIPS_service_indicator_before_call();
int ok = EVP_Digest(input, input_len, output, &output_len, EVP_sha256(), NULL);
uint64_t after = FIPS_service_indicator_after_call();
int approved = ok && FIPS_mode() == 1 && before != after;
```

This illustrates a SHA-256 service, not blanket algorithm/parameter approval. Follow the applicable policy and selected headers for the completion point of multipart/other operations.

4. Upstream recommends `CALL_SERVICE_AND_CHECK_APPROVED`; inspect its exact implementation. In non-FIPS builds this baseline macro unconditionally assigns `AWSLC_APPROVED` for compatibility. Therefore its value cannot establish that the binary is a FIPS build. Gate enforcement on actual runtime FIPS identity as well; the bundled direct probe uses the public 64-bit counters and checks the operation result.
5. For production enforcement, withhold output/transition on a failed operation or non-approved service according to the application's required policy. Do not label plaintext, signatures, or derived keys approved merely because some neighboring call incremented the counter.

## 4. Provider FIPS is another layer

The OpenSSL provider exposes `fips=yes` only for implementations it can approve when its linked AWS-LC reports FIPS mode. Strict approved-only fetches must request it; per-operation checks use the provider's completed-operation `fips-indicator` and applicable callback behavior. Loading a provider or seeing status `active` is not service approval. Verify both module linkage and algorithm/parameter operation results. The provider at the authored baseline serves SHA-2 digests, not all AWS-LC cryptography.

Source: [provider FIPS behavior](https://github.com/aws/aws-lc/blob/v5.12.0/provider/README.md). The provider is not an independently validated replacement for a missing module/security-policy match.

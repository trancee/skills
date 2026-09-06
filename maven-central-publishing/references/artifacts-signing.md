# Artifacts, POM metadata, signing, and bundle layout

## Component file set

For each `groupId:artifactId:version`, generate:

- Primary artifact (`.jar`, `.aar`, `.pom`, or other supported packaging).
- POM.
- Sources JAR for non-`pom` components unless current Central rules exempt it.
- Javadoc JAR for non-`pom` components unless current Central rules exempt it.
- Detached ASCII-armored PGP signature (`.asc`) for every artifact and POM.
- Required `.md5` and `.sha1` checksum for every uploaded artifact/signature/POM.
- Optional `.sha256` and `.sha512` where supported by the route/tool.

Do not sign checksum files. Do not upload local Maven metadata unless the selected Central route explicitly requires it.

For Kotlin/Android/KMP, verify every publication separately. A root metadata publication, JVM/Android artifact, sources/Javadoc artifacts, and native variants have distinct coordinates/files. Route KMP topology to `kotlin-multiplatform` and API documentation generation to `dokka`.

## Maven layout

Map dots in `groupId` to directories:

```text
com.example:widget:1.2.3

com/example/widget/1.2.3/
  widget-1.2.3.jar
  widget-1.2.3.jar.asc
  widget-1.2.3.jar.md5
  widget-1.2.3.jar.sha1
  widget-1.2.3.pom
  widget-1.2.3.pom.asc
  widget-1.2.3.pom.md5
  widget-1.2.3.pom.sha1
  widget-1.2.3-sources.jar
  widget-1.2.3-sources.jar.asc
  widget-1.2.3-sources.jar.md5
  widget-1.2.3-sources.jar.sha1
  widget-1.2.3-javadoc.jar
  widget-1.2.3-javadoc.jar.asc
  widget-1.2.3-javadoc.jar.md5
  widget-1.2.3-javadoc.jar.sha1
```

Bundle the repository tree itself, not an extra enclosing directory. Multiple complete components may share one deployment bundle. The documented Portal bundle maximum was 1 GB when inspected; refresh the current limit before upload.

## POM requirements

Generate POM metadata from one project source of truth:

- `groupId`, `artifactId`, `version`, and packaging.
- Human-readable `name`.
- Nonempty `description`.
- Project `url`.
- At least one license with name, URL, and distribution.
- At least one developer with stable identity/name and appropriate contact/organization fields.
- SCM connection, developer connection, and browsable URL.
- Dependencies and scopes reflecting the published API/runtime contract.

Resolve property placeholders in the generated POM. Verify every module's final POM, not only build-script declarations.

## Version and coordinate invariants

Release:

- Version is immutable and does not end in `-SNAPSHOT`.
- Coordinate is inside a verified namespace.
- The exact coordinate/version has never been published.
- Every module in the deployment intentionally shares or differs in version according to project policy.

Snapshot:

- Version ends in `-SNAPSHOT`.
- Route targets the dedicated Central snapshot repository.
- Namespace snapshot publishing is enabled.
- Consumers accept mutable timestamped resolution and current retention cleanup.

Never send snapshots and releases through the same repository definition merely by changing credentials.

## PGP signing

1. Use a durable signing key controlled by the publisher and accepted by current Central requirements.
2. Publish/distribute the public key according to Central's current guidance before release.
3. Verify fingerprint, UID, expiry, revocation state, and signing capability.
4. Generate detached ASCII-armored signatures over the exact uploaded bytes.
5. Verify each signature locally against the intended public key.
6. Keep private key material and passphrase in an approved secret store; avoid command arguments and debug logs.

Build reproducibility and PGP signatures are separate properties. Rebuilding after signing changes bytes and requires new signatures/checksums.

## Deterministic local validation

Before upload:

1. Enumerate files by relative Maven path.
2. Reject duplicates, path traversal, absolute paths, symlinks, and unexpected roots.
3. Match each artifact with its POM, `.asc`, `.md5`, and `.sha1` companions.
4. Verify checksums and PGP signatures.
5. Parse POM XML securely; reject external entities and unresolved required values.
6. Confirm namespace, release/snapshot version, and file naming.
7. Scan names/content for credential files, private keys, tokens, local paths, and unintended repository metadata.
